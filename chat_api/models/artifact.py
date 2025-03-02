from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from chat_api.database import Base
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.artifact")

class ArtifactModel(Base):
    """SQLAlchemy model for artifacts."""
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"))
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    message = relationship("MessageModel", back_populates="artifacts")
    
    def __repr__(self):
        return f"<Artifact {self.id}: {self.title}>"