# memory/working/working_memory.py

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..base import BaseMemory, MemoryEntry, MemoryType

class WorkingMemory(BaseMemory):
    """Implementation of working memory for active processing"""
    
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry"""
        async with self._lock:
            if entry.agent_id not in self._storage:
                self._storage[entry.agent_id] = {}
            
            # Store as key-value pairs for quick access
            self._storage[entry.agent_id].update(entry.content)
            return True
    
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve memory entries"""
        async with self._lock:
            if agent_id not in self._storage:
                return []
            
            content = self._storage[agent_id]
            if not query:
                return [MemoryEntry(
                    agent_id=agent_id,
                    memory_type=MemoryType.WORKING,
                    content=content,
                    timestamp=datetime.utcnow()
                )]
            
            # Filter based on query
            filtered_content = {
                k: v for k, v in content.items()
                if not query or all(content.get(qk) == qv for qk, qv in query.items())
            }
            
            if filtered_content:
                return [MemoryEntry(
                    agent_id=agent_id,
                    memory_type=MemoryType.WORKING,
                    content=filtered_content,
                    timestamp=datetime.utcnow()
                )]
            return []
    
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """Update existing memory entries"""
        async with self._lock:
            if agent_id not in self._storage:
                return False
            
            content = self._storage[agent_id]
            if all(content.get(k) == v for k, v in query.items()):
                content.update(update_data)
                return True
            return False
    
    async def clear(self, agent_id: str) -> bool:
        """Clear memory entries"""
        async with self._lock:
            if agent_id in self._storage:
                del self._storage[agent_id]
            return True
    
    async def get_working_state(self, agent_id: str) -> Dict[str, Any]:
        """Get the current working state for an agent"""
        async with self._lock:
            return self._storage.get(agent_id, {}).copy()