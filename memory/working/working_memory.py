import asyncio, uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from ..base import BaseMemory, MemoryEntry, MemoryType, AccessLevel, CleanableResource
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

@trace_class
class WorkingMemory(BaseMemory, CleanableResource):
    """
    Implementation of working memory for active processing.
    Provides rapid access to current processing state and temporary data.
    Enhanced to support shared workspaces and multi-agent coordination.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logger("memory.working")
        self.logger.info("Initializing Working Memory")
        
        try:
            # Main storage for agent-specific memory
            self._storage: Dict[str, Dict[str, Any]] = {}
            
            # New storage for shared workspaces
            self._shared_workspaces: Dict[str, Dict[str, Any]] = {}
            
            # Maps workspace IDs to set of participant agent IDs
            self._workspace_participants: Dict[str, Set[str]] = {}
            
            # Storage for project state
            self._project_states: Dict[str, Dict[str, Any]] = {}
            
            # Storage for memory entries by ID for quick lookup
            self._memory_entries: Dict[str, MemoryEntry] = {}
            
            # Tracking data
            self._access_counts: Dict[str, int] = {}
            self._last_access: Dict[str, datetime] = {}
            
            # Locks for concurrency control
            self._agent_locks: Dict[str, asyncio.Lock] = {}
            self._workspace_locks: Dict[str, asyncio.Lock] = {}
            self._project_locks: Dict[str, asyncio.Lock] = {}
            self._global_lock = asyncio.Lock()
            
            # Notification callbacks (optional, for advanced integration)
            self._notification_callbacks: Dict[str, List[callable]] = {}
            
            self.logger.info("Working Memory initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Working Memory: {str(e)}", exc_info=True)
            raise
    
    async def _get_agent_lock(self, agent_id: str) -> asyncio.Lock:
        """Get or create a lock for an agent's memory."""
        async with self._global_lock:
            if agent_id not in self._agent_locks:
                self._agent_locks[agent_id] = asyncio.Lock()
            return self._agent_locks[agent_id]
    
    async def _get_workspace_lock(self, workspace_id: str) -> asyncio.Lock:
        """Get or create a lock for a shared workspace."""
        async with self._global_lock:
            if workspace_id not in self._workspace_locks:
                self._workspace_locks[workspace_id] = asyncio.Lock()
            return self._workspace_locks[workspace_id]
    
    async def _get_project_lock(self, project_id: str) -> asyncio.Lock:
        """Get or create a lock for a project state."""
        async with self._global_lock:
            if project_id not in self._project_locks:
                self._project_locks[project_id] = asyncio.Lock()
            return self._project_locks[project_id]
    
    @trace_method
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a memory entry in working memory.
        Enhanced to handle shared contexts and project states.
        
        Args:
            entry: Memory entry to store
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If entry is invalid
        """
        self.logger.info(f"Storing {entry.memory_type.value} memory for agent {entry.agent_id}")
        
        if not entry.content:
            self.logger.error("Attempted to store empty content")
            raise ValueError("Cannot store empty content")
            
        try:
            # Get memory ID from metadata or create one
            memory_id = entry.metadata.get('memory_id', str(uuid.uuid4())) if entry.metadata else str(uuid.uuid4())
            
            # Ensure metadata exists and has memory_id
            if not entry.metadata:
                entry.metadata = {}
            entry.metadata['memory_id'] = memory_id
            
            # Store based on memory type
            if entry.memory_type == MemoryType.WORKING:
                # Traditional working memory for a single agent
                return await self._store_agent_memory(entry)
                
            elif entry.memory_type == MemoryType.SHARED_CONTEXT:
                # Shared context between agents
                if not entry.project_id:
                    self.logger.error("project_id required for SHARED_CONTEXT memory")
                    return False
                return await self._store_shared_context(entry)
                
            elif entry.memory_type == MemoryType.PROJECT_STATE:
                # Project state tracking
                if not entry.project_id:
                    self.logger.error("project_id required for PROJECT_STATE memory")
                    return False
                return await self._store_project_state(entry)
                
            else:
                # Store as regular working memory by default
                self.logger.warning(f"Converting {entry.memory_type.value} to WORKING memory type")
                entry.memory_type = MemoryType.WORKING
                return await self._store_agent_memory(entry)
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def _store_agent_memory(self, entry: MemoryEntry) -> bool:
        """Store agent-specific working memory."""
        agent_id = entry.agent_id
        
        # Get lock for this agent
        agent_lock = await self._get_agent_lock(agent_id)
        
        async with agent_lock:
            # Initialize agent storage if needed
            if agent_id not in self._storage:
                self._storage[agent_id] = {}
                self._access_counts[agent_id] = 0
            
            # Store as key-value pairs for quick access
            self._storage[agent_id].update(entry.content)
            self._last_access[agent_id] = datetime.utcnow()
            
            # Store the full entry for reference
            self._memory_entries[entry.metadata['memory_id']] = entry
            
            self.logger.debug(f"Stored {len(entry.content)} items for agent {agent_id}")
            return True
    
    @trace_method
    async def _store_shared_context(self, entry: MemoryEntry) -> bool:
        """Store shared context in a workspace."""
        workspace_id = entry.project_id
        
        # Get lock for this workspace
        workspace_lock = await self._get_workspace_lock(workspace_id)
        
        async with workspace_lock:
            # Initialize workspace if needed
            if workspace_id not in self._shared_workspaces:
                self._shared_workspaces[workspace_id] = {}
            
            # Ensure this is a valid workspace participant
            if workspace_id not in self._workspace_participants:
                self._workspace_participants[workspace_id] = set()
            
            # Add the creator and anyone in the accessible_by set
            participants = self._workspace_participants[workspace_id]
            participants.add(entry.agent_id)
            if entry.accessible_by:
                participants.update(entry.accessible_by)
            self._workspace_participants[workspace_id] = participants
            
            # Store context data
            memory_id = entry.metadata['memory_id']
            self._shared_workspaces[workspace_id][memory_id] = entry
            
            # Store reference to the full entry
            self._memory_entries[memory_id] = entry
            
            self.logger.debug(f"Stored shared context in workspace {workspace_id} with {len(participants)} participants")
            
            # Notify participants (optional)
            await self._notify_workspace_update(workspace_id, entry.agent_id, entry)
            
            return True
    
    @trace_method
    async def _store_project_state(self, entry: MemoryEntry) -> bool:
        """Store project state information."""
        project_id = entry.project_id
        
        # Get lock for this project
        project_lock = await self._get_project_lock(project_id)
        
        async with project_lock:
            # Initialize project state if needed
            if project_id not in self._project_states:
                self._project_states[project_id] = {}
            
            # Store state data (overwrite existing)
            self._project_states[project_id] = entry.content
            
            # Store reference to the full entry
            memory_id = entry.metadata['memory_id']
            self._memory_entries[memory_id] = entry
            
            self.logger.debug(f"Stored project state for project {project_id}")
            return True
    
    @trace_method
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memory entries from working memory.
        Enhanced to handle different memory types and queries.
        
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
            # Check if query has memory type
            memory_type_str = query.get("memory_type") if query else None
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except (ValueError, KeyError):
                    self.logger.warning(f"Invalid memory type in query: {memory_type_str}")
            
            # Check if query has project ID
            project_id = query.get("project_id") if query else None
            
            # Retrieve based on memory type or query
            if memory_type == MemoryType.SHARED_CONTEXT and project_id:
                # Get shared context from a workspace
                return await self._retrieve_shared_context(agent_id, project_id, query)
                
            elif memory_type == MemoryType.PROJECT_STATE and project_id:
                # Get project state
                return await self._retrieve_project_state(agent_id, project_id, query)
                
            else:
                # Default to agent's own working memory
                return await self._retrieve_agent_memory(agent_id, query)
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def _retrieve_agent_memory(self, 
                                   agent_id: str,
                                   query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve agent-specific working memory."""
        # Get lock for this agent
        agent_lock = await self._get_agent_lock(agent_id)
        
        async with agent_lock:
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
                        'memory_id': f"working_{agent_id}_{datetime.utcnow().timestamp()}",
                        'access_count': self._access_counts[agent_id],
                        'last_access': self._last_access[agent_id].isoformat()
                    }
                )]
            
            # Filter based on query
            filtered_content = {
                k: v for k, v in content.items()
                if not query or self._matches_query(k, v, query)
            }
            
            self.logger.debug(f"Retrieved {len(filtered_content)} items matching query")
            
            if filtered_content:
                return [MemoryEntry(
                    agent_id=agent_id,
                    memory_type=MemoryType.WORKING,
                    content=filtered_content,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'memory_id': f"working_{agent_id}_{datetime.utcnow().timestamp()}",
                        'access_count': self._access_counts[agent_id],
                        'last_access': self._last_access[agent_id].isoformat()
                    }
                )]
            return []
    
    @trace_method
    async def _retrieve_shared_context(self,
                                     agent_id: str,
                                     workspace_id: str,
                                     query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve shared context from a workspace."""
        # Get lock for this workspace
        workspace_lock = await self._get_workspace_lock(workspace_id)
        
        async with workspace_lock:
            # Check if workspace exists
            if workspace_id not in self._shared_workspaces:
                self.logger.debug(f"Workspace {workspace_id} not found")
                return []
            
            # Check if agent is a participant
            if workspace_id in self._workspace_participants:
                participants = self._workspace_participants[workspace_id]
                if agent_id not in participants:
                    self.logger.warning(f"Agent {agent_id} is not a participant in workspace {workspace_id}")
                    return []
            
            # Get all context entries
            workspace_entries = list(self._shared_workspaces[workspace_id].values())
            
            # Filter based on access control
            accessible_entries = [
                entry for entry in workspace_entries
                if entry.can_access(agent_id)
            ]
            
            # Apply query filters if provided
            if query:
                filtered_entries = []
                for entry in accessible_entries:
                    if self._entry_matches_query(entry, query):
                        filtered_entries.append(entry)
                return filtered_entries
            
            return accessible_entries
    
    @trace_method
    async def _retrieve_project_state(self,
                                    agent_id: str,
                                    project_id: str,
                                    query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """Retrieve project state information."""
        # Get lock for this project
        project_lock = await self._get_project_lock(project_id)
        
        async with project_lock:
            # Check if project state exists
            if project_id not in self._project_states:
                self.logger.debug(f"Project state for {project_id} not found")
                return []
            
            # Get state content
            state_content = self._project_states[project_id]
            
            # Create a memory entry for the state
            state_entry = MemoryEntry(
                agent_id="team_lead",  # Project states are owned by team lead
                memory_type=MemoryType.PROJECT_STATE,
                content=state_content,
                project_id=project_id,
                timestamp=datetime.utcnow(),
                access_level=AccessLevel.TEAM,  # All team members can access
                metadata={
                    'memory_id': f"project_state_{project_id}_{datetime.utcnow().timestamp()}"
                }
            )
            
            # Apply query filters if provided
            if query and not self._entry_matches_query(state_entry, query):
                return []
            
            return [state_entry]
    
    def _matches_query(self, key: str, value: Any, query: Dict[str, Any]) -> bool:
        """Check if a key-value pair matches query criteria."""
        # Simple key-value matching
        for q_key, q_value in query.items():
            if q_key == key and q_value != value:
                return False
            
            # Handle nested dictionary values
            if isinstance(value, dict) and q_key in value:
                if value[q_key] != q_value:
                    return False
        
        return True
    
    def _entry_matches_query(self, entry: MemoryEntry, query: Dict[str, Any]) -> bool:
        """Check if a memory entry matches query criteria."""
        for key, value in query.items():
            # Skip memory_type as it's handled separately
            if key == "memory_type":
                continue
                
            # Check project_id
            if key == "project_id" and entry.project_id != value:
                return False
                
            # Check task_id
            if key == "task_id" and entry.task_id != value:
                return False
                
            # Check memory ID
            if key == "memory_id" and entry.metadata.get("memory_id") != value:
                return False
                
            # Check content fields
            if key in entry.content and entry.content[key] != value:
                return False
        
        return True
    
    @trace_method
    async def retrieve_shared(self,
                            agent_id: str,
                            query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve shared memory entries accessible to the agent.
        
        Args:
            agent_id: Unique identifier for the agent
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of accessible shared memory entries
        """
        self.logger.info(f"Retrieving shared memories for agent {agent_id}")
        
        shared_entries = []
        
        try:
            # Get project ID from query if available
            project_id = query.get("project_id") if query else None
            
            # If project specified, only check that workspace
            if project_id:
                if project_id in self._workspace_participants:
                    if agent_id in self._workspace_participants[project_id]:
                        workspace_entries = await self._retrieve_shared_context(agent_id, project_id, query)
                        shared_entries.extend(workspace_entries)
            else:
                # Check all workspaces this agent participates in
                for workspace_id, participants in self._workspace_participants.items():
                    if agent_id in participants:
                        workspace_entries = await self._retrieve_shared_context(agent_id, workspace_id, query)
                        shared_entries.extend(workspace_entries)
            
            # Sort by timestamp (newest first)
            shared_entries.sort(key=lambda entry: entry.timestamp, reverse=True)
            
            return shared_entries
            
        except Exception as e:
            self.logger.error(f"Error retrieving shared memories: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing memory entries in working memory.
        Enhanced to support different memory types.
        
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
            # Check if query has memory type
            memory_type_str = query.get("memory_type")
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except (ValueError, KeyError):
                    self.logger.warning(f"Invalid memory type in query: {memory_type_str}")
            
            # Check if query has project ID
            project_id = query.get("project_id")
            
            # Update based on memory type
            if memory_type == MemoryType.SHARED_CONTEXT and project_id:
                # Update shared context
                return await self._update_shared_context(agent_id, project_id, query, update_data)
                
            elif memory_type == MemoryType.PROJECT_STATE and project_id:
                # Update project state
                return await self._update_project_state(agent_id, project_id, query, update_data)
                
            else:
                # Default to agent's own working memory
                return await self._update_agent_memory(agent_id, query, update_data)
                
        except Exception as e:
            self.logger.error(f"Error updating memories: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def _update_agent_memory(self,
                                 agent_id: str,
                                 query: Dict[str, Any],
                                 update_data: Dict[str, Any]) -> bool:
        """Update agent-specific working memory."""
        # Get lock for this agent
        agent_lock = await self._get_agent_lock(agent_id)
        
        async with agent_lock:
            if agent_id not in self._storage:
                self.logger.debug(f"No memories found for agent {agent_id}")
                return False
            
            content = self._storage[agent_id]
            
            # Check if query matches
            matches = True
            for key, value in query.items():
                if key != "memory_type" and (key not in content or content[key] != value):
                    matches = False
                    break
            
            if matches:
                # Update content
                content.update(update_data)
                self._last_access[agent_id] = datetime.utcnow()
                self.logger.debug(f"Updated {len(update_data)} items for agent {agent_id}")
                return True
            
            self.logger.debug("No matching content found for update")
            return False
    
    @trace_method
    async def _update_shared_context(self,
                                   agent_id: str,
                                   workspace_id: str,
                                   query: Dict[str, Any],
                                   update_data: Dict[str, Any]) -> bool:
        """Update shared context in a workspace."""
        # Get lock for this workspace
        workspace_lock = await self._get_workspace_lock(workspace_id)
        
        async with workspace_lock:
            # Check if workspace exists
            if workspace_id not in self._shared_workspaces:
                self.logger.debug(f"Workspace {workspace_id} not found")
                return False
            
            # Check if agent is a participant
            if workspace_id in self._workspace_participants:
                participants = self._workspace_participants[workspace_id]
                if agent_id not in participants:
                    self.logger.warning(f"Agent {agent_id} is not a participant in workspace {workspace_id}")
                    return False
            
            # Look for memory to update
            memory_id = query.get("memory_id")
            if memory_id and memory_id in self._shared_workspaces[workspace_id]:
                entry = self._shared_workspaces[workspace_id][memory_id]
                
                # Check if agent can update this entry
                if entry.agent_id != agent_id:
                    # Only allow team_lead to update others' entries
                    if agent_id != "team_lead":
                        self.logger.warning(f"Agent {agent_id} cannot update entry created by {entry.agent_id}")
                        return False
                
                # Update entry content
                entry.content.update(update_data)
                entry.timestamp = datetime.utcnow()  # Update timestamp
                
                # Update version if present
                if entry.version:
                    # Auto-increment version (simple scheme: 1.0, 1.1, 1.2, etc.)
                    try:
                        major, minor = entry.version.split('.')
                        new_minor = int(minor) + 1
                        entry.version = f"{major}.{new_minor}"
                    except (ValueError, AttributeError):
                        # If current version is not in the expected format, reset to 1.0
                        entry.version = "1.0"
                
                # Notify participants
                await self._notify_workspace_update(workspace_id, agent_id, entry)
                
                self.logger.debug(f"Updated shared context {memory_id} in workspace {workspace_id}")
                return True
            
            # If no specific memory_id, look for entries that match other criteria
            for entry_id, entry in self._shared_workspaces[workspace_id].items():
                if self._entry_matches_query(entry, query):
                    # Update entry content
                    entry.content.update(update_data)
                    entry.timestamp = datetime.utcnow()  # Update timestamp
                    
                    # Notify participants
                    await self._notify_workspace_update(workspace_id, agent_id, entry)
                    
                    self.logger.debug(f"Updated shared context {entry_id} in workspace {workspace_id}")
                    return True
            
            self.logger.debug(f"No matching context found in workspace {workspace_id}")
            return False
    
    @trace_method
    async def _update_project_state(self,
                                  agent_id: str,
                                  project_id: str,
                                  query: Dict[str, Any],
                                  update_data: Dict[str, Any]) -> bool:
        """Update project state information."""
        # Get lock for this project
        project_lock = await self._get_project_lock(project_id)
        
        async with project_lock:
            # Check if project state exists
            if project_id not in self._project_states:
                self.logger.debug(f"Project state for {project_id} not found")
                return False
            
            # Get state content
            state_content = self._project_states[project_id]
            
            # Check access control (only team lead or agent updating their task)
            if agent_id != "team_lead":
                task_id = query.get("task_id")
                if not task_id or "tasks" not in state_content or task_id not in state_content["tasks"]:
                    self.logger.warning(f"Agent {agent_id} cannot update project state without task_id")
                    return False
                
                # Non-team-lead can only update their own task
                task = state_content["tasks"].get(task_id)
                if task and task.get("updated_by") != agent_id:
                    self.logger.warning(f"Agent {agent_id} cannot update task assigned to {task.get('updated_by')}")
                    return False
            
            # Apply updates
            if "tasks" in update_data:
                # Updating specific tasks
                if "tasks" not in state_content:
                    state_content["tasks"] = {}
                
                state_content["tasks"].update(update_data["tasks"])
                del update_data["tasks"]  # Remove to avoid duplicate update
            
            # Update other top-level fields
            state_content.update(update_data)
            
            # Add update metadata
            state_content["last_updated"] = datetime.utcnow().isoformat()
            state_content["updated_by"] = agent_id
            
            self.logger.debug(f"Updated project state for {project_id}")
            return True
    
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
            # Get lock for this agent
            agent_lock = await self._get_agent_lock(agent_id)
            
            async with agent_lock:
                # Clear agent-specific storage
                if agent_id in self._storage:
                    del self._storage[agent_id]
                    
                if agent_id in self._access_counts:
                    del self._access_counts[agent_id]
                    
                if agent_id in self._last_access:
                    del self._last_access[agent_id]
                
                # Remove from workspaces (but don't delete shared entries)
                workspaces_to_update = []
                for workspace_id, participants in self._workspace_participants.items():
                    if agent_id in participants:
                        participants.remove(agent_id)
                        workspaces_to_update.append(workspace_id)
                
                # Update workspace participants
                for workspace_id in workspaces_to_update:
                    workspace_lock = await self._get_workspace_lock(workspace_id)
                    async with workspace_lock:
                        if not self._workspace_participants[workspace_id]:
                            # No participants left, remove workspace
                            del self._workspace_participants[workspace_id]
                            if workspace_id in self._shared_workspaces:
                                del self._shared_workspaces[workspace_id]
                
                self.logger.debug(f"Cleared all memories for agent {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing memories: {str(e)}", exc_info=True)
            return False
    
    @trace_method
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
            # Get lock for this agent
            agent_lock = await self._get_agent_lock(agent_id)
            
            async with agent_lock:
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
    
    @trace_method
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
            # Get lock for this agent
            agent_lock = await self._get_agent_lock(agent_id)
            
            async with agent_lock:
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
    
    @trace_method
    async def create_workspace(self, workspace_id: str, creator_id: str, participants: Set[str]) -> bool:
        """
        Create a new shared workspace.
        
        Args:
            workspace_id: Unique identifier for the workspace
            creator_id: ID of the agent creating the workspace
            participants: Set of agent IDs that can participate
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Creating workspace {workspace_id} by agent {creator_id}")
        
        try:
            # Get lock for this workspace
            workspace_lock = await self._get_workspace_lock(workspace_id)
            
            async with workspace_lock:
                # Check if workspace already exists
                if workspace_id in self._shared_workspaces:
                    self.logger.warning(f"Workspace {workspace_id} already exists")
                    
                    # Update participants
                    existing_participants = self._workspace_participants.get(workspace_id, set())
                    updated_participants = existing_participants.union(participants)
                    self._workspace_participants[workspace_id] = updated_participants
                    
                    self.logger.info(f"Updated participants for workspace {workspace_id}")
                    return True
                
                # Create new workspace
                self._shared_workspaces[workspace_id] = {}
                self._workspace_participants[workspace_id] = participants.union({creator_id})
                
                self.logger.info(f"Created workspace {workspace_id} with {len(participants) + 1} participants")
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating workspace: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def get_workspace_participants(self, workspace_id: str) -> Set[str]:
        """
        Get the participants in a workspace.
        
        Args:
            workspace_id: Unique identifier for the workspace
            
        Returns:
            Set[str]: Set of participant agent IDs
        """
        self.logger.info(f"Getting participants for workspace {workspace_id}")
        
        try:
            # Get lock for this workspace
            workspace_lock = await self._get_workspace_lock(workspace_id)
            
            async with workspace_lock:
                return self._workspace_participants.get(workspace_id, set()).copy()
                
        except Exception as e:
            self.logger.error(f"Error getting workspace participants: {str(e)}", exc_info=True)
            return set()
    
    @trace_method
    async def add_workspace_participant(self, workspace_id: str, agent_id: str) -> bool:
        """
        Add a participant to a workspace.
        
        Args:
            workspace_id: Unique identifier for the workspace
            agent_id: ID of the agent to add
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Adding agent {agent_id} to workspace {workspace_id}")
        
        try:
            # Get lock for this workspace
            workspace_lock = await self._get_workspace_lock(workspace_id)
            
            async with workspace_lock:
                # Check if workspace exists
                if workspace_id not in self._shared_workspaces:
                    self.logger.warning(f"Workspace {workspace_id} does not exist")
                    return False
                
                # Add participant
                participants = self._workspace_participants.get(workspace_id, set())
                participants.add(agent_id)
                self._workspace_participants[workspace_id] = participants
                
                self.logger.info(f"Added agent {agent_id} to workspace {workspace_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding workspace participant: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def remove_workspace_participant(self, workspace_id: str, agent_id: str) -> bool:
        """
        Remove a participant from a workspace.
        
        Args:
            workspace_id: Unique identifier for the workspace
            agent_id: ID of the agent to remove
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Removing agent {agent_id} from workspace {workspace_id}")
        
        try:
            # Get lock for this workspace
            workspace_lock = await self._get_workspace_lock(workspace_id)
            
            async with workspace_lock:
                # Check if workspace exists
                if workspace_id not in self._shared_workspaces:
                    self.logger.warning(f"Workspace {workspace_id} does not exist")
                    return False
                
                # Remove participant
                participants = self._workspace_participants.get(workspace_id, set())
                if agent_id in participants:
                    participants.remove(agent_id)
                    self._workspace_participants[workspace_id] = participants
                    
                    # If no participants left, remove workspace
                    if not participants:
                        del self._workspace_participants[workspace_id]
                        del self._shared_workspaces[workspace_id]
                        self.logger.info(f"Removed empty workspace {workspace_id}")
                    else:
                        self.logger.info(f"Removed agent {agent_id} from workspace {workspace_id}")
                    
                    return True
                else:
                    self.logger.warning(f"Agent {agent_id} is not a participant in workspace {workspace_id}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error removing workspace participant: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def _notify_workspace_update(self, workspace_id: str, updater_id: str, entry: MemoryEntry) -> None:
        """
        Notify workspace participants about updates.
        
        Args:
            workspace_id: ID of the workspace
            updater_id: ID of the agent making the update
            entry: The updated memory entry
        """
        self.logger.debug(f"Notifying about update in workspace {workspace_id} by agent {updater_id}")
        
        try:
            # Get participants to notify
            participants = self._workspace_participants.get(workspace_id, set())
            
            # Don't notify the updater
            notify_agents = {agent_id for agent_id in participants if agent_id != updater_id}
            
            if not notify_agents:
                return
                
            # Execute notification callbacks if registered
            for agent_id in notify_agents:
                callbacks = self._notification_callbacks.get(agent_id, [])
                for callback in callbacks:
                    try:
                        if callable(callback):
                            # Pass workspace, updater, and entry to callback
                            await callback(workspace_id, updater_id, entry)
                    except Exception as e:
                        self.logger.error(f"Error in notification callback: {str(e)}", exc_info=True)
            
            self.logger.debug(f"Notified {len(notify_agents)} agents about workspace update")
            
        except Exception as e:
            self.logger.error(f"Error notifying workspace update: {str(e)}", exc_info=True)
    
    @trace_method
    def register_notification_callback(self, agent_id: str, callback: callable) -> None:
        """
        Register a callback for workspace notifications.
        
        Args:
            agent_id: ID of the agent to notify
            callback: Async function to call with (workspace_id, updater_id, entry)
        """
        self.logger.info(f"Registering notification callback for agent {agent_id}")
        
        if agent_id not in self._notification_callbacks:
            self._notification_callbacks[agent_id] = []
            
        self._notification_callbacks[agent_id].append(callback)
    
    @trace_method
    async def cleanup(self) -> None:
        """Cleanup resources before shutdown."""
        self.logger.info("Cleaning up Working Memory resources")
        try:
            async with self._global_lock:
                # Clear all storage
                self._storage.clear()
                self._shared_workspaces.clear()
                self._workspace_participants.clear()
                self._project_states.clear()
                self._memory_entries.clear()
                
                # Clear metrics and tracking data
                self._access_counts.clear()
                self._last_access.clear()
                
                # Clear callbacks
                self._notification_callbacks.clear()
                
                # Clear locks (no need to await them, just discard references)
                self._agent_locks.clear()
                self._workspace_locks.clear()
                self._project_locks.clear()
                
            self.logger.info("Working Memory cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during Working Memory cleanup: {str(e)}", exc_info=True)
            raise