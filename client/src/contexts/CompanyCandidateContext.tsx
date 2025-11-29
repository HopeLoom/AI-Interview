import React, { createContext, useContext, useState, ReactNode } from 'react';
import { apiClient } from '@/services/apiClient';

export interface CompanyCandidateProfile {
  id: string;
  name: string;
  email: string;
  userType: 'candidate';
  isLoggedIn: boolean;
  createdAt: Date;
  // Company-candidate specific fields
  candidateDetails: {
    skills: string[];
    experience: number;
    location: string;
    phone?: string;
    linkedinUrl?: string;
    githubUrl?: string;
    portfolioUrl?: string;
    education?: {
      degree: string;
      institution: string;
      year: number;
    }[];
    workHistory?: {
      company: string;
      position: string;
      duration: string;
      description: string;
    }[];
  };
  // Company information for the candidate
  companyContext?: {
    companyId?: string;
    companyName?: string;
    interviewSessionId?: string;
    currentInterviewStep?: string;
  };
}

interface CompanyCandidateContextType {
  user: CompanyCandidateProfile | null;
  isLoading: boolean;
  login: (name: string, email: string, companyId: string, companyName: string) => Promise<void>;
  logout: () => void;
  updateProfile: (updates: Partial<CompanyCandidateProfile>) => void;
  updateCompanyContext: (companyUpdates: Partial<CompanyCandidateProfile['companyContext']>) => void;
  isLoggedIn: () => boolean;
  getCompanyId: () => string | null;
  getCompanyName: () => string | null;
}

const CompanyCandidateContext = createContext<CompanyCandidateContextType | undefined>(undefined);

export const useCompanyCandidate = () => {
  const context = useContext(CompanyCandidateContext);
  if (!context) {
    throw new Error('useCompanyCandidate must be used within a CompanyCandidateProvider');
  }
  return context;
};

interface CompanyCandidateProviderProps {
  children: ReactNode;
}

export const CompanyCandidateProvider: React.FC<CompanyCandidateProviderProps> = ({ children }) => {
  const [user, setUser] = useState<CompanyCandidateProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = async (
    name: string,
    email: string,
    options?: {
      companyId?: string;
      companyName?: string;
      interviewSessionId?: string;
      currentInterviewStep?: string;
    }
  ) => {
    try {
      const response = await apiClient.post('/api/candidates/login', {
        email,
        name
      });

      const candidate = response.data?.candidate;

      if (!candidate) {
        throw new Error('Candidate login failed');
      }

      const id = candidate.id ?? `candidate_${Date.now()}`;
      const candidateSkills = Array.isArray(candidate.skills) ? candidate.skills : [];
      const experience = Number(candidate.experience_years ?? candidate.experience ?? 0);
      const location = candidate.location ?? candidate.city ?? '';

      const userProfile: CompanyCandidateProfile = {
        id,
        name,
        email,
        userType: 'candidate',
        isLoggedIn: true,
        createdAt: new Date(candidate.createdAt || new Date()),
        candidateDetails: {
          skills: candidateSkills,
          experience,
          location,
          phone: candidate.phone,
          linkedinUrl: candidate.linkedinUrl || candidate.linkedin_url,
          githubUrl: candidate.githubUrl || candidate.github_url,
          portfolioUrl: candidate.portfolioUrl || candidate.portfolio_url,
          education: candidate.education,
          workHistory: candidate.workHistory || candidate.work_history
        },
        companyContext: {
          companyId: options?.companyId ?? candidate.company_id,
          companyName: options?.companyName ?? candidate.company_name,
          interviewSessionId: options?.interviewSessionId,
          currentInterviewStep: options?.currentInterviewStep ?? 'tutorial'
        }
      };

      // Remove undefined company context fields to avoid serialization noise
      if (!userProfile.companyContext?.companyId && !userProfile.companyContext?.companyName) {
        delete userProfile.companyContext;
      }

      setUser(userProfile);

      // Persist company-candidate user data for global access
      localStorage.setItem('companyCandidateProfile', JSON.stringify(userProfile));
      console.log('CompanyCandidateContext: Company-candidate user profile saved to localStorage');
    } catch (error) {
      throw new Error('Company-candidate login failed');
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('companyCandidateProfile');
    console.log('CompanyCandidateContext: Company-candidate user logged out, localStorage cleared');
  };

  const updateProfile = (updates: Partial<CompanyCandidateProfile>) => {
    if (user) {
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
      localStorage.setItem('companyCandidateProfile', JSON.stringify(updatedUser));
      console.log('CompanyCandidateContext: Company-candidate user profile updated in localStorage');
    }
  };

  const updateCompanyContext = (companyUpdates: Partial<CompanyCandidateProfile['companyContext']>) => {
    if (!user) {
      return;
    }

    const updatedUser: CompanyCandidateProfile = {
      ...user,
      companyContext: {
        ...(user.companyContext ?? {}),
        ...companyUpdates
      }
    };

    setUser(updatedUser);
    localStorage.setItem('companyCandidateProfile', JSON.stringify(updatedUser));
    console.log('CompanyCandidateContext: Company context updated:', companyUpdates);
  };

  const isLoggedIn = () => user?.isLoggedIn || false;
  const getCompanyId = () => user?.companyContext?.companyId || null;
  const getCompanyName = () => user?.companyContext?.companyName || null;

  // Load user from localStorage on mount
  React.useEffect(() => {
    console.log('CompanyCandidateContext: Loading company-candidate user from localStorage...');
    
    const savedUser = localStorage.getItem('companyCandidateProfile');
    console.log('CompanyCandidateContext: Saved user from localStorage:', savedUser ? 'Found' : 'Not found');
    
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        
        // Only restore if it's a candidate user
        if (parsedUser.userType === 'candidate') {
          parsedUser.createdAt = new Date(parsedUser.createdAt);
          console.log('CompanyCandidateContext: Restored company-candidate user:', parsedUser);
          setUser(parsedUser);
        } else {
          console.log('CompanyCandidateContext: Found non-candidate user in localStorage - clearing');
          localStorage.removeItem('companyCandidateProfile');
        }
      } catch (error) {
        console.error('CompanyCandidateContext: Failed to parse saved user profile');
        localStorage.removeItem('companyCandidateProfile');
      }
    } else {
      console.log('CompanyCandidateContext: No saved company-candidate user found in localStorage');
    }
    
    setIsLoading(false);
    console.log('CompanyCandidateContext: Loading complete, isLoading set to false');
  }, []);

  return (
    <CompanyCandidateContext.Provider value={{ 
      user, 
      isLoading,
      login, 
      logout, 
      updateProfile,
      updateCompanyContext,
      isLoggedIn, 
      getCompanyId,
      getCompanyName
    }}>
      {children}
    </CompanyCandidateContext.Provider>
  );
};
