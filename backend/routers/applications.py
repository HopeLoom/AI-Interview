"""
Applications router for managing candidate applications to job postings.
Handles application submission, status updates, and retrieval.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from globals import main_logger
from interview_configuration.database_service import InterviewConfigurationDatabase
from interview_configuration.models import CandidateApplicationData

router = APIRouter(prefix="/api/applications", tags=["applications"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_db_service():
    """Get database service instance"""
    return InterviewConfigurationDatabase()


# ============================================================================
# APPLICATION CRUD OPERATIONS
# ============================================================================


@router.post("")
async def create_application(
    application_data: CandidateApplicationData,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Submit a new application

    Args:
        application_data: Application information

    Returns:
        Created application ID
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(application_data.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Verify job posting exists
        job_posting = await db_service.get_job_posting(application_data.job_posting_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Check if application already exists
        existing_applications = await db_service.get_candidate_applications_by_candidate(
            application_data.candidate_id
        )
        for app in existing_applications:
            if app.get("jobPostingId") == application_data.job_posting_id:
                raise HTTPException(
                    status_code=400, detail="Application already submitted for this job"
                )

        # Create application
        application_id = await db_service.create_candidate_application(
            application_data.dict(exclude_none=True)
        )

        main_logger.info(f"Application created successfully: {application_id}")

        return {
            "success": True,
            "application_id": application_id,
            "message": "Application submitted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to create application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {e!s}")


@router.get("/{application_id}")
async def get_application(
    application_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get application details by ID

    Args:
        application_id: Application ID

    Returns:
        Application details
    """
    try:
        # Note: The database service doesn't have a get_application_by_id method
        # We'll need to get all applications and filter
        # This is a limitation of the current database service
        raise HTTPException(
            status_code=501,
            detail="Get application by ID not yet implemented. Use get by candidate or job posting instead.",
        )

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get application {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{application_id}/status")
async def update_application_status(
    application_id: str,
    status_data: dict[str, str],
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Update application status

    Args:
        application_id: Application ID
        status_data: {"status": "screening|interviewing|offered|rejected|accepted"}

    Returns:
        Success status
    """
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")

        # Validate status
        valid_statuses = ["applied", "screening", "interviewing", "offered", "rejected", "accepted"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Update application status
        success = await db_service.update_application_status(application_id, new_status)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update application status")

        main_logger.info(f"Application status updated: {application_id} -> {new_status}")

        return {"success": True, "message": "Application status updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to update application status {application_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# APPLICATION QUERIES
# ============================================================================


@router.get("/job/{job_id}")
async def get_applications_by_job(
    job_id: str,
    status: Optional[str] = None,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Get all applications for a job posting

    Args:
        job_id: Job posting ID
        status: Optional filter by status

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

        # Filter by status if provided
        if status:
            applications = [app for app in applications if app.get("status") == status]

        return {"success": True, "applications": applications, "total": len(applications)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get applications for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/candidate/{candidate_id}")
async def get_applications_by_candidate(
    candidate_id: str,
    status: Optional[str] = None,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Get all applications submitted by a candidate

    Args:
        candidate_id: Candidate ID
        status: Optional filter by status

    Returns:
        List of applications
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get applications
        applications = await db_service.get_candidate_applications_by_candidate(candidate_id)

        # Filter by status if provided
        if status:
            applications = [app for app in applications if app.get("status") == status]

        return {"success": True, "applications": applications, "total": len(applications)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get applications for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# APPLICATION STATISTICS
# ============================================================================


@router.get("/job/{job_id}/statistics")
async def get_job_application_statistics(
    job_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get application statistics for a job posting

    Args:
        job_id: Job posting ID

    Returns:
        Application statistics
    """
    try:
        # Verify job posting exists
        job_posting = await db_service.get_job_posting(job_id)
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job posting not found")

        # Get applications
        applications = await db_service.get_candidate_applications_by_job(job_id)

        # Calculate statistics
        stats = {
            "total_applications": len(applications),
            "by_status": {
                "applied": len([a for a in applications if a.get("status") == "applied"]),
                "screening": len([a for a in applications if a.get("status") == "screening"]),
                "interviewing": len([a for a in applications if a.get("status") == "interviewing"]),
                "offered": len([a for a in applications if a.get("status") == "offered"]),
                "rejected": len([a for a in applications if a.get("status") == "rejected"]),
                "accepted": len([a for a in applications if a.get("status") == "accepted"]),
            },
        }

        return {"success": True, "statistics": stats}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get application statistics for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
