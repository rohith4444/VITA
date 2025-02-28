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
from chat_api.config import MAX_MESSAGE_LENGTH
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

class MessageService:
    """
    Service for managing chat messages.
    """
    
    def __init__(
        self, 
        db_session: Session, 
        memory_service: MemoryService,
        file_adapter: FileAdapter
    ):
        """
        Initialize the message service.
        
        Args:
            db_session: SQLAlchemy database session
            memory_service: Service for memory operations
            file_adapter: Adapter for file operations
        """
        self.db = db_session
        self.memory_service = memory_service
        self.file_adapter = file_adapter
    
    def create_user_message(
        self, 
        session_id: UUID, 
        content: str,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageModel:
        """
        Create a new user message.
        
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
            validate_message_content(content, max_length=MAX_MESSAGE_LENGTH)
            
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
            
            # Add to memory
            self.memory_service.add_user_message(
                session_id=session_id,
                message_content=content,
                message_id=message_id,
                metadata=metadata
            )
            
            logger.info(f"Created user message {message_id} in session {session_id}")
            return message
            
        except ValueError as e:
            # Validation error
            logger.warning(f"Validation error for user message in session {session_id}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating user message in session {session_id}: {str(e)}")
            raise Exception(f"Failed to create message: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating user message in session {session_id}: {str(e)}")
            raise
    
    def create_assistant_response(
        self, 
        session_id: UUID, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[MessageModel, List[ArtifactModel]]:
        """
        Create a new assistant response.
        
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
            validate_message_content(content, max_length=MAX_MESSAGE_LENGTH)
            
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
                    artifact = ArtifactModel(
                        id=uuid4(),
                        message_id=response_id,
                        type=artifact_data.get("type"),
                        content=artifact_data.get("content"),
                        title=artifact_data.get("title"),
                        metadata=artifact_data.get("metadata", {}),
                        created_at=datetime.utcnow()
                    )
                    self.db.add(artifact)
                    artifact_models.append(artifact)
            
            self.db.commit()
            self.db.refresh(response)
            for artifact in artifact_models:
                self.db.refresh(artifact)
            
            # Add to memory
            self.memory_service.add_assistant_response(
                session_id=session_id,
                response_content=content,
                response_id=response_id,
                metadata=metadata
            )
            
            logger.info(f"Created assistant response {response_id} with {len(artifact_models)} artifacts in session {session_id}")
            return response, artifact_models
            
        except ValueError as e:
            # Validation error
            logger.warning(f"Validation error for assistant response in session {session_id}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating assistant response in session {session_id}: {str(e)}")
            raise Exception(f"Failed to create response: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating assistant response in session {session_id}: {str(e)}")
            raise
    
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
            logger.error(f"Error retrieving message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve message: {str(e)}")
    
    def get_session_messages(self, session_id: UUID, limit: Optional[int] = None, 
                           offset: Optional[int] = None) -> List[MessageModel]:
        """
        Get messages for a session.
        
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
            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving messages for session {session_id}: {str(e)}")
            raise Exception(f"Failed to retrieve messages: {str(e)}")
    
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
            logger.error(f"Error retrieving artifacts for message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve artifacts: {str(e)}")
    
    def delete_message(self, message_id: UUID) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: ID of the message to delete
            
        Returns:
            True if the message was deleted, False otherwise
        """
        try:
            message = self.get_message(message_id)
            if not message:
                logger.warning(f"Attempted to delete non-existent message {message_id}")
                return False
            
            # Delete associated artifacts
            artifacts = self.get_artifacts_for_message(message_id)
            for artifact in artifacts:
                self.db.delete(artifact)
            
            # Delete the message
            self.db.delete(message)
            self.db.commit()
            
            logger.info(f"Deleted message {message_id} with {len(artifacts)} artifacts")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting message {message_id}: {str(e)}")
            raise Exception(f"Failed to delete message: {str(e)}")