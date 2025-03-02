# chat_api/routes/session_routes.py

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.session_schemas import SessionCreate, SessionResponse, SessionUpdate, SessionList
from chat_api.schemas.response_schemas import APIResponse, ErrorResponse, ResponseStatus
from chat_api.services.session_service import SessionService
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.auth import get_current_user_id
from chat_api.utils.response_formatter import format_session_response, format_success_response, format_error_response, raise_http_exception
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/sessions", tags=["sessions"])

# Dependency for SessionService
def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    memory_adapter = MemoryAdapter()
    return SessionService(db_session=db, memory_adapter=memory_adapter)

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new chat session.
    """
    try:
        session = service.create_session(
            user_id=user_id,
            title=session_data.title,
            session_type=session_data.session_type,
            primary_agent=session_data.primary_agent,
            settings=session_data.settings.dict() if session_data.settings else None,
            metadata=session_data.metadata
        )
        return format_session_response(session)
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise_http_exception(
            error_code="session_creation_failed",
            message=f"Failed to create session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("", response_model=SessionList)
async def get_user_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all sessions for the current user.
    """
    try:
        sessions = service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=skip,
            include_message_count=True
        )
        
        # Get total count for pagination
        total_sessions = len(service.get_user_sessions(user_id=user_id))
        
        return SessionList(
            items=sessions,
            total=total_sessions,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {str(e)}")
        raise_http_exception(
            error_code="session_retrieval_failed",
            message=f"Failed to retrieve sessions: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific session by ID.
    """
    try:
        session = service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return format_session_response(session)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="session_retrieval_failed",
            message=f"Failed to retrieve session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_data: SessionUpdate,
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update a session.
    """
    try:
        # Check ownership
        session = service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to update this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Update the session
        updated_session = service.update_session(
            session_id=session_id,
            title=session_data.title,
            status=session_data.status,
            primary_agent=session_data.primary_agent,
            settings=session_data.settings.dict() if session_data.settings else None,
            metadata=session_data.metadata
        )
        
        if not updated_session:
            raise_http_exception(
                error_code="session_update_failed",
                message=f"Failed to update session {session_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return format_session_response(updated_session)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="session_update_failed",
            message=f"Failed to update session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a session.
    """
    try:
        # Check ownership
        session = service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to delete this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the session
        success = service.delete_session(session_id=session_id)
        
        if not success:
            raise_http_exception(
                error_code="session_deletion_failed",
                message=f"Failed to delete session {session_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="session_deletion_failed",
            message=f"Failed to delete session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/{session_id}/archive", response_model=SessionResponse)
async def archive_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Archive a session.
    """
    try:
        # Check ownership
        session = service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to archive this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Archive the session
        success = service.archive_session(session_id=session_id)
        
        if not success:
            raise_http_exception(
                error_code="session_archive_failed",
                message=f"Failed to archive session {session_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get updated session
        updated_session = service.get_session(session_id=session_id)
        return format_session_response(updated_session)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error archiving session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="session_archive_failed",
            message=f"Failed to archive session: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )