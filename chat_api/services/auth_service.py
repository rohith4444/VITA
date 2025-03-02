# chat_api/services/auth_service.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID, uuid4

from chat_api.models.user import UserModel
from chat_api.auth.security import get_password_hash, verify_password
from chat_api.auth.jwt_handler import create_access_token, create_refresh_token
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.services.auth_service")

class AuthService:
    """Service for user authentication operations."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the auth service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """
        Get a user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            Optional[UserModel]: User if found, None otherwise
        """
        user = self.db.query(UserModel).filter(UserModel.username == username).first()
        
        if not user:
            logger.debug(f"User not found: {username}")
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email.
        
        Args:
            email: Email to look up
            
        Returns:
            Optional[UserModel]: User if found, None otherwise
        """
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        
        if not user:
            logger.debug(f"User not found for email: {email}")
        
        return user
    
    def create_user(self, username: str, email: str, password: str) -> UserModel:
        """
        Create a new user.
        
        Args:
            username: Username for the new user
            email: Email for the new user
            password: Plain text password
            
        Returns:
            UserModel: Created user
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username already exists
        if self.get_user_by_username(username):
            logger.warning(f"Username already exists: {username}")
            raise ValueError("Username already exists")
        
        # Check if email already exists
        if self.get_user_by_email(email):
            logger.warning(f"Email already exists: {email}")
            raise ValueError("Email already exists")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user
        user = UserModel(
            id=uuid4(),
            username=username,
            email=email,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User created: {username}")
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserModel]:
        """
        Authenticate a user by username and password.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            Optional[UserModel]: User if authentication succeeds, None otherwise
        """
        user = self.get_user_by_username(username)
        
        if not user:
            logger.warning(f"Authentication failed - user not found: {username}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed - invalid password for user: {username}")
            return None
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def create_tokens(self, user_id: UUID) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, str]: Access and refresh tokens
        """
        # Create token payload
        data = {"sub": str(user_id)}
        
        # Create tokens
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        logger.info(f"Tokens created for user: {user_id}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def update_user(self, user_id: UUID, username: Optional[str] = None, 
                  email: Optional[str] = None, password: Optional[str] = None) -> Optional[UserModel]:
        """
        Update user information.
        
        Args:
            user_id: ID of the user to update
            username: Optional new username
            email: Optional new email
            password: Optional new password
            
        Returns:
            Optional[UserModel]: Updated user if successful, None if user not found
            
        Raises:
            ValueError: If username or email already exists
        """
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if not user:
            logger.warning(f"Update failed - user not found: {user_id}")
            return None
        
        # Update username if provided
        if username and username != user.username:
            # Check if username already exists
            if self.get_user_by_username(username):
                logger.warning(f"Username already exists: {username}")
                raise ValueError("Username already exists")
            
            user.username = username
        
        # Update email if provided
        if email and email != user.email:
            # Check if email already exists
            if self.get_user_by_email(email):
                logger.warning(f"Email already exists: {email}")
                raise ValueError("Email already exists")
            
            user.email = email
        
        # Update password if provided
        if password:
            user.hashed_password = get_password_hash(password)
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User updated: {user_id}")
        return user