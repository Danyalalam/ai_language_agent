import { useState, useEffect } from 'react';
import type {
  PronunciationMode,
  Language,
  ProficiencyLevel,
  AssessmentResult as AssessmentResultType,
} from '../types';
import ConfigPanel from './ConfigPanel';
import TextInput from './TextInput';
import AudioRecorder from './AudioRecorder';
import AudioUploader from './AudioUploader';
import AssessmentResult from './AssessmentResult';
import { api } from '../services/api';

function PronunciationView() {
  const [mode, setMode] = useState<PronunciationMode>('reading');
  const [language, setLanguage] = useState<Language>('English (US)');
  const [proficiencyLevel, setProficiencyLevel] = useState<ProficiencyLevel>('Intermediate');
  const [enableProsody, setEnableProsody] = useState(true);
  const [enableMiscue, setEnableMiscue] = useState(true);
  const [sampleText, setSampleText] = useState('Hello, how are you?');
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResultType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (assessmentResult?.audio_url) {
        URL.revokeObjectURL(assessmentResult.audio_url);
      }
    };
  }, [assessmentResult?.audio_url]);

  useEffect(() => {
    if (mode === 'gaming') {
      setSampleText('Autumn leaves lazily linger.');
    } else if (mode === 'reading') {
      setSampleText('Hello, how are you?');
    }
  }, [mode]);

  const handleFileSelected = (file: File) => {
    assessPronunciation(file);
  };

  const handleRecordingComplete = (audioBlob: Blob) => {
    const mime = audioBlob.type || 'audio/webm';
    const extension = mime.split('/')[1]?.split(';')[0] || 'webm';
    const audioFile = new File([audioBlob], `recording.${extension}`, { type: mime });
    assessPronunciation(audioFile);
  };

  const assessPronunciation = async (audioFile: File) => {
    setIsLoading(true);
    setError(null);
    const audioUrl = URL.createObjectURL(audioFile);

    try {
      const result = await api.assessFromAudio(
        mode,
        language,
        audioFile,
        sampleText,
        proficiencyLevel,
        enableProsody,
        enableMiscue
      );
      setAssessmentResult({ ...result, audio_url: audioUrl });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to assess pronunciation';
      setError(errorMessage);
      console.error('Assessment error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="view">
      <header className="view-header">
        <h1 className="view-title">Pronunciation</h1>
        <p className="view-description">
          Read a script aloud and get scored on accuracy, fluency, and prosody.
        </p>
      </header>

      <div className="pronunciation-layout">
        <ConfigPanel
          mode={mode}
          language={language}
          proficiencyLevel={proficiencyLevel}
          enableProsody={enableProsody}
          enableMiscue={enableMiscue}
          onModeChange={setMode}
          onLanguageChange={setLanguage}
          onProficiencyChange={setProficiencyLevel}
          onProsodyToggle={setEnableProsody}
          onMiscueToggle={setEnableMiscue}
        />

        <div className="pronunciation-main">
          <div className="input-section">
            <TextInput value={sampleText} onChange={setSampleText} mode={mode} />
            <AudioUploader
              onFileSelected={handleFileSelected}
              onRecordingFromMicrophone={handleRecordingComplete}
              isLoading={isLoading}
            />
            <AudioRecorder onRecordingComplete={handleRecordingComplete} isLoading={isLoading} />
          </div>

          {error && (
            <div className="error-message">
              <p>{error}</p>
            </div>
          )}

          <AssessmentResult result={assessmentResult} loading={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default PronunciationView;
