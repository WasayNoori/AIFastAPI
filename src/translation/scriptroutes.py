from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from src.auth.dependencies import get_current_app, get_blob_storage_service, get_translation_service, get_summarize_service, get_deepl_translation_service, get_translation_chain_service, get_azure_config, get_workflow_translation_service
from src.services.blob_storage_service import BlobStorageService
from src.services.azure_config import AzureKeyVaultConfig
from src.translation.translationLangChain import TranslationLangChainService, TranslationResult
from src.translation.summarizeLangChain import SummarizeLangChainService, SummarizeResult
from src.translation.deepltranslation import TranslationLangChainService as DeepLTranslationService
from src.translation.translator import TranslationService, TranslationResult as ChainTranslationResult
from src.translation.sentencesplitter import split_text
from src.translation.clients import create_llm_provider
from src.translation.workflow_translation_service import WorkflowTranslationService, CompleteWorkflowResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])

class TranslateScriptRequest(BaseModel):
    blob_path: str
    glossary: Dict[str, str]


class SummarizeScriptRequest(BaseModel):
    blob_path: str


class SimpleTranslationRequest(BaseModel):
    text: str


class TranslateChainRequest(BaseModel):
    container_name: Optional[str] = None  # Optional if blob_path is a full URL
    blob_path: str  # Either relative path or full blob URL
    input_language: str
    output_language: str
    glossary: Optional[Dict[str, str]] = None  # Optional glossary


class AnalyzeTextRequest(BaseModel):
    text: str
    language: str = "en"  # Language code: 'en', 'fr', or 'de'
    correct_grammar: bool = False  # Whether to apply grammar correction before splitting


class WorkflowTranslationRequest(BaseModel):
    text: str
    source_language: str = "en"  # Language code for sentence splitting
    target_language: str = "FR"  # Target language for DeepL translation
    correct_grammar: bool = True  # Whether to apply grammar correction


class SaveTextRequest(BaseModel):
    text: str
    file_path: str  # Path where to save the file


class LoadTextRequest(BaseModel):
    file_path: str  # Path to the file to load


@router.post("/translateScript")
async def translate_script(
    request: TranslateScriptRequest,
    current_user = Depends(get_current_app),
    blob_service: BlobStorageService = Depends(get_blob_storage_service),
    translation_service: TranslationLangChainService = Depends(get_translation_service)
):
    """
    Translate a script file using a provided glossary.

    Args:
        request: Contains blob_path and glossary dictionary
        current_user: Authenticated user
        blob_service: Blob storage service for file access

    Returns:
        Translation result
    """
    try:
        # Convert request to dictionary format for the translation service
        request_data = {
            "blob_path": request.blob_path,
            "glossary": request.glossary
        }

        # Use the injected translation service to translate the script
        result = translation_service.translate_script(request_data, blob_service)

        return {
            "status": "success",
            "translation_result": {
                "translated_text": result.translated_text,
                "word_count": result.word_count,
                "blob_path": request.blob_path,
                "glossary_entries": len(request.glossary),
                "processed_by": current_user.get("sub", "unknown")
            }
        }

    except Exception as e:
        logger.error(f"Script translation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate script: {str(e)}"
        )

@router.post("/analyzetext")
async def analyzetext(
    request: AnalyzeTextRequest,
    current_user = Depends(get_current_app),
    azure_config: AzureKeyVaultConfig = Depends(get_azure_config)
):
    """
    Analyze text by optionally correcting grammar, then splitting it into sentences.

    Args:
        request: Contains text, language code, and correct_grammar flag
        current_user: Authenticated user
        azure_config: Azure configuration for LLM provider

    Returns:
        JSON with sentenceCount and sentences array
    """
    try:
        # Determine which text to use based on correct_grammar flag
        text_to_analyze = request.text

        # Step 1: Optionally correct grammar if requested
        if request.correct_grammar:
            # Create grammar provider
            grammar_provider = create_llm_provider(azure_config, step="grammar")

            # Load grammar template
            grammartemplate = Path("src/translation/prompts/grammartemplate.txt").read_text()

            # Correct grammar using the grammar provider
            prompt = ChatPromptTemplate.from_messages([
                ("system", grammartemplate.replace("{{input_text}}", "{input_text}")),
                ("human", "{input_text}")
            ])
            text_to_analyze = grammar_provider.invoke(prompt, {"input_text": request.text})

        # Step 2: Use the sentence splitter to split text into sentences
        sentences = split_text(text_to_analyze, request.language)

        # Format sentences as numbered list
        formatted_sentences = [f"{s.Number}. {s.Text}" for s in sentences]

        return {
            "sentenceCount": len(sentences),
            "sentences": formatted_sentences
        }
    except ValueError as e:
        # Handle unsupported language errors
        logger.error(f"Unsupported language: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Text analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze text: {str(e)}"
        )
        
@router.post("/deepltranslate")
async def deepltranslate(
    request: SimpleTranslationRequest,
    current_user = Depends(get_current_app),
    deepl_service: DeepLTranslationService = Depends(get_deepl_translation_service)
):
    """
    Translate text using DeepL API.
    Uses source/target languages, context, and glossary from service configuration.
    """
    try:
        # Call translate_deepl - uses service defaults for source_lang, target_lang, context, glossary_id
        result = deepl_service.translate_deepl(request.text)

        return {
            "status": "success",
            "original_text": request.text,
            "translated_text": result["translated_text"],
            "debug": result["debug"],
            "processed_by": current_user.get("sub", "unknown")
        }

    except Exception as e:
        logger.error(f"DeepL translation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate text: {str(e)}"
        )


@router.post("/summarizeScript")
async def summarize_script(
    request: SummarizeScriptRequest,
    current_user = Depends(get_current_app),
    blob_service: BlobStorageService = Depends(get_blob_storage_service),
    summarize_service: SummarizeLangChainService = Depends(get_summarize_service)
):
    """
    Summarize a script file.

    Args:
        request: Contains blob_path
        current_user: Authenticated user
        blob_service: Blob storage service for file access
        summarize_service: Summarization service

    Returns:
        Summarization result
    """
    try:
        # Convert request to dictionary format for the summarization service
        request_data = {
            "blob_path": request.blob_path
        }

        # Use the injected summarization service to summarize the script
        result = summarize_service.summarize_script(request_data, blob_service)

        return {
            "status": "success",
            "summarize_result": {
                "summarized_text": result.summarized_text,
                "action_items": result.action_items,
                "blob_path": request.blob_path,
                "processed_by": current_user.get("sub", "unknown")
            }
        }

    except Exception as e:
        logger.error(f"Script summarization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize script: {str(e)}"
        )


@router.post("/TranslateChain")
async def translate_chain(
    request: TranslateChainRequest,
    current_user = Depends(get_current_app),
    translation_chain_service: TranslationService = Depends(get_translation_chain_service)
):
    """
    Translate a script file using the complete translation chain.

    This endpoint performs a 4-step translation process:
    1. Read text from blob storage
    2. Correct grammar and punctuation
    3. Translate to target language with glossary support
    4. Quality check and adjust translation

    Args:
        request: Contains blob_path (can be full URL or relative path),
                 container_name (optional if blob_path is URL),
                 input_language, output_language, and optional glossary
        current_user: Authenticated user
        translation_chain_service: Translation chain service for processing

    Returns:
        Translation result with translated text and sentence counts

    Examples:
        Using separate container and path:
        {
            "container_name": "mycontainer",
            "blob_path": "folder/script.txt",
            "input_language": "EN",
            "output_language": "FR"
        }

        Using full blob URL:
        {
            "blob_path": "https://account.blob.core.windows.net/mycontainer/folder/script.txt",
            "input_language": "EN",
            "output_language": "FR"
        }
    """
    try:
        # Call the translate_from_blob method from TranslationService
        result: ChainTranslationResult = translation_chain_service.translate_from_blob(
            container_name=request.container_name,
            blob_path=request.blob_path,
            input_language=request.input_language,
            output_language=request.output_language,
            glossary=request.glossary
        )

        return {
            "status": "success",
            "translation_result": {
                "translated_text": result.translatedtext,
                "original_sentence_count": result.OriginalSentenceCount,
                "translation_sentence_count": result.translationSentenceCount,
                "grammar_correction_time_seconds": result.grammar_correction_time_seconds,
                "translation_time_seconds": result.translation_time_seconds,
                "adjustment_time_seconds": result.adjustment_time_seconds,
                "total_time_seconds": result.total_time_seconds,
                "grammar_llm_provider": result.grammar_llm_provider,
                "grammar_llm_model": result.grammar_llm_model,
                "translation_llm_provider": result.translation_llm_provider,
                "translation_llm_model": result.translation_llm_model,
                "adjustment_llm_provider": result.adjustment_llm_provider,
                "adjustment_llm_model": result.adjustment_llm_model,
                "container_name": request.container_name,
                "blob_path": request.blob_path,
                "input_language": request.input_language,
                "output_language": request.output_language,
                "glossary_entries": len(request.glossary) if request.glossary else 0,
                "processed_by": current_user.get("sub", "unknown")
            }
        }

    except ValueError as e:
        # Handle invalid blob path format errors
        logger.error(f"Invalid blob path format: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Translation chain failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate using chain: {str(e)}"
        )


# ============================================================================
# Workflow Translation Endpoints
# ============================================================================

@router.post("/workflow/complete")
async def workflow_complete_translation(
    request: WorkflowTranslationRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Execute the complete translation workflow:
    1. Load and analyze original text
    2. Correct grammar and split into sentences
    3. Translate using DeepL

    Args:
        request: Contains text, source/target languages, and grammar correction flag
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        Complete workflow results with all steps
    """
    try:
        result = workflow_service.execute_complete_workflow(
            original_text=request.text,
            language=request.source_language,
            target_language=request.target_language,
            correct_grammar=request.correct_grammar
        )

        return {
            "status": "success",
            "workflow_result": {
                "original": {
                    "text": result.step1_original.original_text,
                    "char_count": result.step1_original.char_count,
                    "word_count": result.step1_original.word_count
                },
                "corrected_and_split": {
                    "corrected_text": result.step2_corrected.corrected_text,
                    "sentences": result.step2_corrected.sentences,
                    "sentence_count": result.step2_corrected.sentence_count,
                    "grammar_correction_applied": result.step2_corrected.grammar_correction_applied
                },
                "translated": {
                    "translated_text": result.step3_translated.translated_text,
                    "source_language": result.step3_translated.source_language,
                    "target_language": result.step3_translated.target_language,
                    "translated_sentence_count": result.step3_translated.translated_sentence_count
                },
                "workflow_completed": result.workflow_completed,
                "processed_by": current_user.get("sub", "unknown")
            }
        }

    except Exception as e:
        logger.error(f"Workflow translation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.post("/workflow/step1/load")
async def workflow_step1_load_text(
    request: WorkflowTranslationRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Step 1: Load and analyze text

    Args:
        request: Contains the text to load
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        Original text with character and word counts
    """
    try:
        result = workflow_service.step1_load_text(request.text)

        return {
            "status": "success",
            "result": {
                "original_text": result.original_text,
                "char_count": result.char_count,
                "word_count": result.word_count
            }
        }

    except Exception as e:
        logger.error(f"Step 1 failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load text: {str(e)}"
        )


@router.post("/workflow/step2/correct-and-split")
async def workflow_step2_correct_and_split(
    request: WorkflowTranslationRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Step 2: Correct grammar and split into sentences

    Args:
        request: Contains text, language, and grammar correction flag
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        Corrected text and sentence list
    """
    try:
        result = workflow_service.step2_correct_and_split(
            text=request.text,
            language=request.source_language,
            correct_grammar=request.correct_grammar
        )

        return {
            "status": "success",
            "result": {
                "corrected_text": result.corrected_text,
                "sentences": result.sentences,
                "sentence_count": result.sentence_count,
                "grammar_correction_applied": result.grammar_correction_applied
            }
        }

    except Exception as e:
        logger.error(f"Step 2 failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to correct and split text: {str(e)}"
        )


@router.post("/workflow/step3/translate")
async def workflow_step3_translate(
    request: WorkflowTranslationRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Step 3: Translate text using DeepL

    Args:
        request: Contains text and target language
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        Translated text
    """
    try:
        result = workflow_service.step3_translate(
            text=request.text,
            target_language=request.target_language
        )

        return {
            "status": "success",
            "result": {
                "translated_text": result.translated_text,
                "source_language": result.source_language,
                "target_language": result.target_language,
                "translated_sentence_count": result.translated_sentence_count
            }
        }

    except Exception as e:
        logger.error(f"Step 3 failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate text: {str(e)}"
        )


@router.post("/workflow/save-file")
async def workflow_save_file(
    request: SaveTextRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Save text to a file

    Args:
        request: Contains text and file path
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        Save status and file path
    """
    try:
        result = workflow_service.save_text_to_file(
            text=request.text,
            file_path=request.file_path
        )

        return result

    except Exception as e:
        logger.error(f"Save file failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


@router.post("/workflow/load-file")
async def workflow_load_file(
    request: LoadTextRequest,
    current_user = Depends(get_current_app),
    workflow_service: WorkflowTranslationService = Depends(get_workflow_translation_service)
):
    """
    Load text from a file

    Args:
        request: Contains file path
        current_user: Authenticated user
        workflow_service: Workflow translation service

    Returns:
        File content and metadata
    """
    try:
        result = workflow_service.load_text_from_file(request.file_path)

        return result

    except Exception as e:
        logger.error(f"Load file failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load file: {str(e)}"
        )