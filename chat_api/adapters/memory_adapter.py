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
    Adapter for the existing memory system.
    Provides an interface to the three-tier memory architecture for the chat API.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the memory adapter with a memory manager instance.
        
        Args:
            memory_manager: The memory manager from the existing system
        """
        self.logger = setup_logger("chat_api.adapters.memory.instance")
        self.logger.info("Initializing Memory Adapter")
        self.memory_manager = memory_manager
        
    @trace_method
    @monitor_operation(operation_type="memory_store", metadata={"memory_type": "short_term"})
    async def store_short_term(self, agent_id: str, content: Dict[str, Any], 
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store content in short-term memory.
        
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
        Store content in working memory.
        
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
                             importance: float = 0.5) -> bool:
        """
        Store content in long-term memory.
        
        Args:
            agent_id: Unique identifier for the agent/session
            content: Data to store
            metadata: Optional metadata about the memory
            importance: Importance score (0.0 to 1.0)
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Storing in long-term memory for agent {agent_id}")
        try:
            result = await self.memory_manager.store(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=content,
                metadata=metadata,
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
        Retrieve content from long-term memory.
        
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
    @monitor_operation(operation_type="memory_retrieve", metadata={"memory_type": "all"})
    async def retrieve_all_memory_types(self, agent_id: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve content from all memory types.
        
        Args:
            agent_id: Unique identifier for the agent/session
            query: Optional query parameters to filter results
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary with memory types as keys and lists of entries as values
        """
        self.logger.debug(f"Retrieving from all memory types for agent {agent_id}")
        result = {
            "short_term": [],
            "working": [],
            "long_term": []
        }
        
        try:
            # Retrieve from all memory types in parallel
            short_term = await self.retrieve_short_term(agent_id, query)
            working = await self.retrieve_working(agent_id, query)
            long_term = await self.retrieve_long_term(agent_id, query)
            
            result["short_term"] = short_term
            result["working"] = working
            result["long_term"] = long_term
            
            total_count = len(short_term) + len(working) + len(long_term)
            self.logger.debug(f"Retrieved {total_count} total entries from all memory types")
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving from all memory types: {str(e)}", exc_info=True)
            return result
    
    @trace_method
    @monitor_operation(operation_type="memory_update", metadata={"memory_type": "working"})
    async def update_working_memory(self, agent_id: str, query: Dict[str, Any], 
                                  update_data: Dict[str, Any]) -> bool:
        """
        Update content in working memory.
        
        Args:
            agent_id: Unique identifier for the agent/session
            query: Query to identify the memory to update
            update_data: New data to update
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Updating working memory for agent {agent_id}")
        try:
            return await self.memory_manager.update(
                agent_id=agent_id,
                memory_type=MemoryType.WORKING,
                query=query,
                update_data=update_data
            )
        except Exception as e:
            self.logger.error(f"Error updating working memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_consolidate")
    async def consolidate_to_long_term(self, agent_id: str, importance_threshold: float = 0.5) -> bool:
        """
        Consolidate important short-term memories to long-term storage.
        
        Args:
            agent_id: Unique identifier for the agent/session
            importance_threshold: Minimum importance score for consolidation
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Consolidating memories for agent {agent_id}")
        try:
            return await self.memory_manager.consolidate_to_long_term(
                agent_id=agent_id,
                importance_threshold=importance_threshold
            )
        except Exception as e:
            self.logger.error(f"Error consolidating memories: {str(e)}", exc_info=True)
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
                "memory_id": getattr(entry, "id", None),
                "memory_type": entry.memory_type.value,
                "agent_id": entry.agent_id,
                "content": entry.content,
                "metadata": entry.metadata,
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