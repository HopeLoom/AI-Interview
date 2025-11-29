"""
Data models for interview configuration system.
These models handle communication between frontend and backend.
"""

from typing import Dict, List, Optional

from interview_details_agent.base import JobDetails
from pydantic import BaseModel, Field


class ResumeUploadData(BaseModel):
    """Resume upload information"""

    filename: str
    content: str = Field(..., description="Parsed resume content")
    file_path: Optional[str] = None


class FrontendJobDetails(BaseModel):
    """Job details as sent from frontend"""

    job_title: Optional[str] = None
    job_description: str
    input_type: str = Field(..., description="'pdf' or 'text'")
    source_filename: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    job_file_id: Optional[str] = None


class FrontendResumeData(BaseModel):
    """Resume data as sent from frontend"""

    file_count: Optional[int] = 0
    resume_file_ids: Optional[List[str]] = []


class FrontendConfigurationInput(BaseModel):
    """Complete configuration input from frontend"""

    job_details: FrontendJobDetails
    resume_data: Optional[FrontendResumeData] = None
    userMode: str = Field(default="company", description="candidate or company")


class BulkResumeUploadRequest(BaseModel):
    """Request for bulk resume processing"""

    company_id: str
    job_name: str
    resumes: List[ResumeUploadData]
    generate_auth_codes: bool = True


class CandidateCreationResponse(BaseModel):
    """Response after candidate creation"""

    candidate_id: str
    name: str
    email: str
    authentication_code: str
    resume_url: str
    success: bool
    message: str


class BulkCandidateCreationResponse(BaseModel):
    """Response after bulk candidate creation"""

    success: bool
    candidates: List[CandidateCreationResponse]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AuthenticationCodeData(BaseModel):
    """Authentication code information"""

    code: str
    generated_at: str
    expires_at: Optional[str] = None
    is_used: bool = False


class TemplateConfigurationUpdate(BaseModel):
    """Template configuration update request"""

    template_name: str
    job_type: str
    company_name: str
    job_title: str
    job_description: str
    job_requirements: List[str]
    job_qualifications: List[str]


class ConfigurationGenerationResponse(BaseModel):
    """Response after configuration generation"""

    success: bool
    configuration_id: str = ""
    invitation_code: str = ""  # Short code for candidates to join (e.g., "ABC123")
    simulation_config: Optional[Dict] = None
    generated_question: Optional[Dict] = None
    generated_characters: Optional[List[Dict]] = None
    candidate_profile: Optional[Dict] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ConfigurationValidationResult(BaseModel):
    """Result of configuration validation"""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    estimated_duration: float = 0.0  # Total estimated interview duration


class RoundConfiguration(BaseModel):
    """Round configuration for interview templates"""

    round_id: str
    name: str
    description: str
    duration: int
    topics: List[str] = Field(default_factory=list)


class ConfigurationTemplate(BaseModel):
    """Reusable configuration template"""

    template_id: str
    name: str
    description: str
    category: str = "general"  # e.g., "ml_engineer", "frontend", etc.
    job_details: JobDetails
    rounds: List[RoundConfiguration]
    created_by: str = "system"
    is_public: bool = True


# ============================================================================
# COMPANY & CANDIDATE MANAGEMENT MODELS
# ============================================================================


class CompanyData(BaseModel):
    """Company profile data"""

    id: Optional[str] = None
    name: str
    contact_email: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CandidateData(BaseModel):
    """Candidate profile data"""

    id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    education: Optional[str] = None
    current_role: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobPostingData(BaseModel):
    """Job posting data"""

    id: Optional[str] = None
    company_id: str
    title: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract
    experience_level: Optional[str] = None  # junior, mid, senior
    salary_range: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    status: str = "active"  # active, closed, draft
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CandidateApplicationData(BaseModel):
    """Candidate application for a job posting"""

    id: Optional[str] = None
    candidate_id: str
    job_posting_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    status: str = "applied"  # applied, screening, interviewing, offered, rejected, accepted
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    applied_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None


class CompanyDashboardData(BaseModel):
    """Company dashboard summary data"""

    total_job_postings: int = 0
    active_job_postings: int = 0
    total_candidates: int = 0
    total_applications: int = 0
    recent_applications: List[Dict] = Field(default_factory=list)
    upcoming_interviews: List[Dict] = Field(default_factory=list)


class JobPostingSummary(BaseModel):
    """Summary of a job posting for dashboard"""

    id: str
    title: str
    status: str
    location: Optional[str] = None
    applications_count: int = 0
    interviews_scheduled: int = 0
    created_date: Optional[str] = None
    last_updated: Optional[str] = None


class CandidateSummary(BaseModel):
    """Summary of a candidate for company dashboard"""

    id: str
    name: str
    email: str
    applied_jobs: List[str] = Field(default_factory=list)
    total_applications: int = 0
    interview_status: Optional[str] = None
    last_activity: Optional[str] = None
