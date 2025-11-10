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

export interface BatchPortfolioItem {
  id: string;
  name: string;
  portfolio_url: string;
}

export interface BatchResult {
  id: string;
  name: string;
  portfolio_url: string;
  score: number | null;
  status: 'success' | 'failed' | 'skipped';
  error?: string;
  analysis_time?: number;
  from_cache: boolean;
  checklist?: { [key: string]: ChecklistItem };
  ai_analysis?: string;
}

export interface BatchGradingResponse {
  total: number;
  successful: number;
  failed: number;
  avg_score: number | null;
  total_time: number;
  results: BatchResult[];
}

export const api = {
  async gradePortfolio(portfolioUrl: string, forceRefresh: boolean = false): Promise<GradingResult> {
    try {
      const response = await axios.post(`${API_BASE_URL}/grade`, {
        portfolio_url: portfolioUrl,
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

  async uploadCSV(file: File): Promise<{ portfolios: BatchPortfolioItem[]; count: number; message: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/batch-upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new APIError(
          error.response.data.detail || 'Failed to upload CSV',
          error.response.status
        );
      }
      throw new APIError('Failed to upload CSV file');
    }
  },

  async batchGradePortfolios(portfolios: BatchPortfolioItem[]): Promise<BatchGradingResponse> {
    try {
      const response = await axios.post(`${API_BASE_URL}/batch-grade`, {
        portfolios
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new APIError(
          error.response.data.detail || 'Batch grading failed',
          error.response.status
        );
      }
      throw new APIError('Batch grading failed');
    }
  },

  async exportBatchResultsCSV(results: BatchGradingResponse): Promise<Blob> {
    try {
      const response = await axios.post(`${API_BASE_URL}/batch-export-csv`, results, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      throw new APIError('Failed to export results as CSV');
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
  },

  async clearAllCache(): Promise<{ message: string; deleted_entries: number }> {
    try {
      const response = await axios.delete(`${API_BASE_URL}/cache/clear-all`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new APIError(
          error.response.data.detail || 'Failed to clear cache',
          error.response.status
        );
      }
      throw new APIError('Failed to clear cache');
    }
  }
};
