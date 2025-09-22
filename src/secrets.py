import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

KEY_VAULT_URL="https://aifastapi.vault.azure.net"

credential = DefaultAzureCredential()
_secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

def get_secret(secret_name: str) -> str:
    """
    Retrieves a secret from Azure Key Vault by name.
    """
    try:
        logger.info(f"Attempting to fetch secret '{secret_name}' from Key Vault: {KEY_VAULT_URL}")
        secret = _secret_client.get_secret(secret_name)
        logger.info(f"Successfully retrieved secret '{secret_name}' from Key Vault")
        return "name: " + secret.name + " value: " + secret.value
    except Exception as e:
        logger.error(f"Error fetching secret '{secret_name}' from Key Vault: {e}")
        # Check if it's available as an environment variable
        env_value = os.getenv(secret_name)
        if env_value:
            logger.warning(f"Found '{secret_name}' in environment variables instead")
            return env_value
        return None