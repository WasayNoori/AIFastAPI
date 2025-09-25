import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from typing import Dict, Any, Optional


class JWTHandler: #this class is used to handle the JWT token
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            decoded_token = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def create_token(self, payload: Dict[str, Any]) -> str:
        """
        Create a JWT token with the given payload.
        """
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token creation failed: {str(e)}"
            )
    
    def verify_token(self, token: str) -> bool:
        try:
            self.decode_token(token)
            return True
        except HTTPException:
            return False