"""
Candidates router for managing candidate operations.
Handles candidate profiles, practice sessions, skills, and interview history.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from globals import main_logger
from interview_configuration.database_service import InterviewConfigurationDatabase
from interview_configuration.models import CandidateData

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_db_service():
    """Get database service instance"""
    return InterviewConfigurationDatabase()


# ============================================================================
# CANDIDATE AUTHENTICATION
# ============================================================================


@router.get("")
async def list_candidates(db_service: InterviewConfigurationDatabase = Depends(get_db_service)):
    """Get all candidates"""
    try:
        candidates = await db_service.get_all_candidates()
        return {"success": True, "candidates": candidates, "total": len(candidates)}
    except Exception as e:
        main_logger.error(f"Failed to list candidates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def candidate_login(
    credentials: dict[str, str],
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Candidate login endpoint

    Args:
        credentials: {"email": "candidate@example.com", "name": "John Doe"}

    Returns:
        Candidate profile and authentication token
    """
    try:
        email = credentials.get("email")
        name = credentials.get("name")

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Get candidate by email
        candidate = await db_service.get_candidate_by_email(email)

        # If candidate doesn't exist, create a new one (auto-registration)
        if not candidate:
            main_logger.info(f"Candidate not found, creating new candidate: {email}")
            candidate_data = {
                "name": name or "Candidate",
                "email": email,
                "skills": [],
                "userType": "candidate",
            }
            candidate_id = await db_service.create_candidate(candidate_data)
            candidate = await db_service.get_candidate(candidate_id)

        main_logger.info(f"Candidate login successful: {candidate.get('id')}")

        return {
            "success": True,
            "message": "Login successful",
            "candidate": candidate,
            "token": f"candidate_token_{candidate.get('id')}",  # TODO: Implement proper JWT
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Candidate login failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE PROFILE MANAGEMENT
# ============================================================================


@router.post("")
async def create_candidate(
    candidate_data: CandidateData,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Create a new candidate profile

    Args:
        candidate_data: Candidate information

    Returns:
        Created candidate ID and profile
    """
    try:
        # Check if candidate with email already exists
        existing_candidate = await db_service.get_candidate_by_email(candidate_data.email)
        if existing_candidate:
            raise HTTPException(status_code=400, detail="Candidate with this email already exists")

        # Create candidate
        candidate_id = await db_service.create_candidate(candidate_data.dict(exclude_none=True))

        main_logger.info(f"Candidate created successfully: {candidate_id}")

        return {
            "success": True,
            "candidate_id": candidate_id,
            "message": "Candidate created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to create candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create candidate: {e!s}")


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get candidate profile by ID

    Args:
        candidate_id: Candidate ID

    Returns:
        Candidate profile
    """
    try:
        candidate = await db_service.get_candidate(candidate_id)

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {"success": True, "candidate": candidate}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: str,
    update_data: dict[str, Any],
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Update candidate profile

    Args:
        candidate_id: Candidate ID
        update_data: Fields to update

    Returns:
        Success status
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Update candidate
        success = await db_service.update_candidate(candidate_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update candidate")

        main_logger.info(f"Candidate updated successfully: {candidate_id}")

        return {"success": True, "message": "Candidate updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to update candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE INTERVIEW SESSIONS
# ============================================================================


@router.get("/{candidate_id}/interviews")
async def get_candidate_interviews(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get all interview sessions for a candidate

    Args:
        candidate_id: Candidate ID

    Returns:
        List of interview sessions
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get interview sessions
        sessions = await db_service.get_interview_sessions_by_candidate(candidate_id)

        return {"success": True, "interviews": sessions, "total": len(sessions)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interviews for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE APPLICATIONS
# ============================================================================


@router.get("/{candidate_id}/applications")
async def get_candidate_applications(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get all applications submitted by a candidate

    Args:
        candidate_id: Candidate ID

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

        return {"success": True, "applications": applications, "total": len(applications)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get applications for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE SUMMARY/DASHBOARD
# ============================================================================


@router.get("/{candidate_id}/summary")
async def get_candidate_summary(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get candidate summary for dashboard

    Args:
        candidate_id: Candidate ID

    Returns:
        Candidate summary with stats
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get interview sessions
        sessions = await db_service.get_interview_sessions_by_candidate(candidate_id)

        # Get applications
        applications = await db_service.get_candidate_applications_by_candidate(candidate_id)

        # Build summary
        summary = {
            "candidate": candidate,
            "total_interviews": len(sessions),
            "completed_interviews": len([s for s in sessions if s.get("status") == "completed"]),
            "pending_interviews": len(
                [s for s in sessions if s.get("status") in ["scheduled", "in_progress"]]
            ),
            "total_applications": len(applications),
            "recent_activity": sessions[:5] if sessions else [],
        }

        return {"success": True, "summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get summary for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE SKILLS MANAGEMENT
# ============================================================================


@router.get("/{candidate_id}/skills")
async def get_candidate_skills(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get candidate skills

    Args:
        candidate_id: Candidate ID

    Returns:
        List of skills
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Return skills from candidate profile
        skills = candidate.get("skills", [])

        return {"success": True, "skills": skills}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get skills for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{candidate_id}/skills")
async def add_candidate_skill(
    candidate_id: str,
    skill_data: dict[str, Any],
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Add a skill to candidate profile

    Args:
        candidate_id: Candidate ID
        skill_data: Skill information (e.g., {"name": "Python", "level": "expert"})

    Returns:
        Success status
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get current skills
        current_skills = candidate.get("skills", [])

        # Add new skill name to list
        skill_name = skill_data.get("name")
        if skill_name and skill_name not in current_skills:
            current_skills.append(skill_name)

            # Update candidate
            await db_service.update_candidate(candidate_id, {"skills": current_skills})

        return {"success": True, "message": "Skill added successfully"}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to add skill for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE PRACTICE SESSIONS
# ============================================================================


@router.get("/{candidate_id}/practice-sessions")
async def get_candidate_practice_sessions(
    candidate_id: str, db_service: InterviewConfigurationDatabase = Depends(get_db_service)
):
    """
    Get practice sessions for a candidate
    Note: Practice sessions are stored as interview sessions with a specific type

    Args:
        candidate_id: Candidate ID

    Returns:
        List of practice sessions
    """
    try:
        # Verify candidate exists
        candidate = await db_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get all interview sessions for candidate
        # Filter for practice sessions (those without a job_posting_id)
        all_sessions = await db_service.get_interview_sessions_by_candidate(candidate_id)
        practice_sessions = [s for s in all_sessions if not s.get("jobPostingId")]

        return {
            "success": True,
            "practice_sessions": practice_sessions,
            "total": len(practice_sessions),
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get practice sessions for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CANDIDATE SEARCH
# ============================================================================


@router.get("/search")
async def search_candidates(
    skills: Optional[str] = None,
    location: Optional[str] = None,
    experience_min: Optional[int] = None,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service),
):
    """
    Search candidates with filters

    Args:
        skills: Comma-separated list of skills
        location: Location filter
        experience_min: Minimum years of experience

    Returns:
        List of matching candidates
    """
    try:
        # Parse skills
        skills_list = skills.split(",") if skills else None

        # Search candidates
        candidates = await db_service.search_candidates(
            skills=skills_list, location=location, experience_min=experience_min
        )

        return {"success": True, "candidates": candidates, "total": len(candidates)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to search candidates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
