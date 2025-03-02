from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.schemas.session")


class SessionStatus(str, Enum):
    """Enum for possible session statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"


class SessionType(str, Enum):
    """Enum for possible session types."""
    STANDARD = "standard"
    DEVELOPER = "developer"
    RESEARCH = "research"


class AgentType(str, Enum):
    """Enum for available agent types."""
    PROJECT_MANAGER = "project_manager"
    SOLUTION_ARCHITECT = "solution_architect"
    FULL_STACK_DEVELOPER = "full_stack_developer"
    QA_TEST = "qa_test"


class UserSettings(BaseModel):
    """Model for user-specific settings within a session."""
    preferred_language: Optional[str] = "en"
    temperature: float = 0.3
    verbose_mode: bool = False
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """Model representing a chat session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    session_type: SessionType = SessionType.STANDARD
    primary_agent: AgentType = AgentType.PROJECT_MANAGER
    message_count: int = 0
    settings: UserSettings = Field(default_factory=UserSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate the session ID format."""
        if not v or not isinstance(v, str):
            logger.error("Invalid session ID")
            raise ValueError("session_id must be a non-empty string")
        return v

    @validator("updated_at")
    def validate_updated_at(cls, v, values):
        """Ensure updated_at is not earlier than created_at."""
        if 'created_at' in values and v < values['created_at']:
            logger.error("updated_at cannot be earlier than created_at")
            raise ValueError("updated_at cannot be earlier than created_at")
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:15:00",
                "status": "active",
                "session_type": "standard",
                "primary_agent": "project_manager",
                "message_count": 0,
                "settings": {
                    "preferred_language": "en",
                    "temperature": 0.3,
                    "verbose_mode": False,
                    "custom_settings": {}
                },
                "metadata": {}
            }
        }


class SessionCreate(BaseModel):
    """Model for creating a new session."""
    title: Optional[str] = "New Chat"
    session_type: SessionType = SessionType.STANDARD
    primary_agent: AgentType = AgentType.PROJECT_MANAGER
    settings: Optional[UserSettings] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "title": "New Project Discussion",
                "session_type": "developer",
                "primary_agent": "solution_architect",
                "settings": {
                    "preferred_language": "en",
                    "temperature": 0.5,
                    "verbose_mode": True
                },
                "metadata": {"project_id": "12345"}
            }
        }


class SessionUpdate(BaseModel):
    """Model for session updates."""
    title: Optional[str] = None
    status: Optional[SessionStatus] = None
    primary_agent: Optional[AgentType] = None
    settings: Optional[UserSettings] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "title": "Updated Project Discussion",
                "status": "inactive",
                "primary_agent": "solution_architect",
                "settings": {
                    "preferred_language": "fr",
                    "temperature": 0.5,
                    "verbose_mode": True,
                    "custom_settings": {"theme": "dark"}
                },
                "metadata": {"last_topic": "api_design"}
            }
        }