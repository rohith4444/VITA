from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.message import MessageCreate, MessageResponse, MessageList
from chat_api.schemas.response import ResponseCreate, ResponseResponse
from chat_api.services.message_service import MessageService
from chat_api.services.memory_service import MemoryService
from chat_api.services.agent_service import AgentService
from chat_api.services.session_service import SessionService
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.adapters.agent_adapter import AgentAdapter
from chat_api.adapters.file_adapter import FileAdapter
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.response_formatter import ResponseFormatter
from chat_api.core.auth import get_current_user_id
from chat_api.core.logging import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])

# Dependency for MessageService
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder()
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
        context_builder=ContextBuilder()
    )
    return AgentService(
        agent_adapter=AgentAdapter(),
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
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
        
        return MessageList(
            items=messages,
            total=total,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving messages for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
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
        
        return user_message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error creating message in session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Get message
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
        
        # Check that message belongs to the session
        if message.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found in session {session_id}"
            )
        
        return message
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve message: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Get message to check ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
        
        # Check that message belongs to the session
        if message.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found in session {session_id}"
            )
        
        # Check ownership for user messages
        if message.role == "user" and message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this message"
            )
        
        # Delete the message
        success = message_service.delete_message(message_id=message_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete message {message_id}"
            )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
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