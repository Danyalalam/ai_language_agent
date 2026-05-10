import json
import time
import string
import difflib
from typing import List, Optional
import azure.cognitiveservices.speech as speechsdk

from app.config import settings, validate_azure_credentials
from app.models.schemas import (
    PronunciationAssessmentResult,
    PronunciationReport,
    WordResult,
)
from app.utils.audio import validate_audio_file, normalize_reference_text


class AzurePronunciationAssistant:
    """Azure Speech Pronunciation Assessment Service."""
    
    def __init__(self):
        validate_azure_credentials()
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region
        )
    
    def assess_pronunciation(
        self,
        audio_file_path: str,
        reference_text: str,
        language: str = "en-US",
        proficiency_level: str = "Intermediate",
        enable_miscue: bool = True,
        enable_prosody: bool = True,
    ) -> PronunciationReport:
        """
        Assess pronunciation from audio file against reference text.
        
        Args:
            audio_file_path: Path to audio file (WAV, MP3, etc.)
            reference_text: Reference text to compare against
            language: Language code (e.g., 'en-US', 'zh-CN')
            proficiency_level: One of 'Elementary', 'Intermediate', 'Upper-Intermediate'
            enable_miscue: Enable detection of insertions/omissions
            enable_prosody: Enable prosody (intonation, stress) assessment
        
        Returns:
            PronunciationReport with detailed scores and word-level analysis
        """
        # Validate input
        validate_audio_file(audio_file_path)
        if not reference_text.strip():
            raise ValueError("Reference text cannot be empty")
        
        # Set up audio config
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
        
        # Create pronunciation assessment config
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=self._get_granularity(settings.granularity),
            enable_miscue=enable_miscue
        )
        
        if enable_prosody:
            try:
                pronunciation_config.enable_prosody_assessment()
            except AttributeError:
                try:
                    pronunciation_config.enable_prosody = True
                except Exception:
                    # prosody not supported by this SDK build; continue without it
                    pass
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            language=language,
            audio_config=audio_config
        )
        
        # Apply pronunciation config
        pronunciation_config.apply_to(speech_recognizer)
        
        # Collect results
        recognized_words = []
        fluency_scores = []
        prosody_scores = []
        durations = []
        done = False
        
        def on_recognized(evt: speechsdk.SpeechRecognitionEventArgs):
            nonlocal recognized_words, fluency_scores, prosody_scores, durations
            
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                pronunciation_result = speechsdk.PronunciationAssessmentResult(evt.result)
                recognized_words.extend(pronunciation_result.words)
                fluency_scores.append(pronunciation_result.fluency_score)
                prosody_scores.append(pronunciation_result.prosody_score)
                
                # Extract duration from JSON result
                json_result = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                )
                if json_result:
                    try:
                        jo = json.loads(json_result)
                        nb = jo.get('NBest', [{}])[0]
                        duration = sum([int(w['Duration']) for w in nb.get('Words', [])])
                        durations.append(duration)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        durations.append(0)
        
        def on_session_stopped(evt: speechsdk.SessionEventArgs):
            nonlocal done
            done = True
        
        # Connect callbacks
        speech_recognizer.recognized.connect(on_recognized)
        speech_recognizer.session_stopped.connect(on_session_stopped)
        speech_recognizer.canceled.connect(on_session_stopped)
        
        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(0.5)
        
        speech_recognizer.stop_continuous_recognition()
        
        # Process results
        reference_words = normalize_reference_text(reference_text, language)
        final_words = self._apply_miscue_detection(
            recognized_words, reference_words, enable_miscue
        )
        
        # Calculate scores
        accuracy_score = self._calculate_accuracy(final_words)
        completeness_score = self._calculate_completeness(final_words, reference_words)
        fluency_score = self._calculate_fluency(fluency_scores, durations) if fluency_scores else 0
        # Filter prosody scores to remove None values
        valid_prosody_scores = [s for s in prosody_scores if s is not None]
        prosody_score = sum(valid_prosody_scores) / len(valid_prosody_scores) if valid_prosody_scores else None

        # Calculate overall score with weight renormalization when prosody is unavailable
        weights = {
            "accuracy": 0.4,
            "prosody": 0.2,
            "fluency": 0.2,
            "completeness": 0.2,
        }

        if prosody_score is None:
            # remove prosody weight and renormalize remaining weights
            weights.pop("prosody")

        total_weight = sum(weights.values())
        norm = {k: v / total_weight for k, v in weights.items()}

        overall_score = 0.0
        overall_score += accuracy_score * norm.get("accuracy", 0)
        overall_score += fluency_score * norm.get("fluency", 0)
        overall_score += completeness_score * norm.get("completeness", 0)
        if prosody_score is not None:
            overall_score += prosody_score * norm.get("prosody", 0)
        
        # Build report
        word_results = [
            WordResult(
                word=w.word,
                accuracy_score=w.accuracy_score,
                error_type=w.error_type
            )
            for w in final_words
        ]
        
        recognized_text = " ".join([w.word for w in recognized_words])
        
        return PronunciationReport(
            overall_score=overall_score,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            fluency_score=fluency_score,
            prosody_score=prosody_score,
            recognized_text=recognized_text,
            word_details=word_results,
            reference_text=reference_text,
        )
    
    def _get_granularity(self, granularity_str: str):
        """Convert string granularity to Azure enum."""
        mapping = {
            "Phoneme": speechsdk.PronunciationAssessmentGranularity.Phoneme,
            "Word": speechsdk.PronunciationAssessmentGranularity.Word,
            "FullText": speechsdk.PronunciationAssessmentGranularity.FullText,
        }
        return mapping.get(granularity_str, speechsdk.PronunciationAssessmentGranularity.Word)
    
    def _apply_miscue_detection(
        self,
        recognized_words,
        reference_words: List[str],
        enable_miscue: bool
    ):
        """Apply miscue detection to identify insertions and omissions."""
        if not enable_miscue:
            return recognized_words
        
        diff = difflib.SequenceMatcher(
            None,
            reference_words,
            [x.word.lower() for x in recognized_words]
        )
        
        final_words = []
        for tag, i1, i2, j1, j2 in diff.get_opcodes():
            if tag in ['insert', 'replace']:
                for word in recognized_words[j1:j2]:
                    if word.error_type == 'None':
                        word._error_type = 'Insertion'
                    final_words.append(word)
            
            if tag in ['delete', 'replace']:
                for word_text in reference_words[i1:i2]:
                    word = speechsdk.PronunciationAssessmentWordResult({
                        'Word': word_text,
                        'PronunciationAssessment': {
                            'ErrorType': 'Omission',
                        }
                    })
                    final_words.append(word)
            
            if tag == 'equal':
                final_words.extend(recognized_words[j1:j2])
        
        return final_words
    
    def _calculate_accuracy(self, final_words) -> float:
        """Calculate accuracy by averaging word scores."""
        accuracy_scores = [
            w.accuracy_score for w in final_words
            if w.error_type != 'Insertion' and w.accuracy_score is not None
        ]
        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
    
    def _calculate_completeness(self, final_words, reference_words: List[str]) -> float:
        """Calculate completeness score."""
        correct_words = len([w for w in final_words if w.error_type == "None"])
        completeness = (correct_words / len(reference_words) * 100) if reference_words else 0
        return min(completeness, 100)
    
    def _calculate_fluency(self, fluency_scores: List[float], durations: List[int]) -> float:
        """Re-calculate fluency score weighted by duration."""
        valid_fluency = [f for f in fluency_scores if f is not None]
        if not durations or sum(durations) == 0:
            return sum(valid_fluency) / len(valid_fluency) if valid_fluency else 0
        return sum([x * y for x, y in zip(fluency_scores, durations) if x is not None]) / sum(durations)

    def get_streaming_recognizer(
        self,
        reference_text: str,
        language: str = "en-US",
        enable_miscue: bool = True,
        enable_prosody: bool = True,
    ):
        """Create a recognizer and push stream for real-time assessment."""
        # Setup push stream
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        # Create pronunciation assessment config
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=self._get_granularity(settings.granularity),
            enable_miscue=enable_miscue
        )
        
        if enable_prosody:
            try:
                pronunciation_config.enable_prosody_assessment()
            except Exception:
                pass

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            language=language,
            audio_config=audio_config
        )
        
        # Apply pronunciation config
        pronunciation_config.apply_to(speech_recognizer)
        
        return speech_recognizer, push_stream