# app/api/reading.py
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import PronunciationAnalysisResponse
from app.services.AI_service import generate_ai_report
from app.services.azure_pronunciation import AzurePronunciationAssistant

router = APIRouter(tags=["reading"])
pronunciation_assistant = AzurePronunciationAssistant()


@router.post("/analyze", response_model=PronunciationAnalysisResponse)
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

    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"File error: {str(exc)}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)