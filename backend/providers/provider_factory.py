from globals import config

from core.resource.model_providers.deepseek import DeepSeekCredentials, DeepSeekProvider
from core.resource.model_providers.gemini import GeminiCredentials, GeminiProvider
from core.resource.model_providers.grok import GrokCredentials, GrokProvider
from core.resource.model_providers.groq import GroqCredentials, GroqProvider
from core.resource.model_providers.openai import OpenAICredentials, OpenAIProvider
from core.resource.model_providers.perplexity import PerplexityCredentials, PerplexityProvider


class ProviderFactory:
    """Factory class for creating and managing LLM providers"""

    def __init__(self):
        self._providers = {}
        self._provider_mapping = {
            "openai": (OpenAIProvider, OpenAICredentials),
            "gemini": (GeminiProvider, GeminiCredentials),
            "groq": (GroqProvider, GroqCredentials),
            "grok": (GrokProvider, GrokCredentials),
            "deepseek": (DeepSeekProvider, DeepSeekCredentials),
            "perplexity": (PerplexityProvider, PerplexityCredentials),
        }

    def create_provider_from_config(self, provider_config):
        """Create a provider from configuration"""
        provider_name = provider_config.name.lower()

        if provider_name not in self._provider_mapping:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider_class, credentials_class = self._provider_mapping[provider_name]
        settings = provider_class.default_settings

        # Create credentials based on provider type
        if provider_name in ["openai", "deepseek"]:
            credentials = credentials_class(
                api_key=provider_config.api_key, api_type="chat", organization="hopeloom"
            )
        else:
            credentials = credentials_class(api_key=provider_config.api_key)

        settings.credentials = credentials
        return provider_class(settings)

    def create_openai_provider(self):
        """Create and configure OpenAI provider"""
        provider_config = next(
            (p for p in config.llm_providers if p.name.lower() == "openai"), None
        )
        if not provider_config or not provider_config.enabled:
            raise ValueError("OpenAI provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_gemini_provider(self):
        """Create and configure Gemini provider"""
        provider_config = next(
            (p for p in config.llm_providers if p.name.lower() == "gemini"), None
        )
        if not provider_config or not provider_config.enabled:
            raise ValueError("Gemini provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_groq_provider(self):
        """Create and configure GROQ provider"""
        provider_config = next((p for p in config.llm_providers if p.name.lower() == "groq"), None)
        if not provider_config or not provider_config.enabled:
            raise ValueError("Groq provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_grok_provider(self):
        """Create and configure GROK provider"""
        provider_config = next((p for p in config.llm_providers if p.name.lower() == "grok"), None)
        if not provider_config or not provider_config.enabled:
            raise ValueError("Grok provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_deepseek_provider(self):
        """Create and configure DeepSeek provider"""
        provider_config = next(
            (p for p in config.llm_providers if p.name.lower() == "deepseek"), None
        )
        if not provider_config or not provider_config.enabled:
            raise ValueError("DeepSeek provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_perplexity_provider(self):
        """Create and configure Perplexity provider"""
        provider_config = next(
            (p for p in config.llm_providers if p.name.lower() == "perplexity"), None
        )
        if not provider_config or not provider_config.enabled:
            raise ValueError("Perplexity provider not configured or disabled")
        return self.create_provider_from_config(provider_config)

    def create_all_providers(self):
        """Create all enabled providers and return them as a dictionary"""
        providers = {}

        for provider_config in config.llm_providers:
            if provider_config.enabled:
                try:
                    provider = self.create_provider_from_config(provider_config)
                    providers[provider_config.name.lower()] = provider
                except Exception as e:
                    print(f"Failed to create provider {provider_config.name}: {e}")
                    # Continue with other providers
                    continue

        return providers
