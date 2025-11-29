"""
Comprehensive Configuration Router for Interview Simulation Platform
Handles both static configuration data and dynamic configuration generation
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from globals import main_logger
from interview_configuration.database_service import InterviewConfigurationDatabase
from interview_configuration.models import (
    ConfigurationGenerationResponse,
    FrontendConfigurationInput,
    ResumeUploadData,
)

# Import interview configuration service and models
from interview_configuration.service import InterviewConfigurationService
from providers.provider_factory import ProviderFactory
from utils.resume_file_reader import parse_resume

router = APIRouter(prefix="/api/configurations", tags=["Configuration"])

# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_configuration_service():
    """Dependency to get configuration service with LLM provider"""
    provider_factory = ProviderFactory()
    providers = provider_factory.create_all_providers()
    llm_provider = providers["openai"]  # Use OpenAI as default
    return InterviewConfigurationService(llm_provider)


# ============================================================================
# STATIC CONFIGURATION ENDPOINTS
# ============================================================================


def load_static_data(filename: str) -> Dict[str, Any]:
    """Load static configuration data from JSON files"""
    try:
        template_file_path = Path(__file__).parent.parent / "templates" / filename

        if not template_file_path.exists():
            main_logger.warning(f"Template file {filename} not found")
            return {}

        with open(template_file_path) as f:
            return json.load(f)

    except Exception as e:
        main_logger.error(f"Failed to load {filename}: {e}")
        return {}


@router.get("/character-templates")
async def get_character_templates():
    """Get available character templates"""
    try:
        data = load_static_data("character_templates.json")
        templates = data.get("templates", [])

        return {"success": True, "templates": templates}

    except Exception as e:
        main_logger.error(f"Failed to get character templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get character templates: {e!s}")


@router.get("/question-templates")
async def get_question_templates():
    """Get available question templates"""
    try:
        data = load_static_data("question_templates.json")
        templates = data.get("templates", [])

        return {"success": True, "templates": templates}

    except Exception as e:
        main_logger.error(f"Failed to get question templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get question templates: {e!s}")


@router.get("/interview-templates")
async def get_interview_templates():
    """Get available interview round templates"""
    try:
        data = load_static_data("interview_templates.json")
        templates = data.get("templates", [])

        return {"success": True, "templates": templates}

    except Exception as e:
        main_logger.error(f"Failed to get interview templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview templates: {e!s}")


@router.get("/programming-languages")
async def get_programming_languages():
    """Get available programming languages"""
    try:
        # Define common programming languages
        languages = [
            {"id": "python", "name": "Python", "description": "High-level programming language"},
            {"id": "javascript", "name": "JavaScript", "description": "Web development language"},
            {"id": "java", "name": "Java", "description": "Object-oriented programming language"},
            {"id": "cpp", "name": "C++", "description": "System programming language"},
            {"id": "csharp", "name": "C#", "description": "Microsoft programming language"},
            {"id": "go", "name": "Go", "description": "Google's programming language"},
            {"id": "rust", "name": "Rust", "description": "Systems programming language"},
            {"id": "typescript", "name": "TypeScript", "description": "Typed JavaScript"},
            {"id": "php", "name": "PHP", "description": "Server-side scripting language"},
            {"id": "ruby", "name": "Ruby", "description": "Dynamic programming language"},
            {"id": "swift", "name": "Swift", "description": "Apple's programming language"},
            {"id": "kotlin", "name": "Kotlin", "description": "JVM programming language"},
            {"id": "scala", "name": "Scala", "description": "Functional programming language"},
            {"id": "r", "name": "R", "description": "Statistical computing language"},
            {"id": "matlab", "name": "MATLAB", "description": "Numerical computing language"},
        ]

        return {"success": True, "languages": languages}

    except Exception as e:
        main_logger.error(f"Failed to get programming languages: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get programming languages: {e!s}"
        )


@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """Get available difficulty levels"""
    try:
        difficulty_levels = [
            {
                "value": "beginner",
                "label": "Beginner",
                "description": "Basic problems, suitable for junior positions",
                "color": "green",
            },
            {
                "value": "intermediate",
                "label": "Intermediate",
                "description": "Moderate problems, suitable for mid-level positions",
                "color": "blue",
            },
            {
                "value": "advanced",
                "label": "Advanced",
                "description": "Complex problems, suitable for senior positions",
                "color": "purple",
            },
            {
                "value": "expert",
                "label": "Expert",
                "description": "Very complex problems, suitable for lead/architect positions",
                "color": "red",
            },
        ]

        return {"success": True, "difficulty_levels": difficulty_levels}

    except Exception as e:
        main_logger.error(f"Failed to get difficulty levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get difficulty levels: {e!s}")


@router.get("/personality-traits")
async def get_personality_traits():
    """Get available personality traits for AI interviewers"""
    try:
        personality_traits = [
            {
                "id": "friendly",
                "trait": "Friendly",
                "description": "Warm and approachable interviewer",
            },
            {
                "id": "professional",
                "trait": "Professional",
                "description": "Formal and business-like interviewer",
            },
            {
                "id": "challenging",
                "trait": "Challenging",
                "description": "Pushes candidates to think deeper",
            },
            {
                "id": "supportive",
                "trait": "Supportive",
                "description": "Encouraging and helpful interviewer",
            },
            {
                "id": "analytical",
                "trait": "Analytical",
                "description": "Focuses on logical thinking and analysis",
            },
            {
                "id": "creative",
                "trait": "Creative",
                "description": "Encourages innovative and out-of-the-box thinking",
            },
            {
                "id": "detail-oriented",
                "trait": "Detail-Oriented",
                "description": "Focuses on precision and thoroughness",
            },
            {
                "id": "big-picture",
                "trait": "Big Picture",
                "description": "Focuses on high-level strategic thinking",
            },
            {
                "id": "collaborative",
                "trait": "Collaborative",
                "description": "Emphasizes teamwork and cooperation",
            },
            {
                "id": "independent",
                "trait": "Independent",
                "description": "Focuses on individual problem-solving",
            },
        ]

        return {"success": True, "traits": personality_traits}

    except Exception as e:
        main_logger.error(f"Failed to get personality traits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get personality traits: {e!s}")


@router.get("/predefined-topics")
async def get_predefined_topics():
    """Get predefined interview topics by category"""
    try:
        predefined_topics = [
            {
                "category": "Technical Skills",
                "topics": {
                    "Programming": [
                        "Data Structures",
                        "Algorithms",
                        "System Design",
                        "Database Design",
                        "API Design",
                    ],
                    "Computer Science": [
                        "Operating Systems",
                        "Networks",
                        "Security",
                        "Architecture",
                        "Performance",
                    ],
                    "Software Engineering": [
                        "Design Patterns",
                        "Testing",
                        "Code Quality",
                        "Version Control",
                        "CI/CD",
                    ],
                    "Data & ML": [
                        "Machine Learning",
                        "Data Analysis",
                        "Statistics",
                        "Big Data",
                        "AI Ethics",
                    ],
                },
            },
            {
                "category": "Problem Solving",
                "topics": {
                    "Analytical": [
                        "Problem Analysis",
                        "Solution Design",
                        "Trade-offs",
                        "Optimization",
                        "Scalability",
                    ],
                    "Creative": [
                        "Innovation",
                        "User Experience",
                        "Design Thinking",
                        "Prototyping",
                        "Iteration",
                    ],
                    "Critical": [
                        "Code Review",
                        "Debugging",
                        "Performance Analysis",
                        "Security Review",
                        "Architecture Review",
                    ],
                },
            },
            {
                "category": "Soft Skills",
                "topics": {
                    "Communication": [
                        "Technical Writing",
                        "Presentation",
                        "Documentation",
                        "Team Collaboration",
                        "Stakeholder Management",
                    ],
                    "Leadership": [
                        "Project Management",
                        "Mentoring",
                        "Decision Making",
                        "Conflict Resolution",
                        "Strategic Thinking",
                    ],
                    "Adaptability": [
                        "Learning Agility",
                        "Change Management",
                        "Problem Adaptation",
                        "Technology Adoption",
                        "Process Improvement",
                    ],
                },
            },
            {
                "category": "Domain Knowledge",
                "topics": {
                    "Web Development": [
                        "Frontend",
                        "Backend",
                        "Full Stack",
                        "Mobile",
                        "Progressive Web Apps",
                    ],
                    "Cloud & DevOps": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform"],
                    "Data Engineering": [
                        "ETL",
                        "Data Warehousing",
                        "Streaming",
                        "Data Governance",
                        "Data Quality",
                    ],
                },
            },
        ]

        return {"success": True, "topics": predefined_topics}

    except Exception as e:
        main_logger.error(f"Failed to get predefined topics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get predefined topics: {e!s}")


# ============================================================================
# DYNAMIC CONFIGURATION GENERATION ENDPOINTS
# ============================================================================


@router.post("/generate", response_model=ConfigurationGenerationResponse)
async def generate_full_configuration(
    config_input: FrontendConfigurationInput,
    user_id: str = "default_user",  # In real implementation, get from auth
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Generate complete interview configuration from frontend input
    """
    try:
        main_logger.info(f"Generating configuration for user: {user_id}")
        response = await service.generate_full_configuration(config_input, user_id)

        if not response.success:
            raise HTTPException(
                status_code=400, detail={"errors": response.errors, "warnings": response.warnings}
            )

        return response

    except Exception as e:
        main_logger.error(f"Configuration generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration generation failed: {e!s}")


@router.get("/templates")
async def get_configuration_templates():
    """
    Get available interview configuration templates
    """
    try:
        # Return comprehensive templates that match frontend expectations
        templates = [
            {
                "template_id": "frontend-dev",
                "name": "Frontend Developer Interview",
                "description": "Comprehensive frontend development interview covering React, JavaScript, and web fundamentals",
                "category": "frontend",
                "difficulty": "intermediate",
                "estimated_duration": 60,
            },
            {
                "template_id": "backend-dev",
                "name": "Backend Developer Interview",
                "description": "Backend development interview focusing on APIs, databases, and system design",
                "category": "backend",
                "difficulty": "intermediate",
                "estimated_duration": 75,
            },
            {
                "template_id": "fullstack-dev",
                "name": "Full Stack Developer Interview",
                "description": "End-to-end development interview covering both frontend and backend technologies",
                "category": "fullstack",
                "difficulty": "advanced",
                "estimated_duration": 90,
            },
            {
                "template_id": "ml-engineer",
                "name": "Machine Learning Engineer Interview",
                "description": "ML-focused interview covering algorithms, data science, and practical ML applications",
                "category": "machine-learning",
                "difficulty": "advanced",
                "estimated_duration": 80,
            },
            {
                "template_id": "data-scientist",
                "name": "Data Scientist Interview",
                "description": "Data science interview covering statistics, analysis, and data manipulation",
                "category": "data-science",
                "difficulty": "intermediate",
                "estimated_duration": 70,
            },
            {
                "template_id": "product-manager",
                "name": "Product Manager Interview",
                "description": "Product management interview covering strategy, user research, and product development",
                "category": "product-management",
                "difficulty": "intermediate",
                "estimated_duration": 60,
            },
            {
                "template_id": "ui-ux-designer",
                "name": "UI/UX Designer Interview",
                "description": "Design interview covering user experience, visual design, and design thinking",
                "category": "design",
                "difficulty": "intermediate",
                "estimated_duration": 65,
            },
            {
                "template_id": "devops-engineer",
                "name": "DevOps Engineer Interview",
                "description": "DevOps interview covering infrastructure, CI/CD, and cloud technologies",
                "category": "devops",
                "difficulty": "advanced",
                "estimated_duration": 75,
            },
        ]

        return {"success": True, "templates": templates}

    except Exception as e:
        main_logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {e!s}")


@router.get("/templates/{template_id}")
async def get_template_by_id(template_id: str):
    """
    Get specific template by ID
    """
    try:
        # This would typically fetch from database
        # For now, return a mock template
        template = {
            "template_id": template_id,
            "name": f"Template {template_id}",
            "description": f"Description for template {template_id}",
            "category": "general",
            "difficulty": "intermediate",
            "estimated_duration": 60,
            "rounds": [],
            "job_details": {},
        }

        return {"success": True, "template": template}

    except Exception as e:
        main_logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {e!s}")


@router.get("/job-templates")
async def get_job_templates():
    """
    Get job-specific interview templates
    """
    try:
        job_templates = [
            {
                "job_title": "Software Engineer",
                "company": "Tech Corp",
                "template": {
                    "rounds": [
                        {"name": "Technical Screening", "duration": 30},
                        {"name": "Coding Challenge", "duration": 45},
                        {"name": "System Design", "duration": 60},
                        {"name": "Behavioral", "duration": 30},
                    ]
                },
            },
            {
                "job_title": "Data Scientist",
                "company": "Data Corp",
                "template": {
                    "rounds": [
                        {"name": "Statistics & ML", "duration": 45},
                        {"name": "Coding Challenge", "duration": 60},
                        {"name": "Case Study", "duration": 45},
                        {"name": "Behavioral", "duration": 30},
                    ]
                },
            },
        ]

        return {"success": True, "job_templates": job_templates}

    except Exception as e:
        main_logger.error(f"Failed to get job templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job templates: {e!s}")


# ============================================================================
# RESUME AND JOB PARSING ENDPOINTS
# ============================================================================


@router.post("/upload-resume")
async def upload_resume(user_id: str = Form(...), resume: UploadFile = File(...)):
    """
    Upload and parse resume file
    """
    try:
        main_logger.info(f"Uploading resume for user: {user_id}")

        # Validate file type
        if not resume.filename.lower().endswith((".pdf", ".docx", ".doc")):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only PDF and Word documents are supported.",
            )

        # Create upload directory
        upload_dir = f"static/{user_id}/resumes"
        os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded file
        file_path = os.path.join(upload_dir, resume.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

        # Parse resume content
        try:
            parsed_content = parse_resume(file_path)

            resume_data = ResumeUploadData(
                filename=resume.filename,
                content=str(parsed_content),  # Convert to string for now
                file_path=file_path,
            )

            return {
                "success": True,
                "message": "Resume uploaded and parsed successfully",
                "resume_data": resume_data.model_dump(),
            }

        except Exception as parse_error:
            main_logger.error(f"Resume parsing failed: {parse_error}")
            # Still return success but with raw text
            return {
                "success": True,
                "message": "Resume uploaded but parsing failed",
                "resume_data": ResumeUploadData(
                    filename=resume.filename,
                    content=f"Resume file: {resume.filename} (parsing failed)",
                    file_path=file_path,
                ).model_dump(),
                "warning": "Resume parsing failed, using filename only",
            }

    except Exception as e:
        main_logger.error(f"Resume upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {e!s}")


@router.post("/enhanced-resume-upload")
async def enhanced_resume_upload(
    user_id: str = Form(...),
    resume: UploadFile = File(...),
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Enhanced resume upload with AI-powered parsing
    """
    try:
        main_logger.info(f"Enhanced resume upload for user: {user_id}")

        # Validate file type
        if not resume.filename.lower().endswith((".pdf", ".docx", ".doc")):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only PDF and Word documents are supported.",
            )

        # Create upload directory
        upload_dir = f"static/{user_id}/resumes"
        os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded file
        file_path = os.path.join(upload_dir, resume.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

        # Parse resume content
        try:
            parsed_content = parse_resume(file_path)

            # Use AI service to extract structured information
            extracted_info = await service._extract_resume_information_llm(str(parsed_content))

            resume_data = ResumeUploadData(
                filename=resume.filename, content=str(parsed_content), file_path=file_path
            )

            return {
                "success": True,
                "message": "Resume uploaded and AI-parsed successfully",
                "resume_data": resume_data.model_dump(),
                "extracted_info": extracted_info,
            }

        except Exception as parse_error:
            main_logger.error(f"Enhanced resume parsing failed: {parse_error}")
            # Fall back to basic parsing
            return {
                "success": True,
                "message": "Resume uploaded but AI parsing failed",
                "resume_data": ResumeUploadData(
                    filename=resume.filename,
                    content=f"Resume file: {resume.filename} (AI parsing failed)",
                    file_path=file_path,
                ).model_dump(),
                "warning": "AI parsing failed, using basic parsing",
            }

    except Exception as e:
        main_logger.error(f"Enhanced resume upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced resume upload failed: {e!s}")


@router.post("/parse-job-url")
async def parse_job_url(
    job_url: str = Form(...),
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Parse job posting from URL
    """
    try:
        main_logger.info(f"Parsing job URL: {job_url}")

        # This would typically use a web scraping service
        # For now, return mock data
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "description": "We are looking for a talented software engineer...",
            "requirements": ["Python", "JavaScript", "React", "3+ years experience"],
            "url": job_url,
        }

        return {"success": True, "job_data": job_data}

    except Exception as e:
        main_logger.error(f"Job URL parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job URL parsing failed: {e!s}")


@router.post("/parse-job-description")
async def parse_job_description(
    job_description: str = Form(...),
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Parse and analyze job description text
    """
    try:
        main_logger.info("Parsing job description")

        # This would typically use AI to extract structured information
        # For now, return mock data
        parsed_job = {
            "title": "Software Engineer",
            "skills": ["Python", "JavaScript", "React"],
            "experience_level": "Mid-level",
            "responsibilities": ["Develop web applications", "Collaborate with team"],
            "requirements": ["Bachelor's degree", "3+ years experience"],
        }

        return {"success": True, "parsed_job": parsed_job}

    except Exception as e:
        main_logger.error(f"Job description parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job description parsing failed: {e!s}")


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("/register-user")
async def register_user(user_data: Dict[str, Any]):
    """
    Register a new user (company or candidate)
    """
    try:
        main_logger.info(f"Registering user: {user_data.get('email', 'unknown')}")

        db_service = InterviewConfigurationDatabase()
        user_type = user_data.get("userType", "candidate")

        if user_type == "company":
            # Register as company
            user_id = await db_service.create_company(user_data)
            main_logger.info(f"Company registered successfully: {user_id}")
        else:
            # Register as candidate
            user_id = await db_service.create_candidate(user_data)
            main_logger.info(f"Candidate registered successfully: {user_id}")

        return {
            "success": True,
            "user_id": user_id,
            "user_type": user_type,
            "message": "User registered successfully",
        }

    except Exception as e:
        main_logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"User registration failed: {e!s}")


# ============================================================================
# CONFIGURATION RETRIEVAL ENDPOINTS
# ============================================================================


@router.get("/{config_id}")
async def get_configuration_by_id(config_id: str):
    """
    Get configuration by ID
    """
    try:
        main_logger.info(f"Getting configuration: {config_id}")

        db_service = InterviewConfigurationDatabase()
        config_data = await db_service.get_interview_configuration(config_id)

        if not config_data:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return {"success": True, "configuration": config_data}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {e!s}")


@router.post("/join-by-code")
async def join_interview_by_code(request_data: Dict[str, str]):
    """
    Join an interview using an invitation code

    Args:
        request_data: {
            "invitation_code": "ABC123",
            "candidate_id": "cand_123",
            "candidate_email": "candidate@example.com"  # Optional, for auto-registration
        }

    Returns:
        Configuration details, company info, and session information
    """
    try:
        invitation_code = request_data.get("invitation_code", "").strip().upper()
        candidate_id = request_data.get("candidate_id")
        candidate_email = request_data.get("candidate_email", "")

        if not invitation_code:
            raise HTTPException(status_code=400, detail="Invitation code is required")

        if not candidate_id:
            raise HTTPException(status_code=400, detail="Candidate ID is required")

        main_logger.info(
            f"Candidate {candidate_id} attempting to join with code: {invitation_code}"
        )

        db_service = InterviewConfigurationDatabase()

        # Use the new database method to create session and get all details
        result = await db_service.create_interview_session_from_code(
            invitation_code=invitation_code,
            candidate_id=candidate_id,
            candidate_email=candidate_email
            or candidate_id,  # Fallback to candidate_id if email not provided
        )

        if not result or not result.get("success"):
            raise HTTPException(
                status_code=404, detail="Invalid invitation code or interview not available"
            )

        config = result["configuration"]
        company = result.get("company")
        job_posting = result.get("job_posting")
        session_id = result["session_id"]

        main_logger.info(f"Interview session {session_id} created for candidate {candidate_id}")

        return {
            "success": True,
            "message": "Successfully joined interview",
            "configuration_id": config.get("id"),
            "session_id": session_id,
            "configuration": config,
            "company": {
                "id": company.get("id") if company else None,
                "name": company.get("name") if company else "Unknown Company",
                "contact_email": company.get("contact_email") if company else None,
                "industry": company.get("industry") if company else None,
                "location": company.get("location") if company else None,
                "website": company.get("website") if company else None,
            }
            if company
            else None,
            "job_posting": {
                "id": job_posting.get("id") if job_posting else None,
                "title": job_posting.get("title")
                if job_posting
                else config.get("job_title", "Interview"),
                "description": job_posting.get("description") if job_posting else None,
                "requirements": job_posting.get("requirements") if job_posting else None,
            }
            if job_posting
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to join interview by code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to join interview: {e!s}")


# ============================================================================
# INTERVIEW SESSIONS & EVALUATIONS
# ============================================================================


@router.get("/sessions")
async def get_interview_sessions(
    configuration_id: Optional[str] = None, candidate_id: Optional[str] = None
):
    """
    Get interview sessions by configuration or candidate

    Args:
        configuration_id: Filter by configuration ID
        candidate_id: Filter by candidate ID

    Returns:
        List of interview sessions with candidate details and status
    """
    try:
        db_service = InterviewConfigurationDatabase()

        sessions: List[Dict[str, Any]] = []
        if configuration_id:
            # Get all sessions for a configuration
            main_logger.info(f"Getting sessions for configuration: {configuration_id}")
            sessions = await db_service.get_interview_sessions_by_configuration(configuration_id)
        elif candidate_id:
            # Get all sessions for a candidate
            main_logger.info(f"Getting sessions for candidate: {candidate_id}")
            sessions = await db_service.get_interview_sessions_by_candidate(candidate_id)
        else:
            raise HTTPException(
                status_code=400, detail="Either configuration_id or candidate_id is required"
            )

        # Enrich sessions with candidate information
        enriched_sessions = []
        for session in sessions:
            candidate_id_value = (
                session.get("candidate_id")
                or session.get("candidateId")
                or session.get("candidateDetails", {}).get("id")
            )
            candidate = (
                await db_service.get_candidate(candidate_id_value) if candidate_id_value else None
            )

            session_identifier = (
                session.get("id") or session.get("session_id") or session.get("sessionId")
            )

            status = session.get("status") or session.get("current_status") or "unknown"
            score = (
                session.get("overall_score") or session.get("score") or session.get("finalScore")
            )

            enriched_session = {
                **session,
                "session_id": session_identifier,
                "candidate_id": candidate_id_value,
                "candidate_name": candidate.get("name")
                if candidate
                else session.get("candidate_name", "Unknown"),
                "candidate_email": candidate.get("email")
                if candidate
                else session.get("candidate_email", "Unknown"),
                "status": status,
                "overall_score": score,
            }

            enriched_sessions.append(enriched_session)

        return {"success": True, "sessions": enriched_sessions, "total": len(enriched_sessions)}

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get interview sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview sessions: {e!s}")


@router.put("/sessions/{session_id}/end")
async def end_interview_session(session_id: str, request_data: Dict[str, Any]):
    """
    Finalize an interview session when candidate exits or completes

    Args:
        session_id: Interview session ID
        request_data: {
            "final_code": "...",  # Optional: final code submission
            "reason": "completed|exited|timeout",  # Reason for ending
            "feedback": "..."  # Optional: candidate feedback
        }

    Returns:
        Updated session data
    """
    try:
        main_logger.info(f"Ending interview session: {session_id}")

        db_service = InterviewConfigurationDatabase()

        # Get existing session
        session = await db_service.get_interview_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if already completed
        if session.get("status") in ["completed", "evaluated"]:
            return {"success": True, "message": "Session already completed", "session": session}

        # Prepare update data
        from datetime import datetime

        update_data = {
            "status": "completed",
            "completedAt": datetime.utcnow(),
            "endReason": request_data.get("reason", "completed"),
        }

        # Save final code if provided
        if request_data.get("final_code"):
            update_data["finalCode"] = request_data.get("final_code")

        # Save candidate feedback if provided
        if request_data.get("feedback"):
            update_data["candidateFeedback"] = request_data.get("feedback")

        # Calculate duration if possible
        if session.get("startedAt"):
            start_time = session.get("startedAt")
            if isinstance(start_time, str):
                from dateutil import parser

                start_time = parser.parse(start_time)
            duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            update_data["durationMinutes"] = round(duration_seconds / 60, 2)

        # Update session in database
        success = await db_service.update_interview_session(session_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session")

        # Get updated session
        updated_session = await db_service.get_interview_session(session_id)

        main_logger.info(f"Interview session {session_id} ended successfully")

        return {
            "success": True,
            "message": "Interview session ended successfully",
            "session": updated_session,
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to end interview session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end interview session: {e!s}")


@router.get("/sessions/{session_id}/evaluation")
async def get_session_evaluation(session_id: str):
    """
    Get evaluation results for an interview session

    Args:
        session_id: Interview session ID

    Returns:
        Evaluation data including scores and feedback
    """
    try:
        main_logger.info(f"Getting evaluation for session: {session_id}")

        db_service = InterviewConfigurationDatabase()

        # Get session details
        session = await db_service.get_interview_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get candidate details
        candidate_id = session.get("candidate_id")
        candidate = await db_service.get_candidate(candidate_id) if candidate_id else None

        # Get evaluation data (if exists)
        evaluation = await db_service.get_session_evaluation(session_id)

        return {
            "success": True,
            "session": {
                "session_id": session_id,
                "candidate_id": candidate_id,
                "candidate_name": candidate.get("name") if candidate else "Unknown",
                "candidate_email": candidate.get("email") if candidate else "Unknown",
                "status": session.get("status"),
                "started_at": session.get("started_at") or session.get("startedAt"),
                "completed_at": session.get("completed_at") or session.get("completedAt"),
                "created_at": session.get("created_at") or session.get("createdAt"),
            },
            "evaluation": evaluation,
            "configuration_id": session.get("configuration_id"),
        }

    except HTTPException:
        raise
    except Exception as e:
        main_logger.error(f"Failed to get evaluation for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation: {e!s}")
