import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
from typing import Dict
from pydantic import BaseModel
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
load_dotenv()

class TranslationResult(BaseModel):
    translated_text: str
    word_count: int

class TranslationLangChainService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.api_key = azure_config.get_secret("openai-key")
        self.chat_model = ChatOpenAI(api_key=self.api_key)
        self.template = Path("src/translation/prompts/translatorprompt.txt").read_text()

        with open("src/translation/prompts/glossary.json", "r", encoding="utf-8") as f:
            self.default_glossary = json.load(f)

        self.human_template = "{text}"
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self.template),
            ("human", self.human_template)
        ])

    def translate(self, text: str, input_language: str = "English",
                 output_language: str = "French",
                 custom_glossary: Dict[str, str] = None) -> TranslationResult:

        glossary_to_use = custom_glossary if custom_glossary else self.default_glossary
        dict_str = "\n".join([f"{src} → {tgt}" for src, tgt in glossary_to_use.items()])

        messages = self.chat_prompt.format_messages(
            input_language=input_language,
            output_language=output_language,
            dictionary=dict_str,
            text=text
        )

        result = self.chat_model.invoke(messages)
        translated_text = result.content
        word_count = len(translated_text.split())

        return TranslationResult(
            translated_text=translated_text,
            word_count=word_count
        )

    def translate_script(self, request_data: Dict, blob_service: BlobStorageService) -> TranslationResult:
        """
        Translate script using the same JSON object format as the endpoint.

        Args:
            request_data: Dictionary containing blob_path and glossary
            blob_service: BlobStorageService instance for reading blob content

        Returns:
            TranslationResult with translated_text and word_count
        """
        blob_path = request_data.get("blob_path", "")
        glossary = request_data.get("glossary", {})

        # Parse blob_path - handle both full URL and container/path format
        if blob_path.startswith("https://"):
            # Parse full Azure blob URL
            # Format: https://account.blob.core.windows.net/container/path/to/file
            from urllib.parse import urlparse
            parsed_url = urlparse(blob_path)
            path_parts = parsed_url.path.lstrip('/').split('/', 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid blob URL format. Expected URL with container and blob path, got: {blob_path}")
            container_name = path_parts[0]
            blob_name = path_parts[1]
        else:
            # Parse container/path format
            # Expected format: "container/path/to/file.txt"
            path_parts = blob_path.split("/", 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid blob_path format. Expected 'container/path' or full URL, got: {blob_path}")
            container_name = path_parts[0]
            blob_name = path_parts[1]

        # Read the actual blob content
        try:
           
            text_content = blob_service.read_text_from_blob(container_name, blob_name)
           
        except Exception as e:
            
            raise ValueError(f"Failed to read blob {blob_path}: {str(e)}")

        return self.translate(
            text=text_content,
            custom_glossary=glossary
        )