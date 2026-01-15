"""
LLM Provider Factory and Exports
"""
from typing import Optional
from .base import BaseLLMProvider, LLMResponse
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider

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
            provider_name: Name of the provider (anthropic, openai, google)
            api_key: API key for the provider
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
    "LLMFactory",
]
