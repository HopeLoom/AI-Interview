"""
Configuration management system for the interview simulation platform.
Replaces environment variable-based configuration with structured config files.
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator


class Environment(str, Enum):
    """Supported environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    """Database configuration"""

    type: str = Field(..., description="Database type: firebase, postgresql, sqlite")
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None

    # Firebase specific
    firebase_credentials_path: Optional[str] = None
    firebase_storage_bucket: Optional[str] = None

    # SQLite specific
    sqlite_path: Optional[str] = None

    # Connection pool settings
    max_connections: int = 10
    min_connections: int = 1
    connection_timeout: int = 30


class StorageConfig(BaseModel):
    """Storage configuration"""

    type: str = Field(..., description="Storage type: firebase, local, aws_s3")

    # Local storage
    local_path: Optional[str] = None

    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    s3_bucket: Optional[str] = None

    # Firebase storage
    firebase_storage_bucket: Optional[str] = None


class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""

    name: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    enabled: bool = True


class EmailConfig(BaseModel):
    """Email configuration"""

    provider: str = "sendgrid"  # sendgrid, smtp
    api_key: Optional[str] = None
    from_email: str
    recipients: List[str] = []

    # SMTP specific
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True


class SpeechConfig(BaseModel):
    """Speech service configuration"""

    tts_provider: str = "openai"  # openai, elevenlabs, google
    stt_provider: str = "openai"  # openai, google, groq

    # Provider-specific settings
    elevenlabs_api_key: Optional[str] = None
    google_credentials_path: Optional[str] = None
    tts_url: Optional[str] = None


class SecurityConfig(BaseModel):
    """Security configuration"""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    cors_origins: List[str] = []
    rate_limit_per_minute: int = 60
    max_file_size_mb: int = 50


class ApplicationConfig(BaseModel):
    """Main application configuration"""

    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Core configurations
    database: DatabaseConfig
    storage: StorageConfig
    security: SecurityConfig
    email: EmailConfig
    speech: SpeechConfig

    # LLM providers
    llm_providers: List[LLMProviderConfig] = []

    # Feature flags
    features: Dict[str, bool] = {
        "enable_practice_mode": True,
        "enable_company_mode": True,
        "enable_video_recording": True,
        "enable_real_time_evaluation": True,
        "enable_batch_operations": True,
    }

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @validator("llm_providers")
    def validate_llm_providers(cls, v):
        """Ensure at least one LLM provider is configured"""
        if not v:
            raise ValueError("At least one LLM provider must be configured")
        return v


class ConfigManager:
    """Configuration manager for loading and managing application settings"""

    def __init__(
        self, config_path: Optional[Union[str, Path]] = None, environment: Optional[str] = None
    ):
        self.config_path = str(config_path) if config_path else self._get_default_config_path()
        # Check both ENVIRONMENT and STAGE variables, prioritize explicit parameter
        self.environment = environment or os.getenv("ENVIRONMENT") or os.getenv("STAGE", "staging")
        self._config: Optional[ApplicationConfig] = None
        self._config_cache: Dict[str, Any] = {}

        # Load environment-specific .env file
        self._load_env_file()

    def _load_env_file(self):
        """Load environment-specific .env file"""
        if self.environment in ["staging", "production"]:
            env_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", f".env.{self.environment}"
            )

            if os.path.exists(env_file_path):
                # Load .env file manually since we're not using python-dotenv
                with open(env_file_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            # Remove quotes if present
                            value = value.strip('"').strip("'")
                            os.environ[key] = value
                print(f"Loaded environment variables from: {env_file_path}")
            else:
                print(f"Environment file not found: {env_file_path}")

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path"""
        # Look for config in multiple locations
        possible_paths = [
            os.getenv("CONFIG_PATH"),
            "./config/config.yaml",
            "./config/config.yml",
            "./config/config.json",
            "./config.yaml",
            "./config.yml",
            "./config.json",
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        # Default to config.yaml in the backend directory
        root_path = Path(__file__).parent.parent.parent.parent / "backend"
        return str(root_path / "config.yaml")

    def load_config(self) -> ApplicationConfig:
        """Load configuration from file"""
        if self._config is not None:
            return self._config

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path) as f:
                if self.config_path.endswith(".json"):
                    raw_config = json.load(f)
                else:
                    raw_config = yaml.safe_load(f)

            # Handle environment-specific overrides
            if isinstance(raw_config, dict) and "environments" in raw_config:
                base_config = raw_config.get("default", {})
                env_config = raw_config.get("environments", {}).get(self.environment, {})

                # Merge environment-specific config with base config
                merged_config = self._deep_merge(base_config, env_config)
            else:
                merged_config = raw_config

            # Override with environment variables
            merged_config = self._apply_env_overrides(merged_config)

            self._config = ApplicationConfig(**merged_config)
            return self._config

        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Map of environment variables to config paths
        env_mappings = {
            "DATABASE_TYPE": ["database", "type"],
            "DATABASE_HOST": ["database", "host"],
            "DATABASE_PORT": ["database", "port"],
            "DATABASE_NAME": ["database", "name"],
            "DATABASE_USERNAME": ["database", "username"],
            "DATABASE_PASSWORD": ["database", "password"],
            "FIREBASE_CREDENTIALS_PATH": ["database", "firebase_credentials_path"],
            "FIREBASE_STORAGE_BUCKET": ["database", "firebase_storage_bucket"],
            "SQLITE_PATH": ["database", "sqlite_path"],
            "STORAGE_TYPE": ["storage", "type"],
            "LOCAL_STORAGE_PATH": ["storage", "local_path"],
            "AWS_ACCESS_KEY_ID": ["storage", "aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": ["storage", "aws_secret_access_key"],
            "AWS_REGION": ["storage", "aws_region"],
            "S3_BUCKET": ["storage", "s3_bucket"],
            "JWT_SECRET_KEY": ["security", "jwt_secret_key"],
            "CORS_ORIGINS": ["security", "cors_origins"],
            "FROM_EMAIL": ["email", "from_email"],
            "SENDGRID_API_KEY": ["email", "api_key"],
            "TTS_URL": ["speech", "tts_url"],
            "ELEVENLABS_API_KEY": ["speech", "elevenlabs_api_key"],
            "GOOGLE_CREDENTIALS_PATH": ["speech", "google_credentials_path"],
            "LOG_LEVEL": ["log_level"],
            "DEBUG": ["debug"],
            "HOST": ["host"],
            "PORT": ["port"],
        }

        result = config.copy()

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the nested config location
                current = result
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Convert value to appropriate type
                final_key = config_path[-1]
                if final_key in [
                    "port",
                    "max_connections",
                    "min_connections",
                    "connection_timeout",
                ]:
                    value = int(value)
                elif final_key in ["debug", "enabled", "smtp_use_tls"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                elif final_key == "cors_origins":
                    value = [origin.strip() for origin in value.split(",") if origin.strip()]

                current[final_key] = value

        # Handle LLM provider API keys
        llm_providers = result.get("llm_providers", [])
        for provider in llm_providers:
            if isinstance(provider, dict):
                provider_name = provider.get("name", "").upper()
                env_key = f"{provider_name}_API_KEY"
                if env_key in os.environ:
                    provider["api_key"] = os.environ[env_key]

        return result

    def get_config(self) -> ApplicationConfig:
        """Get the loaded configuration"""
        if self._config is None:
            self.load_config()
        return self._config

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.get_config().database

    def get_storage_config(self) -> StorageConfig:
        """Get storage configuration"""
        return self.get_config().storage

    def get_llm_provider_config(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Get LLM provider configuration by name"""
        config = self.get_config()
        for provider in config.llm_providers:
            if provider.name.lower() == provider_name.lower():
                return provider
        return None

    def get_enabled_llm_providers(self) -> List[LLMProviderConfig]:
        """Get all enabled LLM providers"""
        config = self.get_config()
        return [provider for provider in config.llm_providers if provider.enabled]

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        config = self.get_config()
        return config.features.get(feature_name, False)

    def reload_config(self):
        """Reload configuration from file"""
        self._config = None
        self._config_cache.clear()
        return self.load_config()


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> ApplicationConfig:
    """Get the global configuration"""
    return config_manager.get_config()


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return config_manager.get_database_config()


def get_storage_config() -> StorageConfig:
    """Get storage configuration"""
    return config_manager.get_storage_config()
