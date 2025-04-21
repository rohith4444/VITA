import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from ..base import BaseMemory, MemoryEntry, MemoryType, AccessLevel, CleanableResource
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

@trace_class
class ShortTermMemory(BaseMemory, CleanableResource):
    """
    Implementation of short-term memory with automatic decay.
    Maintains temporary memory entries that expire after a configured duration.
    Enhanced to support priority-based retention and coordination messages.
    """
    
    def __init__(self, retention_period: timedelta = timedelta(minutes=30)):
        super().__init__()
        self.logger = setup_logger("memory.short_term")
        self.logger.info("Initializing Short-Term Memory")
        
        try:
            if retention_period.total_seconds() <= 0:
                raise ValueError("retention_period must be positive")
                
            self._storage: Dict[str, List[MemoryEntry]] = defaultdict(list)
            self._prioritized_storage: Dict[str, List[MemoryEntry]] = defaultdict(list)  # New: For high-priority entries
            self._coordination_messages: Dict[str, List[MemoryEntry]] = defaultdict(list)  # New: For coordination messages
            self._lock = asyncio.Lock()
            self.retention_period = retention_period
            self._extended_retention_period = retention_period * 3  # New: Longer retention for high-priority items
            
            # Initialize cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._metrics: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {"access_count": 0, "last_access": None}
            )
            
            # New: Backup storage for critical information
            self._critical_backup: Dict[str, Dict[str, MemoryEntry]] = defaultdict(dict)
            
            self.logger.info(f"Short-Term Memory initialized with {retention_period} retention period")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Short-Term Memory: {str(e)}", exc_info=True)
            raise
    
    @trace_method
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry with automatic expiration.
        Enhanced to handle priority-based retention and coordination messages.
        
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
                # Determine importance from metadata
                importance = entry.metadata.get('importance', 0.0) if entry.metadata else 0.0
                
                # Check if this is a coordination message
                is_coordination = False
                if entry.metadata and entry.metadata.get('message_type') == 'coordination':
                    is_coordination = True
                    self._coordination_messages[entry.agent_id].append(entry)
                    self.logger.debug(f"Stored coordination message for agent {entry.agent_id}")
                
                # Store based on priority
                if importance >= 0.7:  # High priority
                    self._prioritized_storage[entry.agent_id].append(entry)
                    
                    # Backup critical information (importance >= 0.9)
                    if importance >= 0.9:
                        memory_id = entry.metadata.get('memory_id', str(datetime.utcnow().timestamp()))
                        self._critical_backup[entry.agent_id][memory_id] = entry
                        self.logger.debug(f"Backed up critical memory for agent {entry.agent_id}")
                else:
                    # Regular storage
                    self._storage[entry.agent_id].append(entry)
                
                self._metrics[entry.agent_id]["access_count"] += 1
                self._metrics[entry.agent_id]["last_access"] = datetime.utcnow()
                
                self.logger.debug(
                    f"Stored memory for agent {entry.agent_id}, "
                    f"priority: {'high' if importance >= 0.7 else 'normal'}, "
                    f"coordination: {is_coordination}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve non-expired memory entries.
        Enhanced to include prioritized entries and coordination messages.
        
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
                prioritized_entries = self._prioritized_storage[agent_id]
                coordination_entries = self._coordination_messages[agent_id]
                current_time = datetime.utcnow()
                
                # Filter out expired entries based on their respective retention periods
                valid_entries = [
                    entry for entry in entries
                    if (current_time - entry.timestamp) <= self.retention_period
                ]
                
                valid_prioritized = [
                    entry for entry in prioritized_entries
                    if (current_time - entry.timestamp) <= self._extended_retention_period
                ]
                
                # Coordination messages have the same retention as high-priority items
                valid_coordination = [
                    entry for entry in coordination_entries
                    if (current_time - entry.timestamp) <= self._extended_retention_period
                ]
                
                # Combine all valid entries
                all_valid_entries = valid_entries + valid_prioritized + valid_coordination
                
                # Update metrics
                self._metrics[agent_id]["access_count"] += 1
                self._metrics[agent_id]["last_access"] = current_time
                
                if not query:
                    self.logger.debug(f"Retrieved {len(all_valid_entries)} valid memories")
                    return all_valid_entries
                
                # Filter based on query
                filtered_entries = [
                    entry for entry in all_valid_entries
                    if self._matches_query(entry, query)
                ]
                
                self.logger.debug(
                    f"Retrieved {len(filtered_entries)} memories matching query "
                    f"from {len(all_valid_entries)} valid entries"
                )
                return filtered_entries
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []
    
    def _matches_query(self, entry: MemoryEntry, query: Dict[str, Any]) -> bool:
        """
        Check if a memory entry matches query criteria.
        
        Args:
            entry: Memory entry to check
            query: Query criteria
            
        Returns:
            bool: True if entry matches query, False otherwise
        """
        # Check specific memory types
        if "memory_type" in query and entry.memory_type.value != query["memory_type"]:
            return False
            
        # Check project_id and task_id
        if "project_id" in query and entry.project_id != query["project_id"]:
            return False
            
        if "task_id" in query and entry.task_id != query["task_id"]:
            return False
            
        # Check metadata fields
        if "message_type" in query and (not entry.metadata or 
                                      entry.metadata.get("message_type") != query["message_type"]):
            return False
            
        # Check importance threshold if specified
        if "min_importance" in query and (not entry.metadata or 
                                        entry.metadata.get("importance", 0.0) < query["min_importance"]):
            return False
        
        # Check content fields
        for key, value in query.items():
            if key not in ["memory_type", "project_id", "task_id", "message_type", "min_importance"]:
                if key in entry.content and entry.content[key] != value:
                    return False
        
        return True
    
    @trace_method
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
                current_time = datetime.utcnow()
                updated = False
                
                # Function to update an entry
                def update_entry(entry):
                    nonlocal updated
                    # Check if entry matches query
                    if self._matches_query(entry, query):
                        # Update content
                        entry.content.update(update_data)
                        # Reset timestamp to extend expiration
                        entry.timestamp = current_time
                        updated = True
                        return True
                    return False
                
                # Update entries in regular storage
                updated_indices = []
                for i, entry in enumerate(self._storage[agent_id]):
                    if (current_time - entry.timestamp) <= self.retention_period:
                        if update_entry(entry):
                            updated_indices.append(i)
                
                # Update entries in prioritized storage
                updated_prioritized_indices = []
                for i, entry in enumerate(self._prioritized_storage[agent_id]):
                    if (current_time - entry.timestamp) <= self._extended_retention_period:
                        if update_entry(entry):
                            updated_prioritized_indices.append(i)
                
                # Update entries in coordination messages
                updated_coordination_indices = []
                for i, entry in enumerate(self._coordination_messages[agent_id]):
                    if (current_time - entry.timestamp) <= self._extended_retention_period:
                        if update_entry(entry):
                            updated_coordination_indices.append(i)
                
                # Update critical backup if needed
                for memory_id, entry in list(self._critical_backup[agent_id].items()):
                    if self._matches_query(entry, query):
                        entry.content.update(update_data)
                        entry.timestamp = current_time
                        self._critical_backup[agent_id][memory_id] = entry
                
                if updated:
                    self._metrics[agent_id]["access_count"] += 1
                    self._metrics[agent_id]["last_access"] = current_time
                    
                self.logger.info(
                    f"Memory update {'successful' if updated else 'failed'} "
                    f"(updated {len(updated_indices) + len(updated_prioritized_indices) + len(updated_coordination_indices)} entries)"
                )
                return updated
                
        except Exception as e:
            self.logger.error(f"Error updating memories: {str(e)}", exc_info=True)
            return False
    
    @trace_method
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
                # Clear normal storage
                self._storage[agent_id].clear()
                
                # Clear prioritized storage
                self._prioritized_storage[agent_id].clear()
                
                # Clear coordination messages
                self._coordination_messages[agent_id].clear()
                
                # Clear critical backup (but leave backup for audit purposes)
                # self._critical_backup[agent_id].clear()
                
                # Reset metrics
                self._metrics[agent_id] = {"access_count": 0, "last_access": None}
                
                self.logger.debug(f"Cleared all memories for agent {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing memories: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def _cleanup_loop(self):
        """
        Periodically clean up expired entries.
        Enhanced to handle different retention periods for different storage types.
        Runs as a background task to maintain memory freshness.
        """
        self.logger.info("Starting memory cleanup loop")
        while True:
            try:
                current_time = datetime.utcnow()
                cleanup_stats = {
                    "total_checked": 0, 
                    "expired_removed": 0,
                    "storage_types": {
                        "regular": {"checked": 0, "removed": 0},
                        "prioritized": {"checked": 0, "removed": 0},
                        "coordination": {"checked": 0, "removed": 0}
                    }
                }
                
                async with self._lock:
                    # Clean regular storage
                    for agent_id in self._storage:
                        original_count = len(self._storage[agent_id])
                        cleanup_stats["storage_types"]["regular"]["checked"] += original_count
                        cleanup_stats["total_checked"] += original_count
                        
                        # Filter out expired entries
                        self._storage[agent_id] = [
                            entry for entry in self._storage[agent_id]
                            if (current_time - entry.timestamp) <= self.retention_period
                        ]
                        
                        removed_count = original_count - len(self._storage[agent_id])
                        cleanup_stats["storage_types"]["regular"]["removed"] += removed_count
                        cleanup_stats["expired_removed"] += removed_count
                    
                    # Clean prioritized storage (with extended retention)
                    for agent_id in self._prioritized_storage:
                        original_count = len(self._prioritized_storage[agent_id])
                        cleanup_stats["storage_types"]["prioritized"]["checked"] += original_count
                        cleanup_stats["total_checked"] += original_count
                        
                        # Filter out expired entries with extended retention
                        self._prioritized_storage[agent_id] = [
                            entry for entry in self._prioritized_storage[agent_id]
                            if (current_time - entry.timestamp) <= self._extended_retention_period
                        ]
                        
                        removed_count = original_count - len(self._prioritized_storage[agent_id])
                        cleanup_stats["storage_types"]["prioritized"]["removed"] += removed_count
                        cleanup_stats["expired_removed"] += removed_count
                    
                    # Clean coordination messages (with extended retention)
                    for agent_id in self._coordination_messages:
                        original_count = len(self._coordination_messages[agent_id])
                        cleanup_stats["storage_types"]["coordination"]["checked"] += original_count
                        cleanup_stats["total_checked"] += original_count
                        
                        # Filter out expired entries with extended retention
                        self._coordination_messages[agent_id] = [
                            entry for entry in self._coordination_messages[agent_id]
                            if (current_time - entry.timestamp) <= self._extended_retention_period
                        ]
                        
                        removed_count = original_count - len(self._coordination_messages[agent_id])
                        cleanup_stats["storage_types"]["coordination"]["removed"] += removed_count
                        cleanup_stats["expired_removed"] += removed_count
                    
                    # Clean critical backup (keep for much longer - 7 days)
                    seven_days = timedelta(days=7)
                    for agent_id in self._critical_backup:
                        for memory_id in list(self._critical_backup[agent_id].keys()):
                            entry = self._critical_backup[agent_id][memory_id]
                            if (current_time - entry.timestamp) > seven_days:
                                del self._critical_backup[agent_id][memory_id]
                
                self.logger.info(
                    f"Cleanup complete: checked {cleanup_stats['total_checked']} memories, "
                    f"removed {cleanup_stats['expired_removed']} expired entries "
                    f"(regular: {cleanup_stats['storage_types']['regular']['removed']}, "
                    f"prioritized: {cleanup_stats['storage_types']['prioritized']['removed']}, "
                    f"coordination: {cleanup_stats['storage_types']['coordination']['removed']})"
                )
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except asyncio.CancelledError:
                self.logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # Continue cleanup even after errors
    
    @trace_method
    async def get_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get memory usage metrics for an agent.
        Enhanced to include metrics for different storage types.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dict[str, Any]: Memory metrics including access counts and timestamps
        """
        self.logger.debug(f"Retrieving metrics for agent {agent_id}")
        
        try:
            async with self._lock:
                current_time = datetime.utcnow()
                
                # Count valid entries in each storage type
                valid_entries = [
                    entry for entry in self._storage[agent_id]
                    if (current_time - entry.timestamp) <= self.retention_period
                ]
                
                valid_prioritized = [
                    entry for entry in self._prioritized_storage[agent_id]
                    if (current_time - entry.timestamp) <= self._extended_retention_period
                ]
                
                valid_coordination = [
                    entry for entry in self._coordination_messages[agent_id]
                    if (current_time - entry.timestamp) <= self._extended_retention_period
                ]
                
                # Count backup entries
                backup_count = len(self._critical_backup[agent_id])
                
                all_entries = valid_entries + valid_prioritized + valid_coordination
                
                return {
                    "total_memories": len(all_entries),
                    "regular_memories": len(valid_entries),
                    "prioritized_memories": len(valid_prioritized),
                    "coordination_messages": len(valid_coordination),
                    "critical_backups": backup_count,
                    "access_count": self._metrics[agent_id]["access_count"],
                    "last_access": self._metrics[agent_id]["last_access"],
                    "retention_period": self.retention_period.total_seconds(),
                    "extended_retention_period": self._extended_retention_period.total_seconds(),
                    "oldest_memory": min(([e.timestamp for e in all_entries] or [None])),
                    "newest_memory": max(([e.timestamp for e in all_entries] or [None]))
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
            return {}
    
    @trace_method
    async def retrieve_coordination_messages(self, 
                                          agent_id: str, 
                                          query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve coordination messages specifically.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of coordination messages
        """
        self.logger.info(f"Retrieving coordination messages for agent {agent_id}")
        
        try:
            async with self._lock:
                entries = self._coordination_messages[agent_id]
                current_time = datetime.utcnow()
                
                # Filter out expired entries
                valid_entries = [
                    entry for entry in entries
                    if (current_time - entry.timestamp) <= self._extended_retention_period
                ]
                
                # Apply additional query filters if provided
                if query:
                    valid_entries = [
                        entry for entry in valid_entries
                        if self._matches_query(entry, query)
                    ]
                
                self._metrics[agent_id]["access_count"] += 1
                self._metrics[agent_id]["last_access"] = current_time
                
                self.logger.debug(f"Retrieved {len(valid_entries)} coordination messages")
                return valid_entries
                
        except Exception as e:
            self.logger.error(f"Error retrieving coordination messages: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def retrieve_critical_backup(self, 
                                     agent_id: str, 
                                     memory_id: Optional[str] = None) -> Optional[MemoryEntry]:
        """
        Retrieve critical backup information.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_id: Optional specific memory ID to retrieve
            
        Returns:
            Optional[MemoryEntry]: The backed up memory entry if found
        """
        self.logger.info(f"Retrieving critical backup for agent {agent_id}")
        
        try:
            async with self._lock:
                if agent_id not in self._critical_backup:
                    return None
                
                if memory_id:
                    # Return specific memory
                    return self._critical_backup[agent_id].get(memory_id)
                else:
                    # Return most recent backup
                    backups = list(self._critical_backup[agent_id].values())
                    if not backups:
                        return None
                    
                    # Find the most recent
                    most_recent = max(backups, key=lambda entry: entry.timestamp)
                    return most_recent
                
        except Exception as e:
            self.logger.error(f"Error retrieving critical backup: {str(e)}", exc_info=True)
            return None

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

    @trace_method
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