from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime

from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.memory_sync import MemorySynchronizer
from chat_api.models.message import MessageModel
from chat_api.models.artifact import ArtifactModel
from sqlalchemy.orm import Session
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_method

logger = setup_logger(__name__)

class MemoryService:
    """
    Service for managing chat memory and context using a hybrid storage approach.
    Coordinates between SQLAlchemy database and the Long-term Memory system.
    """
    
    def __init__(
        self, 
        memory_adapter: MemoryAdapter, 
        context_builder: ContextBuilder,
        memory_sync: Optional[MemorySynchronizer] = None,
        db_session: Optional[Session] = None
    ):
        """
        Initialize the memory service.
        
        Args:
            memory_adapter: Adapter for memory operations
            context_builder: Utility for building context
            memory_sync: Utility for memory synchronization
            db_session: Database session for SQLAlchemy operations
        """
        self.memory_adapter = memory_adapter
        self.context_builder = context_builder
        self.memory_sync = memory_sync
        self.db = db_session
        self.logger = setup_logger("chat_api.services.memory")
        self.logger.info("Initializing Memory Service with hybrid storage approach")
    
    @trace_method
    @monitor_operation(operation_type="memory_message_store")
    async def add_user_message(
        self, 
        session_id: UUID, 
        message_content: str, 
        message_id: UUID, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a user message to Long-term Memory for agent context.
        
        Args:
            session_id: ID of the session
            message_content: Content of the message
            message_id: ID of the message
            metadata: Optional metadata for the message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            message = {
                "role": "user",
                "content": message_content,
                "message_id": str(message_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Long-term Memory
            success = await self.memory_adapter.store_long_term(
                agent_id=session_id_str,
                content={"message": message},
                metadata={
                    "message_id": str(message_id),
                    "content_type": "message",
                    "role": "user",
                    **(metadata or {})
                },
                importance=0.8  # Higher importance for user messages
            )
            
            if success:
                self.logger.info(f"Added user message {message_id} to Long-term Memory for session {session_id}")
            else:
                self.logger.warning(f"Failed to add user message {message_id} to Long-term Memory for session {session_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error adding user message to memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to add message to memory: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="memory_response_store")
    async def add_assistant_response(
        self, 
        session_id: UUID, 
        response_content: str, 
        response_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add an assistant response to Long-term Memory for agent context.
        
        Args:
            session_id: ID of the session
            response_content: Content of the response
            response_id: ID of the response
            metadata: Optional metadata for the response
            artifacts: Optional list of artifacts generated with the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            message = {
                "role": "assistant",
                "content": response_content,
                "message_id": str(response_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if artifacts:
                message["artifacts"] = [
                    {
                        "artifact_id": artifact.get("artifact_id", ""),
                        "title": artifact.get("title", ""),
                        "type": artifact.get("type", "")
                    }
                    for artifact in artifacts
                ]
            
            # Store in Long-term Memory
            success = await self.memory_adapter.store_long_term(
                agent_id=session_id_str,
                content={"message": message},
                metadata={
                    "message_id": str(response_id),
                    "content_type": "message",
                    "role": "assistant",
                    **(metadata or {})
                },
                importance=0.7  # Standard importance for assistant responses
            )
            
            if success:
                self.logger.info(f"Added assistant response {response_id} to Long-term Memory for session {session_id}")
            else:
                self.logger.warning(f"Failed to add assistant response {response_id} to Long-term Memory for session {session_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error adding assistant response to memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to add response to memory: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="memory_artifact_store")
    async def add_artifact(
        self, 
        session_id: UUID, 
        message_id: UUID,
        artifact_id: UUID,
        artifact_type: str,
        title: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an artifact to Long-term Memory for agent context.
        
        Args:
            session_id: ID of the session
            message_id: ID of the message the artifact is associated with
            artifact_id: ID of the artifact
            artifact_type: Type of the artifact
            title: Title of the artifact
            summary: Short summary of the artifact content
            metadata: Optional metadata for the artifact
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            artifact = {
                "artifact_id": str(artifact_id),
                "message_id": str(message_id),
                "type": artifact_type,
                "title": title,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Long-term Memory
            success = await self.memory_adapter.store_long_term(
                agent_id=session_id_str,
                content={"artifact": artifact},
                metadata={
                    "artifact_id": str(artifact_id),
                    "message_id": str(message_id),
                    "content_type": "artifact",
                    "artifact_type": artifact_type,
                    **(metadata or {})
                },
                importance=0.8  # Higher importance for artifacts
            )
            
            if success:
                self.logger.info(f"Added artifact {artifact_id} to Long-term Memory for session {session_id}")
            else:
                self.logger.warning(f"Failed to add artifact {artifact_id} to Long-term Memory for session {session_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error adding artifact to memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to add artifact to memory: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="memory_context_build")
    async def build_context(
        self, 
        session_id: UUID, 
        system_prompt: Optional[str] = None, 
        user_info: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a comprehensive context object for agent processing.
        Combines database data with memory system data.
        
        Args:
            session_id: ID of the session
            system_prompt: Optional system prompt to use
            user_info: Optional user information to include
            additional_context: Optional additional context to include
            
        Returns:
            The built context object
        """
        try:
            session_id_str = str(session_id)
            
            # Get conversation history from database if available
            db_history = []
            if self.db:
                # This should be implemented based on your database schema
                # Here's a placeholder for how it might look
                from chat_api.models.message import MessageModel
                messages = self.db.query(MessageModel).filter(
                    MessageModel.session_id == session_id
                ).order_by(MessageModel.created_at).all()
                
                db_history = [
                    {
                        "role": message.role,
                        "content": message.content,
                        "message_id": str(message.id),
                        "timestamp": message.created_at.isoformat()
                    }
                    for message in messages
                ]
            
            # Get additional context from Long-term Memory
            long_term_context = await self.memory_adapter.retrieve_long_term(
                agent_id=session_id_str,
                query={"metadata.content_type": {"$ne": "message"}},  # Exclude messages as we got them from DB
                sort_by="timestamp",
                limit=20
            )
            
            # Combine into context
            context = self.context_builder.build_context(
                history=db_history,
                long_term_context=long_term_context,
                system_prompt=system_prompt,
                user_info=user_info,
                additional_context=additional_context
            )
            
            self.logger.info(f"Built context for session {session_id} with {len(db_history)} messages")
            return context
        except Exception as e:
            self.logger.error(f"Error building context for session {session_id}: {str(e)}")
            raise Exception(f"Failed to build context: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="memory_sync")
    async def synchronize_session(self, session_id: UUID) -> bool:
        """
        Synchronize database records with Long-term Memory for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        if not self.memory_sync or not self.db:
            self.logger.warning(f"Cannot synchronize session {session_id}: Missing memory_sync or db_session")
            return False
            
        try:
            return await self.memory_sync.synchronize_session(
                session_id=session_id,
                db_session=self.db
            )
        except Exception as e:
            self.logger.error(f"Error synchronizing session {session_id}: {str(e)}")
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_session_clear")
    async def clear_session_memory(self, session_id: UUID) -> bool:
        """
        Clear all memory for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            
            # Clear from memory system (all tiers)
            success = await self.memory_adapter.clear_memory(session_id_str)
            if success:
                self.logger.info(f"Cleared memory for session {session_id}")
            else:
                self.logger.warning(f"Failed to clear memory for session {session_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error clearing memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to clear memory: {str(e)}")