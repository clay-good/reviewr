
from typing import Dict, Type
from .base import LLMProvider
from .claude import ClaudeProvider
from .openai import OpenAIProvider
from .gemini import GeminiProvider
from ..config.schema import ProviderConfig


class ProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers: Dict[str, Type[LLMProvider]] = {
        'claude': ClaudeProvider,
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: ProviderConfig) -> LLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of the provider (claude, openai, gemini)
            config: Provider configuration
            
        Returns:
            Initialized LLM provider
            
        Raises:
            ValueError: If provider name is unknown or API key is missing
        """
        if provider_name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider: {provider_name}. Available providers: {available}"
            )
        
        if not config.api_key:
            raise ValueError(
                f"API key not configured for provider: {provider_name}. "
                f"Set it via environment variable or configuration file."
            )
        
        provider_class = cls._providers[provider_name]
        return provider_class(
            api_key=config.api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
        )
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())

