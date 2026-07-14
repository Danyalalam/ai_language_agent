"""Bridge between a browser WebSocket and the Azure VoiceLive realtime API.

Unlike ``german_voice_agent.py`` (a local CLI that captures/plays audio with
PyAudio on the host machine), this module runs on the server as a relay: the
browser captures the microphone and plays the response, while FastAPI shuttles
audio and control events between the browser WebSocket and the Azure VoiceLive
WebSocket.

Wire protocol with the browser (see ``frontend/src/services/voiceLiveClient.ts``):

  Browser -> Server
    - binary frames: raw PCM16 mono @ 24 kHz microphone audio.

  Server -> Browser
    - binary frames: raw PCM16 mono @ 24 kHz audio to play back.
    - text frames (JSON): {"type": "status", "state": ...} and other events
      such as {"type": "speech_started"} (barge-in), {"type": "error", ...}.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Union

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.identity import DefaultAzureCredential
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AzureStandardVoice,
    InputAudioFormat,
    Modality,
    OutputAudioFormat,
    RequestSession,
    ServerEventType,
    ServerVad,
)
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.config import settings

logger = logging.getLogger(__name__)


def _build_credential() -> Union[AzureKeyCredential, TokenCredential]:
    """Prefer an API key when configured, otherwise fall back to Azure AD."""
    if settings.azure_voicelive_api_key:
        return AzureKeyCredential(settings.azure_voicelive_api_key)
    return DefaultAzureCredential()


def _build_voice() -> Union[AzureStandardVoice, str]:
    """Azure neural voices contain a locale prefix (e.g. de-DE-KatjaNeural);
    OpenAI voices (alloy, echo, ...) are passed through as plain strings."""
    voice = settings.azure_voicelive_voice
    if "-" in voice:
        return AzureStandardVoice(name=voice)
    return voice


class VoiceLiveBridge:
    """Relays one browser conversation session to Azure VoiceLive."""

    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.connection = None
        self._closed = False

    async def _send_json(self, payload: dict) -> None:
        if self.ws.application_state == WebSocketState.CONNECTED:
            await self.ws.send_json(payload)

    async def _send_status(self, state: str) -> None:
        await self._send_json({"type": "status", "state": state})

    async def run(self) -> None:
        """Open the Azure connection and pump audio in both directions."""
        credential = _build_credential()
        logger.info(
            "Opening VoiceLive bridge (model=%s, voice=%s)",
            settings.azure_voicelive_model,
            settings.azure_voicelive_voice,
        )

        try:
            async with connect(
                endpoint=settings.azure_voicelive_endpoint,
                credential=credential,
                model=settings.azure_voicelive_model,
                connection_options={
                    "max_msg_size": 10 * 1024 * 1024,
                    "heartbeat": 20,
                    "timeout": 20,
                },
            ) as connection:
                self.connection = connection
                await self._setup_session()
                await self._send_status("connected")

                # Browser -> Azure and Azure -> browser run concurrently. When
                # either finishes (disconnect or error) we tear the other down.
                uplink = asyncio.create_task(self._pump_browser_to_azure())
                downlink = asyncio.create_task(self._pump_azure_to_browser())
                done, pending = await asyncio.wait(
                    {uplink, downlink}, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    exc = task.exception()
                    if exc and not isinstance(exc, WebSocketDisconnect):
                        raise exc

        except WebSocketDisconnect:
            logger.info("Browser disconnected from VoiceLive bridge")
        except Exception as exc:  # noqa: BLE001 - surface any error to the client
            logger.exception("VoiceLive bridge error")
            await self._send_json({"type": "error", "message": str(exc)})
        finally:
            self._closed = True

    async def _setup_session(self) -> None:
        session_config = RequestSession(
            modalities=[Modality.TEXT, Modality.AUDIO],
            instructions=settings.azure_voicelive_instructions,
            voice=_build_voice(),
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            turn_detection=ServerVad(
                threshold=0.5, prefix_padding_ms=300, silence_duration_ms=500
            ),
        )
        assert self.connection is not None
        await self.connection.session.update(session=session_config)
        logger.info("VoiceLive session configuration sent")

    async def _pump_browser_to_azure(self) -> None:
        """Forward raw PCM16 mic frames from the browser to Azure."""
        assert self.connection is not None
        while not self._closed:
            message = await self.ws.receive()

            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))

            audio_bytes = message.get("bytes")
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                await self.connection.input_audio_buffer.append(audio=audio_b64)
                continue

            # Text frames from the browser are reserved for future control
            # messages; ignore anything we don't recognise for now.

    async def _pump_azure_to_browser(self) -> None:
        """Forward VoiceLive events (audio + status) to the browser."""
        assert self.connection is not None
        async for event in self.connection:
            if event.type == ServerEventType.SESSION_UPDATED:
                await self._send_status("ready")

            elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                # Barge-in: user started talking over the assistant. Tell the
                # browser to drop queued audio and cancel the current response.
                await self._send_json({"type": "speech_started"})
                await self._send_status("listening")
                try:
                    await self.connection.response.cancel()
                except Exception as exc:  # noqa: BLE001
                    logger.debug("No response to cancel: %s", exc)

            elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                await self._send_status("processing")

            elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
                # The SDK already decodes the base64 wire format: event.delta is
                # raw PCM16 bytes (same value the CLI writes straight to PyAudio).
                # Forward it to the browser as-is.
                await self.ws.send_bytes(event.delta)

            elif event.type == ServerEventType.RESPONSE_AUDIO_DONE:
                await self._send_status("ready")

            elif event.type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE:
                transcript = getattr(event, "transcript", None)
                if transcript:
                    await self._send_json(
                        {"type": "transcript", "role": "assistant", "text": transcript}
                    )

            elif event.type == ServerEventType.ERROR:
                await self._send_json(
                    {"type": "error", "message": event.error.message}
                )


async def run_voicelive_bridge(websocket: WebSocket) -> None:
    """Entry point used by the FastAPI WebSocket route."""
    await VoiceLiveBridge(websocket).run()
