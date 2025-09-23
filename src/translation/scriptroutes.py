from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
from src.auth.dependencies import get_current_app, get_blob_storage_service, get_translation_service
from src.services.blob_storage_service import BlobStorageService
from src.translation.translationLangChain import TranslationLangChainService, TranslationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["translation"])

class TranslateScriptRequest(BaseModel):
    blob_path: str
    glossary: Dict[str, str]


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
