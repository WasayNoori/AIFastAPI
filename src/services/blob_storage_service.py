import os
from typing import Optional
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential, AzureCliCredential
from ..auth.azure_config import AzureKeyVaultConfig
import logging

logger = logging.getLogger(__name__)


class BlobStorageService:
    def __init__(self, account_url: Optional[str] = None):
        if account_url:
            self.account_url = account_url
        else:
            try:
                azure_config = AzureKeyVaultConfig()
                self.account_url = azure_config.get_storage_account_url()
                logger.info("Successfully retrieved storage account URL from Key Vault")
            except Exception as e:
                self.account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
                if not self.account_url:
                    logger.error(f"Failed to get storage URL from Key Vault: {str(e)}")
                    raise ValueError("Azure Storage Account URL must be provided via Key Vault secret 'azure-storage-account-url' or AZURE_STORAGE_ACCOUNT_URL environment variable")
                logger.warning("Using fallback environment variable for storage account URL")
        
        # Try AzureCliCredential first for local development
        try:
            self.credential = AzureCliCredential()
            logger.info("Using AzureCliCredential for blob storage authentication")
        except Exception as e:
            logger.warning(f"AzureCliCredential failed, falling back to DefaultAzureCredential: {str(e)}")
            self.credential = DefaultAzureCredential(logging_enable=True)
        logger.info(f"Initializing BlobServiceClient with account URL: {self.account_url}")
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        )
    
    def read_text_from_blob(self, container_name: str, blob_path: str) -> str:
        try:
            logger.info(f"DEBUG: Attempting to read - Container: '{container_name}', Blob: '{blob_path}'")
            
            # First check what blobs actually exist
            container_client = self.blob_service_client.get_container_client(container_name)
            logger.info("DEBUG: Available blobs in container:")
            blob_names = []
            for blob in container_client.list_blobs():
                blob_names.append(blob.name)
                logger.info(f"  Found blob: '{blob.name}'")
            
            # Check if our target blob matches any of the found blobs
            if blob_path not in blob_names:
                logger.error(f"DEBUG: Blob '{blob_path}' not found in available blobs")
                # Try to find similar names
                for name in blob_names:
                    if blob_path.lower() in name.lower() or name.lower() in blob_path.lower():
                        logger.info(f"DEBUG: Similar blob found: '{name}'")
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_path
            )
            
            blob_data = blob_client.download_blob()
            text_content = blob_data.readall().decode('utf-8')
            
            logger.info(f"Successfully read text from blob: {container_name}/{blob_path}")
            return text_content
            
        except Exception as e:
            logger.error(f"Failed to read blob {container_name}/{blob_path}: {str(e)}")
            raise
    
    def get_blob_info(self, container_name: str, blob_path: str) -> dict:
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_path
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "name": properties.name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type if properties.content_settings else None,
                "creation_time": properties.creation_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get blob info for {container_name}/{blob_path}: {str(e)}")
            raise
    
    def analyze_text_document(self, container_name: str, blob_path: str) -> dict:
        try:
            text_content = self.read_text_from_blob(container_name, blob_path)
            blob_info = self.get_blob_info(container_name, blob_path)
            
            word_count = len(text_content.split())
            character_count = len(text_content)
            line_count = len(text_content.splitlines())
            
            return {
                "blob_info": blob_info,
                "text_analysis": {
                    "word_count": word_count,
                    "character_count": character_count,
                    "line_count": line_count
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze text document {container_name}/{blob_path}: {str(e)}")
            raise
    


    def list_blobs_in_container(self, container_name: str) -> dict:
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            
            blobs = []
            for blob in container_client.list_blobs():
                blob_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None
                }
                blobs.append(blob_info)
            
            logger.info(f"Successfully listed {len(blobs)} blobs in container: {container_name}")
            
            return {
                "container_name": container_name,
                "blob_count": len(blobs),
                "blobs": blobs
            }
            
        except Exception as e:
            logger.error(f"Failed to list blobs in container {container_name}: {str(e)}")
            raise