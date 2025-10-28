"""
LLM Client Factory

This module provides a factory function to create LLM provider instances
based on the configuration settings. This allows easy switching between
different LLM providers (OpenAI, Gemini) without modifying service code.

Supports step-specific configuration for grammar correction, translation, and quality adjustment.
"""
from typing import Optional, Literal
from .config import SETTINGS
from .llm_provider import LLMProvider, OpenAIProvider, GeminiProvider
from src.services.azure_config import AzureKeyVaultConfig


def create_llm_provider(
    azure_config: AzureKeyVaultConfig,
    step: Optional[Literal["grammar", "translation", "adjustment"]] = None
) -> LLMProvider:
    """
    Factory function to create an LLM provider based on configuration.

    Supports both global and step-specific configuration. Step-specific settings
    take precedence over global settings.

    Args:
        azure_config: Azure Key Vault configuration for retrieving API keys
        step: Optional translation pipeline step ('grammar', 'translation', 'adjustment')
              If provided, uses step-specific configuration (e.g., TRANSLATION_GRAMMAR_LLM_PROVIDER)
              Falls back to global configuration if step-specific not set

    Returns:
        An LLMProvider instance (OpenAI or Gemini)

    Examples:
        # Use global configuration
        provider = create_llm_provider(azure_config)

        # Use grammar-specific configuration
        provider = create_llm_provider(azure_config, step="grammar")
        # Uses TRANSLATION_GRAMMAR_LLM_PROVIDER or falls back to TRANSLATION_LLM_PROVIDER

        # Environment variable examples:
        # Global: TRANSLATION_LLM_PROVIDER=gemini, TRANSLATION_LLM_MODEL=gemini-1.5-pro
        # Grammar: TRANSLATION_GRAMMAR_LLM_PROVIDER=gemini, TRANSLATION_GRAMMAR_LLM_MODEL=gemini-1.5-flash
        # Translation: TRANSLATION_TRANSLATION_LLM_PROVIDER=gemini, TRANSLATION_TRANSLATION_LLM_MODEL=gemini-1.5-pro
        # Adjustment: TRANSLATION_ADJUSTMENT_LLM_PROVIDER=openai, TRANSLATION_ADJUSTMENT_LLM_MODEL=gpt-4o
    """
    # Determine which configuration to use based on step
    if step == "grammar":
        provider_type = (SETTINGS.grammar_llm_provider or SETTINGS.llm_provider).lower()
        model = SETTINGS.grammar_llm_model if SETTINGS.grammar_llm_model is not None else SETTINGS.llm_model
        temperature = SETTINGS.grammar_llm_temperature if SETTINGS.grammar_llm_temperature is not None else SETTINGS.llm_temperature
    elif step == "translation":
        provider_type = (SETTINGS.translation_llm_provider or SETTINGS.llm_provider).lower()
        model = SETTINGS.translation_llm_model if SETTINGS.translation_llm_model is not None else SETTINGS.llm_model
        temperature = SETTINGS.translation_llm_temperature if SETTINGS.translation_llm_temperature is not None else SETTINGS.llm_temperature
    elif step == "adjustment":
        provider_type = (SETTINGS.adjustment_llm_provider or SETTINGS.llm_provider).lower()
        model = SETTINGS.adjustment_llm_model if SETTINGS.adjustment_llm_model is not None else SETTINGS.llm_model
        temperature = SETTINGS.adjustment_llm_temperature if SETTINGS.adjustment_llm_temperature is not None else SETTINGS.llm_temperature
    else:
        # No step specified, use global configuration
        provider_type = SETTINGS.llm_provider.lower()
        model = SETTINGS.llm_model
        temperature = SETTINGS.llm_temperature

    # Prepare kwargs for additional parameters
    kwargs = {}
    if SETTINGS.llm_max_tokens:
        kwargs['max_tokens'] = SETTINGS.llm_max_tokens

    # Create the appropriate provider
    if provider_type == "openai":
        api_key = azure_config.get_secret("openai-key")
        return OpenAIProvider(
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )

    elif provider_type == "gemini":
        api_key = azure_config.get_secret("GeminiKey")
        return GeminiProvider(
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}. Supported: openai, gemini")


def create_step_llm_provider(azure_config: AzureKeyVaultConfig, step: str) -> LLMProvider:
    """
    Factory function to create an LLM provider for a specific translation step.
    
    Args:
        azure_config: Azure Key Vault configuration for retrieving API keys
        step: Translation step ('grammar', 'translation', 'adjustment')
        
    Returns:
        An LLMProvider instance configured for the specific step
        
    Example:
        # Get provider optimized for grammar correction
        grammar_provider = create_step_llm_provider(azure_config, "grammar")
        
        # Get provider optimized for translation
        translation_provider = create_step_llm_provider(azure_config, "translation")
    """
    step_config = SETTINGS.get_step_config(step)
    provider_type = step_config["provider"].lower()
    
    # Prepare kwargs for additional parameters
    kwargs = {}
    if step_config["max_tokens"]:
        kwargs['max_tokens'] = step_config["max_tokens"]

    if provider_type == "openai":
        api_key = azure_config.get_secret("openai-key")
        return OpenAIProvider(
            api_key=api_key,
            model=step_config["model"],
            temperature=step_config["temperature"],
            **kwargs
        )

    elif provider_type == "gemini":
        api_key = azure_config.get_secret("GeminiKey")
        return GeminiProvider(
            api_key=api_key,
            model=step_config["model"],
            temperature=step_config["temperature"],
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


def make_step_llm(azure_config: AzureKeyVaultConfig, step: str):
    """
    Legacy factory function for step-specific LLM clients.
    Returns the LangChain client directly for a specific translation step.

    Args:
        azure_config: Azure Key Vault configuration for retrieving API keys
        step: Translation step ('grammar', 'translation', 'adjustment')

    Returns:
        A LangChain BaseChatModel instance configured for the step
    """
    provider = create_step_llm_provider(azure_config, step)
    return provider.client
