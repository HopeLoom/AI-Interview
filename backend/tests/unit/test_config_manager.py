"""
Unit tests for the configuration manager.
"""

import os
from unittest.mock import patch

import pytest
import yaml

from core.config.config_manager import (
    ApplicationConfig,
    ConfigManager,
    DatabaseConfig,
    EmailConfig,
    Environment,
    LLMProviderConfig,
    SecurityConfig,
    SpeechConfig,
    StorageConfig,
)


class TestDatabaseConfig:
    """Test DatabaseConfig model"""

    def test_firebase_config(self):
        """Test Firebase database configuration"""
        config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="firebase.json",
            firebase_storage_bucket="bucket-name",
        )

        assert config.type == "firebase"
        assert config.firebase_credentials_path == "firebase.json"
        assert config.firebase_storage_bucket == "bucket-name"
        assert config.max_connections == 10  # Default value

    def test_postgresql_config(self):
        """Test PostgreSQL database configuration"""
        config = DatabaseConfig(
            type="postgresql",
            host="localhost",
            port=5432,
            name="testdb",
            username="testuser",
            password="testpass",
        )

        assert config.type == "postgresql"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "testdb"
        assert config.username == "testuser"
        assert config.password == "testpass"

    def test_sqlite_config(self):
        """Test SQLite database configuration"""
        config = DatabaseConfig(type="sqlite", sqlite_path="./test.db")

        assert config.type == "sqlite"
        assert config.sqlite_path == "./test.db"

    def test_connection_pool_settings(self):
        """Test connection pool settings"""
        config = DatabaseConfig(
            type="postgresql",
            host="localhost",
            max_connections=20,
            min_connections=5,
            connection_timeout=60,
        )

        assert config.max_connections == 20
        assert config.min_connections == 5
        assert config.connection_timeout == 60


class TestStorageConfig:
    """Test StorageConfig model"""

    def test_local_storage_config(self):
        """Test local storage configuration"""
        config = StorageConfig(type="local", local_path="./storage")

        assert config.type == "local"
        assert config.local_path == "./storage"

    def test_aws_s3_config(self):
        """Test AWS S3 storage configuration"""
        config = StorageConfig(
            type="aws_s3",
            aws_access_key_id="access_key",
            aws_secret_access_key="secret_key",
            aws_region="us-east-1",
            s3_bucket="test-bucket",
        )

        assert config.type == "aws_s3"
        assert config.aws_access_key_id == "access_key"
        assert config.aws_secret_access_key == "secret_key"
        assert config.aws_region == "us-east-1"
        assert config.s3_bucket == "test-bucket"

    def test_firebase_storage_config(self):
        """Test Firebase storage configuration"""
        config = StorageConfig(type="firebase", firebase_storage_bucket="firebase-bucket")

        assert config.type == "firebase"
        assert config.firebase_storage_bucket == "firebase-bucket"


class TestLLMProviderConfig:
    """Test LLMProviderConfig model"""

    def test_basic_provider_config(self):
        """Test basic LLM provider configuration"""
        config = LLMProviderConfig(name="openai", api_key="test-key")

        assert config.name == "openai"
        assert config.api_key == "test-key"
        assert config.enabled is True  # Default value

    def test_full_provider_config(self):
        """Test full LLM provider configuration"""
        config = LLMProviderConfig(
            name="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            max_tokens=4000,
            temperature=0.7,
            enabled=False,
        )

        assert config.name == "openai"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.enabled is False


class TestEmailConfig:
    """Test EmailConfig model"""

    def test_sendgrid_config(self):
        """Test SendGrid email configuration"""
        config = EmailConfig(
            provider="sendgrid",
            api_key="sendgrid-key",
            from_email="test@example.com",
            recipients=["admin@example.com"],
        )

        assert config.provider == "sendgrid"
        assert config.api_key == "sendgrid-key"
        assert config.from_email == "test@example.com"
        assert config.recipients == ["admin@example.com"]

    def test_smtp_config(self):
        """Test SMTP email configuration"""
        config = EmailConfig(
            provider="smtp",
            from_email="test@example.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="user@gmail.com",
            smtp_password="password",
            smtp_use_tls=True,
        )

        assert config.provider == "smtp"
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.smtp_username == "user@gmail.com"
        assert config.smtp_password == "password"
        assert config.smtp_use_tls is True


class TestSpeechConfig:
    """Test SpeechConfig model"""

    def test_default_speech_config(self):
        """Test default speech configuration"""
        config = SpeechConfig()

        assert config.tts_provider == "openai"
        assert config.stt_provider == "openai"

    def test_full_speech_config(self):
        """Test full speech configuration"""
        config = SpeechConfig(
            tts_provider="elevenlabs",
            stt_provider="google",
            elevenlabs_api_key="elevenlabs-key",
            google_credentials_path="google-creds.json",
            tts_url="https://api.elevenlabs.io/v1/text-to-speech",
        )

        assert config.tts_provider == "elevenlabs"
        assert config.stt_provider == "google"
        assert config.elevenlabs_api_key == "elevenlabs-key"
        assert config.google_credentials_path == "google-creds.json"
        assert config.tts_url == "https://api.elevenlabs.io/v1/text-to-speech"


class TestSecurityConfig:
    """Test SecurityConfig model"""

    def test_security_config(self):
        """Test security configuration"""
        config = SecurityConfig(jwt_secret_key="secret-key", cors_origins=["http://localhost:3000"])

        assert config.jwt_secret_key == "secret-key"
        assert config.jwt_algorithm == "HS256"  # Default
        assert config.jwt_expiration_hours == 24  # Default
        assert config.cors_origins == ["http://localhost:3000"]
        assert config.rate_limit_per_minute == 60  # Default
        assert config.max_file_size_mb == 50  # Default


class TestApplicationConfig:
    """Test ApplicationConfig model"""

    def test_minimal_application_config(self, test_config_data):
        """Test minimal application configuration"""
        config = ApplicationConfig(**test_config_data)

        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is True
        assert config.host == "localhost"
        assert config.port == 8000
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.email, EmailConfig)
        assert isinstance(config.speech, SpeechConfig)
        assert len(config.llm_providers) == 2
        assert all(isinstance(provider, LLMProviderConfig) for provider in config.llm_providers)

    def test_llm_providers_validation(self):
        """Test LLM providers validation"""
        # Should raise error if no providers
        with pytest.raises(ValueError, match="At least one LLM provider must be configured"):
            ApplicationConfig(
                database=DatabaseConfig(type="sqlite"),
                storage=StorageConfig(type="local"),
                security=SecurityConfig(jwt_secret_key="test"),
                email=EmailConfig(from_email="test@example.com"),
                speech=SpeechConfig(),
                llm_providers=[],  # Empty list should raise error
            )


class TestConfigManager:
    """Test ConfigManager class"""

    @pytest.fixture
    def config_manager(self, test_config_file):
        """Create a ConfigManager instance"""
        return ConfigManager(str(test_config_file), "development")

    def test_config_manager_initialization(self, test_config_file):
        """Test ConfigManager initialization"""
        manager = ConfigManager(str(test_config_file), "development")
        assert manager.config_path == str(test_config_file)
        assert manager.environment == "development"
        assert manager._config is None

    def test_default_config_path_discovery(self):
        """Test default configuration path discovery"""
        manager = ConfigManager()
        # Should not raise an error and should have a default path
        assert manager.config_path is not None

    def test_load_config(self, config_manager):
        """Test loading configuration from file"""
        config = config_manager.load_config()

        assert isinstance(config, ApplicationConfig)
        assert config.environment == Environment.DEVELOPMENT
        assert config.database.type == "sqlite"
        assert config.database.sqlite_path == ":memory:"

    def test_config_caching(self, config_manager):
        """Test configuration caching"""
        config1 = config_manager.load_config()
        config2 = config_manager.load_config()

        # Should return the same instance (cached)
        assert config1 is config2

    def test_get_config(self, config_manager):
        """Test get_config method"""
        config = config_manager.get_config()
        assert isinstance(config, ApplicationConfig)

    def test_get_database_config(self, config_manager):
        """Test get_database_config method"""
        db_config = config_manager.get_database_config()
        assert isinstance(db_config, DatabaseConfig)
        assert db_config.type == "sqlite"

    def test_get_storage_config(self, config_manager):
        """Test get_storage_config method"""
        storage_config = config_manager.get_storage_config()
        assert isinstance(storage_config, StorageConfig)
        assert storage_config.type == "local"

    def test_get_llm_provider_config(self, config_manager):
        """Test get_llm_provider_config method"""
        openai_config = config_manager.get_llm_provider_config("openai")
        assert openai_config is not None
        assert openai_config.name == "openai"

        nonexistent_config = config_manager.get_llm_provider_config("nonexistent")
        assert nonexistent_config is None

    def test_get_enabled_llm_providers(self, config_manager):
        """Test get_enabled_llm_providers method"""
        enabled_providers = config_manager.get_enabled_llm_providers()
        assert len(enabled_providers) == 2  # Both providers are enabled in test config
        assert all(provider.enabled for provider in enabled_providers)

    def test_is_feature_enabled(self, config_manager):
        """Test is_feature_enabled method"""
        assert config_manager.is_feature_enabled("enable_practice_mode") is True
        assert config_manager.is_feature_enabled("enable_video_recording") is False
        assert config_manager.is_feature_enabled("nonexistent_feature") is False

    def test_reload_config(self, config_manager):
        """Test reload_config method"""
        # Load initial config
        config1 = config_manager.load_config()

        # Reload config
        config2 = config_manager.reload_config()

        # Should be different instances after reload
        assert config1 is not config2
        assert isinstance(config2, ApplicationConfig)

    def test_environment_overrides(self, temp_dir):
        """Test environment variable overrides"""
        # Create config with environment overrides
        config_data = {
            "database": {"type": "sqlite", "sqlite_path": "./default.db"},
            "email": {"from_email": "default@example.com"},
            "llm_providers": [{"name": "openai", "api_key": "default-key", "enabled": True}],
        }

        config_file = temp_dir / "env_test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Set environment variables
        with patch.dict(
            os.environ,
            {
                "DATABASE_TYPE": "postgresql",
                "FROM_EMAIL": "override@example.com",
                "OPENAI_API_KEY": "override-key",
                "DEBUG": "true",
            },
        ):
            manager = ConfigManager(str(config_file))
            config = manager.load_config()

            # Check overrides were applied
            assert config.database.type == "postgresql"
            assert config.email.from_email == "override@example.com"
            assert config.debug is True

            # Find OpenAI provider and check API key override
            openai_provider = next(p for p in config.llm_providers if p.name == "openai")
            assert openai_provider.api_key == "override-key"

    def test_file_not_found_error(self):
        """Test FileNotFoundError when config file doesn't exist"""
        manager = ConfigManager("/nonexistent/config.yaml")

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_invalid_config_error(self, temp_dir):
        """Test ValueError when config is invalid"""
        # Create invalid config (missing required fields)
        invalid_config = {"invalid": "config"}

        config_file = temp_dir / "invalid_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        manager = ConfigManager(str(config_file))

        with pytest.raises(ValueError, match="Failed to load configuration"):
            manager.load_config()

    def test_json_config_support(self, temp_dir, test_config_data):
        """Test JSON configuration file support"""
        import json

        config_file = temp_dir / "test_config.json"
        with open(config_file, "w") as f:
            json.dump(test_config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load_config()

        assert isinstance(config, ApplicationConfig)
        assert config.environment == Environment.DEVELOPMENT

    def test_deep_merge(self, temp_dir):
        """Test deep merging of environment-specific configurations"""
        config_data = {
            "default": {
                "database": {"type": "sqlite", "sqlite_path": "./default.db", "max_connections": 5},
                "features": {"enable_practice_mode": True, "enable_company_mode": False},
            },
            "environments": {
                "development": {
                    "database": {"sqlite_path": "./dev.db", "max_connections": 10},
                    "features": {"enable_company_mode": True},
                }
            },
        }

        config_file = temp_dir / "merge_test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file), "development")

        # Need to add required fields for ApplicationConfig
        with patch.object(manager, "_apply_env_overrides") as mock_apply_env:
            mock_apply_env.return_value = {
                **config_data["default"],
                **config_data["environments"]["development"],
                "database": {
                    **config_data["default"]["database"],
                    **config_data["environments"]["development"]["database"],
                },
                "features": {
                    **config_data["default"]["features"],
                    **config_data["environments"]["development"]["features"],
                },
                # Add required fields
                "storage": {"type": "local"},
                "security": {"jwt_secret_key": "test"},
                "email": {"from_email": "test@example.com"},
                "speech": {},
                "llm_providers": [{"name": "openai", "api_key": "test", "enabled": True}],
            }

            config = manager.load_config()

            # Check that deep merge worked correctly
            assert config.database.sqlite_path == "./dev.db"  # Overridden
            assert config.database.max_connections == 10  # Overridden
            assert config.features["enable_practice_mode"] is True  # From default
            assert config.features["enable_company_mode"] is True  # Overridden


class TestGlobalFunctions:
    """Test global configuration functions"""

    def test_global_config_functions(self, test_config_file):
        """Test global configuration functions"""
        from core.config.config_manager import (
            config_manager,
            get_config,
            get_database_config,
            get_storage_config,
        )

        # Set the config path for the global manager
        config_manager.config_path = str(test_config_file)
        config_manager.environment = "development"
        config_manager._config = None  # Reset cache

        # Test global functions
        config = get_config()
        assert isinstance(config, ApplicationConfig)

        db_config = get_database_config()
        assert isinstance(db_config, DatabaseConfig)

        storage_config = get_storage_config()
        assert isinstance(storage_config, StorageConfig)
