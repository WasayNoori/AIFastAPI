from pydantic_settings import BaseSettings
from typing import Optional


class QuizSettings(BaseSettings):
    """Configuration settings for the quiz module."""

    # External API Configuration
    external_api_url: str = "https://localhost:7003/api/QuizApi/bulk-import"
    external_api_timeout: int = 30  # seconds

    # Quiz Generation Configuration
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Prompt files
    prompts_dir: str = "src/Quizzes/prompts"
    quiz_template_file: str = "QuizTemplate.txt"

    class Config:
        env_prefix = "QUIZ_"
        case_sensitive = False


# Global settings instance
SETTINGS = QuizSettings()
