import os
import string
from typing import List
from app.config import settings


def validate_audio_file(file_path: str) -> bool:
    """Validate audio file exists and has supported format."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if file_ext not in settings.supported_audio_formats:
        raise ValueError(
            f"Unsupported format: {file_ext}. Supported: {settings.supported_audio_formats}"
        )
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > settings.max_audio_file_size_mb:
        raise ValueError(
            f"File size {file_size_mb:.2f}MB exceeds limit of {settings.max_audio_file_size_mb}MB"
        )
    
    return True


def normalize_reference_text(text: str, language: str = "en-US") -> List[str]:
    """Convert reference text to word list, handling language-specific splitting."""
    if language == "zh-CN":
        try:
            import jieba
            import zhon.hanzi
            jieba.suggest_freq([x for x in text], True)
            return [w for w in jieba.cut(text) if w not in zhon.hanzi.punctuation]
        except ImportError:
            raise ImportError("jieba package required for Chinese. Install: pip install jieba zhon")
    else:
        # For English and other languages
        return [w.strip(string.punctuation) for w in text.lower().split()]