"""
Constants for job types available for interview configuration.
These correspond to template folders in onboarding_data/templates/
"""

AVAILABLE_JOB_TYPES = [
    {
        "value": "ml_engineer",
        "label": "Machine Learning Engineer",
        "description": "AI/ML focused engineering roles",
    },
    {
        "value": "senior_ml_engineer",
        "label": "Senior Machine Learning Engineer",
        "description": "Advanced ML engineering positions",
    },
    {
        "value": "data_scientist",
        "label": "Data Scientist",
        "description": "Data analysis and modeling roles",
    },
    {
        "value": "software_engineer",
        "label": "Software Engineer",
        "description": "General software development roles",
    },
    {
        "value": "ai_engineer",
        "label": "AI Engineer",
        "description": "Artificial intelligence focused roles",
    },
    {
        "value": "data_engineer",
        "label": "Data Engineer",
        "description": "Data infrastructure and pipeline roles",
    },
    {
        "value": "product_manager",
        "label": "Product Manager",
        "description": "Product strategy and management roles",
    },
    {
        "value": "devops_engineer",
        "label": "DevOps Engineer",
        "description": "Infrastructure and deployment roles",
    },
    {
        "value": "frontend_engineer",
        "label": "Frontend Engineer",
        "description": "User interface and web development roles",
    },
    {
        "value": "backend_engineer",
        "label": "Backend Engineer",
        "description": "Server-side and API development roles",
    },
]


# Helper function to get job type by value
def get_job_type_by_value(value: str):
    """Get job type configuration by its value"""
    for job in AVAILABLE_JOB_TYPES:
        if job["value"] == value:
            return job
    return None


# Helper function to get job type by label
def get_job_type_by_label(label: str):
    """Get job type configuration by its label (case-insensitive)"""
    for job in AVAILABLE_JOB_TYPES:
        if job["label"].lower() == label.lower():
            return job
    return None


# Get all available job type values
def get_available_job_values():
    """Get list of all available job type values"""
    return [job["value"] for job in AVAILABLE_JOB_TYPES]


# Get all available job type labels
def get_available_job_labels():
    """Get list of all available job type labels"""
    return [job["label"] for job in AVAILABLE_JOB_TYPES]
