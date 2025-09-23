import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AzureKeyVaultConfig:
    def __init__(self, vault_url: Optional[str] = None):
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        if not self.vault_url:
            raise ValueError("Azure Key Vault URL must be provided or set in AZURE_KEY_VAULT_URL environment variable")
        
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
    
    def get_secret(self, secret_name: str) -> str:
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")
            raise
    
    def get_jwt_secret(self) -> str:
        return self.get_secret("jwt-secret-key")
    
    def get_jwt_algorithm(self) -> str:
        try:
            return self.get_secret("jwt-algorithm")
        except Exception:
            logger.info("JWT algorithm not found in Key Vault, using default HS256")
            return "HS256"
    
    def get_storage_account_url(self) -> str:
        return self.get_secret("azure-storage-account-url")