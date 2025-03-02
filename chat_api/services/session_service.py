from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from chat_api.models.session import SessionModel
from chat_api.models.message import MessageModel
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.schemas.session_schemas import SessionStatus, SessionType, AgentType
from chat_api.utils.validators import validate_session_limit
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_method

class SessionService:
    """
    Service for managing chat sessions with integration to both database and memory system.
    Handles session lifecycle, metadata management, and synchronization with memory.
    """
    
    def __init__(self, db_session: Session, memory_adapter: MemoryAdapter):
        """
        Initialize the session service with both database and memory system support.
        
        Args:
            db_session: SQLAlchemy database session
            memory_adapter: Adapter for memory operations
        """
        self.db = db_session
        self.memory_adapter = memory_adapter
        self.logger = setup_logger("chat_api.services.session")
        self.logger.info("Initializing Session Service with DB and memory integration")
    
    @trace_method
    @monitor_operation(operation_type="session_create")
    def create_session(
        self, 
        user_id: UUID, 
        title: Optional[str] = None, 
        session_type: SessionType = SessionType.STANDARD,
        primary_agent: AgentType = AgentType.PROJECT_MANAGER,
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionModel:
        """
        Create a new chat session in both database and memory system.
        
        Args:
            user_id: ID of the user creating the session
            title: Optional title for the session
            session_type: Type of session to create
            primary_agent: Primary agent for this session
            settings: Optional user settings for the session
            metadata: Optional metadata for the session
            
        Returns:
            The created session model
            
        Raises:
            Exception: If session creation fails
        """
        try:
            # Create session in database
            session_id = uuid4()
            session = SessionModel(
                id=session_id,
                user_id=user_id,
                title=title or "New Chat",
                status=SessionStatus.ACTIVE.value,
                session_type=session_type.value,
                primary_agent=primary_agent.value,
                settings=settings or {},
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            # Initialize memory for this session in the memory system
            # We don't await this to avoid blocking the HTTP response
            # Memory initialization failures should not block the database operation
            self.logger.debug(f"Initializing memory for session {session_id}")
            self.memory_adapter.initialize_session_memory(
                session_id=str(session_id),
                agent_id=primary_agent.value
            )
            
            self.logger.info(f"Created new session {session.id} for user {user_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error creating session for user {user_id}: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating session for user {user_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="session_retrieve")
    def get_session(self, session_id: UUID) -> Optional[SessionModel]:
        """
        Get a session by ID.
        
        Args:
            session_id: ID of the session to retrieve
            
        Returns:
            The session model if found, None otherwise
            
        Raises:
            Exception: If session retrieval fails
        """
        try:
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            
            if not session:
                self.logger.debug(f"Session not found: {session_id}")
                return None
                
            return session
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving session {session_id}: {str(e)}")
            raise Exception(f"Failed to retrieve session: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="user_sessions_retrieve")
    def get_user_sessions(
        self, 
        user_id: UUID, 
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_message_count: bool = True
    ) -> List[SessionModel]:
        """
        Get all sessions for a user with optional filtering and pagination.
        
        Args:
            user_id: ID of the user
            status: Optional status filter
            limit: Optional maximum number of sessions to retrieve
            offset: Optional offset for pagination
            include_message_count: Whether to include message count
            
        Returns:
            List of session models
            
        Raises:
            Exception: If session retrieval fails
        """
        try:
            # Start query
            query = self.db.query(SessionModel).filter(
                SessionModel.user_id == user_id
            )
            
            # Apply status filter if provided
            if status:
                query = query.filter(SessionModel.status == status.value)
            
            # Apply sorting (newest first)
            query = query.order_by(SessionModel.updated_at.desc())
            
            # Apply pagination if provided
            if offset is not None:
                query = query.offset(offset)
            
            if limit is not None:
                query = query.limit(limit)
            
            # Execute query
            sessions = query.all()
            
            # Optionally load message counts
            if include_message_count and sessions:
                # This approach is more efficient than counting for each session individually
                # Get all session IDs
                session_ids = [session.id for session in sessions]
                
                # Get message counts for all sessions in one query
                message_counts = self.db.query(
                    MessageModel.session_id, 
                    # This is SQLAlchemy's function for COUNT
                    # pylint: disable=not-callable
                    SessionModel.func.count(MessageModel.id).label('count')
                ).filter(
                    MessageModel.session_id.in_(session_ids)
                ).group_by(
                    MessageModel.session_id
                ).all()
                
                # Convert to dict for faster lookup
                count_dict = {str(session_id): count for session_id, count in message_counts}
                
                # Set counts in session objects
                for session in sessions:
                    session.message_count = count_dict.get(str(session.id), 0)
            
            self.logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sessions for user {user_id}: {str(e)}")
            raise Exception(f"Failed to retrieve sessions: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="session_update")
    def update_session(
        self, 
        session_id: UUID, 
        title: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        primary_agent: Optional[AgentType] = None,
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SessionModel]:
        """
        Update a session's information in both database and memory system.
        
        Args:
            session_id: ID of the session to update
            title: New title for the session
            status: New status for the session
            primary_agent: New primary agent for the session
            settings: New settings for the session
            metadata: New metadata for the session
            
        Returns:
            The updated session model if found, None otherwise
            
        Raises:
            Exception: If session update fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                self.logger.warning(f"Attempted to update non-existent session {session_id}")
                return None
            
            # Track changed fields for memory update
            changed_fields = {}
            
            # Update fields if provided
            if title is not None:
                session.title = title
                changed_fields["title"] = title
                
            if status is not None:
                session.status = status.value
                changed_fields["status"] = status.value
                
            if primary_agent is not None:
                session.primary_agent = primary_agent.value
                changed_fields["primary_agent"] = primary_agent.value
                
            if settings is not None:
                # Merge existing settings with new settings
                merged_settings = {**session.settings, **settings}
                session.settings = merged_settings
                changed_fields["settings"] = merged_settings
                
            if metadata is not None:
                # Merge existing metadata with new metadata
                merged_metadata = {**session.metadata, **metadata}
                session.metadata = merged_metadata
                changed_fields["metadata"] = merged_metadata
            
            # Update timestamp
            session.updated_at = datetime.utcnow()
            changed_fields["updated_at"] = session.updated_at.isoformat()
            
            self.db.commit()
            self.db.refresh(session)
            
            # Update memory system with changes
            # We don't await this to avoid blocking the HTTP response
            if changed_fields:
                try:
                    # Update in memory system
                    self.memory_adapter.update_session_metadata(
                        session_id=str(session_id),
                        changes=changed_fields
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update session metadata in memory: {str(e)}")
            
            self.logger.info(f"Updated session {session_id}")
            return session
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error updating session {session_id}: {str(e)}")
            raise Exception(f"Failed to update session: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error updating session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="session_delete")
    def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a session and all its data from both database and memory system.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
            
        Raises:
            Exception: If session deletion fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                self.logger.warning(f"Attempted to delete non-existent session {session_id}")
                return False
            
            # Delete from database (cascade will handle related entities)
            self.db.delete(session)
            self.db.commit()
            
            # Delete from memory system
            # We don't await this to avoid blocking the HTTP response
            # Memory deletion failures should not block the database operation
            try:
                # Clear memory for this session
                self.memory_adapter.clear_session_memory(str(session_id))
            except Exception as e:
                self.logger.warning(f"Failed to clear session memory: {str(e)}")
            
            self.logger.info(f"Deleted session {session_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error deleting session {session_id}: {str(e)}")
            raise Exception(f"Failed to delete session: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="session_archive")
    def archive_session(self, session_id: UUID) -> bool:
        """
        Archive a session rather than deleting it.
        
        Args:
            session_id: ID of the session to archive
            
        Returns:
            True if the session was archived, False otherwise
            
        Raises:
            Exception: If session archival fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                self.logger.warning(f"Attempted to archive non-existent session {session_id}")
                return False
            
            # Update session status to archived
            session.status = SessionStatus.ARCHIVED.value
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Update in memory system
            try:
                self.memory_adapter.update_session_metadata(
                    session_id=str(session_id),
                    changes={
                        "status": SessionStatus.ARCHIVED.value,
                        "updated_at": session.updated_at.isoformat()
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to update session status in memory: {str(e)}")
            
            self.logger.info(f"Archived session {session_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error archiving session {session_id}: {str(e)}")
            raise Exception(f"Failed to archive session: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error archiving session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="session_validation")
    def validate_session_limits(self, session_id: UUID) -> bool:
        """
        Validate that a session has not exceeded its limits (e.g., message count).
        
        Args:
            session_id: ID of the session to validate
            
        Returns:
            True if session is within limits, False otherwise
            
        Raises:
            Exception: If session validation fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                self.logger.warning(f"Attempted to validate non-existent session {session_id}")
                return False
            
            # Get message count from database
            message_count = self.db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).count()
            
            # Update session message count if it differs
            if session.message_count != message_count:
                session.message_count = message_count
                self.db.commit()
            
            # Validate message count
            if not validate_session_limit(message_count):
                self.logger.warning(f"Session {session_id} has exceeded message limit: {message_count}")
                return False
            
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error validating session {session_id}: {str(e)}")
            raise Exception(f"Failed to validate session: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error validating session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="memory_session_sync")
    def synchronize_session_memory(self, session_id: UUID) -> bool:
        """
        Synchronize session data between database and memory system.
        
        Args:
            session_id: ID of the session to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                self.logger.warning(f"Attempted to synchronize non-existent session {session_id}")
                return False
            
            # Create session metadata for memory
            session_metadata = {
                "session_id": str(session.id),
                "title": session.title,
                "status": session.status,
                "session_type": session.session_type,
                "primary_agent": session.primary_agent,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "metadata": session.metadata,
                "settings": session.settings
            }
            
            # Update memory system with full session data
            try:
                success = self.memory_adapter.store_session_metadata(
                    session_id=str(session_id),
                    metadata=session_metadata
                )
                
                if success:
                    self.logger.info(f"Synchronized session {session_id} with memory system")
                else:
                    self.logger.warning(f"Failed to synchronize session {session_id} with memory system")
                
                return success
            except Exception as e:
                self.logger.warning(f"Error synchronizing session with memory: {str(e)}")
                return False
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during session memory synchronization {session_id}: {str(e)}")
            raise Exception(f"Failed to synchronize session memory: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error during session memory synchronization {session_id}: {str(e)}")
            raise