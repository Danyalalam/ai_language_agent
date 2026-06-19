import React, { useRef, useState } from 'react';
import { Upload } from 'lucide-react';
import '../styles/AudioUploader.css';

interface AudioUploaderProps {
  onFileSelected: (file: File) => void;
  onRecordingFromMicrophone: (audioBlob: Blob) => void;
  isLoading?: boolean;
}

const AudioUploader: React.FC<AudioUploaderProps> = ({
  onFileSelected,
  onRecordingFromMicrophone: _onRecordingFromMicrophone,
  isLoading = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const audioFile = files[0];
      // Some browsers don't provide a clear mime type for all audio files
      if (audioFile.type.startsWith('audio/') || audioFile.name.endsWith('.wav') || audioFile.name.endsWith('.mp3') || audioFile.name.endsWith('.webm') || audioFile.name.endsWith('.m4a')) {
        onFileSelected(audioFile);
      } else {
        alert('Please drop an audio file');
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelected(e.target.files[0]);
    }
  };

  return (
    <div className="audio-uploader-section">
      <h3 className="section-title">Audio upload</h3>

      <div
        className={`upload-area ${isDragActive ? 'active' : ''}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-content">
          <p>
            Drag and drop audio file(s) here,{' '}
            <button
              className="link-button"
              onClick={() => fileInputRef.current?.click()}
            >
              browse files
            </button>
            , or{' '}
            <button
              className="link-button"
              onClick={() => fileInputRef.current?.click()}
            >
              record audio with a microphone
            </button>
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
        </div>

        <div className="timer-section">
          <span className="time-code">00:00</span>
        </div>
      </div>

      <div className="action-buttons">
        <button
          className="btn-primary"
          disabled={isLoading}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={16} />
          Browse Files
        </button>
      </div>
    </div>
  );
};

export default AudioUploader;
