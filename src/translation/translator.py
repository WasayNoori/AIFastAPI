import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import re
from typing import Dict, Optional, Tuple
from pydantic import BaseModel
from urllib.parse import urlparse
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
from src.translation.text_metrics import word_count, syllable_count_en
load_dotenv()

class TranslationResult(BaseModel):
    translatedtext: str
    OriginalSentenceCount: int
    translationSentenceCount: int

class TranslationService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.api_key = azure_config.get_secret("openai-key")
        self.chat_model = ChatOpenAI(api_key=self.api_key)
        self.blob_service = BlobStorageService()

        # Load prompt templates
        self.grammartemplate = Path("src/translation/prompts/grammartemplate.txt").read_text()
        self.translationtemplate = Path("src/translation/prompts/translatorprompt.txt").read_text()
        self.adjustmenttemplate = Path("src/translation/prompts/adjustmentprompt.txt").read_text()

        # Load default glossary
        with open("src/translation/prompts/glossary.json", "r", encoding="utf-8") as f:
            self.default_glossary = json.load(f)

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text using simple heuristic."""
        if not text or not text.strip():
            return 0
        # Split on sentence-ending punctuation followed by space or end of string
        sentences = re.split(r'[.!?]+(?:\s+|$)', text.strip())
        # Filter out empty strings
        return len([s for s in sentences if s.strip()])

    def _correct_grammar(self, text: str) -> str:
        """Step 2: Correct grammar and punctuation using grammartemplate."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.grammartemplate.replace("{{input_text}}", "{input_text}")),
            ("human", "{input_text}")
        ])
        chain = prompt | self.chat_model
        response = chain.invoke({"input_text": text})
        return response.content.strip()

    def _translate_text(self, text: str, input_language: str, output_language: str, glossary: Optional[Dict] = None) -> str:
        """Step 3: Translate text using translatorprompt."""
        if glossary is None:
            glossary = self.default_glossary

        # Format glossary as string
        glossary_str = "\n".join([f"{k}: {v}" for k, v in glossary.items()])

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.translationtemplate),
            ("human", "{text}")
        ])
        chain = prompt | self.chat_model
        response = chain.invoke({
            "text": text,
            "input_language": input_language,
            "output_language": output_language,
            "dictionary": glossary_str
        })
        return response.content.strip()

    def _adjust_translation(self, source_text: str, translated_text: str) -> str:
        """Step 4: Quality check and adjust translation using adjustmentprompt."""
        # Calculate metrics
        src_words = word_count(source_text)
        src_syllables = syllable_count_en(source_text)
        tgt_words = word_count(translated_text)
        tgt_syllables = syllable_count_en(translated_text)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.adjustmenttemplate),
            ("human", "{translated_text}")
        ])
        chain = prompt | self.chat_model
        response = chain.invoke({
            "translated_text": translated_text,
            "src_words": src_words,
            "src_syllables": src_syllables,
            "tgt_words": tgt_words,
            "tgt_syllables": tgt_syllables
        })
        return response.content.strip()

    def _parse_blob_path(self, container_name: Optional[str], blob_path: str) -> Tuple[str, str]:
        """
        Parse blob path to extract container name and blob path.
        Supports both:
        1. Full URL: https://account.blob.core.windows.net/container/path/to/file.txt
        2. Separate params: container_name="container", blob_path="path/to/file.txt"

        Returns:
            Tuple of (container_name, blob_path)
        """
        # If blob_path starts with http:// or https://, parse as URL
        if blob_path.startswith('http://') or blob_path.startswith('https://'):
            parsed_url = urlparse(blob_path)
            # Path format: /container/path/to/file.txt
            path_parts = parsed_url.path.lstrip('/').split('/', 1)
            if len(path_parts) < 2:
                raise ValueError(f"Invalid blob URL format. Expected https://account.blob.core.windows.net/container/path, got: {blob_path}")
            extracted_container = path_parts[0]
            extracted_blob_path = path_parts[1]
            return extracted_container, extracted_blob_path
        else:
            # Use provided container_name and blob_path as-is
            if not container_name:
                raise ValueError("container_name is required when blob_path is not a full URL")
            return container_name, blob_path

    def translate_from_blob(
        self,
        container_name: Optional[str],
        blob_path: str,
        input_language: str,
        output_language: str,
        glossary: Optional[Dict] = None
    ) -> TranslationResult:
        """
        Main translation method that orchestrates all steps from flow.txt:
        1. Read text from blob file
        2. Correct grammar and punctuation
        3. Translate to target language
        4. Quality check and adjust
        5. Return result in specified JSON format

        Args:
            container_name: Container name (optional if blob_path is a full URL)
            blob_path: Either a relative path within container OR a full blob URL
            input_language: Source language
            output_language: Target language
            glossary: Optional glossary dictionary

        Examples:
            # Using separate container and path
            translate_from_blob("mycontainer", "folder/file.txt", "EN", "FR")

            # Using full URL
            translate_from_blob(None, "https://account.blob.core.windows.net/mycontainer/folder/file.txt", "EN", "FR")
        """
        # Step 1: Parse blob path to get container and blob path
        parsed_container, parsed_blob_path = self._parse_blob_path(container_name, blob_path)

        # Step 2: Read text from blob
        original_text = self.blob_service.read_text_from_blob(parsed_container, parsed_blob_path)

        # Step 2: Correct grammar and punctuation
        corrected_text = self._correct_grammar(original_text)

        # Step 3: Translate to target language
        translated_text = self._translate_text(corrected_text, input_language, output_language, glossary)

        # Step 4: Quality check and adjust
        final_text = self._adjust_translation(corrected_text, translated_text)

        # Step 5: Count sentences and return result
        original_sentence_count = self._count_sentences(original_text)
        translated_sentence_count = self._count_sentences(final_text)

        return TranslationResult(
            translatedtext=final_text,
            OriginalSentenceCount=original_sentence_count,
            translationSentenceCount=translated_sentence_count
        )