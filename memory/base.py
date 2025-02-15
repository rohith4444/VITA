from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
from core.logging.logger import setup_logger

# Initialize module logger
logger = setup_logger("memory.base")
logger.info("Initializing memory base module")

class MemoryType(Enum):
    """
    Types of memory available to agents.
    
    Attributes:
        SHORT_TERM: Temporary storage with automatic decay
        WORKING: Active processing state memory
        LONG_TERM: Persistent storage for important information
    """
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
    
    @classmethod
    def validate(cls, value: str) -> 'MemoryType':
        """Validate and convert string to MemoryType."""
        try:
            return cls(value)
        except ValueError as e:
            logger.error(f"Invalid memory type: {value}")
            raise ValueError(f"Invalid memory type. Must be one of {[t.value for t in cls]}")

class MemoryEntry(BaseModel):
    """
    Base model for memory entries.
    
    Attributes:
        timestamp: Time when the memory was created
        memory_type: Type of memory (SHORT_TERM, WORKING, LONG_TERM)
        agent_id: Unique identifier for the agent
        content: Main memory content
        metadata: Optional metadata about the memory
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    memory_type: MemoryType
    agent_id: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('agent_id')
    def validate_agent_id(cls, v: str) -> str:
        """Validate agent_id is not empty."""
        if not v or not v.strip():
            logger.error("Invalid empty agent_id")
            raise ValueError("agent_id cannot be empty")
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content is not empty."""
        if not v:
            logger.error("Invalid empty content")
            raise ValueError("content cannot be empty")
        return v

class BaseMemory(ABC):
    """
    Abstract base class for memory implementations.
    
    Provides interface for memory operations that must be implemented
    by specific memory type classes.
    """
    
    def __init__(self):
        self.logger = setup_logger(f"memory.{self.__class__.__name__.lower()}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry.
        
        Args:
            entry: MemoryEntry to store
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If entry validation fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, 
                      agent_id: str, 
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memory entries.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
            
        Raises:
            ValueError: If agent_id is invalid
        """
        pass
    
    @abstractmethod
    async def update(self, 
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing memory entries.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Query to identify memories to update
            update_data: New data to update with
            
        Returns:
            bool: Success status of the update operation
            
        Raises:
            ValueError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    async def clear(self, agent_id: str) -> bool:
        """
        Clear memory entries.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: Success status of the clear operation
            
        Raises:
            ValueError: If agent_id is invalid
        """
        pass

logger.info("Memory base module initialized successfully")