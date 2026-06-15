from pydantic import BaseModel
from typing import List, Optional


class WordResult(BaseModel):
    """Individual word pronunciation result."""
    word: str
    accuracy_score: Optional[float] = None
    error_type: str  # "None", "Insertion", "Omission", "Mispronunciation"


class PronunciationAssessmentResult(BaseModel):
    """Overall pronunciation assessment result."""
    accuracy_score: float
    pronunciation_score: float
    completeness_score: float
    fluency_score: float
    prosody_score: Optional[float] = None
    recognized_text: str
    words: List[WordResult]


class PronunciationRequest(BaseModel):
    """Request for pronunciation assessment."""
    reference_text: str
    language: str = "en-US"
    proficiency_level: str = "Intermediate"
    enable_miscue: bool = True
    enable_prosody: bool = True


class PronunciationReport(BaseModel):
    """Complete pronunciation analysis report."""
    overall_score: float
    accuracy_score: float
    completeness_score: float
    fluency_score: float
    prosody_score: Optional[float] = None
    recognized_text: str
    word_details: List[WordResult]
    reference_text: str

class AIReport(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    full_report: str


class PronunciationAnalysisResponse(BaseModel):
    azure_result: PronunciationReport
    ai_report: AIReport