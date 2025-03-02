from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from uuid import UUID

from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.schemas.user")

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str
    email: EmailStr
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            logger.warning(f"Invalid username (too short): {v}")
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            logger.warning(f"Invalid username (not alphanumeric): {v}")
            raise ValueError('Username must be alphanumeric')
        return v

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            logger.warning("Password too short")
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """Schema for user information from database."""
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UserResponse(UserBase):
    """Schema for user response to clients."""
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token payload."""
    user_id: Optional[str] = None