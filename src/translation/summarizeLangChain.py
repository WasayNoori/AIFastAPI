import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import json
from typing import Dict
from pydantic import BaseModel
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
from src.translation.clients import create_llm_provider
load_dotenv()

class SummarizeResult(BaseModel):
    summarized_text: str
    action_items: str

class SummarizeLangChainService:
    def __init__(self):
        # Create azure_config internally for backward compatibility
        azure_config = AzureKeyVaultConfig("https://aifastapi.vault.azure.net")
        # Use the LLM provider abstraction instead of direct ChatOpenAI
        self.llm_provider = create_llm_provider(azure_config)
        self.template = Path("src/translation/prompts/summaryprompt.txt").read_text()

        self.human_template = "{lesson_text}"
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self.template),
            ("human", self.human_template)
        ])

    def summarize(self, text: str) -> SummarizeResult:
        """
        Summarize the lesson text.

        Args:
            text: The lesson text to summarize

        Returns:
            SummarizeResult with summarized_text and action_items
        """
        content = self.llm_provider.invoke(self.chat_prompt, {"lesson_text": text})

        # Parse the result - expecting two paragraphs
        paragraphs = content.split('\n\n', 1)

        if len(paragraphs) == 2:
            summarized_text = paragraphs[0]
            action_items = paragraphs[1]
        else:
            summarized_text = content
            action_items = ""

        return SummarizeResult(
            summarized_text=summarized_text,
            action_items=action_items
        )

    def summarize_script(self, request_data: Dict, blob_service: BlobStorageService) -> SummarizeResult:
        """
        Summarize script using blob path.

        Args:
            request_data: Dictionary containing blob_path
            blob_service: BlobStorageService instance for reading blob content

        Returns:
            SummarizeResult with summarized_text and action_items
        """
        blob_path = request_data.get("blob_path", "")

        # Parse blob_path - handle both full URL and container/path format
        if blob_path.startswith("https://"):
            # Parse full Azure blob URL
            from urllib.parse import urlparse
            parsed_url = urlparse(blob_path)
            path_parts = parsed_url.path.lstrip('/').split('/', 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid blob URL format. Expected URL with container and blob path, got: {blob_path}")
            container_name = path_parts[0]
            blob_name = path_parts[1]
        else:
            # Parse container/path format
            path_parts = blob_path.split("/", 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid blob_path format. Expected 'container/path' or full URL, got: {blob_path}")
            container_name = path_parts[0]
            blob_name = path_parts[1]

        # Read the actual blob content
        try:
            print(f"DEBUG: Attempting to read - Container: '{container_name}', Blob: '{blob_name}'")
            text_content = blob_service.read_text_from_blob(container_name, blob_name)
            print(f"DEBUG: Successfully read {len(text_content)} characters")
        except Exception as e:
            print(f"DEBUG: Failed to read blob - Container: '{container_name}', Blob: '{blob_name}', Error: {str(e)}")
            raise ValueError(f"Failed to read blob {blob_path}: {str(e)}")

        return self.summarize(text=text_content)
