export type PronunciationMode = 'reading' | 'gaming';
export type Language = 'English (US)';
export type ProficiencyLevel = 'Beginner' | 'Intermediate' | 'Advanced';

export interface Config {
  modes: PronunciationMode[];
  languages: Language[];
  proficiencyLevels: ProficiencyLevel[];
}

export interface ErrorDetail {
  type: 'mispronunciation' | 'omission' | 'insertion';
  word: string;
  accuracy?: number;
}

export interface AIReport {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  full_report: string;
}

export interface WordResult {
  word: string;
  accuracy_score: number;
  error_type: string;
}

export interface AssessmentResult {
  pronunciation_score: number;
  accuracy_score: number;
  fluency_score: number;
  assessment_text: string;
  errors: ErrorDetail[];
  word_details?: WordResult[];
  audio_path?: string;
  duration?: number;
  ai_report?: AIReport;
  audio_url?: string;
}

export interface PronunciationRequest {
  mode: PronunciationMode;
  language: Language;
  text?: string;
  audio_file?: File;
}
