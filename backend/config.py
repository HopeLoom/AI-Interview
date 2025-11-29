"""
Legacy configuration support for backward compatibility.
This module provides the old get_settings() function while internally using the new configuration system.
"""

import os
from typing import Any

# Import the new configuration system
try:
    from core.config.config_manager import ApplicationConfig, get_config

    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False


def get_settings() -> dict[str, Any]:
    """
    Get application settings.
    Uses the new configuration system if available, falls back to environment variables.
    """
    if NEW_CONFIG_AVAILABLE:
        try:
            config = get_config()
            return _convert_new_config_to_legacy(config)
        except Exception:
            # Fall back to old environment-based config if new config fails
            pass

    # Legacy environment-based configuration
    stage = os.getenv("STAGE", "staging")
    raw_origins = os.getenv("API_ORIGINS", "")
    api_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    return {
        "stage": stage,
        "api_origins": api_origins,
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
        "ELEVEN_LABS_API_KEY": os.getenv("ELEVEN_LABS_API_KEY", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
        "GROK_API_KEY": os.getenv("GROK_API_KEY", ""),
        "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY", ""),
        "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", ""),
        "RECIPIENTS": [
            email.strip() for email in os.getenv("RECIPIENTS", "").split(",") if email.strip()
        ],
        "FROM_EMAIL": os.getenv("FROM_EMAIL", ""),
        "TTS_URL": os.getenv("TTS_URL", "https://api.openai.com/v1/audio/speech"),
        # Add any other variables you need
    }


def _convert_new_config_to_legacy(config: ApplicationConfig) -> dict[str, Any]:
    """Convert new configuration format to legacy format for backward compatibility"""
    # Build LLM provider API keys dictionary
    llm_api_keys = {}
    for provider in config.llm_providers:
        key_name = f"{provider.name.upper()}_API_KEY"
        llm_api_keys[key_name] = provider.api_key

    return {
        "stage": config.environment.value,
        "api_origins": config.security.cors_origins,
        "GOOGLE_APPLICATION_CREDENTIALS": config.database.firebase_credentials_path or "",
        "SENDGRID_API_KEY": config.email.api_key or "",
        "RECIPIENTS": config.email.recipients,
        "FROM_EMAIL": config.email.from_email,
        "TTS_URL": config.speech.tts_url or "https://api.openai.com/v1/audio/speech",
        "ELEVEN_LABS_API_KEY": config.speech.elevenlabs_api_key or "",
        **llm_api_keys,  # Add all LLM provider API keys
    }
