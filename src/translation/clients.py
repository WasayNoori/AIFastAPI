"""
LLM Client Factory

This module provides a factory function to create LLM provider instances
based on the configuration settings. This allows easy switching between
different LLM providers (OpenAI, Gemini) without modifying service code.
"""
from .config import SETTINGS
from .llm_provider import LLMProvider, OpenAIProvider, GeminiProvider
from src.services.azure_config import AzureKeyVaultConfig


def create_llm_provider(azure_config: AzureKeyVaultConfig) -> LLMProvider:
    """
    Factory function to create an LLM provider based on configuration.

    The provider type is determined by SETTINGS.llm_provider, which can be set via:
    1. Environment variable: TRANSLATION_LLM_PROVIDER=gemini
    2. Default value in config.py (currently "gemini")

    Args:
        azure_config: Azure Key Vault configuration for retrieving API keys

    Returns:
        An LLMProvider instance (OpenAI or Gemini)

    Example:
        # Use Gemini (default)
        provider = create_llm_provider(azure_config)

        # Switch to OpenAI by setting env var:
        # export TRANSLATION_LLM_PROVIDER=openai
        provider = create_llm_provider(azure_config)
    """
    provider_type = SETTINGS.llm_provider.lower()

    # Prepare kwargs for additional parameters
    kwargs = {}
    if SETTINGS.llm_max_tokens:
        kwargs['max_tokens'] = SETTINGS.llm_max_tokens

    if provider_type == "openai":
        api_key = azure_config.get_secret("openai-key")
        return OpenAIProvider(
            api_key=api_key,
            model=SETTINGS.llm_model,
            temperature=SETTINGS.llm_temperature,
            **kwargs
        )

    elif provider_type == "gemini":
        api_key = azure_config.get_secret("GeminiAPIKey")
        return GeminiProvider(
            api_key=api_key,
            model=SETTINGS.llm_model,
            temperature=SETTINGS.llm_temperature,
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}. Supported: openai, gemini")


# Backward compatibility: Legacy function that returns the LangChain client directly
def make_llm(azure_config: AzureKeyVaultConfig):
    """
    Legacy factory function for backward compatibility.
    Returns the LangChain client directly instead of the provider wrapper.

    Args:
        azure_config: Azure Key Vault configuration for retrieving API keys

    Returns:
        A LangChain BaseChatModel instance
    """
    provider = create_llm_provider(azure_config)
    return provider.client
