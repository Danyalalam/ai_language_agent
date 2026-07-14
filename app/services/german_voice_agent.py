from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import queue
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, TYPE_CHECKING, Union, cast

try:
    import pyaudio
except ImportError:
    print("This sample requires pyaudio. Install with: pip install pyaudio")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Note: python-dotenv not installed. Using existing environment variables.")

    def load_dotenv(*_args, **_kwargs):  # type: ignore[no-redef]
        return False

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
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

if TYPE_CHECKING:
    from azure.ai.voicelive.aio import VoiceLiveConnection


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles real-time audio capture and playback for the voice assistant."""

    def __init__(self, connection: "VoiceLiveConnection"):
        self.connection = connection
        self.audio = pyaudio.PyAudio()

        # Audio configuration - PCM16, 24kHz, mono as specified
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk_size = 1024

        # Capture and playback state
        self.is_capturing = False
        self.is_playing = False
        self.input_stream = None
        self.output_stream = None

        # Audio queues and threading
        self.audio_queue: "queue.Queue[bytes]" = queue.Queue()
        self.audio_send_queue: "queue.Queue[str]" = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.capture_thread: Optional[threading.Thread] = None
        self.playback_thread: Optional[threading.Thread] = None
        self.send_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info("AudioProcessor initialized with 24kHz PCM16 mono audio")

    async def start_capture(self):
        """Start capturing audio from microphone."""
        if self.is_capturing:
            return

        self.loop = asyncio.get_running_loop()
        self.is_capturing = True

        try:
            self.input_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            self.input_stream.start_stream()

            self.capture_thread = threading.Thread(target=self._capture_audio_thread, daemon=True)
            self.capture_thread.start()

            self.send_thread = threading.Thread(target=self._send_audio_thread, daemon=True)
            self.send_thread.start()

            logger.info("Started audio capture")
        except Exception as exc:
            logger.error("Failed to start audio capture: %s", exc)
            self.is_capturing = False
            raise

    def _capture_audio_thread(self):
        """Audio capture thread - runs in background."""
        while self.is_capturing and self.input_stream:
            try:
                audio_data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                if audio_data and self.is_capturing:
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    self.audio_send_queue.put(audio_base64)
            except Exception as exc:
                if self.is_capturing:
                    logger.error("Error in audio capture: %s", exc)
                break

    def _send_audio_thread(self):
        """Audio send thread - handles async operations from sync thread."""
        while self.is_capturing:
            try:
                audio_base64 = self.audio_send_queue.get(timeout=0.1)
                if audio_base64 and self.is_capturing and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.connection.input_audio_buffer.append(audio=audio_base64),
                        self.loop,
                    )
            except queue.Empty:
                continue
            except Exception as exc:
                if self.is_capturing:
                    logger.error("Error sending audio: %s", exc)
                break

    async def stop_capture(self):
        """Stop capturing audio."""
        if not self.is_capturing:
            return

        self.is_capturing = False

        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None

        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)

        if self.send_thread:
            self.send_thread.join(timeout=1.0)

        while not self.audio_send_queue.empty():
            try:
                self.audio_send_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Stopped audio capture")

    async def start_playback(self):
        """Initialize audio playback system."""
        if self.is_playing:
            return

        self.is_playing = True

        try:
            self.output_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk_size,
            )

            self.playback_thread = threading.Thread(target=self._playback_audio_thread, daemon=True)
            self.playback_thread.start()

            logger.info("Audio playback system ready")
        except Exception as exc:
            logger.error("Failed to initialize audio playback: %s", exc)
            self.is_playing = False
            raise

    def _playback_audio_thread(self):
        """Audio playback thread - runs in background."""
        while self.is_playing:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                if audio_data and self.output_stream and self.is_playing:
                    self.output_stream.write(audio_data)
            except queue.Empty:
                continue
            except Exception as exc:
                if self.is_playing:
                    logger.error("Error in audio playback: %s", exc)
                break

    async def queue_audio(self, audio_data: bytes):
        if self.is_playing:
            self.audio_queue.put(audio_data)

    async def stop_playback(self):
        if not self.is_playing:
            return

        self.is_playing = False

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None

        if self.playback_thread:
            self.playback_thread.join(timeout=1.0)

        logger.info("Stopped audio playback")

    async def cleanup(self):
        await self.stop_capture()
        await self.stop_playback()

        if self.audio:
            self.audio.terminate()

        self.executor.shutdown(wait=True)
        logger.info("Audio processor cleaned up")


class BasicVoiceAssistant:
    """Basic voice assistant implementing the VoiceLive SDK patterns."""

    def __init__(
        self,
        endpoint: str,
        credential: Union[AzureKeyCredential, TokenCredential],
        model: str,
        voice: str,
        instructions: str,
    ):
        self.endpoint = endpoint
        self.credential = credential
        self.model = model
        self.voice = voice
        self.instructions = instructions
        self.connection: Optional["VoiceLiveConnection"] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.session_ready = False

    async def start(self):
        try:
            logger.info("Connecting to VoiceLive API with model %s", self.model)

            async with connect(
                endpoint=self.endpoint,
                credential=self.credential,
                model=self.model,
                connection_options={
                    "max_msg_size": 10 * 1024 * 1024,
                    "heartbeat": 20,
                    "timeout": 20,
                },
            ) as connection:
                self.connection = connection
                self.audio_processor = AudioProcessor(connection)

                await self._setup_session()
                await self.audio_processor.start_playback()

                logger.info("Voice assistant ready! Start speaking...")
                print()
                print("=" * 60)
                print("🎤 VOICE ASSISTANT READY")
                print("Start speaking to begin conversation")
                print("Press Ctrl+C to exit")
                print("=" * 60)
                print()

                await self._process_events()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as exc:
            logger.error("Connection error: %s", exc)
            raise

        if self.audio_processor:
            await self.audio_processor.cleanup()

    async def _setup_session(self):
        logger.info("Setting up voice conversation session...")

        voice_config: Union[AzureStandardVoice, str]
        if self.voice.startswith("en-US-") or self.voice.startswith("en-CA-") or "-" in self.voice:
            voice_config = AzureStandardVoice(name=self.voice)
        else:
            voice_config = self.voice

        turn_detection_config = ServerVad(threshold=0.5, prefix_padding_ms=300, silence_duration_ms=500)

        session_config = RequestSession(
            modalities=[Modality.TEXT, Modality.AUDIO],
            instructions=self.instructions,
            voice=voice_config,
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            turn_detection=turn_detection_config,
        )

        assert self.connection is not None, "Connection must be established before setting up session"
        await self.connection.session.update(session=session_config)
        logger.info("Session configuration sent")

    async def _process_events(self):
        try:
            conn = self.connection
            assert conn is not None, "Connection must be established before processing events"
            async for event in conn:
                await self._handle_event(event)
        except KeyboardInterrupt:
            logger.info("Event processing interrupted")
        except Exception as exc:
            logger.error("Error processing events: %s", exc)
            raise

    async def _handle_event(self, event):
        logger.debug("Received event: %s", event.type)
        ap = self.audio_processor
        conn = self.connection
        assert ap is not None, "AudioProcessor must be initialized"
        assert conn is not None, "Connection must be established"

        if event.type == ServerEventType.SESSION_UPDATED:
            logger.info("Session ready: %s", event.session.id)
            self.session_ready = True
            await ap.start_capture()

        elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
            logger.info("🎤 User started speaking - stopping playback")
            print("🎤 Listening...")
            await ap.stop_playback()
            try:
                await conn.response.cancel()
            except Exception as exc:
                logger.debug("No response to cancel: %s", exc)

        elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
            logger.info("🎤 User stopped speaking")
            print("🤔 Processing...")
            await ap.start_playback()

        elif event.type == ServerEventType.RESPONSE_CREATED:
            logger.info("🤖 Assistant response created")

        elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
            logger.debug("Received audio delta")
            await ap.queue_audio(event.delta)

        elif event.type == ServerEventType.RESPONSE_AUDIO_DONE:
            logger.info("🤖 Assistant finished speaking")
            print("🎤 Ready for next input...")

        elif event.type == ServerEventType.RESPONSE_DONE:
            logger.info("✅ Response complete")

        elif event.type == ServerEventType.ERROR:
            logger.error("❌ VoiceLive error: %s", event.error.message)
            print(f"Error: {event.error.message}")

        elif event.type == ServerEventType.CONVERSATION_ITEM_CREATED:
            logger.debug("Conversation item created: %s", event.item.id)

        else:
            logger.debug("Unhandled event type: %s", event.type)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Basic Voice Assistant using Azure VoiceLive SDK",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--api-key",
        help="Azure VoiceLive API key. If not provided, will use AZURE_VOICELIVE_API_KEY environment variable.",
        type=str,
        default=os.environ.get("AZURE_VOICELIVE_API_KEY"),
    )

    parser.add_argument(
        "--endpoint",
        help="Azure VoiceLive endpoint",
        type=str,
        default=os.environ.get("AZURE_VOICELIVE_ENDPOINT", "wss://api.voicelive.com/v1"),
    )

    parser.add_argument(
        "--model",
        help="VoiceLive model to use",
        type=str,
        default=os.environ.get("AZURE_VOICELIVE_MODEL", "gpt-realtime"),
    )

    parser.add_argument(
        "--voice",
        help="Voice to use for the assistant (any Azure neural voice, e.g. de-DE-KatjaNeural, "
        "or an OpenAI voice such as alloy/echo/nova).",
        type=str,
        default=os.environ.get("AZURE_VOICELIVE_VOICE", "de-DE-KatjaNeural"),
    )

    parser.add_argument(
        "--instructions",
        help="System instructions for the AI assistant",
        type=str,
        default=os.environ.get(
            "AZURE_VOICELIVE_INSTRUCTIONS",
            "Du bist ein freundlicher deutscher Sprachcoach für Deutschlernende. "
            "Sprich natürlich und flüssig auf Deutsch. "
            "Passe dich dem Sprachniveau des Lernenden an. "
            "Korrigiere Fehler kurz und hilfreich, aber unterbrich nicht unnötig.",
        ),
    )

    parser.add_argument(
        "--use-token-credential",
        help="Use Azure token credential instead of API key",
        action="store_true",
    )

    parser.add_argument("--verbose", help="Enable verbose logging", action="store_true")

    return parser.parse_args()


async def main():
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.api_key and not args.use_token_credential:
        print("❌ Error: No authentication provided")
        print("Please provide an API key using --api-key or set AZURE_VOICELIVE_API_KEY environment variable,")
        print("or use --use-token-credential for Azure authentication.")
        sys.exit(1)

    try:
        credential: Union[AzureKeyCredential, TokenCredential]
        if args.use_token_credential:
            credential = InteractiveBrowserCredential()
            logger.info("Using Azure token credential")
        else:
            credential = AzureKeyCredential(args.api_key)
            logger.info("Using API key credential")

        assistant = BasicVoiceAssistant(
            endpoint=args.endpoint,
            credential=credential,
            model=args.model,
            voice=args.voice,
            instructions=args.instructions,
        )

        def signal_handler(_sig, _frame):
            logger.info("Received shutdown signal")
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await assistant.start()

    except KeyboardInterrupt:
        print("\n👋 Voice assistant shut down. Goodbye!")
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        print(f"❌ Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    dependencies = {
        "pyaudio": "Audio processing",
        "azure.ai.voicelive": "Azure VoiceLive SDK",
        "azure.core": "Azure Core libraries",
    }

    missing_deps = []
    for dep, description in dependencies.items():
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing_deps.append(f"{dep} ({description})")

    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall with: pip install azure-ai-voicelive pyaudio python-dotenv")
        sys.exit(1)

    try:
        p = pyaudio.PyAudio()
        input_devices = [
            i
            for i in range(p.get_device_count())
            if cast(Union[int, float], p.get_device_info_by_index(i).get("maxInputChannels", 0) or 0) > 0
        ]
        output_devices = [
            i
            for i in range(p.get_device_count())
            if cast(Union[int, float], p.get_device_info_by_index(i).get("maxOutputChannels", 0) or 0) > 0
        ]
        p.terminate()

        if not input_devices:
            print("❌ No audio input devices found. Please check your microphone.")
            sys.exit(1)
        if not output_devices:
            print("❌ No audio output devices found. Please check your speakers.")
            sys.exit(1)
    except Exception as exc:
        print(f"❌ Audio system check failed: {exc}")
        sys.exit(1)

    print("🎙️  Basic Voice Assistant with Azure VoiceLive SDK")
    print("=" * 50)

    asyncio.run(main())