from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import JWTHandler
from .azure_config import AzureKeyVaultConfig
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Initialize Azure Key Vault and JWT handler
try:
    azure_config = AzureKeyVaultConfig()
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