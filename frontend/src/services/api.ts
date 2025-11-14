import axios from 'axios';

// Strip trailing slash to prevent double slashes in URLs
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface GradingResult {
  portfolio_url: string;
  score: number;
  checklist: { [key: string]: ChecklistItem };
  ai_analysis: string;
  ai_provider: string;
  professional_photo: {
    exists: boolean;
    has_face: boolean;
    confidence: number | null;
    is_professional: boolean;
    details: string;
  };
  learning_resources: LearningResource[];
  responsive_check?: {
    mobile?: { passes: boolean };
    tablet?: { passes: boolean };
    desktop?: { passes: boolean };
  };
  analysis_time: number;
  from_cache: boolean;
  share_url?: string;
}

export interface ChecklistItem {
  pass: boolean;
  details: string[];
}

export interface LearningResource {
  title: string;
  description: string;
  tips: string[];
}

export class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'APIError';
  }
}

export const api = {
  async gradePortfolio(portfolioUrl: string, geminiApiKey: string, forceRefresh: boolean = false): Promise<GradingResult> {
    try {
      const response = await axios.post(`${API_BASE_URL}/grade`, {
        portfolio_url: portfolioUrl,
        gemini_api_key: geminiApiKey,
        force_refresh: forceRefresh
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          throw new APIError(
            'Unable to connect to the grading service. Please make sure the backend server is running on port 8000.'
          );
        }
        if (error.response) {
          const message = error.response.data.detail || error.response.data.message || 'An error occurred during grading';
          throw new APIError(message, error.response.status);
        }
        throw new APIError(error.message);
      }
      throw new APIError('An unexpected error occurred');
    }
  },

  async getSharedResult(shareId: string): Promise<GradingResult> {
    try {
      const response = await axios.get(`${API_BASE_URL}/share/${shareId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new APIError(
          error.response.data.detail || 'Shared result not found',
          error.response.status
        );
      }
      throw new APIError('Failed to load shared result');
    }
  },

  async getSystemStatus() {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      return response.data;
    } catch (error) {
      return { status: 'unavailable' };
    }
  }
};
