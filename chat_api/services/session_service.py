from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from chat_api.models.session import SessionModel
from chat_api.adapters.memory_adapter import MemoryAdapter
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

class SessionService:
    """
    Service for managing chat sessions.
    """
    
    def __init__(self, db_session: Session, memory_adapter: MemoryAdapter):
        """
        Initialize the session service.
        
        Args:
            db_session: SQLAlchemy database session
            memory_adapter: Adapter for memory operations
        """
        self.db = db_session
        self.memory_adapter = memory_adapter
    
    def create_session(self, user_id: UUID, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> SessionModel:
        """
        Create a new chat session.
        
        Args:
            user_id: ID of the user creating the session
            title: Optional title for the session
            metadata: Optional metadata for the session
            
        Returns:
            The created session model
        """
        try:
            # Create session in database
            session = SessionModel(
                id=uuid4(),
                user_id=user_id,
                title=title or "New Chat",
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            # Initialize memory for this session
            self.memory_adapter.initialize_memory(str(session.id))
            
            logger.info(f"Created new session {session.id} for user {user_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating session for user {user_id}: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")
    
    def get_session(self, session_id: UUID) -> Optional[SessionModel]:
        """
        Get a session by ID.
        
        Args:
            session_id: ID of the session to retrieve
            
        Returns:
            The session model if found, None otherwise
        """
        try:
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            raise Exception(f"Failed to retrieve session: {str(e)}")
    
    def get_user_sessions(self, user_id: UUID) -> List[SessionModel]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of session models
        """
        try:
            sessions = self.db.query(SessionModel).filter(
                SessionModel.user_id == user_id
            ).order_by(SessionModel.updated_at.desc()).all()
            
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving sessions for user {user_id}: {str(e)}")
            raise Exception(f"Failed to retrieve sessions: {str(e)}")
    
    def update_session(self, session_id: UUID, title: Optional[str] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[SessionModel]:
        """
        Update a session.
        
        Args:
            session_id: ID of the session to update
            title: New title for the session
            metadata: New metadata for the session
            
        Returns:
            The updated session model if found, None otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Attempted to update non-existent session {session_id}")
                return None
            
            if title is not None:
                session.title = title
            
            if metadata is not None:
                # Merge existing metadata with new metadata
                session.metadata = {**session.metadata, **metadata}
            
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Updated session {session_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating session {session_id}: {str(e)}")
            raise Exception(f"Failed to update session: {str(e)}")
    
    def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Attempted to delete non-existent session {session_id}")
                return False
            
            # Delete from memory adapter first
            self.memory_adapter.clear_memory(str(session_id))
            
            # Delete from database
            self.db.delete(session)
            self.db.commit()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise Exception(f"Failed to delete session: {str(e)}")