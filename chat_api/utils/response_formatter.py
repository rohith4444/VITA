from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel
from fastapi import HTTPException, status
from core.logging.logger import setup_logger
from chat_api.models.response import (
    APIResponse, 
    MessageResponse, 
    SessionResponse, 
    MessageListResponse,
    ErrorResponse, 
    ResponseStatus, 
    ErrorDetail
)
from chat_api.models.session import Session
from chat_api.models.message import Message

# Initialize logger
logger = setup_logger("chat_api.utils.response_formatter")


def format_session_response(session: Session) -> SessionResponse:
    """
    Format a session object into a session response.
    
    Args:
        session: Session object
        
    Returns:
        SessionResponse: Formatted session response
    """
    logger.debug(f"Formatting session response for session: {session.session_id}")
    
    return SessionResponse(
        status=ResponseStatus.SUCCESS,
        timestamp=datetime.utcnow(),
        data=session.dict(),
        error=None
    )


def format_message_response(message: Message) -> MessageResponse:
    """
    Format a message object into a message response.
    
    Args:
        message: Message object
        
    Returns:
        MessageResponse: Formatted message response
    """
    logger.debug(f"Formatting message response for message: {message.message_id}")
    
    return MessageResponse(
        status=ResponseStatus.SUCCESS,
        timestamp=datetime.utcnow(),
        data=message.dict(),
        error=None
    )


def format_message_list_response(messages: List[Message], total: int) -> MessageListResponse:
    """
    Format a list of messages into a message list response.
    
    Args:
        messages: List of message objects
        total: Total number of messages
        
    Returns:
        MessageListResponse: Formatted message list response
    """
    logger.debug(f"Formatting message list response with {len(messages)} messages")
    
    return MessageListResponse(
        status=ResponseStatus.SUCCESS,
        timestamp=datetime.utcnow(),
        data={
            "messages": [message.dict() for message in messages],
            "total": total
        },
        error=None
    )


def format_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    Format an error response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        details: Optional error details
        
    Returns:
        ErrorResponse: Formatted error response
    """
    logger.error(f"Formatting error response: {error_code} - {message}")
    
    error_detail = ErrorDetail(
        code=error_code,
        message=message,
        details=details
    )
    
    return ErrorResponse(
        status=ResponseStatus.ERROR,
        timestamp=datetime.utcnow(),
        error=error_detail
    )


def format_success_response(data: Dict[str, Any]) -> APIResponse:
    """
    Format a generic success response.
    
    Args:
        data: Response data
        
    Returns:
        APIResponse: Formatted success response
    """
    logger.debug("Formatting generic success response")
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        timestamp=datetime.utcnow(),
        data=data,
        error=None
    )


def raise_http_exception(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Raise an HTTP exception with a formatted error response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        details: Optional error details
        
    Raises:
        HTTPException: FastAPI HTTP exception with formatted error response
    """
    logger.error(f"Raising HTTP exception: {error_code} - {message}")
    
    error_response = format_error_response(
        error_code=error_code,
        message=message,
        status_code=status_code,
        details=details
    )
    
    raise HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )


def handle_exception(
    exception: Exception,
    error_code: str = "internal_error",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> ErrorResponse:
    """
    Handle an exception and format an error response.
    
    Args:
        exception: The exception to handle
        error_code: Error code
        status_code: HTTP status code
        
    Returns:
        ErrorResponse: Formatted error response
    """
    logger.error(f"Handling exception: {str(exception)}", exc_info=True)
    
    # Determine appropriate error message
    error_message = str(exception)
    if not error_message or status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        error_message = "An internal server error occurred"
    
    # Include exception type in details
    details = {
        "exception_type": exception.__class__.__name__
    }
    
    return format_error_response(
        error_code=error_code,
        message=error_message,
        status_code=status_code,
        details=details
    )