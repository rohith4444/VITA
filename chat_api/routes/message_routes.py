from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.message_schemas import MessageCreate, MessageResponse, MessageList
from chat_api.schemas.response_schemas import ResponseCreate, ResponseResponse
from chat_api.services.message_service import MessageService
from chat_api.services.memory_service import MemoryService
from chat_api.services.agent_service import AgentService
from chat_api.services.session_service import SessionService
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.adapters.agent_adapter import AgentAdapter
from chat_api.adapters.file_adapter import FileAdapter
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.response_formatter import ResponseFormatter, format_message_response, format_message_list_response, raise_http_exception
from chat_api.auth import get_current_user_id
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])

# Dependency for MessageService
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder(memory_adapter)
    )
    file_adapter = FileAdapter()
    return MessageService(
        db_session=db,
        memory_service=memory_service,
        file_adapter=file_adapter
    )

# Dependency for SessionService
def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    memory_adapter = MemoryAdapter()
    return SessionService(db_session=db, memory_adapter=memory_adapter)

# Dependency for AgentService
def get_agent_service() -> AgentService:
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder(memory_adapter)
    )
    return AgentService(
        agent_adapter=AgentAdapter(memory_adapter.memory_manager),
        memory_service=memory_service,
        response_formatter=ResponseFormatter()
    )

@router.get("", response_model=MessageList)
async def get_messages(
    session_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all messages for a session.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get messages
        messages = message_service.get_session_messages(
            session_id=session_id,
            limit=limit,
            offset=skip
        )
        
        # Get total count for pagination
        all_messages = message_service.get_session_messages(session_id=session_id)
        total = len(all_messages)
        
        return format_message_list_response(messages, total)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving messages for session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="message_retrieval_failed",
            message=f"Failed to retrieve messages: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: UUID,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    agent_service: AgentService = Depends(get_agent_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new user message and generate an assistant response.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check message limit
        if not session_service.validate_session_limits(session_id=session_id):
            raise_http_exception(
                error_code="session_limit_exceeded",
                message="Session has reached the maximum message limit",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = message_service.create_user_message(
            session_id=session_id,
            content=message_data.content,
            user_id=user_id,
            metadata=message_data.metadata
        )
        
        # Generate assistant response in background
        background_tasks.add_task(
            generate_assistant_response,
            session_id=session_id,
            user_message=user_message,
            message_service=message_service,
            agent_service=agent_service
        )
        
        # Update session title if it's the first message
        if session.title == "New Chat":
            background_tasks.add_task(
                update_session_title,
                session_id=session_id,
                message_content=message_data.content,
                session_service=session_service,
                agent_service=agent_service
            )
        
        return format_message_response(user_message)
    except ValueError as e:
        raise_http_exception(
            error_code="validation_error",
            message=str(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error creating message in session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="message_creation_failed",
            message=f"Failed to create message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    session_id: UUID,
    message_id: UUID,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific message by ID.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get message
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise_http_exception(
                error_code="message_not_found",
                message=f"Message {message_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check that message belongs to the session
        if message.session_id != session_id:
            raise_http_exception(
                error_code="message_not_in_session",
                message=f"Message {message_id} not found in session {session_id}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return format_message_response(message)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {str(e)}")
        raise_http_exception(
            error_code="message_retrieval_failed",
            message=f"Failed to retrieve message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    session_id: UUID,
    message_id: UUID,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a message.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get message to check ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise_http_exception(
                error_code="message_not_found",
                message=f"Message {message_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check that message belongs to the session
        if message.session_id != session_id:
            raise_http_exception(
                error_code="message_not_in_session",
                message=f"Message {message_id} not found in session {session_id}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership for user messages
        if message.role == "user" and message.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to delete this message",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the message
        success = message_service.delete_message(message_id=message_id)
        
        if not success:
            raise_http_exception(
                error_code="message_deletion_failed",
                message=f"Failed to delete message {message_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {str(e)}")
        raise_http_exception(
            error_code="message_deletion_failed",
            message=f"Failed to delete message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/{message_id}/feedback", response_model=Dict[str, Any])
async def add_message_feedback(
    session_id: UUID,
    message_id: UUID,
    feedback_data: Dict[str, Any],
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    agent_service: AgentService = Depends(get_agent_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Add feedback to a message.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Verify message exists and belongs to session
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise_http_exception(
                error_code="message_not_found",
                message=f"Message {message_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if message.session_id != session_id:
            raise_http_exception(
                error_code="message_not_in_session",
                message=f"Message {message_id} not found in session {session_id}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Only allow feedback on assistant messages
        if message.role != "assistant":
            raise_http_exception(
                error_code="invalid_feedback_target",
                message="Feedback can only be provided on assistant messages",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate feedback data
        if not isinstance(feedback_data, dict) or "type" not in feedback_data:
            raise_http_exception(
                error_code="invalid_feedback",
                message="Feedback must contain a 'type' field",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Add feedback to message
        added = message_service.add_message_feedback(
            message_id=message_id,
            feedback_type=feedback_data["type"],
            feedback_content=feedback_data,
            user_id=user_id
        )
        
        if not added:
            raise_http_exception(
                error_code="feedback_addition_failed",
                message=f"Failed to add feedback to message {message_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Process feedback with agent
        agent_result = await agent_service.process_feedback(
            session_id=session_id,
            message_id=message_id,
            feedback=feedback_data
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "message_id": str(message_id),
            "feedback_type": feedback_data["type"],
            "agent_result": agent_result
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error adding feedback to message {message_id}: {str(e)}")
        raise_http_exception(
            error_code="feedback_addition_failed",
            message=f"Failed to add feedback: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Background task for generating assistant response
async def generate_assistant_response(
    session_id: UUID,
    user_message: Any,
    message_service: MessageService,
    agent_service: AgentService
):
    try:
        # Generate response from agent
        agent_response = await agent_service.process_message(
            session_id=session_id,
            message_content=user_message.content
        )
        
        # Create assistant response in database
        response_content = agent_response.get("content", "")
        response_artifacts = agent_response.get("artifacts", [])
        
        message_service.create_assistant_response(
            session_id=session_id,
            content=response_content,
            metadata=agent_response.get("metadata", {}),
            artifacts=response_artifacts
        )
        
        logger.info(f"Generated assistant response for message {user_message.id} in session {session_id}")
    except Exception as e:
        logger.error(f"Error generating assistant response for message {user_message.id} in session {session_id}: {str(e)}")

# Background task for updating session title
async def update_session_title(
    session_id: UUID,
    message_content: str,
    session_service: SessionService,
    agent_service: AgentService
):
    try:
        # Generate title
        title = await agent_service.generate_title(
            session_id=session_id,
            first_message=message_content
        )
        
        # Update session
        if title:
            session_service.update_session(
                session_id=session_id,
                title=title
            )
            
            logger.info(f"Updated title for session {session_id}: '{title}'")
    except Exception as e:
        logger.error(f"Error updating title for session {session_id}: {str(e)}")