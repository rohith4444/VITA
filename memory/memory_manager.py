from typing import Dict, Any, Optional, List, Set, Union, Tuple
from datetime import datetime
from core.logging.logger import setup_logger
from .base import MemoryType, MemoryEntry, CleanableResource, AccessLevel, ProjectPhase, RelationType, DeliverableType
from .short_term.in_memory import ShortTermMemory
from .working.working_memory import WorkingMemory
from .long_term.persistent import LongTermMemory
from backend.config import config
from core.tracing.service import trace_class, trace_method
import asyncio
import uuid

# Initialize module logger at the top level
memory_logger = setup_logger("memory.manager")

@trace_class
class MemoryManager:
    """
    Manages and coordinates different types of memory systems for agents.
    Provides a unified interface for memory operations while handling the 
    complexity of different memory types. Extended to support multi-agent
    coordination and project state tracking.
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
            self._locks = {}  # Dict to store locks for concurrent access
            self._project_metadata = {}  # Cache for project metadata
            self._shared_workspace_subscriptions = {}  # Dict to track workspace subscribers
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

    async def _get_lock(self, resource_id: str) -> asyncio.Lock:
        """
        Get or create a lock for a specific resource to manage concurrent access.
        
        Args:
            resource_id: Identifier for the resource to lock
            
        Returns:
            asyncio.Lock: The lock for this resource
        """
        if resource_id not in self._locks:
            self._locks[resource_id] = asyncio.Lock()
        return self._locks[resource_id]

    @trace_method
    async def store(self,
                   agent_id: str,
                   memory_type: MemoryType,
                   content: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None,
                   importance: float = 0.0,
                   project_id: Optional[str] = None,
                   task_id: Optional[str] = None,
                   access_level: AccessLevel = AccessLevel.PRIVATE,
                   accessible_by: Optional[Set[str]] = None,
                   phase: Optional[ProjectPhase] = None,
                   deliverable_type: Optional[DeliverableType] = None,
                   parent_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Store information in the specified memory system.
        Enhanced to support project state, task info, and access control.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to store in
            content: Data to store
            metadata: Optional metadata about the memory
            importance: Importance score (0.0 to 1.0) for long-term memories
            project_id: Optional project identifier
            task_id: Optional task identifier
            access_level: Access control level
            accessible_by: Set of agent IDs that can access this memory if SHARED
            phase: Optional project phase
            deliverable_type: Type of deliverable if memory_type is DELIVERABLE
            parent_id: Optional parent memory ID for hierarchical structures
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, memory entry ID if created)
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Storing {memory_type.value} memory for agent {agent_id}" + 
                        (f" in project {project_id}" if project_id else ""))
        
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
        
        if memory_type == MemoryType.DELIVERABLE and deliverable_type is None:
            self.logger.error("Deliverable type required for deliverable memory")
            raise ValueError("deliverable_type must be provided when memory_type is DELIVERABLE")
            
        if access_level == AccessLevel.SHARED and not accessible_by:
            self.logger.error("Shared access requires accessible_by")
            raise ValueError("accessible_by must be provided when access_level is SHARED")
        
        try:
            # Generate a unique ID for the memory entry
            memory_id = str(uuid.uuid4())
            
            # Add importance to metadata for any memory type
            metadata = {
                **(metadata or {}),
                'importance': importance,
                'memory_id': memory_id
            }
            
            entry = MemoryEntry(
                agent_id=agent_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata,
                timestamp=datetime.utcnow(),
                project_id=project_id,
                task_id=task_id,
                access_level=access_level,
                accessible_by=accessible_by,
                phase=phase,
                deliverable_type=deliverable_type,
                parent_id=parent_id
            )
            
            self.logger.debug(f"Created memory entry with ID {memory_id}")
            
            # Store in appropriate memory system
            if memory_type in [MemoryType.SHORT_TERM, MemoryType.WORKING, MemoryType.LONG_TERM]:
                # Traditional memory types
                if memory_type == MemoryType.SHORT_TERM:
                    result = await self.short_term.store(entry)
                elif memory_type == MemoryType.WORKING:
                    result = await self.working.store(entry)
                elif memory_type == MemoryType.LONG_TERM:
                    result = await self.long_term.store(entry)
                
            elif memory_type == MemoryType.PROJECT_STATE:
                # Project state is stored in working memory with special handling
                if not project_id:
                    self.logger.error("project_id required for PROJECT_STATE memory")
                    return False, None
                
                # Use lock to prevent concurrent modifications to project state
                async with await self._get_lock(f"project_{project_id}"):
                    result = await self.working.store(entry)
                    
                    # Update project metadata cache
                    if project_id not in self._project_metadata:
                        self._project_metadata[project_id] = {}
                    self._project_metadata[project_id].update({
                        "last_updated": datetime.utcnow().isoformat(),
                        "updated_by": agent_id,
                        "state_memory_id": memory_id
                    })
                
            elif memory_type == MemoryType.SHARED_CONTEXT:
                # Shared context stored in working memory with notification
                result = await self.working.store(entry)
                
                # Notify subscribers if this is in a shared workspace
                if project_id and project_id in self._shared_workspace_subscriptions:
                    await self._notify_workspace_update(project_id, agent_id, "context_update", {
                        "memory_id": memory_id,
                        "update_type": "new_context",
                        "workspace": project_id
                    })
                
            elif memory_type == MemoryType.DELIVERABLE:
                # Deliverables stored in long-term memory with special indexing
                if not deliverable_type:
                    self.logger.error("deliverable_type required for DELIVERABLE memory")
                    return False, None
                    
                result = await self.long_term.store(entry)
                
                # If this is task output, notify team lead
                if task_id:
                    # This is a placeholder for actual notification mechanism
                    self.logger.info(f"Deliverable for task {task_id} stored by agent {agent_id}")
                
            else:
                self.logger.error(f"Unsupported memory type: {memory_type}")
                return False, None
                
            self.logger.info(f"Successfully stored {memory_type.value} memory with ID {memory_id}")
            return result, memory_id
                
        except Exception as e:
            self.logger.error(f"Error storing memory: {str(e)}", exc_info=True)
            return False, None
        
    @trace_method
    async def retrieve(self,
                      agent_id: str,
                      memory_type: MemoryType,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100,
                      include_shared: bool = False) -> List[MemoryEntry]:
        """
        Retrieve information from the specified memory system.
        Enhanced to support shared memory access and more filtering options.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_type: Type of memory to retrieve from
            query: Optional query parameters to filter results
            sort_by: Field to sort by (for long-term memory)
            limit: Maximum number of memories to return
            include_shared: Whether to include memories shared with this agent
            
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
            
            # Basic retrieval from memory systems
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
            elif memory_type == MemoryType.PROJECT_STATE:
                # Project state is in working memory with special handling
                if not query or "project_id" not in query:
                    self.logger.error("project_id must be specified in query for PROJECT_STATE")
                    return []
                
                # Use specialized project state retrieval
                project_id = query["project_id"]
                results = await self._retrieve_project_state(agent_id, project_id)
                
            elif memory_type == MemoryType.SHARED_CONTEXT:
                # Retrieve shared context from working memory
                results = await self.working.retrieve(agent_id, query)
                
            elif memory_type == MemoryType.DELIVERABLE:
                # Deliverables are in long-term with special query handling
                deliv_query = query or {}
                deliv_query["memory_type"] = MemoryType.DELIVERABLE.value
                results = await self.long_term.retrieve(
                    agent_id,
                    deliv_query,
                    sort_by=sort_by,
                    limit=limit
                )
                
            else:
                self.logger.error(f"Invalid memory type: {memory_type}")
                return []
                
            # Include shared memories if requested
            if include_shared and memory_type != MemoryType.PROJECT_STATE:
                # Project state is already shared by default
                shared_entries = await self._retrieve_shared_memories(
                    agent_id, memory_type, query, sort_by, limit
                )
                results.extend(shared_entries)
                
                # Re-sort combined results
                results.sort(key=lambda entry: getattr(entry, sort_by, entry.timestamp), reverse=True)
                
                # Re-apply limit
                results = results[:limit]
                
            self.logger.info(f"Retrieved {len(results)} memories from {memory_type.value}")
            return results
                
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}", exc_info=True)
            return []

    @trace_method
    async def _retrieve_project_state(self, agent_id: str, project_id: str) -> List[MemoryEntry]:
        """
        Specialized method to retrieve project state with access control.
        
        Args:
            agent_id: ID of the agent requesting access
            project_id: ID of the project
            
        Returns:
            List[MemoryEntry]: Project state memory entries
        """
        self.logger.info(f"Retrieving project state for project {project_id}")
        
        # Create a query for project state
        query = {
            "memory_type": MemoryType.PROJECT_STATE.value,
            "project_id": project_id
        }
        
        # Get all project state entries
        all_entries = await self.working.retrieve("team_lead", query)  # Use team lead as creator of project state
        
        # Filter for entries this agent can access
        accessible_entries = [
            entry for entry in all_entries
            if entry.can_access(agent_id)
        ]
        
        return accessible_entries
    
    @trace_method
    async def _retrieve_shared_memories(self,
                                       agent_id: str,
                                       memory_type: MemoryType,
                                       query: Optional[Dict[str, Any]],
                                       sort_by: str,
                                       limit: int) -> List[MemoryEntry]:
        """
        Retrieve memories shared with an agent.
        
        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            query: Optional query parameters
            sort_by: Field to sort by
            limit: Maximum number of entries
            
        Returns:
            List[MemoryEntry]: Shared memories accessible to the agent
        """
        self.logger.info(f"Retrieving shared memories for agent {agent_id}")
        
        # Determine which memory store to use
        if memory_type == MemoryType.SHORT_TERM:
            memory_store = self.short_term
        elif memory_type == MemoryType.WORKING or memory_type == MemoryType.SHARED_CONTEXT:
            memory_store = self.working
        elif memory_type in [MemoryType.LONG_TERM, MemoryType.DELIVERABLE]:
            memory_store = self.long_term
        else:
            return []
        
        # For specialized stores that implement retrieve_shared, use that
        if hasattr(memory_store, "retrieve_shared"):
            return await memory_store.retrieve_shared(agent_id, query)
        
        # Otherwise use generic implementation
        # This is inefficient for large datasets but works as a fallback
        
        # Get all entries from other agents
        entries_from_others = []
        
        # Get list of all agents (this is a placeholder - in practice, get from agent registry)
        all_agents = ["team_lead", "solution_architect", "full_stack_developer", "qa_test"]
        
        for other_agent in all_agents:
            if other_agent == agent_id:
                continue  # Skip self
                
            other_entries = await memory_store.retrieve(other_agent, query)
            entries_from_others.extend(other_entries)
        
        # Filter for entries this agent can access
        accessible_entries = [
            entry for entry in entries_from_others
            if entry.can_access(agent_id)
        ]
        
        # Sort and limit
        accessible_entries.sort(key=lambda entry: getattr(entry, sort_by, entry.timestamp), reverse=True)
        return accessible_entries[:limit]

    @trace_method
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
    
    @trace_method
    async def update(self,
                    agent_id: str,
                    memory_type: MemoryType,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any],
                    project_id: Optional[str] = None) -> bool:
        """
        Update existing memories.
        
        Args:
            agent_id: Agent identifier
            memory_type: Type of memory to update
            query: Query to identify memories to update
            update_data: Data to update
            project_id: Optional project identifier for project state updates
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Updating {memory_type.value} memory for agent {agent_id}")
        
        try:
            if memory_type == MemoryType.SHORT_TERM:
                return await self.short_term.update(agent_id, query, update_data)
            elif memory_type == MemoryType.WORKING:
                return await self.working.update(agent_id, query, update_data)
            elif memory_type == MemoryType.LONG_TERM:
                return await self.long_term.update(agent_id, query, update_data)
            elif memory_type == MemoryType.PROJECT_STATE:
                # Project state requires special handling
                if not project_id:
                    self.logger.error("project_id required for PROJECT_STATE memory")
                    return False
                    
                # Use lock to prevent concurrent modifications
                async with await self._get_lock(f"project_{project_id}"):
                    # Update project state
                    combined_query = {**query, "project_id": project_id}
                    result = await self.working.update(agent_id, combined_query, update_data)
                    
                    if result:
                        # Notify subscribers of the update
                        await self._notify_workspace_update(project_id, agent_id, "state_update", {
                            "update_type": "project_state_modified",
                            "modified_fields": list(update_data.keys())
                        })
                        
                        # Update project metadata cache
                        if project_id in self._project_metadata:
                            self._project_metadata[project_id].update({
                                "last_updated": datetime.utcnow().isoformat(),
                                "updated_by": agent_id
                            })
                    
                    return result
            else:
                self.logger.error(f"Unsupported memory type for update: {memory_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating memory: {str(e)}", exc_info=True)
            return False
        
    @trace_method
    async def cleanup(self) -> None:
        """Cleanup memory systems before shutdown."""
        self.logger.info("Starting memory cleanup")
        try:
            # Cleanup cleanable resources
            cleanable_resources = [
                memory for memory in [self.short_term, self.working, self.long_term]
                if isinstance(memory, CleanableResource)
            ]
            
            for resource in cleanable_resources:
                try:
                    await resource.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up {resource.__class__.__name__}: {str(e)}")
            
            # Clear cache and locks
            self._project_metadata.clear()
            self._locks.clear()
            self._shared_workspace_subscriptions.clear()
            
            self.logger.info("Memory cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {str(e)}", exc_info=True)
            raise

    # New methods for multi-agent support and project state tracking

    @trace_method
    async def store_project_state(self,
                                 agent_id: str,
                                 project_id: str,
                                 state_data: Dict[str, Any],
                                 metadata: Optional[Dict[str, Any]] = None,
                                 access_level: AccessLevel = AccessLevel.TEAM) -> Tuple[bool, Optional[str]]:
        """
        Store project state information.
        
        Args:
            agent_id: Agent storing the state
            project_id: Project identifier
            state_data: Project state data
            metadata: Optional metadata
            access_level: Who can access this state
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, memory ID if created)
        """
        self.logger.info(f"Storing project state for project {project_id} by agent {agent_id}")
        
        try:
            # Use the main store method with PROJECT_STATE type
            return await self.store(
                agent_id=agent_id,
                memory_type=MemoryType.PROJECT_STATE,
                content=state_data,
                metadata=metadata,
                project_id=project_id,
                access_level=access_level,
                importance=1.0  # Project state is always important
            )
            
        except Exception as e:
            self.logger.error(f"Error storing project state: {str(e)}", exc_info=True)
            return False, None

    @trace_method
    async def retrieve_project_state(self,
                                   agent_id: str,
                                   project_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current project state.
        
        Args:
            agent_id: Agent requesting the state
            project_id: Project identifier
            
        Returns:
            Optional[Dict[str, Any]]: Project state or None if not found
        """
        self.logger.info(f"Retrieving project state for project {project_id}")
        
        try:
            # Query for project state
            query = {"project_id": project_id}
            
            entries = await self.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.PROJECT_STATE,
                query=query,
                limit=1  # Get the most recent state
            )
            
            if not entries:
                self.logger.warning(f"No project state found for project {project_id}")
                return None
                
            # Return the content of the most recent state
            return entries[0].content
            
        except Exception as e:
            self.logger.error(f"Error retrieving project state: {str(e)}", exc_info=True)
            return None

    @trace_method
    async def store_deliverable(self,
                              agent_id: str,
                              deliverable_type: DeliverableType,
                              content: Dict[str, Any],
                              project_id: str,
                              task_id: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None,
                              access_level: AccessLevel = AccessLevel.TEAM) -> Tuple[bool, Optional[str]]:
        """
        Store a deliverable from an agent.
        
        Args:
            agent_id: Agent creating the deliverable
            deliverable_type: Type of deliverable
            content: Deliverable content
            project_id: Project identifier
            task_id: Optional task identifier
            metadata: Optional metadata
            access_level: Who can access this deliverable
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, deliverable ID if created)
        """
        self.logger.info(f"Storing {deliverable_type.value} deliverable for project {project_id} by agent {agent_id}")
        
        try:
            # Use the main store method with DELIVERABLE type
            return await self.store(
                agent_id=agent_id,
                memory_type=MemoryType.DELIVERABLE,
                content=content,
                metadata=metadata,
                project_id=project_id,
                task_id=task_id,
                access_level=access_level,
                deliverable_type=deliverable_type,
                importance=0.9  # Deliverables are important by default
            )
            
        except Exception as e:
            self.logger.error(f"Error storing deliverable: {str(e)}", exc_info=True)
            return False, None

    @trace_method
    async def retrieve_deliverables(self,
                                  agent_id: str,
                                  project_id: Optional[str] = None,
                                  task_id: Optional[str] = None,
                                  deliverable_type: Optional[DeliverableType] = None,
                                  limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve deliverables.
        
        Args:
            agent_id: Agent requesting deliverables
            project_id: Optional project filter
            task_id: Optional task filter
            deliverable_type: Optional deliverable type filter
            limit: Maximum number of deliverables to return
            
        Returns:
            List[MemoryEntry]: Matching deliverables
        """
        self.logger.info(f"Retrieving deliverables for agent {agent_id}")
        
        try:
            # Build query
            query = {}
            
            if project_id:
                query["project_id"] = project_id
                
            if task_id:
                query["task_id"] = task_id
                
            if deliverable_type:
                query["deliverable_type"] = deliverable_type.value
            
            # Use the main retrieve method with DELIVERABLE type
            return await self.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.DELIVERABLE,
                query=query,
                limit=limit,
                include_shared=True  # Always include shared deliverables
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving deliverables: {str(e)}", exc_info=True)
            return []

    @trace_method
    async def create_shared_workspace(self,
                                    creator_id: str,
                                    project_id: str,
                                    participants: Set[str],
                                    initial_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Create a shared workspace for collaboration.
        
        Args:
            creator_id: Agent creating the workspace
            project_id: Project identifier (used as workspace ID)
            participants: Set of agent IDs that can access the workspace
            initial_context: Optional initial shared context
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, workspace ID if created)
        """
        self.logger.info(f"Creating shared workspace for project {project_id} with {len(participants)} participants")
        
        try:
            # Track workspace subscribers
            self._shared_workspace_subscriptions[project_id] = participants
            
            # Store initial context if provided
            if initial_context:
                result, memory_id = await self.store(
                    agent_id=creator_id,
                    memory_type=MemoryType.SHARED_CONTEXT,
                    content=initial_context,
                    project_id=project_id,
                    access_level=AccessLevel.SHARED,
                    accessible_by=participants,
                    metadata={"workspace_id": project_id, "workspace_creator": creator_id}
                )
                
                # Notify all participants
                for participant in participants:
                    if participant != creator_id:
                        await self._notify_workspace_update(project_id, participant, "workspace_created", {
                            "creator_id": creator_id,
                            "workspace_id": project_id,
                            "participant_count": len(participants)
                        })
                
                self.logger.info(f"Successfully created shared workspace for project {project_id}")
                return True, project_id
            else:
                # Just register the workspace without initial context
                self.logger.info(f"Registered shared workspace for project {project_id} without initial context")
                return True, project_id
                
        except Exception as e:
            self.logger.error(f"Error creating shared workspace: {str(e)}", exc_info=True)
            return False, None

    @trace_method
    async def update_shared_workspace(self,
                                    agent_id: str,
                                    project_id: str,
                                    context_update: Dict[str, Any],
                                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a shared workspace with new context.
        
        Args:
            agent_id: Agent updating the workspace
            project_id: Project/workspace identifier
            context_update: New context data
            metadata: Optional metadata
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Updating shared workspace for project {project_id} by agent {agent_id}")
        
        try:
            # Check if agent is a participant
            if project_id not in self._shared_workspace_subscriptions:
                self.logger.error(f"Workspace {project_id} does not exist")
                return False
                
            participants = self._shared_workspace_subscriptions[project_id]
            if agent_id not in participants:
                self.logger.error(f"Agent {agent_id} is not a participant in workspace {project_id}")
                return False
                
            # Store the context update
            result, memory_id = await self.store(
                agent_id=agent_id,
                memory_type=MemoryType.SHARED_CONTEXT,
                content=context_update,
                project_id=project_id,
                access_level=AccessLevel.SHARED,
                accessible_by=participants,
                metadata=metadata or {"workspace_id": project_id, "update_type": "context"}
            )
            
            if result:
                # Notify other participants
                for participant in participants:
                    if participant != agent_id:
                        await self._notify_workspace_update(project_id, participant, "context_updated", {
                            "updater_id": agent_id,
                            "workspace_id": project_id,
                            "memory_id": memory_id
                        })
                
                self.logger.info(f"Successfully updated shared workspace for project {project_id}")
                return True
            else:
                self.logger.error(f"Failed to store context update for workspace {project_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating shared workspace: {str(e)}", exc_info=True)
            return False

    @trace_method
    async def retrieve_shared_workspace(self,
                                      agent_id: str,
                                      project_id: str,
                                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve context from a shared workspace.
        
        Args:
            agent_id: Agent requesting the context
            project_id: Project/workspace identifier
            limit: Maximum number of context entries to return
            
        Returns:
            List[MemoryEntry]: Shared context entries
        """
        self.logger.info(f"Retrieving shared workspace for project {project_id} by agent {agent_id}")
        
        try:
            # Check if agent is a participant
            if project_id not in self._shared_workspace_subscriptions:
                self.logger.error(f"Workspace {project_id} does not exist")
                return []
                
            participants = self._shared_workspace_subscriptions[project_id]
            if agent_id not in participants:
                self.logger.error(f"Agent {agent_id} is not a participant in workspace {project_id}")
                return []
                
            # Build query
            query = {
                "project_id": project_id,
                "memory_type": MemoryType.SHARED_CONTEXT.value
            }
            
            # Retrieve all context entries accessible to this agent
            entries = await self.retrieve(
                agent_id=agent_id,
                memory_type=MemoryType.SHARED_CONTEXT,
                query=query,
                limit=limit,
                include_shared=True
            )
            
            self.logger.info(f"Retrieved {len(entries)} shared context entries for project {project_id}")
            return entries
            
        except Exception as e:
            self.logger.error(f"Error retrieving shared workspace: {str(e)}", exc_info=True)
            return []

    @trace_method
    async def add_workspace_participant(self,
                                      agent_id: str,
                                      project_id: str,
                                      new_participant: str) -> bool:
        """
        Add a participant to a shared workspace.
        
        Args:
            agent_id: Agent adding the participant (must be creator)
            project_id: Project/workspace identifier
            new_participant: ID of the agent to add
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Adding participant {new_participant} to workspace {project_id}")
        
        try:
            # Check if workspace exists
            if project_id not in self._shared_workspace_subscriptions:
                self.logger.error(f"Workspace {project_id} does not exist")
                return False
                
            # Only allow modifications by team lead for simplicity
            if agent_id != "team_lead":
                self.logger.error(f"Only team lead can add participants, not {agent_id}")
                return False
                
            # Add the new participant
            participants = self._shared_workspace_subscriptions[project_id]
            if new_participant in participants:
                self.logger.warning(f"Participant {new_participant} already in workspace {project_id}")
                return True
                
            participants.add(new_participant)
            self._shared_workspace_subscriptions[project_id] = participants
            
            # Notify the new participant
            await self._notify_workspace_update(project_id, new_participant, "workspace_joined", {
                "workspace_id": project_id,
                "added_by": agent_id,
                "participant_count": len(participants)
            })
            
            self.logger.info(f"Successfully added {new_participant} to workspace {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding workspace participant: {str(e)}", exc_info=True)
            return False

    @trace_method
    async def _notify_workspace_update(self,
                                     workspace_id: str,
                                     agent_id: str,
                                     update_type: str,
                                     update_data: Dict[str, Any]) -> None:
        """
        Notify an agent about workspace updates.
        
        Args:
            workspace_id: ID of the workspace
            agent_id: ID of the agent to notify
            update_type: Type of update
            update_data: Update details
        """
        self.logger.debug(f"Notifying agent {agent_id} about {update_type} in workspace {workspace_id}")
        
        try:
            # In a real implementation, this would integrate with the agent notification system
            # For now, just log the notification
            notification = {
                "workspace_id": workspace_id,
                "update_type": update_type,
                "data": update_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store notification in short-term memory for the agent to pick up
            await self.short_term.store(MemoryEntry(
                agent_id=agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=notification,
                metadata={"notification": True, "workspace_id": workspace_id},
                access_level=AccessLevel.PRIVATE
            ))
            
            self.logger.debug(f"Notification stored for agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error notifying about workspace update: {str(e)}", exc_info=True)

    @trace_method
    async def track_task_status(self,
                              agent_id: str,
                              project_id: str,
                              task_id: str,
                              status: str,
                              progress: float = 0.0,
                              notes: Optional[str] = None) -> bool:
        """
        Track the status of a task in the project.
        
        Args:
            agent_id: Agent updating the task
            project_id: Project identifier
            task_id: Task identifier
            status: New task status
            progress: Completion percentage (0.0 to 1.0)
            notes: Optional status notes
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Tracking status for task {task_id} in project {project_id}: {status}")
        
        try:
            # Validate progress
            if not 0.0 <= progress <= 1.0:
                self.logger.error(f"Invalid progress value: {progress}")
                return False
                
            # Create task status update
            status_update = {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "updated_by": agent_id,
                "update_timestamp": datetime.utcnow().isoformat()
            }
            
            if notes:
                status_update["notes"] = notes
                
            # Get current project state
            current_state = await self.retrieve_project_state("team_lead", project_id)
            
            if not current_state:
                # Initialize project state if it doesn't exist
                current_state = {
                    "tasks": {},
                    "creation_time": datetime.utcnow().isoformat(),
                    "created_by": "team_lead"
                }
                
            # Update task status in project state
            if "tasks" not in current_state:
                current_state["tasks"] = {}
                
            current_state["tasks"][task_id] = status_update
            current_state["last_updated"] = datetime.utcnow().isoformat()
            current_state["updated_by"] = agent_id
            
            # Store updated project state
            result, _ = await self.store_project_state(
                agent_id="team_lead",  # Store as team lead for consistency
                project_id=project_id,
                state_data=current_state,
                metadata={"update_type": "task_status", "task_id": task_id}
            )
            
            if result:
                self.logger.info(f"Successfully tracked status for task {task_id}: {status}")
                return True
            else:
                self.logger.error(f"Failed to store project state for task status update")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking task status: {str(e)}", exc_info=True)
            return False

    @trace_method
    async def retrieve_task_status(self,
                                 agent_id: str,
                                 project_id: str,
                                 task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve the status of tasks in a project.
        
        Args:
            agent_id: Agent requesting status
            project_id: Project identifier
            task_id: Optional specific task to retrieve
            
        Returns:
            Dict[str, Any]: Task status information
        """
        self.logger.info(f"Retrieving task status for project {project_id}" + 
                        (f", task {task_id}" if task_id else ""))
        
        try:
            # Get current project state
            current_state = await self.retrieve_project_state(agent_id, project_id)
            
            if not current_state or "tasks" not in current_state:
                self.logger.warning(f"No task status information found for project {project_id}")
                return {}
                
            # Return all tasks or specific task
            if task_id:
                if task_id in current_state["tasks"]:
                    return {task_id: current_state["tasks"][task_id]}
                else:
                    self.logger.warning(f"No status found for task {task_id}")
                    return {}
            else:
                return current_state["tasks"]
                
        except Exception as e:
            self.logger.error(f"Error retrieving task status: {str(e)}", exc_info=True)
            return {}

    @trace_method
    async def get_project_metadata(self, project_id: str) -> Dict[str, Any]:
        """
        Get metadata about a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict[str, Any]: Project metadata
        """
        self.logger.info(f"Getting metadata for project {project_id}")
        
        try:
            # Check if metadata is in cache
            if project_id in self._project_metadata:
                return self._project_metadata[project_id]
                
            # Get project state for metadata
            state = await self.retrieve_project_state("team_lead", project_id)
            
            if not state:
                self.logger.warning(f"No state found for project {project_id}")
                return {}
                
            # Extract and cache metadata
            metadata = {
                "creation_time": state.get("creation_time", "unknown"),
                "created_by": state.get("created_by", "unknown"),
                "last_updated": state.get("last_updated", "unknown"),
                "updated_by": state.get("updated_by", "unknown"),
                "task_count": len(state.get("tasks", {}))
            }
            
            self._project_metadata[project_id] = metadata
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting project metadata: {str(e)}", exc_info=True)
            return {}