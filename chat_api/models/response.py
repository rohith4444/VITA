from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.models.response")


class ResponseStatus(str, Enum):
    """Enum for API response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ErrorDetail(BaseModel):
    """Model for detailed error information."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    """Base model for all API responses."""
    status: ResponseStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-01-01T00:00:00",
                "data": {"message": "Operation completed successfully"},
                "error": None
            }
        }


class SessionResponse(APIResponse):
    """Response model specific to session operations."""
    data: Dict[str, Any]

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-01-01T00:00:00",
                "data": {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "user123",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                    "status": "active",
                    "message_count": 0
                },
                "error": None
            }
        }


class MessageResponse(APIResponse):
    """Response model specific to message operations."""
    data: Dict[str, Any]

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-01-01T00:00:00",
                "data": {
                    "message_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": "987e6543-e21b-43d3-b654-426614174000",
                    "created_at": "2023-01-01T00:00:00",
                    "role": "assistant",
                    "type": "text",
                    "content": "I can help you design a database schema. What kind of application are you building?",
                    "files": [],
                    "artifacts": []
                },
                "error": None
            }
        }


class MessageListResponse(APIResponse):
    """Response model for listing multiple messages."""
    data: Dict[str, Any]

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-01-01T00:00:00",
                "data": {
                    "messages": [
                        {
                            "message_id": "123e4567-e89b-12d3-a456-426614174000",
                            "session_id": "987e6543-e21b-43d3-b654-426614174000",
                            "created_at": "2023-01-01T00:00:00",
                            "role": "user",
                            "type": "text",
                            "content": "Can you help me design a database schema?",
                            "files": [],
                            "artifacts": []
                        },
                        {
                            "message_id": "234e5678-e89b-12d3-a456-426614174000",
                            "session_id": "987e6543-e21b-43d3-b654-426614174000",
                            "created_at": "2023-01-01T00:01:00",
                            "role": "assistant",
                            "type": "text",
                            "content": "I can help you design a database schema. What kind of application are you building?",
                            "files": [],
                            "artifacts": []
                        }
                    ],
                    "total": 2
                },
                "error": None
            }
        }


class ErrorResponse(APIResponse):
    """Response model for error situations."""
    status: ResponseStatus = ResponseStatus.ERROR
    error: ErrorDetail

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "error",
                "timestamp": "2023-01-01T00:00:00",
                "data": None,
                "error": {
                    "code": "not_found",
                    "message": "The requested resource was not found",
                    "details": {
                        "resource_type": "session",
                        "resource_id": "123e4567-e89b-12d3-a456-426614174000"
                    }
                }
            }
        }