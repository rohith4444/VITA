# memory/base.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel

class MemoryType(Enum):
    """Types of memory available to agents"""
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"

class MemoryEntry(BaseModel):
    """Base model for memory entries"""
    timestamp: datetime
    memory_type: MemoryType
    agent_id: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

class BaseMemory(ABC):
    """Abstract base class for memory implementations"""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry"""
        pass
    
    @abstractmethod
    async def retrieve(self, 
                      agent_id: str, 
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve memory entries"""
        pass
    
    @abstractmethod
    async def update(self, 
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """Update existing memory entries"""
        pass
    
    @abstractmethod
    async def clear(self, agent_id: str) -> bool:
        """Clear memory entries"""
        pass