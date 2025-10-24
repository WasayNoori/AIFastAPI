from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from src.auth.dependencies import get_current_app, get_blob_storage_service, get_translation_service, get_summarize_service, get_deepl_translation_service, get_translation_chain_service
from src.services.blob_storage_service import BlobStorageService
from src.translation.translationLangChain import TranslationLangChainService, TranslationResult
from src.translation.summarizeLangChain import SummarizeLangChainService, SummarizeResult
from src.translation.deepltranslation import TranslationLangChainService as DeepLTranslationService
from src.translation.Translator import TranslationService, TranslationResult as ChainTranslationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])

class TranslateScriptRequest(BaseModel):
    blob_path: str
    glossary: Dict[str, str]


class SummarizeScriptRequest(BaseModel):
    blob_path: str


class SimpleTranslationRequest(BaseModel):
    text: str
    target_language: str = "FR"  # Default to French


class TranslateChainRequest(BaseModel):
    container_name: Optional[str] = None  # Optional if blob_path is a full URL
    blob_path: str  # Either relative path or full blob URL
    input_language: str
    output_language: str
    glossary: Optional[Dict[str, str]] = None  # Optional glossary


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


@router.post("/translationtest")
async def translation_test(
    request: SimpleTranslationRequest,
    current_user = Depends(get_current_app),
    deepl_service: DeepLTranslationService = Depends(get_deepl_translation_service)
):
    """
    Test endpoint to translate a simple phrase using DeepL API.
    """
    try:
        # Call the translate_deepl method from DeepL service
        result = deepl_service.translate_deepl(request.text, request.target_language)

        return {
            "status": "success",
            "original_text": request.text,
            "target_language": request.target_language,
            "translated_text": result,
            "processed_by": current_user.get("sub", "unknown")
        }
        
    except Exception as e:
        logger.error(f"DeepL translation test failed: {str(e)}")
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