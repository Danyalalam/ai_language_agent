import asyncio
import logging
import os
import subprocess
import tempfile
import uvicorn
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form

from app.config import settings
from app.models.schemas import PronunciationAnalysisResponse, PronunciationReport
from app.services.AI_service import generate_ai_report
from app.services.azure_pronunciation import AzurePronunciationAssistant

# Configure logging
logging.basicConfig(
    filename='backend_errors.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Language Agent for English Pronunciation Analysis",
)

pronunciation_assistant = AzurePronunciationAssistant()

# Enable CORS for local development (vite / CRA frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_to_wav(input_path: str) -> str:
    """Convert any audio format to 16kHz mono WAV for Azure."""
    output_path = f"{input_path}_converted.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path],
            check=True,
            capture_output=True
        )
        return output_path
    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise e


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Pronunciation Analysis Agent"}


@app.post("/analyze", response_model=PronunciationAnalysisResponse)
async def analyze_pronunciation(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    language: str = Form("en-US"),
    enable_miscue: bool = Form(True),
    enable_prosody: bool = Form(True),
):
    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")

    # Map human readable language to locale code
    locale = LANGUAGE_MAP.get(language, "en-US")

    tmp_path = None
    wav_path = None
    try:
        suffix = os.path.splitext(file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        # Convert to standard WAV for Azure
        try:
            wav_path = convert_to_wav(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Audio conversion failed: {str(e)}")

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
            language=language,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except Exception as e:
        logger.exception("Error in analyze_pronunciation")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


import azure.cognitiveservices.speech as speechsdk
from fastapi import WebSocket, WebSocketDisconnect


LANGUAGE_MAP = {
    "English (US)": "en-US",
    "en-US": "en-US"
}

@app.get("/api/config")
async def get_config():
    return {
        "modes": ["reading", "gaming"],
        "languages": ["English (US)"],
    }


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
    
    recognizer, push_stream = pronunciation_assistant.get_streaming_recognizer(
        reference_text=reference_text,
        language=locale,
        enable_miscue=enable_miscue,
        enable_prosody=enable_prosody
    )
    
    # Track results
    results = []
    
    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pron_result = speechsdk.PronunciationAssessmentResult(evt.result)
            data = {
                "type": "final",
                "text": evt.result.text,
                "accuracy": pron_result.accuracy_score,
                "fluency": pron_result.fluency_score,
                "prosody": pron_result.prosody_score,
            }
            results.append(data)
    
    recognizer.recognized.connect(on_recognized)
    recognizer.start_continuous_recognition()
    
    try:
        while True:
            # Receive audio chunks from frontend
            data = await websocket.receive_bytes()
            if not data:
                break
            push_stream.write(data)
            
            # If we have new results, send them
            while results:
                res = results.pop(0)
                await websocket.send_json(res)
                
    except WebSocketDisconnect:
        logger.info("Streaming websocket disconnected")
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        recognizer.stop_continuous_recognition()
        push_stream.close()


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
    # Map human readable language to locale code
    locale = LANGUAGE_MAP.get(language, "en-US")
    
    # Reuse the pronunciation assistant logic from /analyze
    if text is None or not text.strip():
        reference_text = ""
    else:
        reference_text = text

    tmp_path = None
    wav_path = None
    try:
        suffix = os.path.splitext(audio_file.filename or "")[-1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(await audio_file.read())
            tmp_path = tmp_file.name

        # Convert to standard WAV for Azure
        try:
            wav_path = convert_to_wav(tmp_path)
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise HTTPException(status_code=400, detail=f"Audio conversion failed: {str(e)}")

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
            language=language,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }
    except Exception as e:
        logger.exception("Error in assess_from_audio")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
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
    # Map human readable language to locale code
    locale = LANGUAGE_MAP.get(language, "en-US")
    
    # Create a minimal synthetic azure report for text-only assessment
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/analyze-with-reference", response_model=PronunciationAnalysisResponse)
async def analyze_with_reference(
    learner_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
    reference_text: str = Form(""),
    language: str = Form("en-US"),
):
    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")

    tmp_path = None
    reference_tmp_path = None
    try:
        learner_suffix = os.path.splitext(learner_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=learner_suffix) as tmp_file:
            tmp_file.write(await learner_file.read())
            tmp_path = tmp_file.name

        # Reference file is accepted for future comparison workflows.
        # For now, Azure pronunciation assessment uses the reference_text.
        reference_suffix = os.path.splitext(reference_file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=reference_suffix) as ref_file:
            ref_file.write(await reference_file.read())
            reference_tmp_path = ref_file.name

        azure_report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=tmp_path,
            reference_text=reference_text,
            language=language,
            enable_miscue=True,
            enable_prosody=True,
        )

        ai_report_payload = generate_ai_report(
            azure_report=azure_report,
            reference_text=reference_text,
            language=language,
        )

        ai_report = ai_report_payload["ai_report"]
        ai_report_data = ai_report.model_dump() if hasattr(ai_report, "model_dump") else ai_report.__dict__

        return {
            "azure_result": azure_report.model_dump(),
            "ai_report": ai_report_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if reference_tmp_path and os.path.exists(reference_tmp_path):
            os.remove(reference_tmp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
