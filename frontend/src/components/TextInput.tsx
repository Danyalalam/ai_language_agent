import React from 'react';
import { Volume2 } from 'lucide-react';
import type { PronunciationMode } from '../types';
import '../styles/TextInput.css';

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  mode: PronunciationMode;
  placeholder?: string;
  readOnly?: boolean;
}

const TONGUE_TWISTERS = [
  "Autumn leaves lazily linger.",
  "Toy boat, toy boat, toy boat.",
  "She sells seashells by the seashore.",
  "Peter Piper picked a peck of pickled peppers.",
  "Six slippery snails slid slowly seaward.",
  "How can a clam cram in a clean cream can?",
  "I scream, you scream, we all scream for ice cream.",
  "Red lorry, yellow lorry.",
  "Friendly fleas and flies."
];

const TextInput: React.FC<TextInputProps> = ({
  value,
  onChange,
  mode,
  placeholder = 'Enter or paste text here...',
  readOnly = false,
}) => {
  const generateNewTwister = () => {
    const currentIndex = TONGUE_TWISTERS.indexOf(value);
    let nextIndex;
    do {
      nextIndex = Math.floor(Math.random() * TONGUE_TWISTERS.length);
    } while (nextIndex === currentIndex && TONGUE_TWISTERS.length > 1);
    
    onChange(TONGUE_TWISTERS[nextIndex]);
  };

  if (mode === 'gaming') {
    return (
      <div className="text-input-container gaming-mode">
        <div className="twister-display-box">
          <div className="twister-content">
            <Volume2 className="speaker-icon" size={24} />
            <span className="twister-text">{value}</span>
          </div>
          
          <div className="twister-footer">
            <p className="twister-instruction">Get ready and start recording as you read the tongue twister aloud.</p>
            <div className="twister-actions">
              <button className="generate-btn" onClick={generateNewTwister}>
                Generate new twister
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="text-input-container">
      <div className="tab-header">
        <button className="tab-button active">Sample 1</button>
        <button className="tab-button">Try with your own</button>
      </div>

      <textarea
        className="text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
      />
    </div>
  );
};

export default TextInput;
