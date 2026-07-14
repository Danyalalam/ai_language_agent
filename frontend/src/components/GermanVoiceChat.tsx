import React, { useRef, useState, useEffect } from 'react';
import { Mic, PhoneOff, Loader2 } from 'lucide-react';
import { VoiceLiveClient, type VoiceState } from '../services/voiceLiveClient';
import '../styles/GermanVoiceChat.css';

interface TranscriptLine {
  role: string;
  text: string;
}

const STATE_LABELS: Record<VoiceState, string> = {
  idle: 'Nicht verbunden',
  connecting: 'Verbinde…',
  connected: 'Verbunden',
  ready: 'Bereit – sprich einfach los',
  listening: 'Ich höre zu…',
  processing: 'Denke nach…',
  error: 'Fehler',
};

const GermanVoiceChat: React.FC = () => {
  const clientRef = useRef<VoiceLiveClient | null>(null);
  const [state, setState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [error, setError] = useState<string | null>(null);

  const isActive = state !== 'idle' && state !== 'error';
  const isConnecting = state === 'connecting';

  useEffect(() => {
    // Ensure the session is torn down if the component unmounts.
    return () => {
      clientRef.current?.stop();
      clientRef.current = null;
    };
  }, []);

  const handleStart = async () => {
    setError(null);
    setTranscript([]);

    const client = new VoiceLiveClient({
      onStateChange: setState,
      onTranscript: (role, text) =>
        setTranscript((prev) => [...prev, { role, text }]),
      onError: (message) => setError(message),
    });
    clientRef.current = client;

    try {
      await client.start();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Konnte die Sitzung nicht starten';
      setError(message);
      setState('error');
      await client.stop();
      clientRef.current = null;
    }
  };

  const handleStop = async () => {
    await clientRef.current?.stop();
    clientRef.current = null;
    setState('idle');
  };

  return (
    <div className="german-voice-chat">
      <div className="gvc-header">
        <div>
          <h2 className="gvc-title">🇩🇪 Deutsch sprechen</h2>
          <p className="gvc-subtitle">
            Live-Gespräch mit deinem deutschen Sprachcoach
          </p>
        </div>
        <span className={`gvc-status gvc-status--${state}`}>
          {STATE_LABELS[state]}
        </span>
      </div>

      <div className="gvc-controls">
        {!isActive ? (
          <button className="gvc-btn gvc-btn--start" onClick={handleStart}>
            <Mic size={20} />
            Gespräch starten
          </button>
        ) : (
          <button
            className="gvc-btn gvc-btn--stop"
            onClick={handleStop}
            disabled={isConnecting}
          >
            {isConnecting ? (
              <Loader2 size={20} className="gvc-spin" />
            ) : (
              <PhoneOff size={20} />
            )}
            Gespräch beenden
          </button>
        )}
      </div>

      {error && <div className="gvc-error">{error}</div>}

      {transcript.length > 0 && (
        <div className="gvc-transcript">
          {transcript.map((line, i) => (
            <div key={i} className={`gvc-line gvc-line--${line.role}`}>
              <span className="gvc-role">
                {line.role === 'assistant' ? 'Coach' : 'Du'}
              </span>
              <span className="gvc-text">{line.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GermanVoiceChat;
