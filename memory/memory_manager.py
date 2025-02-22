from typing import Dict, Any, Optional, List
from datetime import datetime
from core.logging.logger import setup_logger
from .base import MemoryType, MemoryEntry, CleanableResource
from .short_term.in_memory import ShortTermMemory
from .working.working_memory import WorkingMemory
from .long_term.persistent import LongTermMemory
from backend.config import config
from core.tracing.service import trace_class

# Initialize module logger at the top level
memory_logger = setup_logger("memory.manager")

@trace_class
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
        self.logger = setup_logger("memory.manager.instance")
        
        try:
            self.short_term = short_term
            self.working = working
            self.long_term = long_term
            self.logger.info("Memory Manager initialized with all memory systems")
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory Manager: {str(e)}", exc_info=True)
            raise

    @classmethod
    async def create(cls, db_url: str) -> 'MemoryManager':
        """
        Create a new MemoryManager instance with all memory systems.
        """
        memory_logger.info("Creating new Memory Manager instance")
        
        if not db_url:
            memory_logger.error("Invalid database URL provided")
            raise ValueError("Database URL cannot be empty")
            
        try:
            # Initialize memory systems
            short_term = ShortTermMemory()
            memory_logger.debug("Short-term memory initialized")
            
            working = WorkingMemory()
            memory_logger.debug("Working memory initialized")
            
            long_term = await LongTermMemory.create(config.database_url())
            memory_logger.debug("Long-term memory initialized")
            
            memory_logger.info("Successfully created Memory Manager with all subsystems")
            return cls(short_term, working, long_term)
            
        except Exception as e:
            memory_logger.error(f"Failed to create Memory Manager: {str(e)}", exc_info=True)
            raise

    async def store(self,
                   agent_id: str,
                   memory_type: MemoryType,
                   content: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None,
                   importance: float = 0.0) -> bool:
        """
        Store information in the specified memory system.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to store in
            content: Data to store
            metadata: Optional metadata about the memory
            importance: Importance score (0.0 to 1.0) for long-term memories
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Storing memory for agent {agent_id} in {memory_type.value}")
        
        # Validate inputs
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        if not content:
            self.logger.error("Empty content provided")
            raise ValueError("content cannot be empty")
            
        if not 0.0 <= importance <= 1.0:
            self.logger.error(f"Invalid importance score: {importance}")
            raise ValueError("importance must be between 0.0 and 1.0")
        
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
            
            self.logger.debug(f"Created memory entry with timestamp {entry.timestamp}")
            
            if memory_type == MemoryType.SHORT_TERM:
                result = await self.short_term.store(entry)
            elif memory_type == MemoryType.WORKING:
                result = await self.working.store(entry)
            elif memory_type == MemoryType.LONG_TERM:
                result = await self.long_term.store(entry)
            else:
                self.logger.error(f"Invalid memory type: {memory_type}")
                return False
                
            self.logger.info(f"Successfully stored memory in {memory_type.value}")
            return result
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False
        
    async def retrieve(self,
                      agent_id: str,
                      memory_type: MemoryType,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve information from the specified memory system.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to retrieve from
            query: Optional query parameters to filter results
            sort_by: Field to sort by (for long-term memory)
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
            
        Raises:
            ValueError: If parameters are invalid
        """
        #self.logger.info(f"Retrieving memories for agent {agent_id} from {memory_type.value}")
        
        # Validate inputs
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        if limit < 1:
            self.logger.error(f"Invalid limit: {limit}")
            raise ValueError("limit must be positive")
            
        valid_sort_fields = {"timestamp", "importance", "access_count"}
        if sort_by not in valid_sort_fields:
            self.logger.error(f"Invalid sort field: {sort_by}")
            raise ValueError(f"sort_by must be one of {valid_sort_fields}")
        
        try:
            self.logger.debug(f"Retrieving with query: {query}")

            if isinstance(memory_type, str):
                try:
                    memory_type = MemoryType[memory_type.upper()]  # Convert from string to Enum
                except KeyError:
                    self.logger.error(f"Invalid memory type: {memory_type}")
                    return []

            self.logger.info(f"Retrieving memories for agent {agent_id} from {memory_type.value}")
            
            if memory_type == MemoryType.SHORT_TERM:
                results = await self.short_term.retrieve(agent_id, query)
            elif memory_type == MemoryType.WORKING:
                results = await self.working.retrieve(agent_id, query)
            elif memory_type == MemoryType.LONG_TERM:
                results = await self.long_term.retrieve(
                    agent_id,
                    query,
                    sort_by=sort_by,
                    limit=limit
                )
            else:
                self.logger.error(f"Invalid memory type: {memory_type}")
                return []
                
            self.logger.info(f"Retrieved {len(results)} memories from {memory_type.value}")
            self.logger.debug(f"First few results: {results[:3] if results else []}")
            return results
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []

    async def consolidate_to_long_term(self,
                                     agent_id: str,
                                     importance_threshold: float = 0.5) -> bool:
        """
        Consolidate important short-term memories to long-term storage.
        
        Args:
            agent_id: Unique identifier for the agent
            importance_threshold: Minimum importance score for consolidation
            
        Returns:
            bool: Success status of the consolidation operation
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Starting memory consolidation for agent {agent_id}")
        
        # Validate inputs
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        if not 0.0 <= importance_threshold <= 1.0:
            self.logger.error(f"Invalid importance threshold: {importance_threshold}")
            raise ValueError("importance_threshold must be between 0.0 and 1.0")
        
        try:
            self.logger.debug(f"Retrieving memories with importance >= {importance_threshold}")
            memories = await self.short_term.retrieve(agent_id)
            consolidated_count = 0
            
            for memory in memories:
                importance = memory.metadata.get('importance', 0.0) if memory.metadata else 0.0
                
                if importance >= importance_threshold:
                    self.logger.debug(f"Consolidating memory with importance {importance}")
                    
                    # Add consolidation metadata
                    memory.metadata = {
                        **(memory.metadata or {}),
                        'consolidated_at': datetime.utcnow().isoformat(),
                        'original_memory_type': memory.memory_type.value
                    }
                    
                    if await self.long_term.store(memory):
                        consolidated_count += 1
                        self.logger.debug(f"Successfully consolidated memory {consolidated_count}")
            
            self.logger.info(f"Consolidated {consolidated_count} memories for agent {agent_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error during memory consolidation: {str(e)}", exc_info=True)
            return False
        
    async def cleanup(self) -> None:
        """Cleanup memory systems before shutdown."""
        self.logger.info("Starting memory cleanup")
        try:
            # Cleanup cleanable resources
            cleanable_resources = [
                memory for memory in [self.short_term, self.working]
                if isinstance(memory, CleanableResource)
            ]
            
            for resource in cleanable_resources:
                try:
                    await resource.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up {resource.__class__.__name__}: {str(e)}")
            
            self.logger.info("Memory cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {str(e)}", exc_info=True)
            raise