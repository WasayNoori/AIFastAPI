from pathlib import Path
from pydantic import BaseSettings
from typing import Optional


class TranslationSettings(BaseSettings):
    """Configuration settings for the translation module."""
    
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
