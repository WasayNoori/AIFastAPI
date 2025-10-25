from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Literal


class TranslationSettings(BaseSettings):
    """Configuration settings for the translation module."""

    # LLM Provider Configuration
    llm_provider: Literal["openai", "gemini"] = "gemini"
    llm_model: Optional[str] = None  # If None, uses provider's default
    llm_temperature: float = 0.0
    llm_max_tokens: Optional[int] = None

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


# Global settings instance
SETTINGS = TranslationSettings()
