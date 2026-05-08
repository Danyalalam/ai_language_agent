import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""
    
    # Azure Speech API Configuration
    azure_speech_key: str = os.getenv("AZURE_SPEECH_KEY", "")
    azure_speech_region: str = os.getenv("AZURE_SPEECH_REGION", "")
    
    # Optional: Full endpoint URL (if using custom endpoint)
    azure_speech_endpoint: Optional[str] = os.getenv("AZURE_SPEECH_ENDPOINT", None)
    
    # Language configuration
    language: str = "en-US"  # Language for pronunciation assessment
    reference_text: str = ""  # Reference text for pronunciation assessment
    
    # Audio configuration
    max_audio_file_size_mb: int = 100  # Maximum file size in MB
    supported_audio_formats: list = ["wav", "mp3", "ogg", "flac"]
    
    # API configuration
    api_title: str = "Pronunciation Analysis Agent"
    api_version: str = "0.1.0"
    
    # Pronunciation Assessment settings
    proficiency_level: str = "Intermediate"  # Elementary, Intermediate, Upper-Intermediate
    granularity: str = "Word"  # Phoneme, Word, FullText
    enable_prosody: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()


def validate_azure_credentials() -> bool:
    """Validate that Azure credentials are configured."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise ValueError(
            "Azure Speech API credentials not configured. "
            "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables."
        )
    return True