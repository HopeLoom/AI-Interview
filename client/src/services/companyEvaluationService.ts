import { apiClient } from './apiClient';

// Types for company evaluations - matching backend CandidateEvaluationVisualisationReport
export interface OverallVisualSummary {
  score_label: string;
  key_insights: string[];
}

export interface CriteriaScoreVisualSummary {
  criteria: string;
  score: number;
  reason_bullets: string[];
  topics_covered: string[];
}

export interface CodeSubmissionVisualSummary {
  language: string;
  content: string;
}

export interface CodeDimensionSummary {
  name: string;
  comment: string;
  rating: string;
}

export interface CodeAnalysisVisualSummary {
  code_overall_summary: string[];
  code_dimension_summary: CodeDimensionSummary[];
  completion_percentage: number;
}

export interface PanelistFeedbackVisualSummary {
  name: string;
  role: string;
  summary_bullets: string[];
}

export interface ChatMessage {
  speaker: string;
  content: string;
  timestamp?: string;
}

export interface CandidateBackground {
  name: string;
  email: string;
  location?: string;
  experience_level?: string;
  skills?: string[];
  education?: string[];
}

export interface EvaluationReport {
  candidate_id: string;
  candidate_name: string;
  candidate_profile_image: string;
  overall_score: number;
  overall_visual_summary: OverallVisualSummary;
  criteria_scores: CriteriaScoreVisualSummary[];
  code_submission: CodeSubmissionVisualSummary;
  code_analysis: CodeAnalysisVisualSummary;
  panelist_feedback: PanelistFeedbackVisualSummary[];
  transcript: ChatMessage[];
  candidate_profile: CandidateBackground;
}

export interface EvaluationSummary {
  candidate_id: string;
  candidate_name: string;
  position: string;
  interview_date: string;
  overall_score: number;
  status: 'completed' | 'evaluated' | 'in_progress';
  key_strengths: string[];
  areas_for_improvement: string[];
  recommendation: 'hire' | 'consider' | 'reject' | 'strong_hire';
}

export interface EvaluationFilters {
  date_range?: {
    start_date: string;
    end_date: string;
  };
  score_range?: {
    min_score: number;
    max_score: number;
  };
  job_title?: string;
  status?: 'completed' | 'evaluated' | 'in_progress';
}

export class CompanyEvaluationService {
  /**
   * Get evaluation for a specific candidate
   */
  static async getCandidateEvaluation(
    companyId: string, 
    candidateId: string, 
    job_title?: string
  ): Promise<EvaluationReport> {
    try {
      let endpoint = `/api/evaluation/${companyId}/${candidateId}`;
      if (job_title) {
        endpoint += `?job_title=${job_title}`;
      }
      
      const response = await apiClient.get(endpoint);
      return response.data;
    } catch (error) {
      console.error('Failed to get candidate evaluation:', error);
      throw new Error('Unable to load candidate evaluation. Please try again.');
    }
  }

  /**
   * Get all evaluations for a company
   */
  static async getCompanyEvaluations(
    companyId: string, 
    filters?: EvaluationFilters
  ): Promise<EvaluationSummary[]> {
    try {
      let endpoint = `/api/evaluation/summary/${companyId}`;
      
      if (filters) {
        const params = new URLSearchParams();
        if (filters.date_range) {
          params.append('start_date', filters.date_range.start_date);
          params.append('end_date', filters.date_range.end_date);
        }
        if (filters.score_range) {
          params.append('min_score', filters.score_range.min_score.toString());
          params.append('max_score', filters.score_range.max_score.toString());
        }
        if (filters.job_title) {
          params.append('job_title', filters.job_title);
        }
        if (filters.status) {
          params.append('status', filters.status);
        }
        
        if (params.toString()) {
          endpoint += `?${params.toString()}`;
        }
      }
      
      const response = await apiClient.get(endpoint);
      return response.data;
    } catch (error) {
      console.error('Failed to get company evaluations:', error);
      throw new Error('Unable to load company evaluations. Please try again.');
    }
  }

  /**
   * Export evaluations to CSV/PDF
   */
  static async exportEvaluations(
    companyId: string, 
    format: 'csv' | 'pdf', 
    filters?: EvaluationFilters
  ): Promise<string> {
    try {
      let endpoint = `/api/company/${companyId}/evaluations/export?format=${format}`;
      
      if (filters) {
        const params = new URLSearchParams();
        if (filters.date_range) {
          params.append('start_date', filters.date_range.start_date);
          params.append('end_date', filters.date_range.end_date);
        }
        if (filters.score_range) {
          params.append('min_score', filters.score_range.min_score.toString());
          params.append('max_score', filters.score_range.max_score.toString());
        }
        if (filters.status) {
          params.append('status', filters.status);
        }
        
        if (params.toString()) {
          endpoint += `&${params.toString()}`;
        }
      }
      
      const response = await apiClient.get(endpoint);
      
      // Return the download URL or response message
      return response.data.download_url || response.data.message;
    } catch (error) {
      console.error('Failed to export evaluations:', error);
      throw new Error('Unable to export evaluations. Please try again.');
    }
  }

}
