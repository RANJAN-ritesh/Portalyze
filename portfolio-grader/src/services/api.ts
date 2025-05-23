import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Update this with your backend URL

export interface GradingResult {
  score: number;
  feedback: string;
  details: {
    section: string;
    score: number;
    feedback: string;
  }[];
}

export class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'APIError';
  }
}

export const api = {
  async gradePortfolio(repoUrl: string): Promise<GradingResult> {
    try {
      const response = await axios.post(`${API_BASE_URL}/grade`, { repoUrl });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          throw new APIError('Unable to connect to the grading service. Please make sure the backend server is running.');
        }
        if (error.response) {
          throw new APIError(error.response.data.message || 'An error occurred during grading', error.response.status);
        }
        throw new APIError(error.message);
      }
      throw new APIError('An unexpected error occurred');
    }
  },
}; 