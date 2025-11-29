import React, { createContext, useContext, ReactNode } from 'react';
import { useCompany, CompanyProvider, CompanyProfile } from '@/contexts/CompanyContext';
import { useCompanyCandidate, CompanyCandidateProvider, CompanyCandidateProfile } from '@/contexts/CompanyCandidateContext';


// Unified user profile type that can handle both flows
export type UserProfile = CompanyProfile | CompanyCandidateProfile;

// Unified context type that combines both context types
interface UnifiedUserContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (...args: any[]) => Promise<void>;
  logout: () => void;
  updateProfile: (updates: any) => void;
  isLoggedIn: () => boolean;
  // Company-specific methods (only available in company mode)
  signup?: (name: string, email: string, additionalData?: any) => Promise<void>;
  switchToMockUser?: () => void;
  clearMockUser?: () => void;
  // Company-candidate specific methods (only available in company-candidate mode)
  updateCompanyContext?: (companyUpdates: any) => void;
  getCompanyId?: () => string | null;
  getCompanyName?: () => string | null;
}

// Environment-based context selector hook
export const useUser = (): UnifiedUserContextType => {
  // Determine which context to use based on environment
  const mode = import.meta.env.VITE_APP_MODE || 'candidate-practice';
  
  console.log('UserContext: Current mode:', mode);
  
  const candidateModes = ['candidate-practice', 'company-candidate', 'company-candidate-interview'];

  if (candidateModes.includes(mode)) {
    // Use Company-Candidate Context
    console.log('UserContext: Using CompanyCandidateContext');
    const context = useCompanyCandidate();
    
    return {
      user: context.user,
      isLoading: context.isLoading,
      login: context.login,
      logout: context.logout,
      updateProfile: context.updateProfile,
      isLoggedIn: context.isLoggedIn,
      // Company-candidate specific methods
      updateCompanyContext: context.updateCompanyContext,
      getCompanyId: context.getCompanyId,
      getCompanyName: context.getCompanyName,
    };
  } else {
    // Use Company Context (default)
    console.log('UserContext: Using CompanyContext');
    const context = useCompany();
    
    return {
      user: context.user,
      isLoading: context.isLoading,
      login: context.login,
      logout: context.logout,
      updateProfile: context.updateProfile,
      isLoggedIn: context.isLoggedIn,
      // Company specific methods
      signup: context.signup,
      switchToMockUser: context.switchToMockUser,
      clearMockUser: context.clearMockUser,
    };
  }
};

// Helper functions to check user type
export const useUserType = () => {
  const { user } = useUser();
  
  return {
    isCompany: () => user?.userType === 'company',
    isCandidate: () => user?.userType === 'candidate',
    userType: user?.userType || null,
  };
};

// Type guards for user profile types
export const isCompanyProfile = (user: UserProfile | null): user is CompanyProfile => {
  return user?.userType === 'company';
};

export const isCompanyCandidateProfile = (user: UserProfile | null): user is CompanyCandidateProfile => {
  return user?.userType === 'candidate';
};

// Environment-based provider wrapper
interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  // Determine which provider to use based on environment
  const mode = import.meta.env.VITE_APP_MODE || 'candidate-practice';
  
  console.log('UserProvider: Current mode:', mode);
  
  const candidateModes = ['candidate-practice', 'company-candidate', 'company-candidate-interview'];

  if (candidateModes.includes(mode)) {
    // Use Company-Candidate Provider
    console.log('UserProvider: Using CompanyCandidateProvider');
    return (
      <CompanyCandidateProvider>
        {children}
      </CompanyCandidateProvider>
    );
  } else {
    // Use Company Provider (default)
    console.log('UserProvider: Using CompanyProvider');
    return (
      <CompanyProvider>
        {children}
      </CompanyProvider>
    );
  }
};

// Convenience hooks for accessing specific user data
export const useCompanyData = () => {
  const { user } = useUser();
  
  if (isCompanyProfile(user)) {
    return {
      companyId: user.companyDetails.id,
      companyName: user.companyDetails.name,
      industry: user.companyDetails.industry,
      size: user.companyDetails.size,
      location: user.companyDetails.location,
    };
  }
  
  return null;
};

export const useCompanyCandidateData = () => {
  const { user } = useUser();
  
  if (isCompanyCandidateProfile(user)) {
    return {
      candidateId: user.id,
      candidateName: user.name,
      candidateEmail: user.email,
      companyId: user.companyContext?.companyId,
      companyName: user.companyContext?.companyName,
      interviewSessionId: user.companyContext?.interviewSessionId,
      currentInterviewStep: user.companyContext?.currentInterviewStep,
    };
  }
  
  return null;
};

// Helper hook to get company ID regardless of user type
export const useCompanyId = () => {
  const { user } = useUser();
  
  if (isCompanyProfile(user)) {
    return user.companyDetails.id;
  } else if (isCompanyCandidateProfile(user)) {
    return user.companyContext?.companyId ?? null;
  }
  
  return null;
};

// Legacy exports for backward compatibility
export { useUser as useCompanyUser };
export { UserProvider as CompanyUserProvider };

console.log(`UserContext: Initialized with mode: ${import.meta.env.VITE_APP_MODE || 'company'}`);
