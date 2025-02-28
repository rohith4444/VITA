from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.artifact")


class ArtifactType(str, Enum):
    """Enum for possible artifact types."""
    CODE = "application/vnd.ant.code"
    MARKDOWN = "text/markdown"
    HTML = "text/html"
    SVG = "image/svg+xml"
    MERMAID = "application/vnd.ant.mermaid"
    REACT = "application/vnd.ant.react"


class Artifact(BaseModel):
    """Model representing an artifact."""
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    message_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    type: ArtifactType
    title: str
    content: str
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("artifact_id")
    def validate_artifact_id(cls, v):
        """Validate the artifact ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid artifact ID")
            raise ValueError("artifact_id must be a non-empty string")
        return v
    
    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate the session ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid session ID")
            raise ValueError("session_id must be a non-empty string")
        return v
    
    @validator("message_id")
    def validate_message_id(cls, v):
        """Validate the message ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid message ID")
            raise ValueError("message_id must be a non-empty string")
        return v
    
    @validator("updated_at")
    def validate_updated_at(cls, v, values):
        """Ensure updated_at is not earlier than created_at."""
        if 'created_at' in values and v < values['created_at']:
            logger.error("updated_at cannot be earlier than created_at")
            raise ValueError("updated_at cannot be earlier than created_at")
        return v
    
    @validator("content")
    def validate_content(cls, v):
        """Validate that content is not empty."""
        if not v or not isinstance(v, str):
            logger.error("Invalid artifact content")
            raise ValueError("content must be a non-empty string")
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "artifact_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "987e6543-e21b-43d3-b654-426614174000",
                "message_id": "345e6789-e89b-12d3-a456-426614174000",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "type": "application/vnd.ant.code",
                "title": "Database Schema",
                "content": "CREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  name VARCHAR(255) NOT NULL,\n  email VARCHAR(255) UNIQUE NOT NULL\n);",
                "language": "sql",
                "metadata": {}
            }
        }


class ArtifactCreate(BaseModel):
    """Model for creating a new artifact."""
    message_id: str
    type: ArtifactType
    title: str
    content: str
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "message_id": "345e6789-e89b-12d3-a456-426614174000",
                "type": "application/vnd.ant.code",
                "title": "Database Schema",
                "content": "CREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  name VARCHAR(255) NOT NULL,\n  email VARCHAR(255) UNIQUE NOT NULL\n);",
                "language": "sql",
                "metadata": {}
            }
        }


class ArtifactUpdate(BaseModel):
    """Model for updating an existing artifact."""
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "title": "Updated Database Schema",
                "content": "CREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  name VARCHAR(255) NOT NULL,\n  email VARCHAR(255) UNIQUE NOT NULL,\n  created_at TIMESTAMP DEFAULT NOW()\n);",
                "language": "sql",
                "metadata": {"version": "2"}
            }
        }