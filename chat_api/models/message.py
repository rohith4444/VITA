from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from chat_api.database import Base
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.message")

class MessageModel(Base):
    """SQLAlchemy model for messages."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)
    type = Column(String, nullable=False, default="text")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    parent_message_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    session = relationship("SessionModel", back_populates="messages")
    user = relationship("UserModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message {self.id}: {self.role}>"