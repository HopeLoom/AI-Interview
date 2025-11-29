"""
Firebase database adapter for the interview simulation platform.
Wraps the existing Firebase implementation to conform to the DatabaseInterface.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.database import FireBaseDataBase
from .base import CompanyProfile, DatabaseInterface, SessionData, UserProfile


class FirebaseAdapter(DatabaseInterface):
    """Firebase implementation of the database interface"""

    def __init__(self, config, logger=None):
        super().__init__(logger)
        self.config = config
        self._firebase_db = None

    async def initialize(self) -> bool:
        """Initialize Firebase database"""
        try:
            # Extract Firebase configuration from config
            credentials_path = getattr(self.config.database, "firebase_credentials_path", None)
            storage_bucket = getattr(self.config.database, "firebase_storage_bucket", None)

            # Create Firebase database instance with configuration
            self._firebase_db = FireBaseDataBase(
                logger=self.logger, credentials_path=credentials_path, storage_bucket=storage_bucket
            )
            self.log_info("Firebase database initialized successfully")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize Firebase database: {e}")
            return False

    async def close(self):
        """Close the database connection"""
        # Firebase doesn't need explicit closing
        self.log_info("Firebase database connection closed")

    # User Management
    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address"""
        return await asyncio.to_thread(self._firebase_db.get_user_id_by_email, email)

    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        fb_user = await asyncio.to_thread(self._firebase_db.get_user_by_id, user_id)
        if fb_user:
            # Convert Firebase UserProfile to interface UserProfile (they should match now)
            return fb_user
        return None

    async def load_user_data(self, user_id: str) -> bool:
        """Load user profile data"""
        success = await asyncio.to_thread(self._firebase_db.load_user_data, user_id)
        if success:
            # Copy the loaded user data (structures should match now)
            fb_user_data = self._firebase_db.user_data
            self.user_data = fb_user_data
        return success

    async def create_user(self, user_profile: UserProfile) -> bool:
        """Create a new user"""
        # Firebase user creation is typically handled through Firebase Auth
        # For now, we'll simulate this by updating the user data
        try:
            # Convert to Firebase format
            fb_user_data = {
                "user_id": user_profile.user_id,
                "name": user_profile.name,
                "email": user_profile.email,
                "company_name": user_profile.company_name,
                "job_title": user_profile.job_title,
                "location": user_profile.location,
                "auth_code": user_profile.auth_code,
                "resume_url": user_profile.resume_url,
                "starter_code_url": user_profile.starter_code_url,
                "profile_json_url": user_profile.profile_json_url,
                "simulation_config_json_url": user_profile.simulation_config_json_url,
                "panelist_profiles": user_profile.panelist_profiles,
                "panelist_images": user_profile.panelist_images,
                "created_at": user_profile.created_at or datetime.now().isoformat(),
                "role": user_profile.role,
                "organization_id": user_profile.organization_id,
            }

            # Store in Firestore using asyncio.to_thread
            def _set_user_data():
                doc_ref = self._firebase_db.db.collection("users").document(user_profile.user_id)
                doc_ref.set(fb_user_data)

            await asyncio.to_thread(_set_user_data)

            self.log_info(f"User created successfully: {user_profile.user_id}")
            return True
        except Exception as e:
            self.log_error(f"Error creating user {user_profile.user_id}: {e}")
            return False

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            if not updates:
                return True

            def _update_user():
                doc_ref = self._firebase_db.db.collection("users").document(user_id)
                doc_ref.update(updates)

            await asyncio.to_thread(_update_user)

            self.log_info(f"User updated successfully: {user_id}")
            return True
        except Exception as e:
            self.log_error(f"Error updating user {user_id}: {e}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            doc_ref = self._firebase_db.db.collection("users").document(user_id)
            doc_ref.delete()

            self.log_info(f"User deleted successfully: {user_id}")
            return True
        except Exception as e:
            self.log_error(f"Error deleting user {user_id}: {e}")
            return False

    async def get_all_users_data(self) -> List[UserProfile]:
        """Get all user profiles"""
        try:
            fb_users = self._firebase_db.get_all_users_data()
            users = []
            for fb_user in fb_users:
                user = UserProfile(
                    user_id=fb_user.user_id,
                    name=fb_user.name,
                    email=fb_user.email,
                    company_name=fb_user.company_name,
                    location=fb_user.location,
                    resume_url=fb_user.resume_url,
                    starter_code_url=fb_user.starter_code_url,
                    profile_json_url=fb_user.profile_json_url,
                    simulation_config_json_url=fb_user.simulation_config_json_url,
                    panelist_profiles=fb_user.panelist_profiles,
                    panelist_images=fb_user.panelist_images,
                    created_at=fb_user.created_at,
                    role="candidate",  # Default role for existing users
                    organization_id=None,
                )
                users.append(user)
            return users
        except Exception as e:
            self.log_error(f"Error getting all users data: {e}")
            return []

    # Session Management
    async def create_new_session(self, user_id: str) -> str:
        """Create a new session and return session ID"""
        session_id = await asyncio.to_thread(self._firebase_db.create_new_session, user_id)
        self.session_id = session_id
        return session_id

    async def get_session_data(self, user_id: str, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        try:
            session_ref = (
                self._firebase_db.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
            )
            doc = session_ref.get()

            if doc.exists:
                data = doc.to_dict()
                return SessionData(
                    session_id=session_id,
                    user_id=user_id,
                    start_time=data.get("start_time", ""),
                    status=data.get("status", "active"),
                    end_time=data.get("end_time"),
                    metadata=data.get("metadata"),
                )
            return None
        except Exception as e:
            self.log_error(f"Error getting session data for {user_id}/{session_id}: {e}")
            return None

    async def update_session(self, user_id: str, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            if not updates:
                return True

            session_ref = (
                self._firebase_db.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
            )
            session_ref.update(updates)

            self.log_info(f"Session updated: {session_id}")
            return True
        except Exception as e:
            self.log_error(f"Error updating session {session_id}: {e}")
            return False

    async def get_most_recent_session_id_by_user_id(self, user_id: str) -> Optional[str]:
        """Get the most recent session ID for a user"""
        return self._firebase_db.get_most_recent_session_id_by_user_id(user_id)

    async def get_all_session_data(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all data for a session"""
        return self._firebase_db.get_all_session_data(user_id, session_id)

    # Interview Data Management
    async def add_dialog_to_database(self, user_id: str, session_id: str, message: Any):
        """Add dialog message to database"""
        self._firebase_db.add_dialog_to_database(user_id, session_id, message)

    async def add_evaluation_output_to_database(self, user_id: str, session_id: str, output: Any):
        """Add evaluation output to database"""
        self._firebase_db.add_evaluation_output_to_database(user_id, session_id, output)

    async def add_final_evaluation_output_to_database(
        self, user_id: str, session_id: str, output: Any
    ):
        """Add final evaluation output to database"""
        self._firebase_db.add_final_evaluation_output_to_database(user_id, session_id, output)

    async def get_final_evaluation_output_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get final evaluation output from database"""
        return self._firebase_db.get_final_evaluation_output_from_database(user_id, session_id)

    # Configuration Management
    async def store_simulation_config(
        self, config_id: str, config_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> bool:
        """Store simulation configuration"""
        try:
            config_ref = self._firebase_db.db.collection("simulation_configs").document(config_id)
            config_doc = {
                "config_id": config_id,
                "user_id": user_id,
                "config_name": config_data.get("job_details", {}).get(
                    "job_title", "Untitled Configuration"
                ),
                "config_data": config_data,
                "is_template": False,
                "is_public": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            config_ref.set(config_doc)

            self.log_info(f"Simulation config stored: {config_id}")
            return True
        except Exception as e:
            self.log_error(f"Error storing simulation config {config_id}: {e}")
            return False

    async def get_simulation_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation configuration"""
        try:
            config_ref = self._firebase_db.db.collection("simulation_configs").document(config_id)
            doc = config_ref.get()

            if doc.exists:
                return doc.to_dict().get("config_data")
            return None
        except Exception as e:
            self.log_error(f"Error getting simulation config {config_id}: {e}")
            return None

    async def list_simulation_configs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List simulation configurations"""
        try:
            configs_ref = self._firebase_db.db.collection("simulation_configs")

            if user_id:
                # Get user's configs and public configs
                query = configs_ref.where("user_id", "==", user_id)
                user_configs = query.stream()

                public_query = configs_ref.where("is_public", "==", True)
                public_configs = public_query.stream()

                all_configs = list(user_configs) + list(public_configs)
            else:
                # Get only public and template configs
                query = configs_ref.where("is_public", "==", True)
                all_configs = query.stream()

            configs = []
            for doc in all_configs:
                data = doc.to_dict()
                config = {
                    "config_id": data.get("config_id"),
                    "config_name": data.get("config_name"),
                    "is_template": data.get("is_template", False),
                    "is_public": data.get("is_public", False),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                }
                configs.append(config)

            return configs
        except Exception as e:
            self.log_error(f"Error listing simulation configs: {e}")
            return []

    async def delete_simulation_config(self, config_id: str) -> bool:
        """Delete simulation configuration"""
        try:
            config_ref = self._firebase_db.db.collection("simulation_configs").document(config_id)
            config_ref.delete()

            self.log_info(f"Simulation config deleted: {config_id}")
            return True
        except Exception as e:
            self.log_error(f"Error deleting simulation config {config_id}: {e}")
            return False

    # Batch Operations
    async def add_to_batch(
        self, user_id: str, session_id: str, operation_type: str, data: Any, collection_path: str
    ):
        """Add operation to batch queue"""
        self._firebase_db.add_to_batch(user_id, session_id, operation_type, data, collection_path)

    async def commit_batch(self) -> bool:
        """Commit batch operations"""
        try:
            self._firebase_db.commit_batch()
            return True
        except Exception as e:
            self.log_error(f"Error committing batch operations: {e}")
            return False

    # Generic Data Operations
    async def add_json_data_output_to_database(
        self, user_id: str, session_id: str, name: str, json_data: Dict[str, Any]
    ):
        """Add JSON data to database"""
        self._firebase_db.add_json_data_output_to_database(user_id, session_id, name, json_data)

    async def get_json_data_output_from_database(
        self, name: str, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get JSON data from database"""
        return self._firebase_db.get_json_data_output_from_database(name, user_id, session_id)

    # File and Media Operations (DatabaseInterface implementation)
    async def upload_image(self, image_path: str, user_id: str, file_name: str) -> str:
        """Upload image to storage"""
        return self._firebase_db.upload_image(image_path, user_id, file_name)

    async def upload_json(self, user_id: str, json_data: Dict[str, Any], file_name: str) -> str:
        """Upload JSON data to storage"""
        return self._firebase_db.upload_json(user_id, json_data, file_name)

    async def get_image_url(
        self, user_id: str, file_name: str, cache_bust: bool = True
    ) -> Optional[str]:
        """Get image URL from storage"""
        return self._firebase_db.get_image_url(user_id, file_name, cache_bust)

    async def get_image_url_from_name(self, image_name: str) -> Optional[str]:
        """Get image URL by image name"""
        return self._firebase_db.get_image_url_from_name(image_name)

    async def upload_video(
        self, user_id: str, session_id: str, filename: str, content: bytes, content_type: str
    ) -> str:
        """Upload video to storage"""
        return self._firebase_db.upload_video(user_id, session_id, filename, content, content_type)

    async def upload_file(self, file_path: str, user_id: str, file_name: str) -> str:
        """Upload file to storage"""
        return self._firebase_db.upload_file(file_path, user_id, file_name)

    # Code and Configuration Operations (DatabaseInterface implementation)
    async def fetch_starter_code_from_url(self) -> Optional[str]:
        """Fetch starter code from URL"""
        return self._firebase_db.fetch_starter_code_from_url()

    async def get_recent_code_data(self, user_id: str) -> Optional[str]:
        """Get recent code data for user"""
        return self._firebase_db.get_recent_code_data(user_id)

    async def get_profile_json_data(self) -> Optional[Dict[str, Any]]:
        """Get profile JSON data"""
        return self._firebase_db.get_profile_json_data()

    async def get_simulation_config_json_data(self) -> Optional[Dict[str, Any]]:
        """Get simulation config JSON data"""
        return self._firebase_db.get_simulation_config_json_data()

    async def get_panelist_profile_json_data(self, panelist_name: str) -> Optional[Dict[str, Any]]:
        """Get panelist profile JSON data"""
        return self._firebase_db.get_panelist_profile_json_data(panelist_name)

    # Specialized Data Operations (DatabaseInterface implementation)
    async def get_activity_progress_analysis_output_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get activity progress analysis output"""
        return self._firebase_db.get_activity_progress_analysis_output_from_database(
            user_id, session_id
        )

    async def get_metadata_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata from database"""
        return self._firebase_db.get_metadata_from_database(user_id, session_id)

    async def get_final_visualisation_report_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get final visualisation report from database"""
        return self._firebase_db.get_final_visualisation_report_from_database(user_id, session_id)

    # Company Management
    async def create_company(self, company_profile: CompanyProfile) -> bool:
        """Create a new company"""
        try:
            company_data = {
                "company_id": company_profile.company_id,
                "name": company_profile.name,
                "email": company_profile.email,
                "industry": company_profile.industry,
                "size": company_profile.size,
                "location": company_profile.location,
                "website": company_profile.website,
                "description": company_profile.description,
                "created_at": company_profile.created_at or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": company_profile.is_active,
            }

            # Use the original FireBaseDataBase method
            return self._firebase_db.create_company(company_data)
        except Exception as e:
            self.log_error(f"Error creating company {company_profile.company_id}: {e}")
            return False

    async def get_company_by_id(self, company_id: str) -> Optional[CompanyProfile]:
        """Get company by ID"""
        try:
            data = self._firebase_db.get_company_by_id(company_id)

            if data:
                return CompanyProfile(
                    company_id=data.get("company_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    industry=data.get("industry"),
                    size=data.get("size"),
                    location=data.get("location"),
                    website=data.get("website"),
                    description=data.get("description"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    is_active=data.get("is_active", True),
                )
            return None
        except Exception as e:
            self.log_error(f"Error getting company {company_id}: {e}")
            return None

    async def get_company_by_email(self, email: str) -> Optional[CompanyProfile]:
        """Get company by email"""
        try:
            data = self._firebase_db.get_company_by_email(email)

            if data:
                return CompanyProfile(
                    company_id=data.get("company_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    industry=data.get("industry"),
                    size=data.get("size"),
                    location=data.get("location"),
                    website=data.get("website"),
                    description=data.get("description"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    is_active=data.get("is_active", True),
                )
            return None
        except Exception as e:
            self.log_error(f"Error getting company by email {email}: {e}")
            return None

    async def update_company(self, company_id: str, updates: Dict[str, Any]) -> bool:
        """Update company profile"""
        try:
            if not updates:
                return True

            # Use the original FireBaseDataBase method
            return self._firebase_db.update_company(company_id, updates)
        except Exception as e:
            self.log_error(f"Error updating company {company_id}: {e}")
            return False

    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        try:
            # Use the original FireBaseDataBase method
            return self._firebase_db.delete_company(company_id)
        except Exception as e:
            self.log_error(f"Error deleting company {company_id}: {e}")
            return False

    async def search_companies_by_name(self, name: str) -> List[CompanyProfile]:
        """Search companies by name"""
        try:
            companies_data = self._firebase_db.search_companies_by_name(name)

            companies = []
            for data in companies_data:
                company = CompanyProfile(
                    company_id=data.get("company_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    industry=data.get("industry"),
                    size=data.get("size"),
                    location=data.get("location"),
                    website=data.get("website"),
                    description=data.get("description"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    is_active=data.get("is_active", True),
                )
                companies.append(company)

            return companies
        except Exception as e:
            self.log_error(f"Error searching companies by name {name}: {e}")
            return []

    async def check_company_email_availability(self, email: str) -> bool:
        """Check if company email is available"""
        try:
            # Use the original FireBaseDataBase method
            return self._firebase_db.check_company_email_availability(email)
        except Exception as e:
            self.log_error(f"Error checking email availability {email}: {e}")
            return False

    async def get_all_companies(self) -> List[CompanyProfile]:
        """Get all companies"""
        try:
            companies_data = self._firebase_db.get_all_companies()

            companies = []
            for data in companies_data:
                company = CompanyProfile(
                    company_id=data.get("company_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    industry=data.get("industry"),
                    size=data.get("size"),
                    location=data.get("location"),
                    website=data.get("website"),
                    description=data.get("description"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    is_active=data.get("is_active", True),
                )
                companies.append(company)

            return companies
        except Exception as e:
            self.log_error(f"Error getting all companies: {e}")
            return []

    async def validate_company_session(self, token: str) -> bool:
        """Validate company session token"""
        try:
            # Use the original FireBaseDataBase method
            return self._firebase_db.validate_company_session(token)
        except Exception as e:
            self.log_error(f"Error validating company session: {e}")
            return False

    # Dashboard and Candidate Management
    async def get_candidates_by_company_name(self, company_name: str) -> List[UserProfile]:
        """Get all candidates for a specific company by company name"""
        try:
            candidates_data = self._firebase_db.get_candidates_by_company_name(company_name)

            candidates = []
            for data in candidates_data:
                candidate = UserProfile(
                    user_id=data.get("user_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    company_name=data.get("company_name"),
                    location=data.get("location"),
                    resume_url=data.get("resume_url"),
                    starter_code_url=data.get("starter_code_url"),
                    profile_json_url=data.get("profile_json_url"),
                    simulation_config_json_url=data.get("simulation_config_json_url"),
                    panelist_profiles=data.get("panelist_profiles"),
                    panelist_images=data.get("panelist_images"),
                    created_at=data.get("created_at"),
                    role=data.get("role", "candidate"),
                    organization_id=data.get("organization_id"),
                )
                candidates.append(candidate)

            return candidates
        except Exception as e:
            self.log_error(f"Error getting candidates by company name {company_name}: {e}")
            return []

    async def get_candidates_by_company_id(self, company_id: str) -> List[UserProfile]:
        """Get all candidates for a specific company by company ID"""
        try:
            candidates_data = self._firebase_db.get_candidates_by_company_id(company_id)

            candidates = []
            for data in candidates_data:
                candidate = UserProfile(
                    user_id=data.get("user_id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    company_name=data.get("company_name"),
                    location=data.get("location"),
                    resume_url=data.get("resume_url"),
                    starter_code_url=data.get("starter_code_url"),
                    profile_json_url=data.get("profile_json_url"),
                    simulation_config_json_url=data.get("simulation_config_json_url"),
                    panelist_profiles=data.get("panelist_profiles"),
                    panelist_images=data.get("panelist_images"),
                    created_at=data.get("created_at"),
                    role=data.get("role", "candidate"),
                    organization_id=data.get("organization_id"),
                )
                candidates.append(candidate)

            return candidates
        except Exception as e:
            self.log_error(f"Error getting candidates by company ID {company_id}: {e}")
            return []

    async def get_candidate_evaluation_data(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get evaluation data for a specific candidate"""
        try:
            return self._firebase_db.get_candidate_evaluation_data(user_id, session_id)
        except Exception as e:
            self.log_error(f"Error getting evaluation data for candidate {user_id}: {e}")
            return None

    async def get_candidate_interview_sessions(self, user_id: str) -> List[SessionData]:
        """Get all interview sessions for a candidate"""
        try:
            sessions_data = self._firebase_db.get_candidate_interview_sessions(user_id)

            sessions = []
            for data in sessions_data:
                session = SessionData(
                    session_id=data.get("session_id"),
                    user_id=data.get("user_id"),
                    start_time=data.get("start_time", ""),
                    status=data.get("status", "active"),
                    end_time=data.get("end_time"),
                    metadata=data.get("metadata"),
                )
                sessions.append(session)

            return sessions
        except Exception as e:
            self.log_error(f"Error getting interview sessions for candidate {user_id}: {e}")
            return []

    async def get_company_dashboard_data(self, company_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a company"""
        try:
            return self._firebase_db.get_company_dashboard_data(company_id)
        except Exception as e:
            self.log_error(f"Error getting dashboard data for company {company_id}: {e}")
            return {}

    async def get_candidates_with_evaluations(self, company_id: str) -> List[Dict[str, Any]]:
        """Get candidates with their evaluation data for a company"""
        try:
            return self._firebase_db.get_candidates_with_evaluations(company_id)
        except Exception as e:
            self.log_error(
                f"Error getting candidates with evaluations for company {company_id}: {e}"
            )
            return []

    async def get_company_interviews(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all interviews/job postings for a company"""
        try:
            return await asyncio.to_thread(self._firebase_db.get_company_interviews, company_id)
        except Exception as e:
            self.log_error(f"Error getting interviews for company {company_id}: {e}")
            return []

    async def get_interview_candidates(
        self, company_id: str, interview_id: str
    ) -> List[Dict[str, Any]]:
        """Get candidates for a specific interview/job posting"""
        try:
            return await asyncio.to_thread(
                self._firebase_db.get_interview_candidates, company_id, interview_id
            )
        except Exception as e:
            self.log_error(f"Error getting candidates for interview {interview_id}: {e}")
            return []

    # Additional Firebase-specific methods (kept for backward compatibility)
    def get_all_video_urls(self, user_id: str, session_id: str) -> List[str]:
        """Get all video URLs (Firebase-specific)"""
        return self._firebase_db.get_all_video_urls(user_id, session_id)
