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
        self.DEEPL_API_KEY = azure_config.get_secret("DeeplAPITemp")
        self.api_url = "https://api-free.deepl.com/v2/translate"
        self.OPENAI_API_KEY = azure_config.get_secret("OPENAI-KEY")
        self.GEMINI_API_KEY = azure_config.get_secret("GeminiAPIKey")

#define deepL Runnable



    def translate_deepl(self, text: str, target_lang: str = "FR") -> str:
        """
        Translate text using DeepL API.

        Args:
            text: Text to translate
            target_lang: Target language code (default: FR for French)

        Returns:
            Translated text
        """
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.DEEPL_API_KEY}",
            "User-Agent": "YourApp/1.2.3",
            "Content-Type": "application/json",
        }

        payload = {
            "text": [text],
            "target_lang": target_lang,
            "context": "CAD Tutorial Script"
             
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
                return translated_text
            else:
                raise ValueError("'translations' key not found in response")

        except requests.exceptions.HTTPError as errh:
            raise Exception(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            raise Exception(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            raise Exception(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            raise Exception(f"An unexpected error occurred: {err}")

    def translate_deepl_simple(self, text: str, target_lang: str = "FR") -> str:
        return "This is a simple translation"
        