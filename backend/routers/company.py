"""
Company router for managing company operations.
Handles company authentication, profile management, and dashboard data.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from globals import main_logger
from interview_configuration.database_service import InterviewConfigurationDatabase
from interview_configuration.models import CompanyData
from pydantic import BaseModel

from core.database.base import CompanyProfile
from core.database.db_manager import get_database

router = APIRouter(prefix="/api/companies", tags=["companies"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_db_service():
    """Get database service instance"""
    return InterviewConfigurationDatabase()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class CompanyLoginRequest(BaseModel):
    email: str
    password: str


class CompanySignupRequest(BaseModel):
    name: str
    email: str
    userType: str = "company"
    industry: str
    size: str
    location: str
    website: Optional[str] = None
    description: Optional[str] = None


class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    company_id: str
    name: str
    email: str
    industry: str
    size: str
    location: str
    website: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CompanyLoginResponse(BaseModel):
    success: bool
    message: str
    company: CompanyResponse
    token: str


class CompanyRegistrationResponse(BaseModel):
    success: bool
    message: str
    company_id: str
    profile: CompanyResponse
    next_steps: str


class CandidateResponse(BaseModel):
    candidate_id: str
    name: str
    email: str
    position: str = "Unknown"
    status: str
    interview_date: Optional[str] = None
    overall_score: Optional[float] = None
    evaluation_id: Optional[str] = None
    resume_url: Optional[str] = None
    applied_date: Optional[str] = None

    def to_frontend_format(self):
        return {
            "id": self.candidate_id,
            "name": self.name,
            "email": self.email,
            "position": self.position,
            "status": self.status,
            "interview_date": self.interview_date,
            "overall_score": self.overall_score,
            "evaluation_id": self.evaluation_id,
            "resume_url": self.resume_url,
            "applied_date": self.applied_date,
        }


class CompanyInfo(BaseModel):
    company_id: str
    name: str
    industry: str
    size: str
    location: str


class DashboardData(BaseModel):
    total_candidates: int
    completed_interviews: int
    pending_interviews: int
    average_score: float
    recent_interviews: list[CandidateResponse]
    active_jobs: int
    total_evaluations: int


class CompanyDashboardResponse(BaseModel):
    success: bool
    dashboard: DashboardData


class CompanyCandidatesResponse(BaseModel):
    success: bool
    candidates: list[CandidateResponse]
    total: int


# ============================================================================
# COMPANY AUTHENTICATION
# ============================================================================


@router.post("/login", response_model=CompanyLoginResponse)
async def company_login(credentials: CompanyLoginRequest):
    """
    Company login endpoint
    """
    try:
        email = credentials.email

        # Try to get from database first
        try:
            database = await get_database(main_logger)
            company = await database.get_company_by_email(email)

            if company:
                company_response = CompanyResponse(
                    company_id=company.company_id,
                    name=company.name,
                    email=company.email,
                    industry=company.industry,
                    size=company.size,
                    location=company.location,
                    website=company.website,
                    description=company.description,
                    created_at=company.created_at,
                    updated_at=company.updated_at,
                )

                return CompanyLoginResponse(
                    success=True,
                    message="Login successful",
                    company=company_response,
                    token=f"token_{company.company_id}",
                )
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")

        except Exception:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/register-company", response_model=CompanyRegistrationResponse)
async def register_company(company_data: CompanySignupRequest):
    """
    Register a new company
    """
    try:
        database = await get_database(main_logger)

        # Check if company email already exists
        existing_company = await database.get_company_by_email(company_data.email)
        if existing_company:
            raise HTTPException(status_code=400, detail="Company with this email already exists")

        # Generate company ID
        company_id = f"company_{uuid.uuid4().hex[:8]}"

        # Create company profile
        company_profile = CompanyProfile(
            company_id=company_id,
            name=company_data.name,
            email=company_data.email,
            industry=company_data.industry,
            size=company_data.size,
            location=company_data.location,
            website=company_data.website,
            description=company_data.description,
            created_at=datetime.now().isoformat(),
            is_active=True,
        )

        # Save to database
        success = await database.create_company(company_profile)

        if success:
            company_response = CompanyResponse(
                company_id=company_profile.company_id,
                name=company_profile.name,
                email=company_profile.email,
                industry=company_profile.industry,
                size=company_profile.size,
                location=company_profile.location,
                website=company_profile.website,
                description=company_profile.description,
                created_at=company_profile.created_at,
            )

            return CompanyRegistrationResponse(
                success=True,
                message="Company registered successfully",
                company_id=company_id,
                profile=company_response,
                next_steps="You can now log in and start using the platform",
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to register company")

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Company registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/email/{email}")
async def get_company_by_email_route(email: str):
    """Get company details by email"""
    try:
        database = await get_database(main_logger)
        company = await database.get_company_by_email(email)

        if company:
            company_response = CompanyResponse(
                company_id=company.company_id,
                name=company.name,
                email=company.email,
                industry=company.industry,
                size=company.size,
                location=company.location,
                website=company.website,
                description=company.description,
                created_at=company.created_at,
                updated_at=company.updated_at,
            )
            return {"success": True, "company": company_response}
        else:
            raise HTTPException(status_code=404, detail="Company not found")

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get company by email {email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/validate-session")
async def validate_company_session():
    """Basic session validation placeholder"""
    return {"valid": True}


@router.post("/logout")
async def company_logout(payload: dict[str, Any]):
    """Placeholder logout endpoint"""
    token = payload.get("token")
    main_logger.info(f"Company logout requested for token: {token}")
    return {"success": True, "message": "Logout successful"}


# ============================================================================
# COMPANY PROFILE MANAGEMENT
# ============================================================================


@router.post("")
async def create_company(
    company_data: CompanyData, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Create a new company profile

    Args:
        company_data: Company information

    Returns:
        Created company ID and profile
    """
    try:
        # Check if company with email already exists
        existing_company = await db_service.get_company_by_email(company_data.contact_email)
        if existing_company:
            raise HTTPException(status_code=400, detail="Company with this email already exists")

        # Create company
        company_id = await db_service.create_company(company_data.dict(exclude_none=True))

        main_logger.info(f"Company created successfully: {company_id}")

        return {
            "success": True,
            "company_id": company_id,
            "message": "Company created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to create company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create company: {e!s}")


@router.get("/{company_id}")
async def get_company(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get company details by ID

    Args:
        company_id: Company ID

    Returns:
        Company profile
    """
    try:
        company = await db_service.get_company(company_id)

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Try database first
        try:
            database = await get_database(main_logger)
            company = await database.get_company_by_id(company_id)

            if company:
                company_response = CompanyResponse(
                    company_id=company.company_id,
                    name=company.name,
                    email=company.email,
                    industry=company.industry,
                    size=company.size,
                    location=company.location,
                    website=company.website,
                    description=company.description,
                    created_at=company.created_at,
                    updated_at=company.updated_at,
                )
                return {"success": True, "company": company_response}
            else:
                raise HTTPException(status_code=404, detail="Company not found")

        except Exception:
            raise HTTPException(status_code=404, detail="Company not found")

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{company_id}")
async def update_company(company_id: str, update_data: CompanyUpdateRequest):
    """
    Update company profile

    Args:
        company_id: Company ID
        update_data: Fields to update

    Returns:
        Success status
    """
    try:
        database = await get_database(main_logger)

        # Check if company exists
        company = await database.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Prepare update data (exclude None values)
        updates = {k: v for k, v in update_data.dict().items() if v is not None}

        if updates:
            success = await database.update_company(company_id, updates)
            if success:
                return {"message": "Company updated successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update company")
        else:
            return {"message": "No updates provided"}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to update company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY DASHBOARD
# ============================================================================


@router.get("/{company_id}/dashboard")
async def get_company_dashboard(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get company dashboard data

    Args:
        company_id: Company ID

    Returns:
        Dashboard metrics and summaries
    """
    try:
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get dashboard data
        dashboard_data = await db_service.get_company_dashboard_data(company_id)

        return {
            "success": True,
            "dashboard": dashboard_data.dict()
            if hasattr(dashboard_data, "dict")
            else dashboard_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get dashboard for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY CANDIDATES
# ============================================================================


@router.get("/{company_id}/candidates")
async def get_company_candidates(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get list of candidates for a company

    Args:
        company_id: Company ID

    Returns:
        List of candidate summaries
    """
    try:
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get candidates summary
        candidates = await db_service.get_candidates_summary_by_company(company_id)

        # Try database first
        try:
            database = await get_database(main_logger)
            candidates = await database.get_candidates_by_company_id(company_id)

            if candidates:
                candidate_responses = []
                for candidate in candidates:
                    # Get candidate's most recent session to determine status
                    sessions = await database.get_candidate_interview_sessions(candidate.user_id)
                    status = "pending"
                    interview_date = None
                    overall_score = None
                    evaluation_id = None
                    position = "Unknown"

                    if sessions:
                        # Check if any session is completed
                        completed_sessions = [s for s in sessions if s.status == "completed"]
                        if completed_sessions:
                            status = "completed"
                            # Get the most recent completed session
                            recent_session = completed_sessions[0]
                            interview_date = recent_session.start_time
                            evaluation_id = recent_session.session_id

                            # Get evaluation data
                            evaluation = await database.get_candidate_evaluation_data(
                                candidate.user_id, recent_session.session_id
                            )
                            if evaluation and "final_evaluation" in evaluation:
                                try:
                                    eval_data = json.loads(evaluation["final_evaluation"])
                                    overall_score = eval_data.get("overall_score")
                                    position = eval_data.get("position", "Unknown")
                                except (json.JSONDecodeError, KeyError):
                                    pass

                    candidate_response = CandidateResponse(
                        candidate_id=candidate.user_id,
                        name=candidate.name,
                        email=candidate.email,
                        position=position,
                        status=status,
                        interview_date=interview_date,
                        overall_score=overall_score,
                        evaluation_id=evaluation_id,
                        resume_url=candidate.resume_url,
                        applied_date=candidate.created_at,
                    )
                    candidate_responses.append(candidate_response)

                # Convert to frontend format
                frontend_candidates = [c.to_frontend_format() for c in candidate_responses]

                return {
                    "success": True,
                    "candidates": frontend_candidates,
                    "total": len(frontend_candidates),
                }
            else:
                raise HTTPException(status_code=404, detail="No candidates found for this company")

        except Exception:
            raise HTTPException(status_code=404, detail="No candidates found for this company")

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get candidates for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY JOB POSTINGS
# ============================================================================


@router.get("/{company_id}/job-postings")
async def get_company_job_postings(
    company_id: str,
    status: Optional[str] = None,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Get all job postings for a company

    Args:
        company_id: Company ID
        status: Optional filter by status (active, closed, draft)

    Returns:
        List of job postings
    """
    try:
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get job postings
        if status:
            job_postings = await db_service.search_job_postings(
                company_id=company_id, status=status
            )
        else:
            job_postings = await db_service.get_job_postings_by_company(company_id)

        return {"success": True, "job_postings": job_postings, "total": len(job_postings)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get job postings for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/job-postings/summary")
async def get_company_job_postings_summary(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get job posting summaries for company dashboard

    Args:
        company_id: Company ID

    Returns:
        List of job posting summaries with metrics
    """
    try:
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get job postings summary
        summaries = await db_service.get_job_postings_summary_by_company(company_id)

        return {
            "success": True,
            "summaries": [s.dict() if hasattr(s, "dict") else s for s in summaries],
            "total": len(summaries),
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get job postings summary for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY INTERVIEW CONFIGURATIONS
# ============================================================================


@router.get("/{company_id}/interview-configurations")
async def get_company_interview_configurations(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get all interview configurations created by a company

    Args:
        company_id: Company ID

    Returns:
        List of interview configurations
    """
    try:
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get interview configurations
        configurations = await db_service.get_interview_configurations_by_company(company_id)

        return {"success": True, "configurations": configurations, "total": len(configurations)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interview configurations for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY INTERVIEW SESSIONS & EVALUATIONS
# ============================================================================


def _extract_configuration_metadata(configuration: dict[str, Any]) -> dict[str, Any]:
    """Helper to normalize configuration metadata for responses"""
    simulation_config = configuration.get("simulation_config") or {}
    interview_data = (
        simulation_config.get("interview_data") or simulation_config.get("interview") or {}
    )
    job_details = interview_data.get("job_details") or configuration.get("job_details") or {}

    name = (
        configuration.get("name")
        or job_details.get("title")
        or configuration.get("template_name")
        or "Interview Configuration"
    )

    return {
        "id": configuration.get("id") or configuration.get("configuration_id"),
        "name": name,
        "job_title": job_details.get("title") or name,
        "department": job_details.get("department")
        or interview_data.get("department")
        or "General",
        "status": configuration.get("status", "active"),
        "created_date": configuration.get("createdAt") or configuration.get("created_at"),
        "last_activity": configuration.get("updatedAt") or configuration.get("updated_at"),
        "job_description": job_details.get("description") or configuration.get("description"),
        "requirements": job_details.get("requirements") or interview_data.get("requirements") or [],
    }


@router.get("/{company_id}/interviews")
async def get_company_interviews_overview(
    company_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get aggregated overview for interviews (configurations) created by a company
    """
    try:
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        configurations = await db_service.get_interview_configurations_by_company(company_id)
        interviews = []

        for configuration in configurations:
            metadata = _extract_configuration_metadata(configuration)
            configuration_id = metadata["id"]

            sessions = []
            if configuration_id:
                sessions = await db_service.get_interview_sessions_by_configuration(
                    configuration_id
                )

            total_candidates = len(sessions)
            completion_statuses = {"completed", "completed_with_feedback", "evaluated"}
            completed_candidates = sum(
                1
                for session in sessions
                if (session.get("status") or "").lower() in completion_statuses
            )

            scores = [
                session.get("overall_score") or session.get("score") or session.get("finalScore")
                for session in sessions
                if session.get("overall_score") or session.get("score") or session.get("finalScore")
            ]

            average_score = sum(scores) / len(scores) if scores else 0.0

            last_activity_candidates = [
                session.get("updatedAt")
                or session.get("updated_at")
                or session.get("completedAt")
                or session.get("completed_at")
                for session in sessions
            ]
            last_activity = metadata["last_activity"] or max(last_activity_candidates, default=None)

            interviews.append(
                {
                    **metadata,
                    "total_candidates": total_candidates,
                    "completed_candidates": completed_candidates,
                    "average_score": average_score,
                    "last_activity": last_activity,
                }
            )

        return {"success": True, "interviews": interviews, "total": len(interviews)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interviews overview for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/interviews/{configuration_id}/sessions")
async def get_company_configuration_sessions(
    company_id: str,
    configuration_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Get interview sessions for a specific configuration belonging to a company
    """
    try:
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        configuration = await db_service.get_interview_configuration(configuration_id)
        if not configuration or (
            configuration.get("companyId") != company_id
            and configuration.get("company_id") != company_id
        ):
            raise HTTPException(status_code=404, detail="Configuration not found for this company")

        sessions = await db_service.get_interview_sessions_by_configuration(configuration_id)
        enriched_sessions = []

        for session in sessions:
            candidate_id = (
                session.get("candidate_id")
                or session.get("candidateId")
                or session.get("candidate_details", {}).get("id")
            )
            candidate = await db_service.get_candidate(candidate_id) if candidate_id else None

            session_id = session.get("id") or session.get("session_id") or session.get("sessionId")
            status = session.get("status") or "unknown"
            overall_score = (
                session.get("overall_score") or session.get("score") or session.get("finalScore")
            )

            enriched_sessions.append(
                {
                    **session,
                    "session_id": session_id,
                    "candidate_id": candidate_id,
                    "candidate_name": candidate.get("name")
                    if candidate
                    else session.get("candidate_name", "Unknown"),
                    "candidate_email": candidate.get("email")
                    if candidate
                    else session.get("candidate_email", "Unknown"),
                    "status": status,
                    "overall_score": overall_score,
                }
            )

        return {"success": True, "sessions": enriched_sessions, "total": len(enriched_sessions)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get sessions for configuration {configuration_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/interviews/{configuration_id}/evaluations")
async def get_company_configuration_evaluations(
    company_id: str,
    configuration_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Get evaluation summaries for sessions within a specific configuration
    """
    try:
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        configuration = await db_service.get_interview_configuration(configuration_id)
        if not configuration or (
            configuration.get("companyId") != company_id
            and configuration.get("company_id") != company_id
        ):
            raise HTTPException(status_code=404, detail="Configuration not found for this company")

        sessions = await db_service.get_interview_sessions_by_configuration(configuration_id)
        evaluations = []

        for session in sessions:
            session_id = session.get("id") or session.get("session_id") or session.get("sessionId")
            candidate_id = (
                session.get("candidate_id")
                or session.get("candidateId")
                or session.get("candidate_details", {}).get("id")
            )
            candidate = await db_service.get_candidate(candidate_id) if candidate_id else None

            evaluation = await db_service.get_session_evaluation(session_id) if session_id else None

            overall_score = None
            if evaluation:
                overall_score = evaluation.get("overall_score") or evaluation.get("score")
            if overall_score is None:
                overall_score = (
                    session.get("overall_score")
                    or session.get("score")
                    or session.get("finalScore")
                )

            evaluations.append(
                {
                    "session_id": session_id,
                    "candidate_id": candidate_id,
                    "candidate_name": candidate.get("name")
                    if candidate
                    else session.get("candidate_name", "Unknown"),
                    "candidate_email": candidate.get("email")
                    if candidate
                    else session.get("candidate_email", "Unknown"),
                    "status": session.get("status"),
                    "overall_score": overall_score,
                    "evaluation": evaluation,
                    "completed_at": session.get("completedAt") or session.get("completed_at"),
                }
            )

        return {"success": True, "evaluations": evaluations, "total": len(evaluations)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get evaluations for configuration {configuration_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# COMPANY SEARCH
# ============================================================================


@router.get("/search")
async def search_company_by_name(
    name: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Search for a company by name

    Args:
        name: Company name to search

    Returns:
        Company profile if found
    """
    try:
        # Search through all companies (in a production system, you'd have a proper search index)
        # For now, we'll need to implement a search method in the database service
        # This is a placeholder implementation

        raise HTTPException(
            status_code=501,
            detail="Company search by name not yet implemented. Use get_company_by_email or get_company by ID instead.",
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to search for company {name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/dashboard", response_model=CompanyDashboardResponse)
async def get_company_dashboard_new(company_id: str):
    """
    Get company dashboard data
    """
    try:
        # Try database first
        try:
            database = await get_database(main_logger)
            dashboard_data = await database.get_company_dashboard_data(company_id)

            if dashboard_data:
                # Convert to response models
                recent_interviews = []
                for interview in dashboard_data["recent_interviews"]:
                    candidate_response = CandidateResponse(
                        candidate_id=interview["candidate_id"],
                        name=interview["candidate_name"],
                        email=interview["email"],
                        position=interview.get("position", "Unknown"),
                        status="completed",
                        interview_date=interview["interview_date"],
                        overall_score=interview["overall_score"],
                        evaluation_id=interview["evaluation_id"],
                        resume_url=interview.get("resume_url"),
                        applied_date=interview.get("applied_date"),
                    )
                    recent_interviews.append(candidate_response)

                dashboard = DashboardData(
                    total_candidates=dashboard_data["total_candidates"],
                    completed_interviews=dashboard_data["completed_interviews"],
                    pending_interviews=dashboard_data["pending_interviews"],
                    average_score=dashboard_data["average_score"],
                    recent_interviews=recent_interviews,
                    active_jobs=dashboard_data.get(
                        "active_jobs", 1
                    ),  # Default to 1 if not provided
                    total_evaluations=dashboard_data.get(
                        "total_evaluations", dashboard_data["completed_interviews"]
                    ),  # Use completed interviews as fallback
                )

                return CompanyDashboardResponse(success=True, dashboard=dashboard)
            else:
                raise HTTPException(status_code=404, detail="Company not found")

        except Exception:
            raise HTTPException(status_code=404, detail="Company not found")

    except HTTPException:
        raise

    except Exception as e:
        main_logger.error(f"Failed to get dashboard for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/email/{email}")
async def get_company_by_email(email: str):
    """
    Get company details by email
    """
    try:
        database = await get_database(main_logger)
        company = await database.get_company_by_email(email)

        if company:
            company_response = CompanyResponse(
                company_id=company.company_id,
                name=company.name,
                email=company.email,
                industry=company.industry,
                size=company.size,
                location=company.location,
                website=company.website,
                description=company.description,
                created_at=company.created_at,
                updated_at=company.updated_at,
            )
            return {"success": True, "company": company_response}
        else:
            raise HTTPException(status_code=404, detail="Company not found")

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get company by email {email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{company_id}")
async def update_company(company_id: str, update_data: CompanyUpdateRequest):
    """
    Update company profile
    """
    try:
        database = await get_database(main_logger)

        # Check if company exists
        company = await database.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Prepare update data (exclude None values)
        updates = {k: v for k, v in update_data.dict().items() if v is not None}

        if updates:
            success = await database.update_company(company_id, updates)
            if success:
                return {"message": "Company updated successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update company")
        else:
            return {"message": "No updates provided"}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to update company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/check-email-availability/{email}")
async def check_email_availability(email: str):
    """
    Check if company email is available
    """
    try:
        database = await get_database(main_logger)
        is_available = await database.check_company_email_availability(email)

        return {"available": is_available}

    except Exception as e:
        main_logger.error(f"Failed to check email availability for {email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/interviews")
async def get_company_interviews(company_id: str):
    """
    Get all interviews for a company
    """
    try:
        # Try database first
        try:
            database = await get_database(main_logger)
            interviews = await database.get_company_interviews(company_id)

            if interviews is not None:
                return {"success": True, "interviews": interviews, "total": len(interviews)}
            else:
                raise HTTPException(status_code=404, detail="No interviews found for this company")

        except Exception as db_error:
            main_logger.warning(f"Database lookup failed, returning empty list: {db_error}")
            # Return empty list instead of error for better UX
            return {"success": True, "interviews": [], "total": 0}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interviews for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}/interviews/{interview_id}/candidates")
async def get_interview_candidates(company_id: str, interview_id: str):
    """
    Get candidates for a specific interview
    """
    try:
        # Try database first
        try:
            database = await get_database(main_logger)
            candidates = await database.get_interview_candidates(company_id, interview_id)

            if candidates is not None:
                return {"success": True, "candidates": candidates, "total": len(candidates)}
            else:
                raise HTTPException(
                    status_code=404, detail="No candidates found for this interview"
                )

        except Exception as db_error:
            main_logger.warning(f"Database lookup failed, returning empty list: {db_error}")
            # Return empty list instead of error for better UX
            return {"success": True, "candidates": [], "total": 0}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get candidates for interview {interview_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/validate-session")
async def validate_session():
    """
    Validate company session token
    """
    try:
        # In a real implementation, you would extract the token from headers
        # For now, we'll return a simple validation
        return {"valid": True}

    except Exception as e:
        main_logger.error(f"Session validation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout")
async def logout():
    """
    Logout company user
    """
    try:
        # In a real implementation, you would invalidate the token
        # For now, we'll return success
        return {"message": "Logged out successfully"}

    except Exception as e:
        main_logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
