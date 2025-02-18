import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ..base import BaseMemory, MemoryEntry, MemoryType
from core.logging.logger import setup_logger

class WorkingMemory(BaseMemory):
    """
    Implementation of working memory for active processing.
    Provides rapid access to current processing state and temporary data.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logger("memory.working")
        self.logger.info("Initializing Working Memory")
        
        try:
            self._storage: Dict[str, Dict[str, Any]] = {}
            self._lock = asyncio.Lock()
            self._access_counts: Dict[str, int] = {}
            self._last_access: Dict[str, datetime] = {}
            self.logger.info("Working Memory initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Working Memory: {str(e)}", exc_info=True)
            raise
    
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry in working memory.
        
        Args:
            entry: Memory entry to store
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If entry is invalid
        """
        self.logger.info(f"Storing memory for agent {entry.agent_id}")
        
        if not entry.content:
            self.logger.error("Attempted to store empty content")
            raise ValueError("Cannot store empty content")
            
        try:
            async with self._lock:
                if entry.agent_id not in self._storage:
                    self._storage[entry.agent_id] = {}
                    self._access_counts[entry.agent_id] = 0
                
                # Store as key-value pairs for quick access
                self._storage[entry.agent_id].update(entry.content)
                self._last_access[entry.agent_id] = datetime.utcnow()
                
                self.logger.debug(f"Stored {len(entry.content)} items for agent {entry.agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False
    
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memory entries from working memory.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
        """
        self.logger.info(f"Retrieving memories for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
        
        try:
            async with self._lock:
                if agent_id not in self._storage:
                    self.logger.debug(f"No memories found for agent {agent_id}")
                    return []
                
                content = self._storage[agent_id]
                self._access_counts[agent_id] = self._access_counts.get(agent_id, 0) + 1
                self._last_access[agent_id] = datetime.utcnow()
                
                if not query:
                    self.logger.debug(f"Retrieving all memories for agent {agent_id}")
                    return [MemoryEntry(
                        agent_id=agent_id,
                        memory_type=MemoryType.WORKING,
                        content=content,
                        timestamp=datetime.utcnow(),
                        metadata={
                            'access_count': self._access_counts[agent_id],
                            'last_access': self._last_access[agent_id].isoformat()
                        }
                    )]
                
                # Filter based on query
                filtered_content = {
                    k: v for k, v in content.items()
                    if not query or all(content.get(qk) == qv for qk, qv in query.items())
                }
                
                self.logger.debug(f"Retrieved {len(filtered_content)} items matching query")
                
                if filtered_content:
                    return [MemoryEntry(
                        agent_id=agent_id,
                        memory_type=MemoryType.WORKING,
                        content=filtered_content,
                        timestamp=datetime.utcnow(),
                        metadata={
                            'access_count': self._access_counts[agent_id],
                            'last_access': self._last_access[agent_id].isoformat()
                        }
                    )]
                return []
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []
        
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing memory entries in working memory.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Query to identify the memory to update
            update_data: New data to update with
            
        Returns:
            bool: Success status of the update operation
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Updating memories for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        if not query:
            self.logger.error("Empty query provided")
            raise ValueError("Query cannot be empty")
            
        if not update_data:
            self.logger.error("Empty update data provided")
            raise ValueError("Update data cannot be empty")
        
        try:
            async with self._lock:
                if agent_id not in self._storage:
                    self.logger.debug(f"No memories found for agent {agent_id}")
                    return False
                
                content = self._storage[agent_id]
                if all(content.get(k) == v for k, v in query.items()):
                    content.update(update_data)
                    self._last_access[agent_id] = datetime.utcnow()
                    self.logger.debug(f"Updated {len(update_data)} items for agent {agent_id}")
                    return True
                
                self.logger.debug("No matching content found for update")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating memories: {str(e)}", exc_info=True)
            return False
    
    async def clear(self, agent_id: str) -> bool:
        """
        Clear all memory entries for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: Success status of the clear operation
            
        Raises:
            ValueError: If agent_id is invalid
        """
        self.logger.info(f"Clearing memories for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
        
        try:
            async with self._lock:
                if agent_id in self._storage:
                    del self._storage[agent_id]
                    if agent_id in self._access_counts:
                        del self._access_counts[agent_id]
                    if agent_id in self._last_access:
                        del self._last_access[agent_id]
                    self.logger.debug(f"Cleared all memories for agent {agent_id}")
                else:
                    self.logger.debug(f"No memories found to clear for agent {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing memories: {str(e)}", exc_info=True)
            return False
    
    async def get_working_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the current working state for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dict[str, Any]: Current working state
            
        Raises:
            ValueError: If agent_id is invalid
        """
        self.logger.info(f"Getting working state for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
        
        try:
            async with self._lock:
                state = self._storage.get(agent_id, {}).copy()
                if state:
                    self._access_counts[agent_id] = self._access_counts.get(agent_id, 0) + 1
                    self._last_access[agent_id] = datetime.utcnow()
                    self.logger.debug(f"Retrieved working state with {len(state)} items")
                else:
                    self.logger.debug("No working state found")
                return state
                
        except Exception as e:
            self.logger.error(f"Error getting working state: {str(e)}", exc_info=True)
            return {}
        
    async def clear_if_inactive(self, agent_id: str, inactive_duration: timedelta = timedelta(hours=6)) -> bool:
        """
        Clears working memory if inactive for more than specified duration.
        
        Args:
            agent_id: Unique identifier for the agent
            inactive_duration: Duration after which memory is considered inactive
            
        Returns:
            bool: True if memory was cleared, False otherwise
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Checking inactivity for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        if inactive_duration.total_seconds() <= 0:
            self.logger.error("Invalid inactive duration provided")
            raise ValueError("inactive_duration must be positive")
        
        try:
            async with self._lock:
                last_access = self._last_access.get(agent_id)
                if not last_access:
                    self.logger.debug(f"No access history for agent {agent_id}")
                    return False
                
                if datetime.utcnow() - last_access > inactive_duration:
                    self.logger.info(f"Clearing inactive memory for agent {agent_id}")
                    await self.clear(agent_id)
                    return True
                
                self.logger.debug(f"Memory still active for agent {agent_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking inactivity: {str(e)}", exc_info=True)
            return False
        
    async def cleanup(self) -> None:
        """Cleanup resources before shutdown."""
        self.logger.info("Cleaning up Working Memory resources")
        try:
            async with self._lock:
                # Clear all storage
                self._storage.clear()
                
                # Clear metrics and tracking data
                self._access_counts.clear()
                self._last_access.clear()
                
                # Reset any other instance variables to initial state
                self._storage = {}
                self._access_counts = {}
                self._last_access = {}
                
            self.logger.info("Working Memory cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during Working Memory cleanup: {str(e)}", exc_info=True)
            raise