# chat_api/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID

from chat_api.database import get_db
from chat_api.schemas.user_schemas import UserCreate, UserResponse, Token, UserUpdate
from chat_api.services.auth_service import AuthService
from chat_api.auth.dependencies import get_current_user, get_current_user_id
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.routes.auth_routes")

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])

# Dependency for AuthService
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db_session=db)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    """
    try:
        user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        logger.info(f"User registered successfully: {user.username}")
        return user
    except ValueError as e:
        logger.warning(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and provide access token.
    """
    user = auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = auth_service.create_tokens(user_id=user.id)
    logger.info(f"Login successful for user: {user.username}")
    
    return tokens

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user.
    """
    logger.info(f"User profile retrieved: {current_user.username}")
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user's information.
    """
    try:
        updated_user = auth_service.update_user(
            user_id=current_user_id,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        if not updated_user:
            logger.error(f"User not found during update: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User updated successfully: {updated_user.username}")
        return updated_user
    except ValueError as e:
        logger.warning(f"User update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during user update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )