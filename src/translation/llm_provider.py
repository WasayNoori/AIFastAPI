"""
LLM Provider Abstraction Layer

This module provides an abstraction for different LLM providers (OpenAI, Gemini)
allowing easy switching between providers without modifying service code.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: Optional[str] = None, temperature: float = 0.0, **kwargs):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider
            model: Model name/identifier (provider-specific)
            temperature: Temperature for generation (0.0 - 2.0)
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.temperature = temperature
        self.kwargs = kwargs
        self._client: Optional[BaseChatModel] = None

    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model for this provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'gemini')."""
        pass

    @abstractmethod
    def create_client(self) -> BaseChatModel:
        """Create and return the LangChain chat model client."""
        pass

    @property
    def client(self) -> BaseChatModel:
        """Lazy-load and return the LLM client."""
        if self._client is None:
            self._client = self.create_client()
        return self._client

    def invoke(self, prompt_template: ChatPromptTemplate, variables: Dict[str, Any]) -> str:
        """
        Invoke the LLM with a prompt template and variables.

        Args:
            prompt_template: LangChain ChatPromptTemplate
            variables: Dictionary of variables to inject into the template

        Returns:
            The LLM response content as a string
        """
        chain = prompt_template | self.client
        response = chain.invoke(variables)
        return response.content.strip()


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider (GPT models)."""

    def get_default_model(self) -> str:
        return "gpt-4o"

    def get_provider_name(self) -> str:
        return "openai"

    def create_client(self) -> BaseChatModel:
        return ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            **self.kwargs
        )


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def get_default_model(self) -> str:
        return "gemini-2.5-flash"

    def get_provider_name(self) -> str:
        return "gemini"

    def create_client(self) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            **self.kwargs
        )
