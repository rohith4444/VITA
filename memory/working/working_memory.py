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