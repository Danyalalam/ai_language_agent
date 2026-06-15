import asyncio
import logging
from fastapi import subprocess
import FastAPI
import uvicorn
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.models.schemas import PronunciationAnalysisResponse, PronunciationReport
from app.services.AI_service import generate_ai_report
from app.services.azure_pronunciation import AzurePronunciationAssistant
from fastapi import FastAPI, File, Form, HTTPException, UploadFile


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Language Agent for English Pronunciation Analysis",
)

app.include_router(reading_router)
app.include_router(gaming_router)

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

    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        azure_report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=tmp_path,
            reference_text=reference_text,
            language=language,
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

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"File error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


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
