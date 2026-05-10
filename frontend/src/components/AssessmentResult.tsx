import React, { useRef, useState, useEffect } from 'react';
import { AlertCircle, X, Play, Pause } from 'lucide-react';
import type { AssessmentResult, ErrorDetail } from '../types';
import '../styles/AssessmentResult.css';

interface AssessmentResultProps {
  result: AssessmentResult | null;
  loading?: boolean;
}

const PronunciationResultComponent: React.FC<AssessmentResultProps> = ({
  result,
  loading = false,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    // Reset state when result changes
    setIsPlaying(false);
    setCurrentTime(0);
  }, [result?.audio_url]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const formatTime = (time: number) => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  if (loading) {
    return (
      <div className="assessment-container">
        <div className="loading">
          <p>Assessing pronunciation...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="assessment-container">
        <div className="placeholder">
          <p>Upload or record audio to see assessment results</p>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#2ecc71';
    if (score >= 60) return '#f39c12';
    return '#e74c3c';
  };

  const renderError = (error: ErrorDetail, index: number) => {
    let icon = null;
    let label = '';

    if (error.type === 'mispronunciation') {
      icon = <AlertCircle size={16} className="error-icon" />;
      label = 'Mispronunciation';
    } else if (error.type === 'omission') {
      icon = <X size={16} className="error-icon" />;
      label = 'Omission';
    } else if (error.type === 'insertion') {
      icon = <AlertCircle size={16} className="error-icon" />;
      label = 'Insertion';
    }

    return (
      <div key={`${error.type}-${error.word}-${index}`} className="error-item">
        <div className="error-header">
          {icon}
          <span className="error-label">{label}</span>
        </div>
        <div className="error-word">{error.word}</div>
      </div>
    );
  };

  const pronunciationScore = result.pronunciation_score ?? 0;
  const accuracyScore = result.accuracy_score ?? 0;
  const fluencyScore = result.fluency_score ?? 0;
  
  const score = Math.round(Number(pronunciationScore) || 0);

  const renderHighlightedText = () => {
    if (!result.word_details || result.word_details.length === 0) {
      return <p className="assessment-text">{result.assessment_text}</p>;
    }

    return (
      <p className="assessment-text highlighted">
        {result.word_details.map((w, i) => {
          const isError = w.accuracy_score < 80 || w.error_type !== 'None';
          const bgColor = isError ? getScoreColor(w.accuracy_score) : 'transparent';
          const textColor = isError ? '#fff' : 'inherit';
          
          return (
            <span 
              key={i} 
              className={`word-span ${isError ? 'has-error' : ''}`}
              style={{ 
                backgroundColor: isError ? bgColor : 'transparent',
                color: textColor,
                padding: isError ? '2px 4px' : '0',
                borderRadius: isError ? '4px' : '0',
                margin: '0 2px',
                display: 'inline-block'
              }}
            >
              {w.word}
            </span>
          );
        })}
      </p>
    );
  };

  return (
    <div className="assessment-container">
      <div className="assessment-grid">
        <div className="assessment-left">
          <div className="audio-player-section">
            <audio
              ref={audioRef}
              src={result.audio_url}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={handleEnded}
              hidden
            />
            <div className="player-controls">
              <button className="play-btn" onClick={togglePlay}>
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                ></div>
              </div>
              <span className="time-display">
                {formatTime(currentTime)} / {formatTime(duration || (result.duration ? result.duration / 1000 : 0))}
              </span>
            </div>
          </div>

          <div className="assessment-text-section">
            {renderHighlightedText()}
          </div>

          {result.ai_report && (
            <div className="ai-report-section">
              <h3 className="ai-report-title">AI Feedback</h3>
              <p className="ai-summary">{result.ai_report.summary}</p>
              
              <div className="ai-details">
                <div className="ai-detail-item">
                  <h4>Strengths</h4>
                  <ul>
                    {result.ai_report.strengths.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
                <div className="ai-detail-item">
                  <h4>Weaknesses</h4>
                  <ul>
                    {result.ai_report.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
                <div className="ai-detail-item">
                  <h4>Recommendations</h4>
                  <ul>
                    {result.ai_report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="assessment-right">
          <div className="errors-section">
            <h3 className="errors-title">Errors</h3>

            <div className="error-toggles">
              <label className="toggle-item">
                <input type="checkbox" defaultChecked />
                <span className="toggle-label">
                  <AlertCircle size={14} /> Mispronunciations
                </span>
              </label>
              <label className="toggle-item">
                <input type="checkbox" defaultChecked />
                <span className="toggle-label">
                  <X size={14} /> Omissions
                </span>
              </label>
              <label className="toggle-item">
                <input type="checkbox" defaultChecked />
                <span className="toggle-label">
                  <AlertCircle size={14} /> Insertions
                </span>
              </label>
            </div>
          </div>

          <div className="score-section">
            <h3 className="score-title">Pronunciation score</h3>

            <div className="score-display">
              <div className="score-circle" style={{ borderTopColor: getScoreColor(score) }}>
                <div className="score-number">{score}</div>
              </div>

              <div className="score-breakdown">
                <div className="score-item">
                  <label className="score-label">Accuracy score</label>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${accuracyScore}%`,
                        backgroundColor: getScoreColor(accuracyScore),
                      }}
                    ></div>
                  </div>
                  <span className="score-value">{accuracyScore} / 100</span>
                </div>

                <div className="score-item">
                  <label className="score-label">Fluency score</label>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${fluencyScore}%`,
                        backgroundColor: getScoreColor(fluencyScore),
                      }}
                    ></div>
                  </div>
                  <span className="score-value">{fluencyScore} / 100</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {result.errors && result.errors.length > 0 && (
        <div className="errors-list-section">
          <h4 className="errors-list-title">Detected errors:</h4>
          <div className="errors-list">
            {result.errors.map((error, index) => renderError(error, index))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PronunciationResultComponent;
