import { Candidate } from '../lib/types';
import { apiClient } from './apiClient';

// Additional candidate-related interfaces
export interface PracticeSession {
  id: string;
  title: string;
  role: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number;
  status: 'completed' | 'in-progress' | 'scheduled';
  completedAt?: Date;
  score?: number;
  feedback?: string;
}

export interface Skill {
  id?: string;
  name: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  category: 'technical' | 'soft-skills' | 'domain';
}

// Candidate signup interfaces (merged from candidateSignupService)
export interface CandidateSignupData {
  name: string;
  email: string;
  userType: 'candidate';
  phone?: string;
  skills: string[];
  experience: number;
  location: string;
  linkedinUrl?: string;
  githubUrl?: string;
  portfolioUrl?: string;
  resumeFile?: File;
}

export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  resume_data: {
    filename: string;
    content: string;
    file_path?: string;
  };
  extracted_info: {
    name?: string;
    email?: string;
    phone?: string;
    location?: string;
    skills: string[];
    education: string[];
    experience: string[];
    summary: string;
  };
}

export interface UserRegistrationResponse {
  success: boolean;
  message: string;
  user_id: string;
  profile: any;
  next_steps: string;
}

export class CandidateService {
  /**
   * Get all candidates
   */
  static async getCandidates(): Promise<any[]> {
    try {
      const response = await apiClient.get('/api/candidates');
      if (response.data?.success) {
        return response.data.candidates ?? [];
      }
      throw new Error('Failed to fetch candidates');
    } catch (error) {
      console.error('Candidates API failed:', error);
      throw error;
    }
  }

  /**
   * Get candidate by ID
   */
  static async getCandidateById(id: string): Promise<any | null> {
    try {
      const response = await apiClient.get(`/api/candidates/${id}`);
      if (response.data?.success) {
        return response.data.candidate;
      }
      throw new Error('Candidate not found');
    } catch (error) {
      console.error('Candidate API failed:', error);
      throw error;
    }
  }

  /**
   * Get practice sessions for a candidate
   */
  static async getPracticeSessions(candidateId: string): Promise<PracticeSession[]> {
    try {
      const response = await apiClient.get(`/api/candidates/${candidateId}/practice-sessions`);
      if (response.data?.success) {
        return response.data.practice_sessions ?? [];
      }
      throw new Error('Failed to fetch practice sessions');
    } catch (error) {
      console.error('Practice sessions API failed:', error);
      throw error;
    }
  }

  /**
   * Get skills for a candidate
   */
  static async getSkills(candidateId: string): Promise<Skill[]> {
    try {
      const response = await apiClient.get(`/api/candidates/${candidateId}/skills`);
      if (response.data?.success) {
        return response.data.skills ?? [];
      }
      throw new Error('Failed to fetch skills');
    } catch (error) {
      console.error('Skills API failed:', error);
      throw error;
    }
  }

  /**
   * Update candidate profile
   */
  static async updateProfile(candidateId: string, profileData: any): Promise<any> {
    try {
      await apiClient.put(`/api/candidates/${candidateId}`, profileData);
      const updated = await this.getCandidateById(candidateId);
      if (!updated) {
        throw new Error('Failed to load updated candidate');
      }
      return updated;
    } catch (error) {
      console.error('Profile update API failed:', error);
      throw error;
    }
  }

  /**
   * Add skill to candidate
   */
  static async addSkill(candidateId: string, skill: Omit<Skill, 'id'>): Promise<Skill> {
    try {
      await apiClient.post(`/api/candidates/${candidateId}/skills`, skill);
      return { ...skill };
    } catch (error) {
      console.warn('Add skill API failed, using mock response:', error);
      // Return mock skill with generated ID
      return { ...skill, id: `skill_${Date.now()}` };
    }
  }

  // Candidate signup methods (merged from candidateSignupService)
  /**
   * Upload resume and extract information
   */
  static async uploadResume(
    userId: string,
    resumeFile: File,
    extractInfo: boolean = true
  ): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('resume', resumeFile);
    formData.append('extract_info', extractInfo.toString());

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/candidates/enhanced-resume-upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Resume upload failed:', error);
      throw new Error('Failed to upload resume');
    }
  }

  /**
   * Register a new user
   */
  static async registerUser(
    userData: CandidateSignupData
  ): Promise<UserRegistrationResponse> {
    try {
      const response = await apiClient.post('/api/candidates/register-user', userData);
      return response.data;
    } catch (error) {
      console.error('User registration failed:', error);
      throw new Error('Failed to register user');
    }
  }

  /**
   * Complete candidate signup with resume
   */
  static async completeCandidateSignup(
    candidateData: CandidateSignupData
  ): Promise<UserRegistrationResponse> {
    try {
      // First, create a temporary user ID for resume upload
      const tempUserId = `temp_${Date.now()}`;
      
      let resumeData = null;
      let extractedInfo = null;

      // Upload resume if provided
      if (candidateData.resumeFile) {
        const resumeResponse = await this.uploadResume(
          tempUserId,
          candidateData.resumeFile
        );
        
        if (resumeResponse.success) {
          resumeData = resumeResponse.resume_data;
          extractedInfo = resumeResponse.extracted_info;
          
          // Update candidate data with extracted information
          if (extractedInfo) {
            if (extractedInfo.name && !candidateData.name) {
              candidateData.name = extractedInfo.name;
            }
            if (extractedInfo.email && !candidateData.email) {
              candidateData.email = extractedInfo.email;
            }
            if (extractedInfo.phone && !candidateData.phone) {
              candidateData.phone = extractedInfo.phone;
            }
            if (extractedInfo.location && !candidateData.location) {
              candidateData.location = extractedInfo.location;
            }
            if (extractedInfo.skills && extractedInfo.skills.length > 0) {
              // Merge extracted skills with user-provided skills
              const allSkills = Array.from(new Set([...candidateData.skills, ...extractedInfo.skills]));
              candidateData.skills = allSkills;
            }
          }
        }
      }

      // Register the user with all collected data
      const registrationData = {
        ...candidateData,
        resumeData,
        extractedInfo
      };

      return await this.registerUser(registrationData);
    } catch (error) {
      console.error('Candidate signup failed:', error);
      throw new Error('Failed to complete candidate signup');
    }
  }
}
