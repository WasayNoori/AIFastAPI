from pathlib import Path
from .config import SETTINGS

def load_prompt_text(filename: str) -> str:
    """Load prompt text from a file in the prompts directory."""
    path = Path(SETTINGS.prompts_dir) / filename
    return path.read_text(encoding="utf-8")

def load_translation_prompt() -> str:
    """Load the main translation prompt."""
    return load_prompt_text(SETTINGS.translation_prompt_file)

def load_adjustment_prompt() -> str:
    """Load the adjustment prompt for refining translations."""
    return load_prompt_text(SETTINGS.adjustment_prompt_file)
