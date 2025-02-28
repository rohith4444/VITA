from typing import List, Dict, Any, Optional
from uuid import UUID

from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.utils.context_builder import ContextBuilder
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

class MemoryService:
    """
    Service for managing chat memory and context.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter, context_builder: ContextBuilder):
        """
        Initialize the memory service.
        
        Args:
            memory_adapter: Adapter for memory operations
            context_builder: Utility for building context
        """
        self.memory_adapter = memory_adapter
        self.context_builder = context_builder
    
    def add_user_message(self, session_id: UUID, message_content: str, message_id: UUID, 
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a user message to memory.
        
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
                "id": str(message_id),
                "metadata": metadata or {}
            }
            
            success = self.memory_adapter.add_message(session_id_str, message)
            if success:
                logger.info(f"Added user message {message_id} to memory for session {session_id}")
            else:
                logger.warning(f"Failed to add user message {message_id} to memory for session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding user message to memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to add message to memory: {str(e)}")
    
    def add_assistant_response(self, session_id: UUID, response_content: str, response_id: UUID,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an assistant response to memory.
        
        Args:
            session_id: ID of the session
            response_content: Content of the response
            response_id: ID of the response
            metadata: Optional metadata for the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            message = {
                "role": "assistant",
                "content": response_content,
                "id": str(response_id),
                "metadata": metadata or {}
            }
            
            success = self.memory_adapter.add_message(session_id_str, message)
            if success:
                logger.info(f"Added assistant response {response_id} to memory for session {session_id}")
            else:
                logger.warning(f"Failed to add assistant response {response_id} to memory for session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding assistant response to memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to add response to memory: {str(e)}")
    
    def get_chat_history(self, session_id: UUID, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the chat history for a session.
        
        Args:
            session_id: ID of the session
            limit: Optional maximum number of messages to retrieve
            
        Returns:
            List of messages in chronological order
        """
        try:
            session_id_str = str(session_id)
            history = self.memory_adapter.get_messages(session_id_str, limit)
            logger.info(f"Retrieved {len(history)} messages from memory for session {session_id}")
            return history
        except Exception as e:
            logger.error(f"Error retrieving chat history for session {session_id}: {str(e)}")
            raise Exception(f"Failed to retrieve chat history: {str(e)}")
    
    def build_context(self, session_id: UUID, system_prompt: Optional[str] = None, 
                     user_info: Optional[Dict[str, Any]] = None,
                     additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build a context object for agent processing.
        
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
            history = self.memory_adapter.get_messages(session_id_str)
            
            context = self.context_builder.build_context(
                history=history,
                system_prompt=system_prompt,
                user_info=user_info,
                additional_context=additional_context
            )
            
            logger.info(f"Built context for session {session_id} with {len(history)} messages")
            return context
        except Exception as e:
            logger.error(f"Error building context for session {session_id}: {str(e)}")
            raise Exception(f"Failed to build context: {str(e)}")
    
    def clear_memory(self, session_id: UUID) -> bool:
        """
        Clear all memory for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id_str = str(session_id)
            success = self.memory_adapter.clear_memory(session_id_str)
            if success:
                logger.info(f"Cleared memory for session {session_id}")
            else:
                logger.warning(f"Failed to clear memory for session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error clearing memory for session {session_id}: {str(e)}")
            raise Exception(f"Failed to clear memory: {str(e)}")