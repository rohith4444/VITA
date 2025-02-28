# chat_api/routes/session_routes.py

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.session import SessionCreate, SessionResponse, SessionUpdate
from chat_api.services.session_service import SessionService
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.core.auth import get_current_user_id
from chat_api.core.logging import setup_logger

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
            metadata=session_data.metadata
        )
        return session
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("", response_model=List[SessionResponse])
async def get_user_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all sessions for the current user.
    """
    try:
        sessions = service.get_user_sessions(user_id=user_id)
        # Apply pagination manually
        return sessions[skip:skip + limit]
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Check ownership
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        return session
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this session"
            )
        
        # Update the session
        updated_session = service.update_session(
            session_id=session_id,
            title=session_data.title,
            metadata=session_data.metadata
        )
        
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return updated_session
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this session"
            )
        
        # Delete the session
        success = service.delete_session(session_id=session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete session {session_id}"
            )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )