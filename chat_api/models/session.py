from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, UUID, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from chat_api.database import Base
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.session")

class SessionModel(Base):
    """SQLAlchemy model for chat sessions."""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False, default="New Chat")
    status = Column(String, nullable=False, default="active")
    session_type = Column(String, nullable=False, default="standard")
    primary_agent = Column(String, nullable=False, default="project_manager")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)
    settings = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session {self.id}: {self.title}>"