"""
Unit tests for the database base classes and interfaces.
"""

from datetime import datetime
from typing import Optional

import pytest

from core.database.base import DatabaseInterface, DatabaseType, SessionData, UserProfile


class TestUserProfile:
    """Test UserProfile data class"""

    def test_user_profile_creation(self):
        """Test creating a UserProfile instance"""
        user = UserProfile(
            user_id="test_123",
            name="Test User",
            email="test@example.com",
            company_name="Test Company",
            location="Test City",
        )

        assert user.user_id == "test_123"
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.company_name == "Test Company"
        assert user.location == "Test City"
        assert user.role == "candidate"  # Default value
        assert user.organization_id is None  # Default value

    def test_user_profile_with_optional_fields(self):
        """Test UserProfile with all optional fields"""
        user = UserProfile(
            user_id="test_456",
            name="Admin User",
            email="admin@example.com",
            company_name="Admin Company",
            location="Admin City",
            resume_url="https://example.com/resume.pdf",
            starter_code_url="https://example.com/code.py",
            profile_json_url="https://example.com/profile.json",
            simulation_config_json_url="https://example.com/config.json",
            panelist_profiles=["profile1.json", "profile2.json"],
            panelist_images=["image1.png", "image2.png"],
            role="company_admin",
            organization_id="org_123",
            created_at="2024-01-01T00:00:00Z",
        )

        assert user.role == "company_admin"
        assert user.organization_id == "org_123"
        assert user.resume_url == "https://example.com/resume.pdf"
        assert len(user.panelist_profiles) == 2
        assert len(user.panelist_images) == 2


class TestSessionData:
    """Test SessionData data class"""

    def test_session_data_creation(self):
        """Test creating a SessionData instance"""
        session = SessionData(
            session_id="20240101-120000", user_id="user_123", start_time="2024-01-01T12:00:00Z"
        )

        assert session.session_id == "20240101-120000"
        assert session.user_id == "user_123"
        assert session.start_time == "2024-01-01T12:00:00Z"
        assert session.status == "active"  # Default value
        assert session.end_time is None
        assert session.metadata is None

    def test_session_data_with_optional_fields(self):
        """Test SessionData with optional fields"""
        metadata = {"test_key": "test_value"}
        session = SessionData(
            session_id="20240101-130000",
            user_id="user_456",
            start_time="2024-01-01T13:00:00Z",
            status="completed",
            end_time="2024-01-01T14:00:00Z",
            metadata=metadata,
        )

        assert session.status == "completed"
        assert session.end_time == "2024-01-01T14:00:00Z"
        assert session.metadata == metadata


class TestDatabaseType:
    """Test DatabaseType enum"""

    def test_database_types(self):
        """Test all database types are defined"""
        assert DatabaseType.FIREBASE.value == "firebase"
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.SQLITE.value == "sqlite"

    def test_database_type_values(self):
        """Test database type values"""
        types = [db_type.value for db_type in DatabaseType]
        assert "firebase" in types
        assert "postgresql" in types
        assert "sqlite" in types
        assert len(types) == 3


class MockDatabaseInterface(DatabaseInterface):
    """Mock implementation of DatabaseInterface for testing"""

    def __init__(self, logger=None):
        super().__init__(logger)
        self._initialized = False
        self._closed = False
        self._users = {}
        self._sessions = {}
        self._configs = {}

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def close(self):
        self._closed = True

    async def get_user_id_by_email(self, email: str):
        for user_id, user in self._users.items():
            if user.email == email:
                return user_id
        return None

    async def load_user_data(self, user_id: str) -> bool:
        if user_id in self._users:
            self.user_data = self._users[user_id]
            return True
        return False

    async def create_user(self, user_profile: UserProfile) -> bool:
        self._users[user_profile.user_id] = user_profile
        return True

    async def update_user(self, user_id: str, updates: dict) -> bool:
        if user_id in self._users:
            # Simple update simulation
            for key, value in updates.items():
                setattr(self._users[user_id], key, value)
            return True
        return False

    async def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    async def get_all_users_data(self):
        return list(self._users.values())

    async def create_new_session(self, user_id: str) -> str:
        session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._sessions[session_id] = SessionData(
            session_id=session_id, user_id=user_id, start_time=datetime.now().isoformat()
        )
        self.session_id = session_id
        return session_id

    async def get_session_data(self, user_id: str, session_id: str):
        return self._sessions.get(session_id)

    async def update_session(self, user_id: str, session_id: str, updates: dict) -> bool:
        if session_id in self._sessions:
            for key, value in updates.items():
                setattr(self._sessions[session_id], key, value)
            return True
        return False

    async def get_most_recent_session_id_by_user_id(self, user_id: str):
        # Simple implementation - return the first session for the user
        for session in self._sessions.values():
            if session.user_id == user_id:
                return session.session_id
        return None

    async def get_all_session_data(self, user_id: str, session_id: Optional[str] = None):
        return {}

    async def add_dialog_to_database(self, user_id: str, session_id: str, message):
        pass

    async def add_evaluation_output_to_database(self, user_id: str, session_id: str, output):
        pass

    async def add_final_evaluation_output_to_database(self, user_id: str, session_id: str, output):
        pass

    async def get_final_evaluation_output_from_database(self, user_id: str, session_id: str):
        return None

    async def store_simulation_config(
        self, config_id: str, config_data: dict, user_id: Optional[str] = None
    ) -> bool:
        self._configs[config_id] = config_data
        return True

    async def get_simulation_config(self, config_id: str):
        return self._configs.get(config_id)

    async def list_simulation_configs(self, user_id: Optional[str] = None):
        return [
            {"config_id": k, "config_name": v.get("job_details", {}).get("job_title", "Untitled")}
            for k, v in self._configs.items()
        ]

    async def delete_simulation_config(self, config_id: str) -> bool:
        if config_id in self._configs:
            del self._configs[config_id]
            return True
        return False

    async def add_to_batch(
        self, user_id: str, session_id: str, operation_type: str, data, collection_path: str
    ):
        pass

    async def commit_batch(self) -> bool:
        return True

    async def add_json_data_output_to_database(
        self, user_id: str, session_id: str, name: str, json_data: dict
    ):
        pass

    async def get_json_data_output_from_database(self, name: str, user_id: str, session_id: str):
        return None


class TestDatabaseInterface:
    """Test DatabaseInterface abstract class and helper methods"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database instance"""
        return MockDatabaseInterface()

    @pytest.mark.asyncio
    async def test_database_initialization(self, mock_db):
        """Test database initialization"""
        assert not mock_db._initialized

        success = await mock_db.initialize()
        assert success
        assert mock_db._initialized

    @pytest.mark.asyncio
    async def test_database_close(self, mock_db):
        """Test database close"""
        assert not mock_db._closed

        await mock_db.close()
        assert mock_db._closed

    @pytest.mark.asyncio
    async def test_user_operations(self, mock_db, sample_user_profile):
        """Test user CRUD operations"""
        await mock_db.initialize()

        # Test create user
        success = await mock_db.create_user(sample_user_profile)
        assert success

        # Test get user by email
        user_id = await mock_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id

        # Test load user data
        success = await mock_db.load_user_data(sample_user_profile.user_id)
        assert success
        assert mock_db.user_data.email == sample_user_profile.email

        # Test update user
        updates = {"name": "Updated Name"}
        success = await mock_db.update_user(sample_user_profile.user_id, updates)
        assert success

        # Verify update
        await mock_db.load_user_data(sample_user_profile.user_id)
        assert mock_db.user_data.name == "Updated Name"

        # Test get all users
        users = await mock_db.get_all_users_data()
        assert len(users) == 1
        assert users[0].user_id == sample_user_profile.user_id

        # Test delete user
        success = await mock_db.delete_user(sample_user_profile.user_id)
        assert success

        # Verify deletion
        users = await mock_db.get_all_users_data()
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_session_operations(self, mock_db, sample_user_profile):
        """Test session operations"""
        await mock_db.initialize()
        await mock_db.create_user(sample_user_profile)

        # Test create session
        session_id = await mock_db.create_new_session(sample_user_profile.user_id)
        assert session_id is not None
        assert mock_db.session_id == session_id

        # Test get session data
        session_data = await mock_db.get_session_data(sample_user_profile.user_id, session_id)
        assert session_data is not None
        assert session_data.user_id == sample_user_profile.user_id
        assert session_data.session_id == session_id

        # Test update session
        updates = {"status": "completed"}
        success = await mock_db.update_session(sample_user_profile.user_id, session_id, updates)
        assert success

        # Verify update
        session_data = await mock_db.get_session_data(sample_user_profile.user_id, session_id)
        assert session_data.status == "completed"

        # Test get most recent session
        recent_session_id = await mock_db.get_most_recent_session_id_by_user_id(
            sample_user_profile.user_id
        )
        assert recent_session_id == session_id

    @pytest.mark.asyncio
    async def test_simulation_config_operations(self, mock_db, sample_simulation_config):
        """Test simulation configuration operations"""
        await mock_db.initialize()

        config_id = "test_config_123"

        # Test store config
        success = await mock_db.store_simulation_config(config_id, sample_simulation_config)
        assert success

        # Test get config
        retrieved_config = await mock_db.get_simulation_config(config_id)
        assert retrieved_config is not None
        assert (
            retrieved_config["job_details"]["job_title"]
            == sample_simulation_config["job_details"]["job_title"]
        )

        # Test list configs
        configs = await mock_db.list_simulation_configs()
        assert len(configs) == 1
        assert configs[0]["config_id"] == config_id

        # Test delete config
        success = await mock_db.delete_simulation_config(config_id)
        assert success

        # Verify deletion
        configs = await mock_db.list_simulation_configs()
        assert len(configs) == 0

    def test_helper_methods(self, mock_db):
        """Test helper methods"""
        # Test logger setting
        mock_logger = object()  # Mock logger
        mock_db.set_logger(mock_logger)
        assert mock_db.logger == mock_logger

        # Test logging methods (should not raise exceptions)
        mock_db.log_info("Test info message")
        mock_db.log_error("Test error message")
        mock_db.log_warning("Test warning message")

    def test_batch_operations(self, mock_db):
        """Test batch operation attributes"""
        assert mock_db.pending_batch_operations == []
        assert mock_db.batch_size_limit == 5

        # Test batch size limit modification
        mock_db.batch_size_limit = 10
        assert mock_db.batch_size_limit == 10
