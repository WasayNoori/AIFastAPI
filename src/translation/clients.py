from langchain_openai import ChatOpenAI
from .config import SETTINGS

def make_llm():
    """
    Factory for the LLM client. Relies on OPENAI_API_KEY in env.
    Swap here to use Anthropic or Azure OpenAI without touching the rest.
    """
    return ChatOpenAI(model=SETTINGS.model, temperature=SETTINGS.temperature)
