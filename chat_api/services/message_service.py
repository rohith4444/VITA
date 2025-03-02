from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from chat_api.models.message import MessageModel
from chat_api.models.artifact import ArtifactModel
from chat_api.services.memory_service import MemoryService
from chat_api.adapters.file_adapter import FileAdapter
from chat_api.utils.validators import validate_message_content
from chat_api.config import settings
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_method

logger = setup_logger(__name__)

class MessageService:
    """
    Service for managing chat messages with dual storage (database + memory system).
    """
    
    def __init__(
        self, 
        db_session: Session, 
        memory_service: MemoryService,
        file_adapter: FileAdapter
    ):
        """
        Initialize the message service with both database and memory system support.
        
        Args:
            db_session: SQLAlchemy database session
            memory_service: Service for memory operations
            file_adapter: Adapter for file operations
        """
        self.db = db_session
        self.memory_service = memory_service
        self.file_adapter = file_adapter
        self.logger = setup_logger("chat_api.services.message")
        self.logger.info("Initializing Message Service with dual storage")
    
    @trace_method
    @monitor_operation(operation_type="user_message_create")
    def create_user_message(
        self, 
        session_id: UUID, 
        content: str,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageModel:
        """
        Create a new user message with storage in both database and memory system.
        
        Args:
            session_id: ID of the session
            content: Content of the message
            user_id: ID of the user sending the message
            metadata: Optional metadata for the message
            
        Returns:
            The created message model
        """
        try:
            # Validate message content
            validate_message_content(content, max_length=settings.MAX_MESSAGE_LENGTH)
            
            # Create message in database
            message_id = uuid4()
            message = MessageModel(
                id=message_id,
                session_id=session_id,
                user_id=user_id,
                content=content,
                role="user",
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # Add to session message count
            from chat_api.models.session import SessionModel
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.message_count += 1
                session.updated_at = datetime.utcnow()
                self.db.commit()
            
            # Add to memory system asynchronously
            # We don't await this to avoid blocking the HTTP response
            # Memory storage failures should not block the database operation
            self.logger.debug(f"Storing message {message_id} in memory system")
            self.memory_service.add_user_message(
                session_id=session_id,
                message_content=content,
                message_id=message_id,
                metadata=metadata
            )
            
            self.logger.info(f"Created user message {message_id} in session {session_id}")
            return message
            
        except ValueError as e:
            # Validation error
            self.logger.warning(f"Validation error for user message in session {session_id}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error creating user message in session {session_id}: {str(e)}")
            raise Exception(f"Failed to create message: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating user message in session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="assistant_response_create")
    def create_assistant_response(
        self, 
        session_id: UUID, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[MessageModel, List[ArtifactModel]]:
        """
        Create a new assistant response with storage in both database and memory system.
        
        Args:
            session_id: ID of the session
            content: Content of the response
            metadata: Optional metadata for the response
            artifacts: Optional list of artifacts to attach
            
        Returns:
            Tuple of (response model, list of artifact models)
        """
        try:
            # Validate message content
            validate_message_content(content, max_length=settings.MAX_MESSAGE_LENGTH)
            
            # Create response in database
            response_id = uuid4()
            response = MessageModel(
                id=response_id,
                session_id=session_id,
                user_id=None,  # Assistant responses don't have a user_id
                content=content,
                role="assistant",
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            self.db.add(response)
            
            # Create artifacts if any
            artifact_models = []
            if artifacts:
                for artifact_data in artifacts:
                    artifact_id = uuid4()
                    artifact = ArtifactModel(
                        id=artifact_id,
                        message_id=response_id,
                        type=artifact_data.get("type"),
                        content=artifact_data.get("content"),
                        title=artifact_data.get("title"),
                        language=artifact_data.get("language"),
                        metadata=artifact_data.get("metadata", {}),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(artifact)
                    artifact_models.append(artifact)
            
            self.db.commit()
            self.db.refresh(response)
            for artifact in artifact_models:
                self.db.refresh(artifact)
            
            # Add to session message count
            from chat_api.models.session import SessionModel
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.message_count += 1
                session.updated_at = datetime.utcnow()
                self.db.commit()
            
            # Add to memory system asynchronously
            # We don't await this to avoid blocking the HTTP response
            self.logger.debug(f"Storing response {response_id} in memory system")
            self.memory_service.add_assistant_response(
                session_id=session_id,
                response_content=content,
                response_id=response_id,
                metadata=metadata,
                artifacts=[
                    {
                        "artifact_id": str(artifact.id),
                        "type": artifact.type,
                        "title": artifact.title
                    }
                    for artifact in artifact_models
                ]
            )
            
            # Store artifacts in memory system if any
            for artifact in artifact_models:
                # Create a truncated summary of the content
                content_preview = artifact.content[:200] + "..." if len(artifact.content) > 200 else artifact.content
                
                self.memory_service.add_artifact(
                    session_id=session_id,
                    message_id=response_id,
                    artifact_id=artifact.id,
                    artifact_type=artifact.type,
                    title=artifact.title,
                    summary=content_preview,
                    metadata=artifact.metadata
                )
            
            self.logger.info(f"Created assistant response {response_id} with {len(artifact_models)} artifacts in session {session_id}")
            return response, artifact_models
            
        except ValueError as e:
            # Validation error
            self.logger.warning(f"Validation error for assistant response in session {session_id}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Database error creating assistant response in session {session_id}: {str(e)}")
            raise Exception(f"Failed to create response: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating assistant response in session {session_id}: {str(e)}")
            raise
    
    @trace_method
    @monitor_operation(operation_type="message_retrieve")
    def get_message(self, message_id: UUID) -> Optional[MessageModel]:
        """
        Get a message by ID.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            The message model if found, None otherwise
        """
        try:
            message = self.db.query(MessageModel).filter(MessageModel.id == message_id).first()
            return message
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve message: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="session_messages_retrieve")
    def get_session_messages(
        self, 
        session_id: UUID, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[MessageModel]:
        """
        Get messages for a session with pagination.
        
        Args:
            session_id: ID of the session
            limit: Optional maximum number of messages to retrieve
            offset: Optional offset for pagination
            
        Returns:
            List of message models
        """
        try:
            query = self.db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(MessageModel.created_at)
            
            if offset is not None:
                query = query.offset(offset)
            
            if limit is not None:
                query = query.limit(limit)
            
            messages = query.all()
            self.logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving messages for session {session_id}: {str(e)}")
            raise Exception(f"Failed to retrieve messages: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="message_artifacts_retrieve")
    def get_artifacts_for_message(self, message_id: UUID) -> List[ArtifactModel]:
        """
        Get artifacts for a message.
        
        Args:
            message_id: ID of the message
            
        Returns:
            List of artifact models
        """
        try:
            artifacts = self.db.query(ArtifactModel).filter(
                ArtifactModel.message_id == message_id
            ).all()
            
            return artifacts
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving artifacts for message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve artifacts: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="message_delete")
    def delete_message(self, message_id: UUID) -> bool:
        """
        Delete a message and its artifacts from both database and memory system.
        
        Args:
            message_id: ID of the message to delete
            
        Returns:
            True if the message was deleted, False otherwise
        """
        try:
            message = self.get_message(message_id)
            if not message:
                self.logger.warning(f"Attempted to delete non-existent message {message_id}")
                return False
            
            session_id = message.session_id
            
            # Delete associated artifacts
            artifacts = self.get_artifacts_for_message(message_id)
            for artifact in artifacts:
                # If this is a file artifact, delete the file
                if artifact.type == "file" and artifact.content:
                    try:
                        self.file_adapter.delete_file(artifact.content)
                    except Exception as e:
                        self.logger.warning(f"Error deleting file for artifact {artifact.id}: {str(e)}")
                
                self.db.delete(artifact)
            
            # Delete the message from database
            self.db.delete(message)
            
            # Update session message count
            from chat_api.models.session import SessionModel
            session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session and session.message_count > 0:
                session.message_count -= 1
                session.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Delete from memory system asynchronously
            # Memory deletion failures should not block the database operation
            try:
                # For memory system, we can't directly delete the message,
                # but we can mark it as deleted in working memory
                self.memory_service.update_message_status(
                    session_id=session_id,
                    message_id=message_id,
                    status="deleted"
                )
            except Exception as e:
                self.logger.warning(f"Failed to update message status in memory system: {str(e)}")
            
            self.logger.info(f"Deleted message {message_id} with {len(artifacts)} artifacts")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error deleting message {message_id}: {str(e)}")
            raise Exception(f"Failed to delete message: {str(e)}")
            
    @trace_method
    @monitor_operation(operation_type="message_feedback_add")
    def add_message_feedback(
        self,
        message_id: UUID,
        feedback_type: str,
        feedback_content: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        Add feedback to a message.
        
        Args:
            message_id: ID of the message
            feedback_type: Type of feedback (e.g., "thumbs_up", "thumbs_down", "rating")
            feedback_content: Content of the feedback
            user_id: Optional ID of the user providing feedback
            
        Returns:
            True if feedback was added successfully
        """
        try:
            message = self.get_message(message_id)
            if not message:
                self.logger.warning(f"Attempted to add feedback to non-existent message {message_id}")
                return False
            
            # Update message metadata with feedback
            if "feedback" not in message.metadata:
                message.metadata["feedback"] = []
                
            feedback_entry = {
                "feedback_id": str(uuid4()),
                "feedback_type": feedback_type,
                "content": feedback_content,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": str(user_id) if user_id else None
            }
            
            message.metadata["feedback"].append(feedback_entry)
            self.db.commit()
            
            # Update in memory system
            try:
                self.memory_service.add_message_feedback(
                    session_id=message.session_id,
                    message_id=message_id,
                    feedback_type=feedback_type,
                    feedback_content=feedback_content,
                    user_id=user_id
                )
            except Exception as e:
                self.logger.warning(f"Failed to add feedback to memory system: {str(e)}")
            
            self.logger.info(f"Added {feedback_type} feedback to message {message_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"Error adding feedback to message {message_id}: {str(e)}")
            raise Exception(f"Failed to add feedback: {str(e)}")