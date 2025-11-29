import { apiClient } from './apiClient';

// Types for company dashboard and interviews
export interface Candidate {
  id: string;
  name: string;
  email: string;
  position: string;
  status: 'pending' | 'completed' | 'in_progress';
  interview_date?: string;
  overall_score?: number;
  evaluation_id?: string;
  resume_url?: string;
  applied_date?: string;
}

export interface Interview {
  id: string;
  name: string;
  job_title: string;
  department: string;
  total_candidates: number;
  completed_candidates: number;
  average_score: number;
  status: 'active' | 'completed' | 'draft';
  created_date: string;
  last_activity: string;
  job_description?: string;
  requirements?: string[];
}

export interface SessionSummary {
  session_id: string;
  candidate_id?: string;
  candidate_name: string;
  candidate_email?: string;
  status: string;
  overall_score?: number;
  started_at?: string;
  completed_at?: string;
  interview_duration?: number;
  duration_minutes?: number;
  [key: string]: any;
}

export interface SessionEvaluationSummary {
  session_id: string;
  candidate_id?: string;
  candidate_name: string;
  candidate_email?: string;
  status?: string;
  overall_score?: number;
  evaluation?: any;
  completed_at?: string;
}

export interface CandidatesResponse {
  success: boolean;
  candidates: Candidate[];
  total: number;
}

export interface InterviewsResponse {
  success: boolean;
  interviews: Interview[];
  total: number;
}

export interface DashboardData {
  total_candidates: number;
  completed_interviews: number;
  pending_interviews: number;
  average_score: number;
  recent_interviews: Candidate[];
  active_jobs: number;
  total_evaluations: number;
}

export interface DashboardResponse {
  success: boolean;
  dashboard: DashboardData;
}

export interface CandidatePipelineData {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  shortlisted: number;
  pipeline: Array<{
    stage: string;
    count: number;
    percentage: number;
  }>;
}

export interface JobPosting {
  id: string;
  company_id: string;
  title: string;
  description: string;
  requirements: string[];
  location?: string;
  job_type?: string;
  experience_level?: string;
  salary_range?: string;
  benefits: string[];
  status: 'active' | 'closed' | 'draft';
  created_at?: string;
  updated_at?: string;
}

export class CompanyDashboardService {
  /**
   * Get company dashboard overview data
   */
  static async getCompanyDashboard(companyId: string): Promise<DashboardData> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/dashboard`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch dashboard data');
      }
      return response.data.dashboard;
    } catch (error) {
      console.error('Failed to get dashboard data:', error);
      throw new Error('Unable to load dashboard data. Please try again.');
    }
  }

  static async getDashboardData(companyId: string): Promise<DashboardData> {
    return this.getCompanyDashboard(companyId);
  }

  /**
   * Get all interviews for a company
   */
  static async getCompanyInterviews(companyId: string): Promise<Interview[]> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/interviews`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch interviews');
      }
      return response.data.interviews || [];
    } catch (error) {
      console.error('Failed to get interviews:', error);
      throw new Error('Unable to load interviews. Please try again.');
    }
  }

  static async getInterviews(companyId: string): Promise<Interview[]> {
    return this.getCompanyInterviews(companyId);
  }

  /**
   * Get sessions for a specific interview configuration
   */
  static async getInterviewSessions(companyId: string, configurationId: string): Promise<SessionSummary[]> {
    const response = await apiClient.get(`/api/companies/${companyId}/interviews/${configurationId}/sessions`);

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch interview sessions');
    }

    return response.data.sessions || [];
  }

  /**
   * Get evaluation summaries for sessions in a configuration
   */
  static async getInterviewEvaluations(
    companyId: string,
    configurationId: string
  ): Promise<SessionEvaluationSummary[]> {
    const response = await apiClient.get(`/api/companies/${companyId}/interviews/${configurationId}/evaluations`);

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch interview evaluations');
    }

    return response.data.evaluations || [];
  }

  /**
   * Get detailed evaluation for a specific session
   */
  static async getSessionEvaluation(sessionId: string): Promise<any> {
    const response = await apiClient.get(`/api/configurations/sessions/${sessionId}/evaluation`);

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch session evaluation');
    }

    return response.data;
  }

  /**
   * Get candidates for a specific interview
   */
  static async getInterviewCandidates(companyId: string, interviewId: string): Promise<Candidate[]> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/interviews/${interviewId}/candidates`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch interview candidates');
      }
      return response.data.candidates || [];
    } catch (error) {
      console.error('Failed to get interview candidates:', error);
      throw new Error('Unable to load interview candidates. Please try again.');
    }
  }

  /**
   * Get all candidates for a company
   */
  static async getCompanyCandidates(companyId: string): Promise<Candidate[]> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/candidates`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch candidates');
      }
      return response.data.candidates || [];
    } catch (error) {
      console.error('Failed to get candidates:', error);
      throw new Error('Unable to load candidates. Please try again.');
    }
  }

  static async getCandidates(companyId: string): Promise<Candidate[]> {
    return this.getCompanyCandidates(companyId);
  }

  /**
   * Get candidate pipeline data
   */
  static async getCandidatePipeline(companyId: string): Promise<CandidatePipelineData> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/candidates/pipeline`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch candidate pipeline');
      }
      return response.data.pipeline || response.data;
    } catch (error) {
      console.error('Failed to get candidate pipeline:', error);
      throw new Error('Unable to load candidate pipeline data. Please try again.');
    }
  }

  /**
   * Get company job postings
   */
  static async getCompanyJobPostings(companyId: string): Promise<JobPosting[]> {
    try {
      const response = await apiClient.get(`/api/companies/${companyId}/job-postings`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to fetch job postings');
      }
      return response.data.job_postings || [];
    } catch (error) {
      console.error('Failed to get job postings:', error);
      throw new Error('Unable to load job postings. Please try again.');
    }
  }

  /**
   * Create a new job posting
   */
  static async createJobPosting(companyId: string, jobData: Partial<JobPosting>): Promise<JobPosting> {
    const response = await apiClient.post(`/api/job-postings`, {
      company_id: companyId,
      ...jobData
    });

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to create job posting');
    }

    // Fetch the created job posting
    const jobId = response.data.job_id;
    const jobResponse = await apiClient.get(`/api/job-postings/${jobId}`);

    return jobResponse.data.job_posting;
  }

  /**
   * Update job posting status
   */
  static async updateJobPostingStatus(companyId: string, jobId: string, status: JobPosting['status']): Promise<void> {
    const response = await apiClient.put(`/api/job-postings/${jobId}`, { status });

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to update job posting status');
    }
  }


  /**
   * Get recent activity for company
   */
  static async getRecentActivity(companyId: string, limit: number = 10): Promise<Array<{
    type: 'interview_started' | 'evaluation_completed' | 'candidate_applied' | 'job_posting_created';
    timestamp: string;
    description: string;
    related_id: string;
  }>> {
    const response = await apiClient.get(`/api/companies/${companyId}/activity?limit=${limit}`);

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch recent activity');
    }

    return response.data.activities || [];
  }

  /**
   * Get interview configurations for a company
   */
  static async getCompanyInterviewConfigurations(companyId: string): Promise<Array<any>> {
    const response = await apiClient.get(`/api/companies/${companyId}/interview-configurations`);

    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to fetch interview configurations');
    }

    return response.data.configurations || [];
  }
}
