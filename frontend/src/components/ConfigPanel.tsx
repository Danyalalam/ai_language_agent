import React, { useEffect, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { PronunciationMode, Language, ProficiencyLevel } from '../types';
import { api } from '../services/api';
import '../styles/ConfigPanel.css';

interface ConfigPanelProps {
  mode: PronunciationMode;
  language: Language;
  proficiencyLevel: ProficiencyLevel;
  enableProsody: boolean;
  enableMiscue: boolean;
  onModeChange: (mode: PronunciationMode) => void;
  onLanguageChange: (language: Language) => void;
  onProficiencyChange: (level: ProficiencyLevel) => void;
  onProsodyToggle: (enabled: boolean) => void;
  onMiscueToggle: (enabled: boolean) => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({
  mode,
  language,
  proficiencyLevel,
  enableProsody,
  enableMiscue,
  onModeChange,
  onLanguageChange,
  onProficiencyChange,
  onProsodyToggle,
  onMiscueToggle,
}) => {
  const [availableModes, setAvailableModes] = useState<PronunciationMode[]>([]);
  const [availableLanguages, setAvailableLanguages] = useState<Language[]>([]);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await api.getConfig();
        setAvailableModes(config.modes as PronunciationMode[]);
        setAvailableLanguages(config.languages as Language[]);
      } catch (error) {
        console.error('Error fetching config:', error);
        // Fallback defaults
        setAvailableModes(['reading', 'gaming']);
        setAvailableLanguages(['English (US)']);
      }
    };
    fetchConfig();
  }, []);

  const getModeDescription = (m: PronunciationMode): string => {
    const descriptions: Record<PronunciationMode, string> = {
      reading: 'Read a prepared script to receive pronunciation scores.',
      gaming: 'Read a tongue twister to receive scores for pronunciation and for each syllable.',
    };
    return descriptions[m];
  };

  return (
    <div className="config-panel">
      <h1 className="config-title">Speech Playground</h1>

      <div className="config-section">
        <label className="section-label">Pronunciation mode</label>

        <div className="radio-group">
          {availableModes.map((m) => (
            <div key={m} className="radio-item">
              <input
                type="radio"
                id={`mode-${m}`}
                name="pronunciation-mode"
                value={m}
                checked={mode === m}
                onChange={() => onModeChange(m)}
              />
              <label htmlFor={`mode-${m}`}>
                <span className="mode-title">{m.charAt(0).toUpperCase() + m.slice(1)}</span>
                <span className="mode-description">{getModeDescription(m)}</span>
              </label>
            </div>
          ))}
        </div>
      </div>

      <div className="config-section">
        <label htmlFor="language-select" className="section-label">
          Language to assess
        </label>

        <div className="dropdown-wrapper">
          <button
            className="dropdown-button"
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
          >
            <span>{language}</span>
            <ChevronDown size={20} />
          </button>

          {showLanguageMenu && (
            <div className="dropdown-menu">
              {availableLanguages.map((lang) => (
                <button
                  key={lang}
                  className={`dropdown-item ${lang === language ? 'active' : ''}`}
                  onClick={() => {
                    onLanguageChange(lang);
                    setShowLanguageMenu(false);
                  }}
                >
                  {lang}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="config-section">
        <button
          className={`advanced-options-toggle ${showAdvanced ? 'active' : ''}`}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? 'Hide advanced options' : 'Show advanced options'}
          <ChevronDown size={16} style={{ transform: showAdvanced ? 'rotate(180deg)' : 'none' }} />
        </button>

        {showAdvanced && (
          <div className="advanced-options-panel">
            <div className="advanced-field">
              <label className="field-label">Proficiency Level</label>
              <select
                value={proficiencyLevel}
                onChange={(e) => onProficiencyChange(e.target.value as ProficiencyLevel)}
                className="advanced-select"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>

            <div className="advanced-field checkbox-field">
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={enableProsody}
                  onChange={(e) => onProsodyToggle(e.target.checked)}
                />
                <span>Enable Prosody Assessment</span>
              </label>
            </div>

            <div className="advanced-field checkbox-field">
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={enableMiscue}
                  onChange={(e) => onMiscueToggle(e.target.checked)}
                />
                <span>Enable Miscue Detection (Insertion/Omission)</span>
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConfigPanel;
