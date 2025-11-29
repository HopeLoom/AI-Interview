"""
Comprehensive Configuration Router for Interview Simulation Platform
Handles both static configuration data and dynamic configuration generation
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from globals import main_logger
from interview_configuration.models import (
    ConfigurationGenerationResponse,
    FrontendConfigurationInput,
)

# Import interview configuration service and models
from interview_configuration.service import InterviewConfigurationService
from providers.provider_factory import ProviderFactory

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


@router.post("/generate", response_model=ConfigurationGenerationResponse)
async def generate_full_configuration(
    config_input: FrontendConfigurationInput,
    company_id: str,  # In real implementation, get from auth
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Generate complete interview configuration from frontend input
    """
    try:
        main_logger.info(f"Generating configuration for company: {company_id}")
        response = await service.generate_full_configuration(config_input, company_id)

        if not response.success:
            raise HTTPException(
                status_code=400, detail={"errors": response.errors, "warnings": response.warnings}
            )

        return response

    except Exception as e:
        main_logger.error(f"Configuration generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration generation failed: {e!s}")


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    company_id: str = Form(...),
    job_name: str = Form(...),
):
    """
    Upload file (job description or resume) and return file ID
    """
    try:
        main_logger.info(f"Uploading {file_type} file for company: {company_id}, job: {job_name}")

        # Validate file type
        if file_type not in ["job_description", "resume"]:
            raise HTTPException(
                status_code=400, detail="Invalid file type. Must be 'job_description' or 'resume'"
            )

        # Create upload directory
        upload_dir = f"static/{company_id}/{job_name}/{file_type}"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = int(datetime.now().timestamp())
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{file_type}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return file information
        return {
            "success": True,
            "file_id": unique_filename,
            "file_path": file_path,
            "file_type": file_type,
            "message": f"{file_type.title()} file uploaded successfully",
        }

    except Exception as e:
        main_logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {e!s}")


@router.get("/job-types")
async def get_available_job_types(
    service: InterviewConfigurationService = Depends(get_configuration_service),
):
    """
    Get list of available job types for frontend dropdown
    """
    try:
        main_logger.info("Getting available job types")
        job_types = service.get_available_job_types()

        return {"success": True, "job_types": job_types}

    except Exception as e:
        main_logger.error(f"Failed to get job types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job types: {e!s}")
