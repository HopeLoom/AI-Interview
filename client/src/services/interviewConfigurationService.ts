// Service for interview configuration API calls and configuration data fetching
import { SimpleConfigurationInput, GeneratedConfiguration } from '@/contexts/ConfigurationContext';

// Job types interfaces (merged from jobTypesService)
export interface JobType {
  value: string;
  label: string;
  description: string;
}

export interface JobTypesResponse {
  success: boolean;
  job_types: JobType[];
}

// Interview configuration interfaces
export interface Template {
  template_id: string;
  name: string;
  description: string;
  category: string;
  difficulty?: string;
  estimated_duration?: number;
  job_details?: any;
  rounds?: any[];
}

export interface ResumeUploadResponse {
  success: boolean;
  message: string;
  resume_data: {
    filename: string;
    content: string;
    file_path?: string;
  };
  warning?: string;
}

export interface CandidateCreationResponse {
  candidate_id: string;
  name: string;
  email: string;
  authentication_code: string;
  resume_url: string;
  success: boolean;
  message: string;
}

export interface BulkCandidateCreationResponse {
  success: boolean;
  candidates: CandidateCreationResponse[];
  errors: string[];
  warnings: string[];
}

export interface TemplateConfigurationUpdate {
  template_name: string;
  job_type: string;
  company_name: string;
  job_title: string;
  job_description: string;
  job_requirements: string[];
  job_qualifications: string[];
}

export class InterviewConfigurationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  // Main configuration generation method
  async generateFullConfiguration(
    config: SimpleConfigurationInput, 
    companyId: string,
    jobName: string 
  ): Promise<GeneratedConfiguration> {
    try {
      // Step 1: Upload job description file if it exists
      let jobFileId: string | null = null;
      if (config.job_details.input_type === 'pdf' && config.job_details.uploaded_file) {
        try {
          const jobUploadResponse = await this.uploadFile(
            config.job_details.uploaded_file,
            'job_description',
            companyId,
            jobName
          );
          jobFileId = jobUploadResponse.file_id;
        } catch (error) {
          console.error('Failed to upload job description file:', error);
          throw new Error('Job description file upload failed');
        }
      }

      // Step 2: Upload resume files sequentially
      const resumeFileIds: string[] = [];
      if (config.resume_data?.uploaded_files && config.resume_data.uploaded_files.length > 0) {
        for (let i = 0; i < config.resume_data.uploaded_files.length; i++) {
          const file = config.resume_data.uploaded_files[i];
          try {
            console.log(`Uploading resume ${i + 1}/${config.resume_data.uploaded_files.length}: ${file.name}`);
            const resumeUploadResponse = await this.uploadFile(
              file,
              'resume',
              companyId,
              jobName
            );
            resumeFileIds.push(resumeUploadResponse.file_id);
          } catch (error) {
            console.error(`Failed to upload resume ${file.name}:`, error);
            throw new Error(`Resume file upload failed: ${file.name}`);
          }
        }
      }

      // Step 3: Send configuration data with file references
      const configData = {
        job_details: {
          job_title: config.job_details.job_title, // Job title/position name
          input_type: config.job_details.input_type,
          source_filename: config.job_details.source_filename,
          source_url: config.job_details.source_url,
          file_size: config.job_details.file_size,
          file_type: config.job_details.file_type,
          job_file_id: jobFileId, // Reference to uploaded file
          job_description: config.job_details.job_description // Text content if not file
        },
        resume_data: {
          file_count: config.resume_data?.file_count || 0,
          resume_file_ids: resumeFileIds // Array of uploaded file IDs
        },
        userMode: config.userMode
      };

      const response = await fetch(`${this.baseUrl}/api/configurations/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Configuration generation failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Configuration generation failed:', error);
      throw new Error('Failed to generate interview configuration. Please try again.');
    }
  }

  // Enhanced file upload method
  async uploadFile(
    file: File, 
    fileType: 'job_description' | 'resume', 
    companyId: string, 
    jobName: string
  ): Promise<{ file_id: string; content: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    formData.append('company_id', companyId);
    formData.append('job_name', jobName);

    const response = await fetch(`${this.baseUrl}/api/configurations/upload-file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `${fileType} file upload failed`);
    }

    return await response.json();
  }

  // Job types methods (merged from jobTypesService)
  async getAvailableJobTypes(): Promise<JobType[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/configurations/job-types`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json() as JobTypesResponse;
      
      if (data.success) {
        return data.job_types;
      } else {
        throw new Error('Failed to fetch job types');
      }
    } catch (error) {
      console.error('Error fetching job types:', error);
      return [];
    }
  }

  // Keep the file upload methods we just added
  private async uploadJobDescriptionFile(file: File): Promise<{ file_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'job_description');

    const response = await fetch(`${this.baseUrl}/api/configurations/upload-file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Job description file upload failed');
    }

    return await response.json();
  }

  private async uploadResumeFile(file: File): Promise<{ file_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'resume');

    const response = await fetch(`${this.baseUrl}/api/configurations/upload-file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Resume file upload failed');
    }

    return await response.json();
  }

  /**
   * Generate mock configuration data as fallback when API fails
   */
  private getMockConfiguration(config: SimpleConfigurationInput): GeneratedConfiguration {
    return {
      success: true,
      configuration_id: `mock_config_${Date.now()}`,
      simulation_config: {
        simulation_id: "interview_001",
        simulation_name: "ML_Engineer_Interview",
        settings: {
          fast_llm: "gpt-4o",
          slow_llm: "gpt-4o",
          big_brain: true
        },
        interview_data: {
          job_details: {
            job_title: config.job_details.job_description?.includes('ML') ? "Senior ML Engineer" : "Software Engineer",
            job_description: config.job_details.job_description || "We are looking for a talented engineer to join our team...",
            job_requirements: [
              "Strong programming skills",
              "Experience with modern frameworks",
              "Knowledge of software design principles"
            ],
            job_qualifications: [
              "3+ years of experience",
              "Bachelor's degree in Computer Science or related field",
              "Experience with modern development practices"
            ],
            company_name: config.userMode === 'company' ? "Your Company" : "Practice Interview",
            company_description: config.userMode === 'company'
              ? "Company interview configuration"
              : "Mock interview for practice"
          },
          interview_round_details: {
            rounds: {
              "round_1": {
                description: "Technical Assessment",
                objective: "Evaluate technical skills and problem-solving abilities",
                metrics_covered: ["coding", "problem_solving", "technical_knowledge"],
                topic_info: [
                  {
                    name: "Coding Challenge",
                    description: "Implement a solution to a given problem",
                    time_limit: 45,
                    subtopics: [
                      {
                        name: "Problem Understanding",
                        description: "Clarify requirements and constraints",
                        time_limit: 10,
                        sections: ["Requirements", "Constraints"]
                      },
                      {
                        name: "Implementation",
                        description: "Write clean, efficient code",
                        time_limit: 30,
                        sections: ["Algorithm Design", "Code Quality"]
                      },
                      {
                        name: "Discussion",
                        description: "Explain approach and trade-offs",
                        time_limit: 5,
                        sections: ["Approach", "Trade-offs"]
                      }
                    ]
                  }
                ]
              },
              "round_2": {
                description: "System Design & Architecture",
                objective: "Assess system design thinking and scalability knowledge",
                metrics_covered: ["system_design", "architecture", "scalability"],
                topic_info: [
                  {
                    name: "System Design Challenge",
                    description: "Design a scalable system architecture",
                    time_limit: 60,
                    subtopics: [
                      {
                        name: "Requirements Analysis",
                        description: "Understand system requirements",
                        time_limit: 15,
                        sections: ["Functional Requirements", "Non-functional Requirements"]
                      },
                      {
                        name: "Architecture Design",
                        description: "Design system architecture",
                        time_limit: 35,
                        sections: ["High-level Design", "Component Design"]
                      },
                      {
                        name: "Discussion & Q&A",
                        description: "Address questions and concerns",
                        time_limit: 10,
                        sections: ["Design Decisions", "Trade-offs"]
                      }
                    ]
                  }
                ]
              }
            }
          },
          character_data: {
            data: [
              {
                character_id: "1",
                character_name: "Dr. Sarah Chen",
                role: "Senior Engineer",
                objective: "Evaluate technical depth and coding skills",
                job_description: "Expert in software engineering with 8+ years of experience",
                interview_round_part_of: "TECHNICAL_ROUND"
              },
              {
                character_id: "2",
                character_name: "Alex Rodriguez",
                role: "Engineering Manager",
                objective: "Assess system design and architecture skills",
                job_description: "Manages engineering infrastructure and platform teams",
                interview_round_part_of: "SYSTEM_DESIGN_ROUND"
              },
              {
                character_id: "3",
                character_name: "Lisa Thompson",
                role: "HR Manager",
                objective: "Evaluate cultural fit and communication skills",
                job_description: "Focuses on team culture and employee development",
                interview_round_part_of: "CULTURAL_FIT_ROUND"
              }
            ],
            reason: "Multi-disciplinary panel covering technical, architectural, and cultural aspects"
          },
          activity_details: {
            scenario: "Design and implement a scalable solution for a real-world problem",
            data_available: "Problem statement, requirements, and constraints",
            task_for_the_candidate: "Create a solution architecture and discuss implementation details"
          }
        },
        generated_question: "Design a system that can handle millions of concurrent users",
        generated_characters: [
          {
            name: "Technical Interviewer",
            role: "Senior Engineer",
            objective: "Assess technical skills"
          }
        ],
        candidate_profile: {
          name: "Candidate",
          skills: ["Programming", "System Design", "Problem Solving"]
        }
      },
      errors: [],
      warnings: ["Using mock data due to API failure"]
    };
  }
}

export const interviewConfigurationService = new InterviewConfigurationService();