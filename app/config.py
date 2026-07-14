import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Azure Speech API Configuration
    azure_speech_key: str = os.getenv("AZURE_SPEECH_KEY", "")
    azure_speech_region: str = os.getenv("AZURE_SPEECH_REGION", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Optional: Full endpoint URL (if using custom endpoint)
    azure_speech_endpoint: Optional[str] = os.getenv("AZURE_SPEECH_ENDPOINT", None)

    # Azure VoiceLive configuration for the live German speaking agent
    azure_voicelive_api_key: str = os.getenv("AZURE_VOICELIVE_API_KEY", "")
    azure_voicelive_endpoint: str = os.getenv(
        "AZURE_VOICELIVE_ENDPOINT",
        "https://your-resource-name.services.ai.azure.com/",
    )
    azure_voicelive_api_version: str = os.getenv("AZURE_VOICELIVE_API_VERSION", "2026-04-10")
    azure_voicelive_model: str = os.getenv("AZURE_VOICELIVE_MODEL", "gpt-realtime")
    azure_voicelive_project_name: str = os.getenv("AZURE_VOICELIVE_PROJECT_NAME", "")
    azure_voicelive_agent_id: str = os.getenv("AZURE_VOICELIVE_AGENT_ID", "")
    azure_voicelive_voice: str = os.getenv("AZURE_VOICELIVE_VOICE", "de-DE-KatjaNeural")
    azure_voicelive_instructions: str = os.getenv(
        "AZURE_VOICELIVE_INSTRUCTIONS",
        (
            "Du bist ein freundlicher deutscher Sprachcoach für Deutschlernende. "
            "Sprich natürlich und flüssig auf Deutsch. "
            "Passe dich dem Sprachniveau des Lernenden an. "
            "Korrigiere Fehler kurz und hilfreich, aber unterbrich nicht unnötig. "
            "Wenn der Lernende ausdrücklich Feedback möchte, gib danach eine knappe Verbesserung."
        ),
    )
    
    # Language configuration
    language: str = "en-US"  # Language for pronunciation assessment
    reference_text: str = ""  # Reference text for pronunciation assessment
    
    # Audio configuration
    max_audio_file_size_mb: int = 100  # Maximum file size in MB
    supported_audio_formats: list = ["wav", "mp3", "ogg", "flac", "webm", "m4a", "mp4"]
    
    # API configuration
    api_title: str = "Pronunciation Analysis Agent"
    api_version: str = "0.1.0"
    allowed_origins: list[str] = ["*"]
    
    # Pronunciation Assessment settings
    proficiency_level: str = "Intermediate"  # Elementary, Intermediate, Upper-Intermediate
    granularity: str = "Word"  # Phoneme, Word, FullText
    enable_prosody: bool = True
    
# Create settings instance
# This will read the environment variables and populate the settings
settings = Settings()


def validate_azure_credentials() -> bool:
    """Validate that Azure credentials are configured."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise ValueError(
            "Azure Speech API credentials not configured. "
            "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables."
        )
    return True