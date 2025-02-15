import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from ..base import BaseMemory, MemoryEntry, MemoryType

class ShortTermMemory(BaseMemory):
    """Implementation of short-term memory with automatic decay"""
    
    def __init__(self, retention_period: timedelta = timedelta(minutes=30)):
        self._storage: Dict[str, List[MemoryEntry]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self.retention_period = retention_period
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry"""
        async with self._lock:
            self._storage[entry.agent_id].append(entry)
            return True
    
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve memory entries"""
        async with self._lock:
            entries = self._storage[agent_id]
            current_time = datetime.utcnow()
            
            # Filter out expired entries
            valid_entries = [
                entry for entry in entries
                if (current_time - entry.timestamp) <= self.retention_period
            ]
            
            if not query:
                return valid_entries
            
            # Filter entries based on query
            return [
                entry for entry in valid_entries
                if all(entry.content.get(k) == v for k, v in query.items())
            ]
    
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """Update existing memory entries"""
        async with self._lock:
            entries = self._storage[agent_id]
            updated = False
            current_time = datetime.utcnow()
            
            for entry in entries:
                if (current_time - entry.timestamp) <= self.retention_period:
                    if all(entry.content.get(k) == v for k, v in query.items()):
                        entry.content.update(update_data)
                        entry.timestamp = current_time
                        updated = True
            
            return updated
    
    async def clear(self, agent_id: str) -> bool:
        """Clear memory entries"""
        async with self._lock:
            self._storage[agent_id].clear()
            return True
    
    async def _cleanup_loop(self):
        """Periodically clean up expired entries"""
        while True:
            try:
                current_time = datetime.utcnow()
                async with self._lock:
                    for agent_id in self._storage:
                        self._storage[agent_id] = [
                            entry for entry in self._storage[agent_id]
                            if (current_time - entry.timestamp) <= self.retention_period
                        ]
                await asyncio.sleep(60)  # Run cleanup every minute
            except Exception as e:
                print(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)