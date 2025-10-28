import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import json
import re
from typing import Dict, Optional, Tuple
from pydantic import BaseModel
from urllib.parse import urlparse
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
from src.translation.text_metrics import word_count, syllable_count_en
from src.translation.clients import create_llm_provider
load_dotenv()

class TranslationResult(BaseModel):
    translatedtext: str
    OriginalSentenceCount: int
    translationSentenceCount: int
    grammar_correction_time_seconds: float
    translation_time_seconds: float
    adjustment_time_seconds: float
    total_time_seconds: float
    grammar_llm_provider: str
    grammar_llm_model: str
    translation_llm_provider: str
    translation_llm_model: str
    adjustment_llm_provider: str
    adjustment_llm_model: str

class TranslationService:
    def __init__(self, azure_config: AzureKeyVaultConfig):
        # Create step-specific LLM providers for each translation pipeline step
        # This allows using different models/providers for grammar, translation, and adjustment
        # E.g., Gemini Flash for grammar, Gemini Pro for translation, GPT-4o for adjustment
        self.grammar_provider = create_llm_provider(azure_config, step="grammar")
        self.translation_provider = create_llm_provider(azure_config, step="translation")
        self.adjustment_provider = create_llm_provider(azure_config, step="adjustment")

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
        return self.grammar_provider.invoke(prompt, {"input_text": text})

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
        return self.translation_provider.invoke(prompt, {
            "text": text,
            "input_language": input_language,
            "output_language": output_language,
            "dictionary": glossary_str
        })

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
        return self.adjustment_provider.invoke(prompt, {
            "translated_text": translated_text,
            "src_words": src_words,
            "src_syllables": src_syllables,
            "tgt_words": tgt_words,
            "tgt_syllables": tgt_syllables
        })

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
        # Start total timer
        total_start_time = time.time()

        # Step 1: Parse blob path to get container and blob path
        parsed_container, parsed_blob_path = self._parse_blob_path(container_name, blob_path)

        # Step 2: Read text from blob
        original_text = self.blob_service.read_text_from_blob(parsed_container, parsed_blob_path)

        # Step 3: Correct grammar and punctuation (with timing)
        grammar_start_time = time.time()
        corrected_text = self._correct_grammar(original_text)
        grammar_time = time.time() - grammar_start_time

        # Step 4: Translate to target language (with timing)
        translation_start_time = time.time()
        translated_text = self._translate_text(corrected_text, input_language, output_language, glossary)
        translation_time = time.time() - translation_start_time

        # Step 5: Quality check and adjust (with timing)
        adjustment_start_time = time.time()
        final_text = self._adjust_translation(corrected_text, translated_text)
        adjustment_time = time.time() - adjustment_start_time

        # Calculate total time
        total_time = time.time() - total_start_time

        # Step 6: Count sentences and return result
        original_sentence_count = self._count_sentences(original_text)
        translated_sentence_count = self._count_sentences(final_text)

        return TranslationResult(
            translatedtext=final_text,
            OriginalSentenceCount=original_sentence_count,
            translationSentenceCount=translated_sentence_count,
            grammar_correction_time_seconds=round(grammar_time, 3),
            translation_time_seconds=round(translation_time, 3),
            adjustment_time_seconds=round(adjustment_time, 3),
            total_time_seconds=round(total_time, 3),
            grammar_llm_provider=self.grammar_provider.get_provider_name(),
            grammar_llm_model=self.grammar_provider.model,
            translation_llm_provider=self.translation_provider.get_provider_name(),
            translation_llm_model=self.translation_provider.model,
            adjustment_llm_provider=self.adjustment_provider.get_provider_name(),
            adjustment_llm_model=self.adjustment_provider.model
        )