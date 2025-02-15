import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import MemoryType, MemoryEntry
from .short_term.in_memory import ShortTermMemory
from .working.working_memory import WorkingMemory
from .long_term.persistent import LongTermMemory
from backend.config import Config

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages and coordinates different types of memory systems for agents.
    Provides a unified interface for memory operations while handling the 
    complexity of different memory types.
    """
    
    def __init__(self,
                 short_term: ShortTermMemory,
                 working: WorkingMemory,
                 long_term: LongTermMemory):
        self.short_term = short_term
        self.working = working
        self.long_term = long_term
        logger.info("Memory Manager initialized with all memory systems")
    
    @classmethod
    async def create(cls, db_url: str):
        """
        Create a new MemoryManager instance with all memory systems
        
        Args:
            db_url: Database connection string for long-term memory
            
        Returns:
            MemoryManager: Initialized memory manager instance
        """
        try:
            # Initialize memory systems
            short_term = ShortTermMemory()
            working = WorkingMemory()
            long_term = await LongTermMemory.create(Config.database_url())
            
            logger.info("Successfully created Memory Manager with all subsystems")
            return cls(short_term, working, long_term)
            
        except Exception as e:
            logger.error(f"Failed to create Memory Manager: {str(e)}")
            raise
    
    async def store(self,
                   agent_id: str,
                   memory_type: MemoryType,
                   content: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None,
                   importance: float = 0.0) -> bool:
        """
        Store information in the specified memory system
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to store in
            content: Data to store
            metadata: Optional metadata about the memory
            importance: Importance score (0.0 to 1.0) for long-term memories
            
        Returns:
            bool: Success status of the store operation
        """
        try:
            # Add importance to metadata for long-term storage
            if memory_type == MemoryType.LONG_TERM:
                metadata = {
                    **(metadata or {}),
                    'importance': importance
                }
            
            entry = MemoryEntry(
                agent_id=agent_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )
            
            if memory_type == MemoryType.SHORT_TERM:
                return await self.short_term.store(entry)
            elif memory_type == MemoryType.WORKING:
                return await self.working.store(entry)
            elif memory_type == MemoryType.LONG_TERM:
                return await self.long_term.store(entry)
            else:
                logger.error(f"Invalid memory type: {memory_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    async def retrieve(self,
                      agent_id: str,
                      memory_type: MemoryType,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve information from the specified memory system
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to retrieve from
            query: Optional query parameters to filter results
            sort_by: Field to sort by (for long-term memory)
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
        """
        try:
            if memory_type == MemoryType.SHORT_TERM:
                return await self.short_term.retrieve(agent_id, query)
            elif memory_type == MemoryType.WORKING:
                return await self.working.retrieve(agent_id, query)
            elif memory_type == MemoryType.LONG_TERM:
                return await self.long_term.retrieve(
                    agent_id,
                    query,
                    sort_by=sort_by,
                    limit=limit
                )
            else:
                logger.error(f"Invalid memory type: {memory_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    async def update(self,
                    agent_id: str,
                    memory_type: MemoryType,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing information in the specified memory system
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to update
            query: Query to identify the memory to update
            update_data: New data to update with
            
        Returns:
            bool: Success status of the update operation
        """
        try:
            if memory_type == MemoryType.SHORT_TERM:
                return await self.short_term.update(agent_id, query, update_data)
            elif memory_type == MemoryType.WORKING:
                return await self.working.update(agent_id, query, update_data)
            elif memory_type == MemoryType.LONG_TERM:
                return await self.long_term.update(agent_id, query, update_data)
            else:
                logger.error(f"Invalid memory type: {memory_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            return False
    
    async def consolidate_to_long_term(self,
                                     agent_id: str,
                                     importance_threshold: float = 0.5) -> bool:
        """
        Consolidate important short-term memories to long-term storage
        
        Args:
            agent_id: Unique identifier for the agent
            importance_threshold: Minimum importance score for consolidation
            
        Returns:
            bool: Success status of the consolidation operation
        """
        try:
            memories = await self.short_term.retrieve(agent_id)
            consolidated_count = 0
            
            for memory in memories:
                importance = memory.metadata.get('importance', 0.0) if memory.metadata else 0.0
                if importance >= importance_threshold:
                    memory.metadata = {**(memory.metadata or {}), 'consolidated_at': datetime.utcnow().isoformat()}
                    if await self.long_term.store(memory):
                        consolidated_count += 1
            
            logger.info(f"Consolidated {consolidated_count} short-term memories to long-term storage for agent {agent_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error consolidating memories: {str(e)}")
            return False
    
    async def add_memory_relationship(self,
                                    agent_id: str,
                                    source_id: int,
                                    target_id: int,
                                    relationship_type: str,
                                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a relationship between two long-term memories
        
        Args:
            agent_id: Agent identifier
            source_id: ID of the source memory
            target_id: ID of the target memory
            relationship_type: Type of relationship
            metadata: Optional relationship metadata
            
        Returns:
            bool: Success status
        """
        try:
            return await self.long_term.add_relationship(
                source_id,
                target_id,
                relationship_type,
                metadata
            )
        except Exception as e:
            logger.error(f"Error adding memory relationship: {str(e)}")
            return False
    
    async def update_memory_importance(self,
                                     agent_id: str,
                                     memory_id: int,
                                     importance: float) -> bool:
        """
        Update the importance score of a long-term memory
        
        Args:
            agent_id: Agent identifier
            memory_id: ID of the memory
            importance: New importance score (0.0 to 1.0)
            
        Returns:
            bool: Success status
        """
        try:
            return await self.long_term.update_importance(memory_id, importance)
        except Exception as e:
            logger.error(f"Error updating memory importance: {str(e)}")
            return False
    
    async def cleanup_old_memories(self,
                                 agent_id: str,
                                 max_age_days: int = 90,
                                 min_importance: float = 0.5) -> bool:
        """
        Clean up old, low-importance memories from long-term storage
        
        Args:
            agent_id: Agent identifier
            max_age_days: Maximum age of memories to keep
            min_importance: Minimum importance score to keep
            
        Returns:
            bool: Success status
        """
        try:
            return await self.long_term.cleanup_old_memories(
                max_age_days,
                min_importance
            )
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {str(e)}")
            return False