from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re
import uuid
from pydantic import ValidationError
from core.logging.logger import setup_logger
from chat_api.models.session import SessionStatus, SessionType, AgentType
from chat_api.models.message import MessageRole, MessageType
from chat_api.config import settings

# Initialize logger
logger = setup_logger("chat_api.utils.validators")

def validate_session_id(session_id: str) -> bool:
    """
    Validate a session ID format.
    
    Args:
        session_id: The session ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not session_id or not isinstance(session_id, str):
        logger.error("Invalid session ID: empty or not a string")
        return False
    
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(session_id)
        return True
    except ValueError:
        logger.error(f"Invalid session ID format: {session_id}")
        return False

def validate_message_id(message_id: str) -> bool:
    """
    Validate a message ID format.
    
    Args:
        message_id: The message ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not message_id or not isinstance(message_id, str):
        logger.error("Invalid message ID: empty or not a string")
        return False
    
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(message_id)
        return True
    except ValueError:
        logger.error(f"Invalid message ID format: {message_id}")
        return False

def validate_agent_type(agent_type: str) -> bool:
    """
    Validate that an agent type is supported.
    
    Args:
        agent_type: The agent type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        AgentType(agent_type)
        return True
    except ValueError:
        logger.error(f"Invalid agent type: {agent_type}")
        return False

def validate_session_status(status: str) -> bool:
    """
    Validate that a session status is valid.
    
    Args:
        status: The status to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        SessionStatus(status)
        return True
    except ValueError:
        logger.error(f"Invalid session status: {status}")
        return False

def validate_message_role(role: str) -> bool:
    """
    Validate that a message role is valid.
    
    Args:
        role: The role to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        MessageRole(role)
        return True
    except ValueError:
        logger.error(f"Invalid message role: {role}")
        return False

def validate_message_type(message_type: str) -> bool:
    """
    Validate that a message type is valid.
    
    Args:
        message_type: The message type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        MessageType(message_type)
        return True
    except ValueError:
        logger.error(f"Invalid message type: {message_type}")
        return False

def validate_message_content(content: str, message_type: str) -> bool:
    """
    Validate message content based on message type.
    
    Args:
        content: The message content to validate
        message_type: The type of message
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not content or not isinstance(content, str):
        logger.error("Invalid message content: empty or not a string")
        return False
    
    # Different validation rules based on message type
    if message_type == MessageType.TEXT.value:
        # Basic validation for text messages
        if len(content) > settings.MAX_MESSAGE_LENGTH:
            logger.error(f"Message content exceeds maximum length of {settings.MAX_MESSAGE_LENGTH}")
            return False
    elif message_type == MessageType.FILE.value:
        # File message validation could be more complex
        pass
    elif message_type == MessageType.ARTIFACT.value:
        # Artifact message validation
        pass
    
    return True

def validate_session_limit(session_message_count: int) -> bool:
    """
    Validate that a session has not exceeded the maximum message limit.
    
    Args:
        session_message_count: Current message count in the session
        
    Returns:
        bool: True if under limit, False otherwise
    """
    if session_message_count >= settings.MAX_MESSAGES_PER_SESSION:
        logger.error(f"Session has reached maximum message count: {session_message_count}")
        return False
    return True

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate metadata structure and content.
    
    Args:
        metadata: The metadata to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(metadata, dict):
        logger.error("Invalid metadata: not a dictionary")
        return False
    
    # Check for any invalid types in metadata values
    for key, value in metadata.items():
        if not isinstance(key, str):
            logger.error(f"Invalid metadata key: {key}, must be a string")
            return False
        
        # Validate that values are of JSON-serializable types
        if not _is_json_serializable(value):
            logger.error(f"Invalid metadata value for key {key}: not JSON serializable")
            return False
    
    return True

def _is_json_serializable(value: Any) -> bool:
    """
    Check if a value is JSON serializable.
    
    Args:
        value: The value to check
        
    Returns:
        bool: True if JSON serializable, False otherwise
    """
    if value is None:
        return True
    elif isinstance(value, (str, int, float, bool)):
        return True
    elif isinstance(value, (list, tuple)):
        return all(_is_json_serializable(item) for item in value)
    elif isinstance(value, dict):
        return (all(isinstance(k, str) for k in value.keys()) and
                all(_is_json_serializable(v) for v in value.values()))
    else:
        return False