import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from ..base import BaseMemory, MemoryEntry, MemoryType
from core.logging.logger import setup_logger

class ShortTermMemory(BaseMemory):
    """
    Implementation of short-term memory with automatic decay.
    Maintains temporary memory entries that expire after a configured duration.
    """
    
    def __init__(self, retention_period: timedelta = timedelta(minutes=30)):
        super().__init__()
        self.logger = setup_logger("memory.short_term")
        self.logger.info("Initializing Short-Term Memory")
        
        try:
            if retention_period.total_seconds() <= 0:
                raise ValueError("retention_period must be positive")
                
            self._storage: Dict[str, List[MemoryEntry]] = defaultdict(list)
            self._lock = asyncio.Lock()
            self.retention_period = retention_period
            
            # Initialize cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._metrics: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {"access_count": 0, "last_access": None}
            )
            
            self.logger.info(f"Short-Term Memory initialized with {retention_period} retention period")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Short-Term Memory: {str(e)}", exc_info=True)
            raise
    
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry with automatic expiration.
        
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
                self._storage[entry.agent_id].append(entry)
                self._metrics[entry.agent_id]["access_count"] += 1
                self._metrics[entry.agent_id]["last_access"] = datetime.utcnow()
                
                self.logger.debug(
                    f"Stored memory for agent {entry.agent_id}, "
                    f"total memories: {len(self._storage[entry.agent_id])}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False
    
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve non-expired memory entries.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of valid memory entries
        """
        self.logger.info(f"Retrieving memories for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
        
        try:
            async with self._lock:
                entries = self._storage[agent_id]
                current_time = datetime.utcnow()
                
                # Filter out expired entries
                valid_entries = [
                    entry for entry in entries
                    if (current_time - entry.timestamp) <= self.retention_period
                ]
                
                # Update metrics
                self._metrics[agent_id]["access_count"] += 1
                self._metrics[agent_id]["last_access"] = current_time
                
                if not query:
                    self.logger.debug(f"Retrieved {len(valid_entries)} valid memories")
                    return valid_entries
                
                # Filter based on query
                filtered_entries = [
                    entry for entry in valid_entries
                    if all(entry.content.get(k) == v for k, v in query.items())
                ]
                
                self.logger.debug(
                    f"Retrieved {len(filtered_entries)} memories matching query "
                    f"from {len(valid_entries)} valid entries"
                )
                return filtered_entries
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []
        
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update non-expired memory entries matching the query.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Query to identify memories to update
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
                entries = self._storage[agent_id]
                updated = False
                current_time = datetime.utcnow()
                
                for entry in entries:
                    # Check if entry is still valid
                    if (current_time - entry.timestamp) <= self.retention_period:
                        # Check if entry matches query
                        if all(entry.content.get(k) == v for k, v in query.items()):
                            entry.content.update(update_data)
                            entry.timestamp = current_time  # Reset expiration
                            updated = True
                            self.logger.debug(f"Updated memory entry from {entry.timestamp}")
                
                if updated:
                    self._metrics[agent_id]["access_count"] += 1
                    self._metrics[agent_id]["last_access"] = current_time
                    
                self.logger.info(f"Memory update {'successful' if updated else 'failed'}")
                return updated
                
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
                self._storage[agent_id].clear()
                self._metrics[agent_id] = {"access_count": 0, "last_access": None}
                self.logger.debug(f"Cleared all memories for agent {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing memories: {str(e)}", exc_info=True)
            return False
    
    async def _cleanup_loop(self):
        """
        Periodically clean up expired entries.
        Runs as a background task to maintain memory freshness.
        """
        self.logger.info("Starting memory cleanup loop")
        while True:
            try:
                current_time = datetime.utcnow()
                cleanup_stats = {"total_checked": 0, "expired_removed": 0}
                
                async with self._lock:
                    for agent_id in self._storage:
                        original_count = len(self._storage[agent_id])
                        cleanup_stats["total_checked"] += original_count
                        
                        # Filter out expired entries
                        self._storage[agent_id] = [
                            entry for entry in self._storage[agent_id]
                            if (current_time - entry.timestamp) <= self.retention_period
                        ]
                        
                        removed_count = original_count - len(self._storage[agent_id])
                        cleanup_stats["expired_removed"] += removed_count
                        
                        if removed_count > 0:
                            self.logger.debug(
                                f"Removed {removed_count} expired memories for agent {agent_id}"
                            )
                
                self.logger.info(
                    f"Cleanup complete: checked {cleanup_stats['total_checked']} memories, "
                    f"removed {cleanup_stats['expired_removed']} expired entries"
                )
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except asyncio.CancelledError:
                self.logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # Continue cleanup even after errors
    
    async def get_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get memory usage metrics for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dict[str, Any]: Memory metrics including access counts and timestamps
        """
        self.logger.debug(f"Retrieving metrics for agent {agent_id}")
        
        try:
            async with self._lock:
                current_time = datetime.utcnow()
                valid_entries = [
                    entry for entry in self._storage[agent_id]
                    if (current_time - entry.timestamp) <= self.retention_period
                ]
                
                return {
                    "total_memories": len(valid_entries),
                    "access_count": self._metrics[agent_id]["access_count"],
                    "last_access": self._metrics[agent_id]["last_access"],
                    "retention_period": self.retention_period.total_seconds(),
                    "oldest_memory": min((e.timestamp for e in valid_entries), default=None),
                    "newest_memory": max((e.timestamp for e in valid_entries), default=None)
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
            return {}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        Ensures cleanup task is properly cancelled.
        """
        self.logger.info("Shutting down Short-Term Memory")
        if self._cleanup_task and not self._cleanup_task.cancelled():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def cleanup(self) -> None:
        """Cleanup resources before shutdown."""
        self.logger.info("Cleaning up Short-Term Memory resources")
        if self._cleanup_task and not self._cleanup_task.cancelled():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Short-Term Memory cleanup completed")