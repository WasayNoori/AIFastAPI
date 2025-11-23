from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import JWTHandler
from ..services.azure_config import AzureKeyVaultConfig
from ..services.blob_storage_service import BlobStorageService
from ..translation.translationLangChain import TranslationLangChainService
from ..translation.summarizeLangChain import SummarizeLangChainService
from ..translation.deepltranslation import TranslationLangChainService as DeepLTranslationService
from ..translation.translator import TranslationService
from ..translation.workflow_translation_service import WorkflowTranslationService
from ..Quizzes.quiz_service import QuizGenerationService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Initialize Azure Key Vault and JWT handler
try:
    azure_config = AzureKeyVaultConfig("https://aifastapi.vault.azure.net")
    jwt_secret = azure_config.get_jwt_secret()
    jwt_algorithm = azure_config.get_jwt_algorithm()
    jwt_handler = JWTHandler(jwt_secret, jwt_algorithm)
except Exception as e:
    logger.error(f"Failed to initialize authentication: {str(e)}")
    raise


def get_current_app(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to validate JWT token and extract app information.
    Use this as a dependency in your protected endpoints.
    """
    token = credentials.credentials
    
    try:
        payload = jwt_handler.decode_token(token)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def get_blob_storage_service() -> BlobStorageService:
    """
    Dependency to provide BlobStorageService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return BlobStorageService()
    except Exception as e:
        logger.error(f"Failed to initialize BlobStorageService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blob Storage service is not available"
        )


def get_translation_service() -> TranslationLangChainService:
    """
    Dependency to provide TranslationLangChainService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return TranslationLangChainService(azure_config)
    except Exception as e:
        logger.error(f"Failed to initialize TranslationLangChainService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation service is not available"
        )


def get_summarize_service() -> SummarizeLangChainService:
    """
    Dependency to provide SummarizeLangChainService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return SummarizeLangChainService()
    except Exception as e:
        logger.error(f"Failed to initialize SummarizeLangChainService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summarization service is not available"
        )


def get_deepl_translation_service() -> DeepLTranslationService:
    """
    Dependency to provide DeepL TranslationLangChainService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return DeepLTranslationService(azure_config)
    except Exception as e:
        logger.error(f"Failed to initialize DeepL TranslationService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DeepL Translation service is not available"
        )


def get_translation_chain_service() -> TranslationService:
    """
    Dependency to provide TranslationService instance (chain-based translation).
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return TranslationService(azure_config)
    except Exception as e:
        logger.error(f"Failed to initialize TranslationService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation chain service is not available"
        )


def get_azure_config() -> AzureKeyVaultConfig:
    """
    Dependency to provide AzureKeyVaultConfig instance.
    Returns the globally initialized azure_config.
    """
    return azure_config


def get_workflow_translation_service() -> WorkflowTranslationService:
    """
    Dependency to provide WorkflowTranslationService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return WorkflowTranslationService(azure_config)
    except Exception as e:
        logger.error(f"Failed to initialize WorkflowTranslationService: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workflow translation service is not available"
        )


def get_quiz_service() -> QuizGenerationService:
    """
    Dependency to provide QuizGenerationService instance.
    Creates a new instance on each request for better error handling and isolation.
    """
    try:
        return QuizGenerationService(azure_config)
    except Exception as e:
        logger.error(f"Failed to initialize QuizGenerationService: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation service is not available: {str(e)}"
        )