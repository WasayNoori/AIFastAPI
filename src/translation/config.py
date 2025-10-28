from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Literal


class TranslationSettings(BaseSettings):
    """Configuration settings for the translation module."""

    # Global LLM Configuration (fallback if step-specific not set)
    llm_provider: Literal["openai", "gemini"] = "gemini"
    llm_model: Optional[str] = None  # If None, uses provider's default
    llm_temperature: float = 0.0
    llm_max_tokens: Optional[int] = None

    # Grammar Correction Step Configuration
    grammar_llm_provider: Optional[Literal["openai", "gemini"]] = None  # Falls back to llm_provider
    grammar_llm_model: Optional[str] = None  # Falls back to llm_model
    grammar_llm_temperature: Optional[float] = None  # Falls back to llm_temperature

    # Translation Step Configuration
    translation_llm_provider: Optional[Literal["openai", "gemini"]] = None  # Falls back to llm_provider
    translation_llm_model: Optional[str] = None  # Falls back to llm_model
    translation_llm_temperature: Optional[float] = None  # Falls back to llm_temperature

    # Quality Adjustment Step Configuration
    adjustment_llm_provider: Optional[Literal["openai", "gemini"]] = None  # Falls back to llm_provider
    adjustment_llm_model: Optional[str] = None  # Falls back to llm_model
    adjustment_llm_temperature: Optional[float] = None  # Falls back to llm_temperature

    # Base directory for prompts
    prompts_dir: str = "src/translation/prompts"

    # Specific prompt files
    translation_prompt_file: str = "translatorprompt.txt"
    adjustment_prompt_file: str = "adjustmentprompt.txt"
    summary_prompt_file: str = "summaryprompt.txt"
    grammar_template_file: str = "grammartemplate.txt"

    # Glossary file
    glossary_file: str = "glossary.json"

    class Config:
        env_prefix = "TRANSLATION_"
        case_sensitive = False


    def get_step_config(self, step: str) -> dict:
        """
        Get LLM configuration for a specific step with fallback to global config.
        
        Args:
            step: One of 'grammar', 'translation', 'adjustment'
            
        Returns:
            Dict with provider, model, temperature for the step
        """
        step_provider = getattr(self, f"{step}_llm_provider", None) or self.llm_provider
        step_model = getattr(self, f"{step}_llm_model", None) or self.llm_model
        step_temperature = getattr(self, f"{step}_llm_temperature", None)
        if step_temperature is None:
            step_temperature = self.llm_temperature
            
        return {
            "provider": step_provider,
            "model": step_model,
            "temperature": step_temperature,
            "max_tokens": self.llm_max_tokens
        }


# Global settings instance
SETTINGS = TranslationSettings()
