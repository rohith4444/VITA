from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from uuid import UUID

from chat_api.config import settings
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.auth.jwt_handler")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to payload
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.TOKEN_SECRET_KEY, 
        algorithm=settings.TOKEN_ALGORITHM
    )
    
    logger.debug(f"Created access token for user ID: {data.get('sub', 'unknown')}")
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        str: Encoded JWT refresh token
    """
    refresh_expires = timedelta(days=7)  # Refresh tokens last 7 days
    return create_access_token(data, expires_delta=refresh_expires)

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and extract its payload.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Dict[str, Any]: Token payload
        
    Raises:
        JWTError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.TOKEN_SECRET_KEY, 
            algorithms=[settings.TOKEN_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise