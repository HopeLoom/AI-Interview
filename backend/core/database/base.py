"""
Database abstraction layer for the interview simulation platform.
Provides a unified interface for different database backends (Firebase, PostgreSQL, SQLite).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DatabaseType(Enum):
    """Supported database types"""

    FIREBASE = "firebase"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


@dataclass
class UserProfile:
    """User profile data structure"""

    user_id: str
    name: str
    email: str
    company_name: str
    job_title: str
    location: str
    auth_code: str
    resume_url: Optional[str] = None
    starter_code_url: Optional[str] = None
    profile_json_url: Optional[str] = None
    simulation_config_json_url: Optional[str] = None
    panelist_profiles: Optional[List[str]] = None
    panelist_images: Optional[List[str]] = None
    created_at: Optional[str] = None
    role: Optional[str] = "candidate"  # candidate, company_admin, super_admin
    organization_id: Optional[str] = None


@dataclass
class CompanyProfile:
    """Company profile data structure"""

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
    is_active: bool = True


@dataclass
class SessionData:
    """Session data structure"""

    session_id: str
    user_id: str
    start_time: str
    status: str = "active"  # active, completed, terminated
    end_time: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DatabaseInterface(ABC):
    """Abstract base class for database implementations"""

    def __init__(self, logger=None):
        self.logger = logger
        self.user_data: Optional[UserProfile] = None
        self.session_id: Optional[str] = None
        self.pending_batch_operations = []
        self.batch_size_limit = 5

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the database connection"""
        pass

    @abstractmethod
    async def close(self):
        """Close the database connection"""
        pass

    # User Management
    @abstractmethod
    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def load_user_data(self, user_id: str) -> bool:
        """Load user profile data"""
        pass

    @abstractmethod
    async def create_user(self, user_profile: UserProfile) -> bool:
        """Create a new user"""
        pass

    @abstractmethod
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        pass

    @abstractmethod
    async def get_all_users_data(self) -> List[UserProfile]:
        """Get all user profiles"""
        pass

    # Session Management
    @abstractmethod
    async def create_new_session(self, user_id: str) -> str:
        """Create a new session and return session ID"""
        pass

    @abstractmethod
    async def get_session_data(self, user_id: str, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        pass

    @abstractmethod
    async def update_session(self, user_id: str, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        pass

    @abstractmethod
    async def get_most_recent_session_id_by_user_id(self, user_id: str) -> Optional[str]:
        """Get the most recent session ID for a user"""
        pass

    @abstractmethod
    async def get_all_session_data(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all data for a session"""
        pass

    # Interview Data Management
    @abstractmethod
    async def add_dialog_to_database(self, user_id: str, session_id: str, message: Any):
        """Add dialog message to database"""
        pass

    @abstractmethod
    async def add_evaluation_output_to_database(self, user_id: str, session_id: str, output: Any):
        """Add evaluation output to database"""
        pass

    @abstractmethod
    async def add_final_evaluation_output_to_database(
        self, user_id: str, session_id: str, output: Any
    ):
        """Add final evaluation output to database"""
        pass

    @abstractmethod
    async def get_final_evaluation_output_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get final evaluation output from database"""
        pass

    # Configuration Management
    @abstractmethod
    async def store_simulation_config(
        self, config_id: str, config_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> bool:
        """Store simulation configuration"""
        pass

    @abstractmethod
    async def get_simulation_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation configuration"""
        pass

    @abstractmethod
    async def list_simulation_configs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List simulation configurations"""
        pass

    @abstractmethod
    async def delete_simulation_config(self, config_id: str) -> bool:
        """Delete simulation configuration"""
        pass

    # Batch Operations
    @abstractmethod
    async def add_to_batch(
        self, user_id: str, session_id: str, operation_type: str, data: Any, collection_path: str
    ):
        """Add operation to batch queue"""
        pass

    @abstractmethod
    async def commit_batch(self) -> bool:
        """Commit batch operations"""
        pass

    # Generic Data Operations
    @abstractmethod
    async def add_json_data_output_to_database(
        self, user_id: str, session_id: str, name: str, json_data: Dict[str, Any]
    ):
        """Add JSON data to database"""
        pass

    @abstractmethod
    async def get_json_data_output_from_database(
        self, name: str, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get JSON data from database"""
        pass

    # File and Media Operations
    @abstractmethod
    async def upload_image(self, image_path: str, user_id: str, file_name: str) -> str:
        """Upload image to storage"""
        pass

    @abstractmethod
    async def get_image_url(
        self, user_id: str, file_name: str, cache_bust: bool = True
    ) -> Optional[str]:
        """Get image URL from storage"""
        pass

    @abstractmethod
    async def get_image_url_from_name(self, image_name: str) -> Optional[str]:
        """Get image URL by image name"""
        pass

    @abstractmethod
    async def upload_video(
        self, user_id: str, session_id: str, filename: str, content: bytes, content_type: str
    ) -> str:
        """Upload video to storage"""
        pass

    @abstractmethod
    async def upload_file(self, user_id: str, session_id: str, file_path: str) -> str:
        """Upload file to storage"""
        pass

    # Code and Configuration Operations
    @abstractmethod
    async def fetch_starter_code_from_url(self) -> Optional[str]:
        """Fetch starter code from URL"""
        pass

    @abstractmethod
    async def get_recent_code_data(self, user_id: str) -> Optional[str]:
        """Get recent code data for user"""
        pass

    @abstractmethod
    async def get_profile_json_data(self) -> Optional[Dict[str, Any]]:
        """Get profile JSON data"""
        pass

    @abstractmethod
    async def get_simulation_config_json_data(self) -> Optional[Dict[str, Any]]:
        """Get simulation config JSON data"""
        pass

    @abstractmethod
    async def get_panelist_profile_json_data(self, panelist_name: str) -> Optional[Dict[str, Any]]:
        """Get panelist profile JSON data"""
        pass

    # Specialized Data Operations
    @abstractmethod
    async def get_activity_progress_analysis_output_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get activity progress analysis output"""
        pass

    @abstractmethod
    async def get_metadata_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata from database"""
        pass

    @abstractmethod
    async def get_final_visualisation_report_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get final visualisation report from database"""
        pass

    # Company Management
    @abstractmethod
    async def create_company(self, company_profile: CompanyProfile) -> bool:
        """Create a new company"""
        pass

    @abstractmethod
    async def get_company_by_id(self, company_id: str) -> Optional[CompanyProfile]:
        """Get company by ID"""
        pass

    @abstractmethod
    async def get_company_by_email(self, email: str) -> Optional[CompanyProfile]:
        """Get company by email"""
        pass

    @abstractmethod
    async def update_company(self, company_id: str, updates: Dict[str, Any]) -> bool:
        """Update company profile"""
        pass

    @abstractmethod
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        pass

    @abstractmethod
    async def search_companies_by_name(self, name: str) -> List[CompanyProfile]:
        """Search companies by name"""
        pass

    @abstractmethod
    async def check_company_email_availability(self, email: str) -> bool:
        """Check if company email is available"""
        pass

    @abstractmethod
    async def get_all_companies(self) -> List[CompanyProfile]:
        """Get all companies"""
        pass

    @abstractmethod
    async def validate_company_session(self, token: str) -> bool:
        """Validate company session token"""
        pass

    # Dashboard and Candidate Management
    @abstractmethod
    async def get_candidates_by_company_name(self, company_name: str) -> List[UserProfile]:
        """Get all candidates for a specific company by company name"""
        pass

    @abstractmethod
    async def get_candidates_by_company_id(self, company_id: str) -> List[UserProfile]:
        """Get all candidates for a specific company by company ID"""
        pass

    @abstractmethod
    async def get_candidate_evaluation_data(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get evaluation data for a specific candidate"""
        pass

    @abstractmethod
    async def get_candidate_interview_sessions(self, user_id: str) -> List[SessionData]:
        """Get all interview sessions for a candidate"""
        pass

    @abstractmethod
    async def get_company_dashboard_data(self, company_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a company"""
        pass

    @abstractmethod
    async def get_candidates_with_evaluations(self, company_id: str) -> List[Dict[str, Any]]:
        """Get candidates with their evaluation data for a company"""
        pass

    @abstractmethod
    async def get_company_interviews(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all interviews/job postings for a company"""
        pass

    @abstractmethod
    async def get_interview_candidates(
        self, company_id: str, interview_id: str
    ) -> List[Dict[str, Any]]:
        """Get candidates for a specific interview/job posting"""
        pass

    # Helper methods that can be implemented in base class
    def set_logger(self, logger):
        """Set the logger for the class"""
        self.logger = logger
        if self.logger is not None:
            self.logger.info("Logger set successfully.")

    def log_info(self, message: str):
        """Log info message if logger is available"""
        if self.logger is not None:
            self.logger.info(message)

    def log_error(self, message: str):
        """Log error message if logger is available"""
        if self.logger is not None:
            self.logger.error(message)

    def log_warning(self, message: str):
        """Log warning message if logger is available"""
        if self.logger is not None:
            self.logger.warning(message)
