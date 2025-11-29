import { CompanyProfile } from '@/contexts/CompanyContext';
import { CompanyCandidateProfile } from '@/contexts/CompanyCandidateContext';

// Type guards for user profile types
export const isCompanyProfile = (user: CompanyProfile | CompanyCandidateProfile | null): user is CompanyProfile => {
  return user?.userType === 'company';
};

export const isCompanyCandidateProfile = (user: CompanyProfile | CompanyCandidateProfile | null): user is CompanyCandidateProfile => {
  return user?.userType === 'candidate';
};

// Helper functions for accessing specific user data
export const getCompanyData = (user: CompanyProfile | CompanyCandidateProfile | null) => {
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

export const getCompanyCandidateData = (user: CompanyProfile | CompanyCandidateProfile | null) => {
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

// Helper function to get company ID regardless of user type
export const getCompanyId = (user: CompanyProfile | CompanyCandidateProfile | null) => {
  if (isCompanyProfile(user)) {
    return user.companyDetails.id;
  } else if (isCompanyCandidateProfile(user)) {
    return user.companyContext?.companyId ?? null;
  }
  
  return null;
};
