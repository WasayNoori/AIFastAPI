import os
from dotenv import load_dotenv
from pathlib import Path
import json
import requests
from typing import Dict
from pydantic import BaseModel
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
import langchain_google_genai
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
load_dotenv()


class TranslationLangChainService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.azure_config = azure_config
        self._deepl_api_key = None
        self._deepl_glossary_id = None
        self._openai_api_key = None
        self._gemini_api_key = None
        self.api_url = "https://api-free.deepl.com/v2/translate"

        # Load context from file
        self.deepl_context = Path("src/translation/prompts/deeplcontext.txt").read_text(encoding="utf-8").strip()

    @property
    def DEEPL_API_KEY(self):
        """Lazy load DeepL API key"""
        if self._deepl_api_key is None:
            self._deepl_api_key = self.azure_config.get_secret("DeeplAPITemp")
        return self._deepl_api_key

    @property
    def DEEPL_GLOSSARY_ID(self):
        """Lazy load DeepL Glossary ID"""
        if self._deepl_glossary_id is None:
            self._deepl_glossary_id = self.azure_config.get_secret("DeepLGlossaryID")
        return self._deepl_glossary_id

    @property
    def OPENAI_API_KEY(self):
        """Lazy load OpenAI API key"""
        if self._openai_api_key is None:
            self._openai_api_key = self.azure_config.get_secret("OPENAI-KEY")
        return self._openai_api_key

    @property
    def GEMINI_API_KEY(self):
        """Lazy load Gemini API key"""
        if self._gemini_api_key is None:
            self._gemini_api_key = self.azure_config.get_secret("GeminiAPIKey")
        return self._gemini_api_key

#define deepL Runnable



    def translate_deepl(self, text: str, target_lang: str = "FR") -> Dict:
        """
        Translate text using DeepL API.

        Args:
            text: Text to translate
            target_lang: Target language code (default: FR for French)

        Returns:
            Dict with translated text and debug info
        """
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_API_KEY}",
            "User-Agent": "YourApp/1.2.3",
            "Content-Type": "application/json",
        }

        payload = {
            "text": [text],
            "target_lang": "Fr",
            "source_lang": "En",
            "glossary_id": "b0f983c2-d00b-4b93-b045-a6ee00201d7e",
            "context": self.deepl_context
        }

        # Debug info to return
        debug_info = {
            "glossary_id": "b0f983c2-d00b-4b93-b045-a6ee00201d7e",
            "context": self.deepl_context,
            "source_lang": "En",
            "target_lang": "Fr",
            "api_url": self.api_url
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            translation_data = response.json()

            if 'translations' in translation_data:
                translated_text = translation_data['translations'][0]['text']
                return {
                    "translated_text": translated_text,
                    "debug": debug_info
                }
            else:
                raise ValueError("'translations' key not found in response")

        except requests.exceptions.HTTPError as errh:
            # Capture the response body for debugging
            error_body = None
            try:
                error_body = response.json()
            except:
                error_body = response.text
            raise Exception(f"HTTP Error: {errh}. Response: {error_body}")
        except requests.exceptions.ConnectionError as errc:
            raise Exception(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            raise Exception(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            raise Exception(f"An unexpected error occurred: {err}")

    def translate_deepl_simple(self, text: str, target_lang: str = "FR") -> str:
        return "This is a simple translation"
        