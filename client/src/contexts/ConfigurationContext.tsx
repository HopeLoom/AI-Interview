import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { interviewConfigurationService, Template } from '@/services/interviewConfigurationService';
import { useUser } from '@/contexts/UserContext';

// Simplified configuration types for the 3-step process
export interface SimpleJobDetails {
  job_title?: string; // Job title/position name
  job_description: string;
  input_type: 'pdf' | 'text' | 'url'; // How the job description was provided
  source_filename?: string; // If uploaded as PDF
  source_url?: string; // If provided as URL
  file_size?: number; // File size in bytes
  file_type?: string; // MIME type of the file
  uploaded_file?: File; // The actual File object for backend upload
}

export interface ResumeData {
  file_count?: number; // Number of resume files
  uploaded_files?: File[]
}

export interface SimpleConfigurationInput {
  job_details: SimpleJobDetails;
  resume_data?: ResumeData;
  userMode: 'candidate' | 'company';
}

export interface GeneratedConfiguration {
  success: boolean;
  configuration_id: string;
  simulation_config?: any;
  generated_question?: any;
  generated_characters?: any[];
  candidate_profile?: any;
  errors: string[];
  warnings: string[];
}

export interface ConfigurationState {
  // Current configuration being built
  currentConfig: SimpleConfigurationInput
  
  // Generation state
  isGenerating: boolean;
  generationProgress: number;
  generationStep: string;
  
  // Generated results
  generatedConfig?: GeneratedConfiguration;
  
  // Validation
  validationErrors: string[];
  validationWarnings: string[];
  
  // UI state
  currentStep: number;
  maxSteps: number;
  userMode: 'candidate' | 'company';
}

interface ConfigurationContextType {
  state: ConfigurationState;
  actions: {
    // Configuration building
    updateJobDetails: (jobDetails: Partial<SimpleJobDetails>) => void;
    setResumeData: (resume: ResumeData) => void;
    
    // Generation
    generateFullConfiguration: () => Promise<void>;
    
    // Navigation
    nextStep: () => void;
    previousStep: () => void;
    goToStep: (step: number) => void;
    
    // Validation
    validateConfiguration: () => boolean;
    clearValidation: () => void;
    
    // Reset
    resetConfiguration: () => void;
    updateUserMode: (mode: 'candidate' | 'company') => void;
  };
}

const ConfigurationContext = createContext<ConfigurationContextType | undefined>(undefined);

export const useConfiguration = () => {
  const context = useContext(ConfigurationContext);
  if (!context) {
    throw new Error('useConfiguration must be used within a ConfigurationProvider');
  }
  return context;
};

interface ConfigurationProviderProps {
  children: ReactNode;
}

const defaultJobDetails: SimpleJobDetails = {
  job_title: '',
  job_description: '',
  input_type: 'text'
};

const defaultConfigurationInput: SimpleConfigurationInput = {
  job_details: defaultJobDetails,
  userMode: 'company'
};

const defaultState: ConfigurationState = {
  currentConfig: defaultConfigurationInput,
  isGenerating: false,
  generationProgress: 0,
  generationStep: '',
  validationErrors: [],
  validationWarnings: [],
  currentStep: 1,
  maxSteps: 3,
  userMode: 'company'
};

export const ConfigurationProvider: React.FC<ConfigurationProviderProps> = ({ children }) => {
  const [state, setState] = useState<ConfigurationState>(defaultState);
  const { user } = useUser();
  
  // Debug initial state
  console.log('ConfigurationContext: Initial state:', defaultState);
  console.log('ConfigurationContext: Current state:', state);

  // Configuration building actions
  const updateJobDetails = (jobDetails: Partial<SimpleJobDetails>) => {
    setState(prev => ({
      ...prev,
      currentConfig: {
        ...prev.currentConfig,
        job_details: {
          ...prev.currentConfig.job_details,
          ...jobDetails
        }
      }
    }));
  };

  const setResumeData = (resume: ResumeData) => {
    setState(prev => ({
      ...prev,
      currentConfig: {
        ...prev.currentConfig,
        resume_data: resume
      }
    }));
  };

  // Update user mode and adjust steps accordingly
  const updateUserMode = (mode: 'candidate' | 'company') => {
    setState(prev => ({
      ...prev,
      userMode: mode,
      currentConfig: {
        ...prev.currentConfig,
        userMode: mode
      }
    }));
  };

  // Generation actions - use real API calls
  const generateFullConfiguration = async () => {
    setState(prev => ({ 
      ...prev, 
      isGenerating: true, 
      generationProgress: 0,
      generationStep: 'Starting configuration generation...'
    }));

    try {
      setState(prev => ({ ...prev, generationStep: 'Validating configuration...' }));
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setState(prev => ({ ...prev, generationStep: 'Generating interview setup...' }));
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setState(prev => ({ ...prev, generationProgress: 100, generationStep: 'Configuration complete!' }));
      let companyId = 'default_company';
      let jobName = 'default_job';
      if (user) {
        if (user.userType === 'company') {
          companyId = user.companyDetails.id;
          jobName = 'interview_configuration';
        } else if (user.userType === 'candidate') {
          companyId = user.companyContext?.companyId ?? 'default_company';
          jobName = 'candidate_interview';
        }
      }
      
      console.log('ConfigurationContext: Using company ID:', companyId, 'job name:', jobName);
      
      // Call the actual backend API with company ID
      const response = await interviewConfigurationService.generateFullConfiguration(
        state.currentConfig, 
        companyId, 
        jobName
      );
      
      if (response.success) {
        setState(prev => ({
          ...prev,
          generatedConfig: response,
          isGenerating: false
        }));
      } else {
        // Handle backend validation errors
        setState(prev => ({
          ...prev,
          isGenerating: false,
          validationErrors: response.errors || [`Configuration generation failed: Unknown error`]
        }));
      }
      
    } catch (error) {
      console.error('Configuration generation error:', error);
      setState(prev => ({
        ...prev,
        isGenerating: false,
        validationErrors: [`Configuration generation failed: ${error}`]
      }));
    }
  };

  // Removed generateQuestionOnly and generateCharactersOnly - these are part of main generation

  // Navigation actions
  const nextStep = () => {
    setState(prev => ({
      ...prev,
      currentStep: Math.min(prev.currentStep + 1, prev.maxSteps)
    }));
  };

  const previousStep = () => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 1)
    }));
  };

  const goToStep = (step: number) => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(1, Math.min(step, prev.maxSteps))
    }));
  };

  // Validation actions
  const validateConfiguration = (): boolean => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Simple validation for the 3-step process
    if (!state.currentConfig.job_details.job_description || 
        state.currentConfig.job_details.job_description.trim().length === 0) {
      errors.push('Job description is required');
    }
    
    if (!state.currentConfig.resume_data || !state.currentConfig.resume_data.uploaded_files || state.currentConfig.resume_data.uploaded_files.length === 0) {
      errors.push('At least one candidate resume is required');
    }
    
    setState(prev => ({
      ...prev,
      validationErrors: errors,
      validationWarnings: warnings
    }));
    
    return errors.length === 0;
  };

  const clearValidation = () => {
    setState(prev => ({
      ...prev,
      validationErrors: [],
      validationWarnings: []
    }));
  };

  // Reset action
  const resetConfiguration = () => {
    setState(defaultState);
  };

  const actions = {
    updateJobDetails,
    setResumeData,
    generateFullConfiguration,
    nextStep,
    previousStep,
    goToStep,
    validateConfiguration,
    clearValidation,
    resetConfiguration,
    updateUserMode
  };

  return (
    <ConfigurationContext.Provider value={{ state, actions }}>
      {children}
    </ConfigurationContext.Provider>
  );
};
