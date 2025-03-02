from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from memory.memory_manager import MemoryManager
from memory.base import MemoryType, MemoryEntry
from agents.core.monitoring.decorators import monitor_operation
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

# Initialize logger
logger = setup_logger("chat_api.adapters.memory")


@trace_class
class MemoryAdapter:
    """
    Adapter for the existing memory system with focus on Long-term Memory.
    Provides an interface to connect the chat API with the underlying memory architecture,
    prioritizing Long-term Memory for persistent storage of agent context.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the memory adapter with a memory manager instance.
        
        Args:
            memory_manager: The memory manager from the existing system
        """
        self.logger = setup_logger("chat_api.adapters.memory.instance")
        self.logger.info("Initializing Memory Adapter with Long-term focus")
        self.memory_manager = memory_manager
        
    @trace_method
    @monitor_operation(operation_type="memory_store", metadata={"memory_type": "short_term"})
    async def store_short_term(self, agent_id: str, content: Dict[str, Any], 
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store content in short-term memory (for ephemeral context).
        
        Args:
            agent_id: Unique identifier for the agent/session
            content: Data to store
            metadata: Optional metadata about the memory
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Storing in short-term memory for agent {agent_id}")
        try:
            result = await self.memory_manager.store(
                agent_id=agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=content,
                metadata=metadata
            )
            self.logger.debug(f"Short-term memory storage result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error storing in short-term memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_store", metadata={"memory_type": "working"})
    async def store_working(self, agent_id: str, content: Dict[str, Any], 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store content in working memory (for current session state).
        
        Args:
            agent_id: Unique identifier for the agent/session
            content: Data to store
            metadata: Optional metadata about the memory
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Storing in working memory for agent {agent_id}")
        try:
            result = await self.memory_manager.store(
                agent_id=agent_id,
                memory_type=MemoryType.WORKING,
                content=content,
                metadata=metadata
            )
            self.logger.debug(f"Working memory storage result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error storing in working memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_store", metadata={"memory_type": "long_term"})
    async def store_long_term(self, agent_id: str, content: Dict[str, Any], 
                             metadata: Optional[Dict[str, Any]] = None,
                             importance: float = 0.7) -> bool:
        """
        Store content in long-term memory (primary storage for agent context).
        
        Args:
            agent_id: Unique identifier for the agent/session
            content: Data to store
            metadata: Optional metadata about the memory
            importance: Importance score (0.0 to 1.0), defaults higher for chat context
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Storing in long-term memory for agent {agent_id}")
        try:
            # Enhance metadata with source information
            enhanced_metadata = {
                "source": "chat_api",
                "storage_timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            result = await self.memory_manager.store(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=content,
                metadata=enhanced_metadata,
                importance=importance
            )
            self.logger.debug(f"Long-term memory storage result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error storing in long-term memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_retrieve", metadata={"memory_type": "short_term"})
    async def retrieve_short_term(self, agent_id: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve content from short-term memory.
        
        Args:
            agent_id: Unique identifier for the agent/session
            query: Optional query parameters to filter results
            
        Returns:
            List[Dict[str, Any]]: List of matching memory entries
        """
        self.logger.debug(f"Retrieving from short-term memory for agent {agent_id}")
        try:
            entries = await self.memory_manager.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.SHORT_TERM,
                query=query
            )
            results = [self._format_memory_entry(entry) for entry in entries]
            self.logger.debug(f"Retrieved {len(results)} entries from short-term memory")
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving from short-term memory: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    @monitor_operation(operation_type="memory_retrieve", metadata={"memory_type": "working"})
    async def retrieve_working(self, agent_id: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve content from working memory.
        
        Args:
            agent_id: Unique identifier for the agent/session
            query: Optional query parameters to filter results
            
        Returns:
            List[Dict[str, Any]]: List of matching memory entries
        """
        self.logger.debug(f"Retrieving from working memory for agent {agent_id}")
        try:
            entries = await self.memory_manager.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.WORKING,
                query=query
            )
            results = [self._format_memory_entry(entry) for entry in entries]
            self.logger.debug(f"Retrieved {len(results)} entries from working memory")
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving from working memory: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    @monitor_operation(operation_type="memory_retrieve", metadata={"memory_type": "long_term"})
    async def retrieve_long_term(self, agent_id: str, query: Optional[Dict[str, Any]] = None, 
                               sort_by: str = "timestamp", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve content from long-term memory (primary agent context source).
        
        Args:
            agent_id: Unique identifier for the agent/session
            query: Optional query parameters to filter results
            sort_by: Field to sort by
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching memory entries
        """
        self.logger.debug(f"Retrieving from long-term memory for agent {agent_id}")
        try:
            if not query:
                query = {}
                
            # Add source filter to prioritize chat API memories
            query["metadata.source"] = "chat_api"
            
            entries = await self.memory_manager.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                query=query,
                sort_by=sort_by,
                limit=limit
            )
            results = [self._format_memory_entry(entry) for entry in entries]
            self.logger.debug(f"Retrieved {len(results)} entries from long-term memory")
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving from long-term memory: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    @monitor_operation(operation_type="memory_query", metadata={"memory_type": "long_term"})
    async def search_long_term(self, agent_id: str, keywords: List[str], 
                              content_type: Optional[str] = None, 
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search long-term memory for specific content using keywords.
        
        Args:
            agent_id: Unique identifier for the agent/session
            keywords: List of keywords to search for
            content_type: Optional type of content to filter by
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching memory entries
        """
        self.logger.debug(f"Searching long-term memory for agent {agent_id} with keywords: {keywords}")
        try:
            # Construct text search query
            query = {
                "$text": {"$search": " ".join(keywords)},
                "metadata.source": "chat_api"
            }
            
            # Add content type filter if specified
            if content_type:
                query["metadata.content_type"] = content_type
                
            entries = await self.memory_manager.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                query=query,
                sort_by="metadata.importance",
                limit=limit
            )
            
            results = [self._format_memory_entry(entry) for entry in entries]
            self.logger.debug(f"Found {len(results)} entries matching keywords in long-term memory")
            return results
        except Exception as e:
            self.logger.error(f"Error searching long-term memory: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    @monitor_operation(operation_type="memory_update", metadata={"memory_type": "long_term"})
    async def update_long_term(self, agent_id: str, memory_id: str, 
                             update_data: Dict[str, Any],
                             importance: Optional[float] = None) -> bool:
        """
        Update a specific memory entry in long-term storage.
        
        Args:
            agent_id: Unique identifier for the agent/session
            memory_id: ID of the memory to update
            update_data: New data to update
            importance: Optional new importance score
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Updating long-term memory {memory_id} for agent {agent_id}")
        try:
            query = {"id": memory_id}
            
            # Prepare update data
            memory_update = {
                "content": update_data,
                "metadata.updated_at": datetime.utcnow().isoformat()
            }
            
            # Update importance if specified
            if importance is not None:
                memory_update["metadata.importance"] = importance
                
            success = await self.memory_manager.update(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                query=query,
                update_data=memory_update
            )
            
            self.logger.debug(f"Long-term memory update result: {success}")
            return success
        except Exception as e:
            self.logger.error(f"Error updating long-term memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_initialize")
    async def initialize_session_memory(self, session_id: str, agent_id: str) -> bool:
        """
        Initialize memory structure for a new chat session.
        
        Args:
            session_id: ID of the session
            agent_id: ID of the primary agent
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Initializing memory for session {session_id} with agent {agent_id}")
        try:
            # Create session metadata in long-term memory
            session_info = {
                "session_id": str(session_id),
                "agent_id": agent_id,
                "session_type": "chat",
                "created_at": datetime.utcnow().isoformat()
            }
            
            metadata = {
                "content_type": "session_info",
                "importance": 0.9  # High importance for session metadata
            }
            
            # Store in long-term memory
            success = await self.store_long_term(
                agent_id=str(session_id),
                content=session_info,
                metadata=metadata,
                importance=0.9
            )
            
            self.logger.info(f"Session memory initialization result: {success}")
            return success
        except Exception as e:
            self.logger.error(f"Error initializing session memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_cleanup")
    async def cleanup(self) -> bool:
        """
        Clean up memory resources.
        
        Returns:
            bool: Success status
        """
        self.logger.debug("Cleaning up memory resources")
        try:
            await self.memory_manager.cleanup()
            return True
        except Exception as e:
            self.logger.error(f"Error cleaning up memory: {str(e)}", exc_info=True)
            return False
            
    def _format_memory_entry(self, entry: MemoryEntry) -> Dict[str, Any]:
        """
        Format a MemoryEntry object as a dictionary.
        
        Args:
            entry: Memory entry to format
            
        Returns:
            Dict[str, Any]: Formatted memory entry
        """
        try:
            return {
                "memory_id": getattr(entry, "id", str(hash(entry))),
                "memory_type": entry.memory_type.value,
                "agent_id": entry.agent_id,
                "content": entry.content,
                "metadata": entry.metadata or {},
                "timestamp": entry.timestamp.isoformat() if hasattr(entry.timestamp, "isoformat") else str(entry.timestamp)
            }
        except Exception as e:
            self.logger.error(f"Error formatting memory entry: {str(e)}", exc_info=True)
            return {
                "memory_type": "unknown",
                "agent_id": "unknown",
                "content": {},
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat()
            }