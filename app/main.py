"""FastAPI application for Pronunciation Analysis Agent."""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os

from app.config import settings
from app.models.schemas import PronunciationRequest, PronunciationReport
from app.services.azure_pronunciation import AzurePronunciationAssistant

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Language Agent for English Pronunciation Analysis"
)

# Initialize pronunciation assistant
pronunciation_assistant = AzurePronunciationAssistant()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Pronunciation Analysis Agent"}


@app.post("/analyze", response_model=PronunciationReport)
async def analyze_pronunciation(
    file: UploadFile = File(...),
    reference_text: str = "",
    language: str = "en-US",
    enable_miscue: bool = True,
    enable_prosody: bool = True,
):
    """
    Analyze pronunciation from uploaded audio file.
    
    Args:
        file: Audio file (WAV, MP3, OGG, FLAC)
        reference_text: Reference text to compare against
        language: Language code (default: en-US)
        enable_miscue: Enable insertion/omission detection
        enable_prosody: Enable prosody assessment
    
    Returns:
        PronunciationReport with detailed analysis
    """
    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Process pronunciation
        report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=tmp_path,
            reference_text=reference_text,
            language=language,
            enable_miscue=enable_miscue,
            enable_prosody=enable_prosody,
        )
        
        return report
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"File error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/analyze-with-reference", response_model=PronunciationReport)
async def analyze_with_reference(
    learner_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
    reference_text: str = "",
    language: str = "en-US",
):
    """
    Analyze learner pronunciation compared to native speaker reference.
    
    Args:
        learner_file: Audio from learner
        reference_file: Audio from native speaker (for comparison)
        reference_text: The reference text spoken
        language: Language code
    
    Returns:
        PronunciationReport for learner audio
    """
    # For now, we analyze the learner audio
    # Reference file can be used for future enhancement (acoustic comparison)
    
    if not reference_text.strip():
        raise HTTPException(status_code=400, detail="reference_text cannot be empty")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            contents = await learner_file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        report = pronunciation_assistant.assess_pronunciation(
            audio_file_path=tmp_path,
            reference_text=reference_text,
            language=language,
            enable_miscue=True,
            enable_prosody=True,
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)