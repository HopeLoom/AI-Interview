"""
Job Postings router for managing job postings and related operations.
Handles job creation, updates, applications, and search.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from globals import main_logger
from interview_configuration.database_service import InterviewConfigurationDatabase
from interview_configuration.models import JobPostingData

router = APIRouter(prefix="/api/job-postings", tags=["job-postings"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db_service():
    """Get database service instance"""
    return InterviewConfigurationDatabase()

# ============================================================================
# JOB POSTING CRUD OPERATIONS
# ============================================================================

@router.post("")
async def create_job_posting(
    job_data: JobPostingData,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Create a new job posting

    Args:
        job_data: Job posting information

    Returns:
        Created job posting ID
    """
    try:
        # Verify company exists
        company = await db_service.get_company(job_data.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Create job posting
        job_id = await db_service.create_job_posting(job_data.company_id, job_data.dict(exclude_none=True))

        main_logger.info(f"Job posting created successfully: {job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "message": "Job posting created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to create job posting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job posting: {str(e)}")

@router.get("/{job_id}")
async def get_job_posting(
    job_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get job posting by ID

    Args:
        job_id: Job posting ID

    Returns:
        Job posting details
    """
    try:
        job_posting = await db_service.get_job_posting(job_id)

        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        return {
            "success": True,
            "job_posting": job_posting
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get job posting {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{job_id}")
async def update_job_posting(
    job_id: str,
    update_data: Dict[str, Any],
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Update job posting

    Args:
        job_id: Job posting ID
        update_data: Fields to update

    Returns:
        Success status
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Update job posting
        success = await db_service.update_job_posting(job_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update job posting")

        main_logger.info(f"Job posting updated successfully: {job_id}")

        return {
            "success": True,
            "message": "Job posting updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to update job posting {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{job_id}")
async def delete_job_posting(
    job_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Delete (close) job posting

    Args:
        job_id: Job posting ID

    Returns:
        Success status
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Delete (soft delete - set status to closed)
        success = await db_service.delete_job_posting(job_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete job posting")

        main_logger.info(f"Job posting deleted successfully: {job_id}")

        return {
            "success": True,
            "message": "Job posting deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to delete job posting {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# JOB POSTING APPLICATIONS
# ============================================================================

@router.get("/{job_id}/applications")
async def get_job_applications(
    job_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get all applications for a job posting

    Args:
        job_id: Job posting ID

    Returns:
        List of applications
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Get applications
        applications = await db_service.get_candidate_applications_by_job(job_id)

        return {
            "success": True,
            "applications": applications,
            "total": len(applications)
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get applications for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# JOB POSTING SEARCH
# ============================================================================

@router.get("/search")
async def search_job_postings(
    company_id: Optional[str] = None,
    location: Optional[str] = None,
    level: Optional[str] = None,
    job_type: Optional[str] = None,
    status: str = "active",
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Search job postings with filters

    Args:
        company_id: Filter by company
        location: Filter by location
        level: Filter by experience level
        job_type: Filter by job type
        status: Filter by status (default: active)

    Returns:
        List of matching job postings
    """
    try:
        job_postings = await db_service.search_job_postings(
            company_id=company_id,
            location=location,
            level=level,
            type=job_type,
            status=status
        )

        return {
            "success": True,
            "job_postings": job_postings,
            "total": len(job_postings)
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to search job postings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# JOB POSTING INTERVIEW CONFIGURATIONS
# ============================================================================

@router.get("/{job_id}/interview-configurations")
async def get_job_interview_configurations(
    job_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get interview configurations for a job posting

    Args:
        job_id: Job posting ID

    Returns:
        List of interview configurations
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Get interview configurations
        configurations = await db_service.get_interview_configurations_by_job(job_id)

        return {
            "success": True,
            "configurations": configurations,
            "total": len(configurations)
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interview configurations for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# JOB POSTING INTERVIEW SESSIONS
# ============================================================================

@router.get("/{job_id}/interview-sessions")
async def get_job_interview_sessions(
    job_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get all interview sessions for a job posting

    Args:
        job_id: Job posting ID

    Returns:
        List of interview sessions
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Get interview sessions
        sessions = await db_service.get_interview_sessions_by_job(job_id)

        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interview sessions for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
