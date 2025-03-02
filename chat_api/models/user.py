from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from chat_api.database import Base
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.user")

class UserModel(Base):
    """SQLAlchemy model for users."""
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("MessageModel", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"