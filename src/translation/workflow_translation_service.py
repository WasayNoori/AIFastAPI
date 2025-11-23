"""
Translation Workflow Service
Orchestrates the complete translation workflow:
1. Load text from file
2. Correct grammar and split into sentences
3. Translate using DeepL
4. Save results to file
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from src.services.azure_config import AzureKeyVaultConfig
from src.translation.clients import create_llm_provider
from src.translation.sentencesplitter import split_text, Sentence
from src.translation.deepltranslation import TranslationLangChainService as DeepLTranslationService


class WorkflowStep1Result(BaseModel):
    """Result from Step 1: Loading original text"""
    original_text: str
    char_count: int
    word_count: int


class WorkflowStep2Result(BaseModel):
    """Result from Step 2: Grammar correction and sentence splitting"""
    corrected_text: str
    sentences: List[str]  # Formatted sentences with numbers
    sentence_count: int
    grammar_correction_applied: bool


class WorkflowStep3Result(BaseModel):
    """Result from Step 3: DeepL translation"""
    translated_text: str
    source_language: str
    target_language: str
    translated_sentence_count: int


class CompleteWorkflowResult(BaseModel):
    """Complete workflow result with all steps"""
    step1_original: WorkflowStep1Result
    step2_corrected: WorkflowStep2Result
    step3_translated: WorkflowStep3Result
    workflow_completed: bool


class WorkflowTranslationService:
    """Service for managing the complete translation workflow"""

    def __init__(self, azure_config: AzureKeyVaultConfig):
        self.azure_config = azure_config
        self.deepl_service = DeepLTranslationService(azure_config)

        # Load grammar template for Step 2
        self.grammartemplate = Path("src/translation/prompts/grammartemplate.txt").read_text()

    def step1_load_text(self, text: str) -> WorkflowStep1Result:
        """
        Step 1: Load and analyze original text

        Args:
            text: The original text to process

        Returns:
            WorkflowStep1Result with original text and metrics
        """
        char_count = len(text)
        word_count = len(text.split())

        return WorkflowStep1Result(
            original_text=text,
            char_count=char_count,
            word_count=word_count
        )

    def step2_correct_and_split(
        self,
        text: str,
        language: str = "en",
        correct_grammar: bool = True
    ) -> WorkflowStep2Result:
        """
        Step 2: Correct grammar and split into sentences

        Args:
            text: The text to process
            language: Language code (en, fr, de)
            correct_grammar: Whether to apply grammar correction

        Returns:
            WorkflowStep2Result with corrected text and sentences
        """
        text_to_analyze = text

        # Optionally correct grammar
        if correct_grammar:
            grammar_provider = create_llm_provider(self.azure_config, step="grammar")
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.grammartemplate.replace("{{input_text}}", "{input_text}")),
                ("human", "{input_text}")
            ])
            text_to_analyze = grammar_provider.invoke(prompt, {"input_text": text})

        # Split into sentences
        sentences = split_text(text_to_analyze, language)
        formatted_sentences = [f"{s.Number}. {s.Text}" for s in sentences]

        return WorkflowStep2Result(
            corrected_text=text_to_analyze,
            sentences=formatted_sentences,
            sentence_count=len(sentences),
            grammar_correction_applied=correct_grammar
        )

    def step3_translate(
        self,
        text: str,
        target_language: str = "FR"
    ) -> WorkflowStep3Result:
        """
        Step 3: Translate text using DeepL and count sentences

        Args:
            text: The text to translate
            target_language: Target language code (FR, DE, ES, etc.)

        Returns:
            WorkflowStep3Result with translated text and sentence count
        """
        # Map DeepL language codes to spaCy language codes
        deepl_to_spacy = {
            "FR": "fr",
            "DE": "de",
            "EN": "en",
            "EN-US": "en",
            "EN-GB": "en",
        }

        result = self.deepl_service.translate_deepl(text, target_language)
        translated_text = result["translated_text"]

        # Count sentences in translated text using sentence splitter
        spacy_lang = deepl_to_spacy.get(target_language.upper(), "fr")
        translated_sentences = split_text(translated_text, spacy_lang)
        translated_sentence_count = len(translated_sentences)

        return WorkflowStep3Result(
            translated_text=translated_text,
            source_language="EN",  # Assuming English source for now
            target_language=target_language,
            translated_sentence_count=translated_sentence_count
        )

    def execute_complete_workflow(
        self,
        original_text: str,
        language: str = "en",
        target_language: str = "FR",
        correct_grammar: bool = True
    ) -> CompleteWorkflowResult:
        """
        Execute the complete translation workflow

        Args:
            original_text: The original text to process
            language: Source language code for sentence splitting
            target_language: Target language for translation
            correct_grammar: Whether to apply grammar correction

        Returns:
            CompleteWorkflowResult with all workflow steps
        """
        # Step 1: Load text
        step1_result = self.step1_load_text(original_text)

        # Step 2: Correct grammar and split
        step2_result = self.step2_correct_and_split(
            original_text,
            language=language,
            correct_grammar=correct_grammar
        )

        # Step 3: Translate the corrected text with sentence numbers
        # Join formatted sentences (e.g., "1. First sentence.\n2. Second sentence.")
        text_with_numbers = "\n".join(step2_result.sentences)
        step3_result = self.step3_translate(
            text_with_numbers,
            target_language=target_language
        )

        return CompleteWorkflowResult(
            step1_original=step1_result,
            step2_corrected=step2_result,
            step3_translated=step3_result,
            workflow_completed=True
        )

    @staticmethod
    def save_text_to_file(text: str, file_path: str) -> Dict[str, str]:
        """
        Save text to a file

        Args:
            text: The text to save
            file_path: Path where to save the file

        Returns:
            Dict with success status and file path
        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

            return {
                "status": "success",
                "file_path": str(output_path.absolute()),
                "message": f"File saved successfully to {output_path.absolute()}"
            }
        except Exception as e:
            return {
                "status": "error",
                "file_path": file_path,
                "message": f"Failed to save file: {str(e)}"
            }

    @staticmethod
    def load_text_from_file(file_path: str) -> Dict[str, str]:
        """
        Load text from a file

        Args:
            file_path: Path to the file to load

        Returns:
            Dict with text content and metadata
        """
        try:
            input_path = Path(file_path)

            if not input_path.exists():
                return {
                    "status": "error",
                    "text": "",
                    "message": f"File not found: {file_path}"
                }

            text = input_path.read_text(encoding="utf-8")

            return {
                "status": "success",
                "text": text,
                "file_path": str(input_path.absolute()),
                "file_size": input_path.stat().st_size,
                "message": "File loaded successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "text": "",
                "message": f"Failed to load file: {str(e)}"
            }
