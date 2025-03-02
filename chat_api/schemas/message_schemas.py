from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, validator, root_validator
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.schemas.message")


class MessageRole(str, Enum):
    """Enum for possible message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Enum for possible message types."""
    TEXT = "text"
    FILE = "file"
    ARTIFACT = "artifact"
    ERROR = "error"
    NOTIFICATION = "notification"


class FileReference(BaseModel):
    """Model for file references within messages."""
    file_id: str
    filename: str
    mime_type: str
    size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactReference(BaseModel):
    """Model for artifact references within messages."""
    artifact_id: str
    title: str
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content_preview: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """Model representing a chat message."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    role: MessageRole
    type: MessageType = MessageType.TEXT
    content: str
    files: List[FileReference] = Field(default_factory=list)
    artifacts: List[ArtifactReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[str] = None
    
    @validator("message_id")
    def validate_message_id(cls, v):
        """Validate the message ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid message ID")
            raise ValueError("message_id must be a non-empty string")
        return v
    
    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate the session ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid session ID")
            raise ValueError("session_id must be a non-empty string")
        return v
    
    @root_validator
    def validate_file_consistency(cls, values):
        """Ensure file references are present for file message types."""
        message_type = values.get('type')
        files = values.get('files', [])
        
        if message_type == MessageType.FILE and not files:
            logger.error("File message type requires file references")
            raise ValueError("File message must include at least one file reference")
        
        return values
    
    @root_validator
    def validate_artifact_consistency(cls, values):
        """Ensure artifact references are present for artifact message types."""
        message_type = values.get('type')
        artifacts = values.get('artifacts', [])
        
        if message_type == MessageType.ARTIFACT and not artifacts:
            logger.error("Artifact message type requires artifact references")
            raise ValueError("Artifact message must include at least one artifact reference")
        
        return values

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "987e6543-e21b-43d3-b654-426614174000",
                "created_at": "2023-01-01T00:00:00",
                "role": "user",
                "type": "text",
                "content": "Can you help me design a database schema?",
                "files": [],
                "artifacts": [],
                "metadata": {},
                "parent_message_id": None
            }
        }


class MessageCreate(BaseModel):
    """Model for creating a new message."""
    content: str
    role: MessageRole = MessageRole.USER
    type: MessageType = MessageType.TEXT
    files: List[str] = Field(default_factory=list)  # List of file IDs
    parent_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "content": "Can you help me design a database schema?",
                "role": "user",
                "type": "text",
                "files": [],
                "parent_message_id": None,
                "metadata": {}
            }
        }


class ResponseCreate(BaseModel):
    """Model for creating an assistant response."""
    content: str
    type: MessageType = MessageType.TEXT
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "content": "I'd be happy to help you design a database schema. What type of application are you building?",
                "type": "text",
                "artifacts": [],
                "metadata": {"response_type": "question"}
            }
        }