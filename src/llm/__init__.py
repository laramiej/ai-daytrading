"""
LLM Provider Factory and Exports
"""
from typing import Optional
from .base import BaseLLMProvider, LLMResponse
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .n8n_provider import N8nProvider

# Google provider is optional (requires Python 3.10+)
try:
    from .google_provider import GoogleProvider
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    GoogleProvider = None


class LLMFactory:
    """Factory for creating LLM provider instances"""

    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "n8n": N8nProvider,
    }

    # Add Google if available
    if GOOGLE_AVAILABLE:
        PROVIDERS["google"] = GoogleProvider

    @staticmethod
    def create_provider(
        provider_name: str,
        api_key: str,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance

        Args:
            provider_name: Name of the provider (anthropic, openai, google, n8n)
            api_key: API key for the provider (for n8n, this is the webhook URL)
            model: Optional specific model to use

        Returns:
            Instance of the requested provider

        Raises:
            ValueError: If provider_name is not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in LLMFactory.PROVIDERS:
            available = ", ".join(LLMFactory.PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )

        provider_class = LLMFactory.PROVIDERS[provider_name]

        # Special handling for n8n - api_key is actually the webhook URL
        if provider_name == "n8n":
            return provider_class(webhook_url=api_key, model=model)

        return provider_class(api_key=api_key, model=model)

    @staticmethod
    def list_providers() -> list[str]:
        """Return list of available provider names"""
        return list(LLMFactory.PROVIDERS.keys())


__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "AnthropicProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "N8nProvider",
    "LLMFactory",
]
