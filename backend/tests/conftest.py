"""
pytest configuration and shared fixtures for the interview simulation backend tests.
"""

import asyncio
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

from core.config.config_manager import ApplicationConfig, ConfigManager, DatabaseConfig
from core.database.base import SessionData, UserProfile
from core.database.database_factory import DatabaseFactory


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config_data() -> dict:
    """Test configuration data."""
    return {
        "environment": "development",
        "debug": True,
        "host": "localhost",
        "port": 8000,
        "database": {
            "type": "sqlite",
            "sqlite_path": ":memory:",  # In-memory SQLite for testing
            "max_connections": 5,
            "min_connections": 1,
            "connection_timeout": 10,
        },
        "storage": {"type": "local", "local_path": "/tmp/test_storage"},
        "security": {
            "jwt_secret_key": "test-secret-key",
            "jwt_algorithm": "HS256",
            "jwt_expiration_hours": 24,
            "cors_origins": ["http://localhost:3000"],
            "rate_limit_per_minute": 100,
            "max_file_size_mb": 10,
        },
        "email": {
            "provider": "sendgrid",
            "from_email": "test@example.com",
            "api_key": "test-api-key",
            "recipients": ["admin@example.com"],
        },
        "speech": {
            "tts_provider": "openai",
            "stt_provider": "openai",
            "tts_url": "https://api.openai.com/v1/audio/speech",
        },
        "llm_providers": [
            {"name": "openai", "api_key": "test-openai-key", "model": "gpt-4", "enabled": True},
            {"name": "deepseek", "api_key": "test-deepseek-key", "enabled": True},
        ],
        "features": {
            "enable_practice_mode": True,
            "enable_company_mode": True,
            "enable_video_recording": False,  # Disabled for testing
            "enable_real_time_evaluation": True,
            "enable_batch_operations": True,
        },
        "log_level": "DEBUG",
    }


@pytest.fixture
def test_config_file(temp_dir: Path, test_config_data: dict) -> Path:
    """Create a test configuration file."""
    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(test_config_data, f)
    return config_file


@pytest.fixture
def test_config_manager(test_config_file: Path) -> ConfigManager:
    """Create a ConfigManager instance with test configuration."""
    return ConfigManager(str(test_config_file), "development")


@pytest.fixture
def test_app_config(test_config_manager: ConfigManager) -> ApplicationConfig:
    """Load test application configuration."""
    return test_config_manager.load_config()


@pytest.fixture
def sqlite_config() -> DatabaseConfig:
    """SQLite database configuration for testing."""
    return DatabaseConfig(
        type="sqlite",
        sqlite_path=":memory:",  # In-memory database for testing
        max_connections=5,
        min_connections=1,
        connection_timeout=10,
    )


@pytest.fixture
def postgresql_config() -> DatabaseConfig:
    """PostgreSQL database configuration for testing (requires running PostgreSQL)."""
    return DatabaseConfig(
        type="postgresql",
        host=os.getenv("TEST_POSTGRES_HOST", "localhost"),
        port=int(os.getenv("TEST_POSTGRES_PORT", "5432")),
        name=os.getenv("TEST_POSTGRES_DB", "interview_sim_test"),
        username=os.getenv("TEST_POSTGRES_USER", "test_user"),
        password=os.getenv("TEST_POSTGRES_PASSWORD", "test_password"),
        max_connections=5,
        min_connections=1,
        connection_timeout=10,
    )


@pytest.fixture
async def sqlite_db(sqlite_config: DatabaseConfig):
    """Create and initialize an SQLite database for testing."""
    db = DatabaseFactory.create_database(sqlite_config)
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
async def postgresql_db(postgresql_config: DatabaseConfig):
    """Create and initialize a PostgreSQL database for testing."""
    # Skip if PostgreSQL is not available
    pytest.importorskip("asyncpg")

    db = DatabaseFactory.create_database(postgresql_config)
    try:
        await db.initialize()
        yield db
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    finally:
        await db.close()


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """Sample user profile for testing."""
    return UserProfile(
        user_id="test_user_123",
        name="Test User",
        email="testuser@example.com",
        company_name="Test Company",
        location="Test City",
        resume_url="https://example.com/resume.pdf",
        starter_code_url="https://example.com/starter.py",
        profile_json_url="https://example.com/profile.json",
        simulation_config_json_url="https://example.com/config.json",
        panelist_profiles=["profile1.json", "profile2.json"],
        panelist_images=["image1.png", "image2.png"],
        role="candidate",
        organization_id="org_123",
        created_at="2024-01-01T00:00:00Z",
    )


@pytest.fixture
def sample_session_data() -> SessionData:
    """Sample session data for testing."""
    return SessionData(
        session_id="20240101-120000",
        user_id="test_user_123",
        start_time="2024-01-01T12:00:00Z",
        status="active",
        end_time=None,
        metadata={"test_key": "test_value"},
    )


@pytest.fixture
def sample_simulation_config() -> dict:
    """Sample simulation configuration for testing."""
    return {
        "job_details": {
            "job_title": "Software Engineer",
            "company_name": "Test Company",
            "job_description": "Test job description",
            "required_skills": ["Python", "JavaScript", "SQL"],
        },
        "interview_rounds": [
            {
                "round_name": "Technical Round",
                "duration_minutes": 45,
                "topics": [
                    {
                        "topic_name": "Algorithms",
                        "subtopics": ["Sorting", "Searching", "Graph Algorithms"],
                        "time_allocation_minutes": 20,
                    },
                    {
                        "topic_name": "System Design",
                        "subtopics": ["Scalability", "Database Design"],
                        "time_allocation_minutes": 25,
                    },
                ],
            }
        ],
        "panelists": [
            {
                "name": "John Doe",
                "role": "Senior Engineer",
                "expertise": ["Algorithms", "System Design"],
            }
        ],
        "evaluation_criteria": [
            {"criterion": "Technical Knowledge", "weight": 0.4},
            {"criterion": "Problem Solving", "weight": 0.3},
            {"criterion": "Communication", "weight": 0.3},
        ],
    }


@pytest.fixture
def mock_dialog_message():
    """Mock dialog message for testing."""

    class MockMessage:
        def __init__(self, speaker="Test Speaker", content="Test message content"):
            self.speaker = speaker
            self.content = content

    return MockMessage()


@pytest.fixture
def mock_evaluation_output():
    """Mock evaluation output for testing."""

    class MockEvaluationOutput:
        def __init__(self):
            self.question_criteria_specific_scoring = []

        def model_dump(self):
            return {
                "question_criteria_specific_scoring": self.question_criteria_specific_scoring,
                "overall_score": 85.5,
                "feedback": "Good performance overall",
            }

    return MockEvaluationOutput()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "postgresql: mark test as requiring PostgreSQL")
    config.addinivalue_line("markers", "firebase: mark test as requiring Firebase")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location and dependencies."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark PostgreSQL tests
        if "postgresql" in str(item.fspath) or "postgresql" in item.name:
            item.add_marker(pytest.mark.postgresql)

        # Mark Firebase tests
        if "firebase" in str(item.fspath) or "firebase" in item.name:
            item.add_marker(pytest.mark.firebase)


# Skip markers for CI/CD
def pytest_runtest_setup(item):
    """Skip tests based on environment and available services."""
    # Skip PostgreSQL tests if not available
    if item.get_closest_marker("postgresql"):
        if os.getenv("TEST_POSTGRES_AVAILABLE", "").lower() != "true":
            pytest.skip("PostgreSQL not available for testing")

    # Skip Firebase tests if not available
    if item.get_closest_marker("firebase"):
        if not os.path.exists("interview-simulation-firebase.json"):
            pytest.skip("Firebase credentials not available for testing")
