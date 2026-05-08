"""Test script for pronunciation assessment."""
import sys
from app.services.azure_pronunciation import AzurePronunciationAssistant

def test_pronunciation():
    """Test the pronunciation assessment service."""
    try:
        assistant = AzurePronunciationAssistant()
        
        # You'll need a real audio file to test with
        report = assistant.assess_pronunciation(
            audio_file_path="test_audio.wav",  # Replace with your test audio file path
            reference_text="Hello, how are you?",
            language="en-US",
            enable_miscue=True,
            enable_prosody=True
        )
        
        print(f"✓ Overall Score: {report.overall_score}")
        print(f"✓ Accuracy: {report.accuracy_score}")
        print(f"✓ Fluency: {report.fluency_score}")
        print(f"✓ Completeness: {report.completeness_score}")
        print(f"✓ Prosody: {report.prosody_score}")
        print(f"\nWord Details:")
        for word in report.word_details:
            print(f"  {word.word}: {word.accuracy_score} ({word.error_type})")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_pronunciation()
    sys.exit(0 if success else 1)