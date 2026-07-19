import axios from 'axios';
import type { AssessmentResult, Config } from '../types';

// Default to a same-origin relative path so a single FastAPI deployment can
// serve both the API and the SPA. In local dev the Vite proxy (see
// vite.config.ts) forwards /api to the backend on :8000. Override with
// VITE_API_BASE_URL for split deployments (e.g. the docker-compose frontend).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const api = {
  // Get configuration (modes, languages)
  getConfig: async (): Promise<Config> => {
    try {
      const response = await apiClient.get('/config');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch config:', error);
      throw error;
    }
  },

  // Assess pronunciation from text
  assessFromText: async (
    mode: string,
    language: string,
    text: string
  ): Promise<AssessmentResult> => {
    try {
      const response = await apiClient.post('/assess/text', {
        mode,
        language,
        text,
      });
      const data = response.data;
      const azure = data.azure_result;
      
      return {
        pronunciation_score: azure.overall_score || 0,
        accuracy_score: azure.accuracy_score || 0,
        fluency_score: azure.fluency_score || 0,
        assessment_text: azure.reference_text || azure.recognized_text || '',
        errors: (azure.word_details || [])
          .filter((w: any) => w.error_type && w.error_type !== 'None')
          .map((w: any) => ({
            type: w.error_type.toLowerCase(),
            word: w.word,
            accuracy: w.accuracy_score
          })),
        word_details: azure.word_details,
        ai_report: data.ai_report,
      };
    } catch (error) {
      console.error('Failed to assess from text:', error);
      throw error;
    }
  },

  // Assess pronunciation from audio file
  assessFromAudio: async (
    mode: string,
    language: string,
    audioFile: File,
    text?: string,
    proficiencyLevel?: string,
    enableProsody?: boolean,
    enableMiscue?: boolean
  ): Promise<AssessmentResult> => {
    try {
      const formData = new FormData();
      formData.append('mode', mode);
      formData.append('language', language);
      formData.append('audio_file', audioFile);
      if (text) {
        formData.append('text', text);
      }
      if (proficiencyLevel) {
        formData.append('proficiency_level', proficiencyLevel);
      }
      if (enableProsody !== undefined) {
        formData.append('enable_prosody', String(enableProsody));
      }
      if (enableMiscue !== undefined) {
        formData.append('enable_miscue', String(enableMiscue));
      }

      const response = await apiClient.post('/assess/audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const data = response.data;
      const azure = data.azure_result;
      
      return {
        pronunciation_score: azure.overall_score || 0,
        accuracy_score: azure.accuracy_score || 0,
        fluency_score: azure.fluency_score || 0,
        assessment_text: azure.reference_text || azure.recognized_text || '',
        errors: (azure.word_details || [])
          .filter((w: any) => w.error_type && w.error_type !== 'None')
          .map((w: any) => ({
            type: w.error_type.toLowerCase() as any,
            word: w.word,
            accuracy: w.accuracy_score
          })),
        word_details: azure.word_details,
        ai_report: data.ai_report,
      };
    } catch (error) {
      console.error('Failed to assess from audio:', error);
      throw error;
    }
  },

  // Get available voices for a language
  getVoices: async (language: string): Promise<string[]> => {
    try {
      const response = await apiClient.get(`/voices/${language}`);
      return response.data.voices || [];
    } catch (error) {
      console.error('Failed to fetch voices:', error);
      return [];
    }
  },
};
