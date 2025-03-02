from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from uuid import UUID

from chat_api.auth.jwt_handler import verify_token
from chat_api.database import get_db
from chat_api.models.user import UserModel
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.auth.dependencies")

# OAuth2 scheme for token extraction from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    FastAPI dependency to get the current authenticated user.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        UserModel: Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            logger.warning("Token missing subject claim")
            raise credentials_exception
        
        # Get user from database
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if user is None:
            logger.warning(f"User not found for ID: {user_id}")
            raise credentials_exception
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        logger.debug(f"Successfully authenticated user: {user.username}")
        return user
        
    except JWTError:
        logger.error("JWT verification failed")
        raise credentials_exception

async def get_current_user_id(
    current_user: UserModel = Depends(get_current_user)
) -> UUID:
    """
    FastAPI dependency to get just the current user's ID.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UUID: Current user's ID
    """
    return current_user.id

async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    FastAPI dependency to verify the current user is an admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserModel: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user attempted admin action: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    logger.debug(f"Admin access granted for user: {current_user.username}")
    return current_user