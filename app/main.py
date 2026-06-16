"""FastAPI application for Pronunciation Analysis Agent."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile

import azure.cognitiveservices.speech as speechsdk
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import PronunciationAnalysisResponse, PronunciationReport
from app.services.AI_service import generate_ai_report
from app.services.azure_pronunciation import AzurePronunciationAssistant

logging.basicConfig(
    filename="backend_errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Language Agent for English Pronunciation Analysis",
)

pronunciation_assistant = AzurePronunciationAssistant()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LANGUAGE_MAP = {
    "English (US)": "en-US",
    "en-US": "en-US",
}


def convert_to_wav(input_path: str) -> str:
    """Convert any audio format to 16kHz mono WAV for Azure."""
    output_path = f"{input_path}_converted.wav"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return output_path
    except Exception as exc:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        raise exc


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Pronunciation Analysis Agent"}


@app.get("/api/config")
async def get_config():
    return {
        "modes": ["reading", "gaming"],
        "languages": ["English (US)"],
        "proficiencyLevels": ["Beginner", "Intermediate", "Advanced"],
    }


@app.post("/api/assess/audio", response_model=PronunciationAnalysisResponse)
async def assess_from_audio(
    audio_file: UploadFile = File(...),
    mode: str = Form("reading"),
    language: str = Form("en-US"),
    text: str | None = Form(None),
    proficiency_level: str = Form("Intermediate"),
    enable_prosody: bool = Form(True),
    enable_miscue: bool = Form(True),
):
    locale = LANGUAGE_MAP.get(language, "en-US")
    reference_text = text.strip() if text and text.strip() else ""

    if not reference_text:
        raise HTTPException(status_code=400, detail="text cannot be empty")

    tmp_path = None
    wav_path = None
    try:
        suffix = os.path.splitext(audio_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(await audio_file.read())
            tmp_path = tmp_file.name

        try:
            wav_path = convert_to_wav(tmp_path)
        except Exception as exc:
            logger.exception("Audio conversion failed")
            raise HTTPException(status_code=400, detail=f"Audio conversion failed: {str(exc)}")

        azure_report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=wav_path,
            reference_text=reference_text,
            language=locale,
            proficiency_level=proficiency_level,
            enable_miscue=enable_miscue,
            enable_prosody=enable_prosody,
        )

        ai_report_payload = generate_ai_report(
            azure_report=azure_report,
            reference_text=reference_text,
            language=locale,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"File error: {str(exc)}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(exc)}")
    except Exception as exc:
        logger.exception("Error in assess_from_audio")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


@app.post("/api/assess/text", response_model=PronunciationAnalysisResponse)
async def assess_from_text(
    mode: str = Form("reading"),
    language: str = Form("en-US"),
    text: str = Form(...),
):
    locale = LANGUAGE_MAP.get(language, "en-US")

    if not text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")

    try:
        azure_report = PronunciationReport(
            overall_score=95.0,
            accuracy_score=95.0,
            completeness_score=100.0,
            fluency_score=95.0,
            prosody_score=90.0,
            recognized_text=text,
            word_details=[],
            reference_text=text,
        )

        ai_report_payload = generate_ai_report(
            azure_report=azure_report,
            reference_text=text,
            language=locale,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except Exception as exc:
        logger.exception("Error in assess_from_text")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")


@app.post("/analyze", response_model=PronunciationAnalysisResponse)
async def analyze_pronunciation(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    language: str = Form("en-US"),
    enable_miscue: bool = Form(True),
    enable_prosody: bool = Form(True),
):
    locale = LANGUAGE_MAP.get(language, "en-US")

    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")

    tmp_path = None
    wav_path = None
    try:
        suffix = os.path.splitext(file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        try:
            wav_path = convert_to_wav(tmp_path)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Audio conversion failed: {str(exc)}")

        azure_report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=wav_path,
            reference_text=reference_text,
            language=locale,
            enable_miscue=enable_miscue,
            enable_prosody=enable_prosody,
        )

        ai_report_payload = generate_ai_report(
            azure_report=azure_report,
            reference_text=reference_text,
            language=locale,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"File error: {str(exc)}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(exc)}")
    except Exception as exc:
        logger.exception("Error in analyze_pronunciation")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


@app.post("/analyze-with-reference", response_model=PronunciationAnalysisResponse)
async def analyze_with_reference(
    learner_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
    reference_text: str = Form(""),
    language: str = Form("en-US"),
):
    locale = LANGUAGE_MAP.get(language, "en-US")

    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")

    tmp_path = None
    reference_tmp_path = None
    try:
        learner_suffix = os.path.splitext(learner_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=learner_suffix) as tmp_file:
            tmp_file.write(await learner_file.read())
            tmp_path = tmp_file.name

        reference_suffix = os.path.splitext(reference_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=reference_suffix) as ref_file:
            ref_file.write(await reference_file.read())
            reference_tmp_path = ref_file.name

        azure_report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=tmp_path,
            reference_text=reference_text,
            language=locale,
            enable_miscue=True,
            enable_prosody=True,
        )

        ai_report_payload = generate_ai_report(
            azure_report=azure_report,
            reference_text=reference_text,
            language=locale,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except Exception as exc:
        logger.exception("Error in analyze_with_reference")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if reference_tmp_path and os.path.exists(reference_tmp_path):
            os.remove(reference_tmp_path)


@app.websocket("/api/assess/stream")
async def assess_stream(
    websocket: WebSocket,
    mode: str = "reading",
    language: str = "en-US",
    text: str | None = None,
    proficiency_level: str = "Intermediate",
    enable_prosody: bool = True,
    enable_miscue: bool = True,
):
    await websocket.accept()

    locale = LANGUAGE_MAP.get(language, "en-US")
    reference_text = text if text else ""

    if not reference_text.strip():
        await websocket.send_json({"type": "error", "message": "text cannot be empty"})
        await websocket.close()
        return

    recognizer, push_stream = pronunciation_assistant.get_streaming_recognizer(
        reference_text=reference_text,
        language=locale,
        enable_miscue=enable_miscue,
        enable_prosody=enable_prosody,
    )

    results: list[dict[str, object]] = []

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pron_result = speechsdk.PronunciationAssessmentResult(evt.result)
            results.append(
                {
                    "type": "final",
                    "text": evt.result.text,
                    "accuracy": pron_result.accuracy_score,
                    "fluency": pron_result.fluency_score,
                    "prosody": pron_result.prosody_score,
                }
            )

    recognizer.recognized.connect(on_recognized)
    recognizer.start_continuous_recognition()

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                break

            push_stream.write(data)

            while results:
                await websocket.send_json(results.pop(0))

    except WebSocketDisconnect:
        logger.info("Streaming websocket disconnected")
    except Exception as exc:
        logger.exception("Streaming error")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            recognizer.stop_continuous_recognition()
        except Exception:
            pass
        try:
            push_stream.close()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)