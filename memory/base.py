from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Union
from enum import Enum, auto
from pydantic import BaseModel, Field, validator, root_validator
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize module logger
logger = setup_logger("memory.base")
logger.info("Initializing memory base module")

@trace_class
class CleanableResource(ABC):
    """Interface for resources that need cleanup on shutdown."""
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources before shutdown."""
        pass

@trace_class  
class MemoryType(Enum):
    """
    Types of memory available to agents.
    
    Attributes:
        SHORT_TERM: Temporary storage with automatic decay
        WORKING: Active processing state memory
        LONG_TERM: Persistent storage for important information
        PROJECT_STATE: Shared project state accessible to all agents
        SHARED_CONTEXT: Context shared between specific agents
        DELIVERABLE: Agent output that contributes to final project
    """
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
    PROJECT_STATE = "project_state"     # New: For tracking overall project state
    SHARED_CONTEXT = "shared_context"   # New: For context shared between agents
    DELIVERABLE = "deliverable"         # New: For agent outputs/deliverables
    
    @classmethod
    def validate(cls, value: str) -> 'MemoryType':
        """Validate and convert string to MemoryType."""
        try:
            return cls(value)
        except ValueError as e:
            logger.error(f"Invalid memory type: {value}")
            raise ValueError(f"Invalid memory type. Must be one of {[t.value for t in cls]}")

@trace_class
class ProjectPhase(Enum):
    """
    Phases of a project lifecycle for categorizing memories.
    
    Attributes:
        INITIALIZATION: Project setup and requirement gathering
        PLANNING: Architecture and task planning
        DEVELOPMENT: Implementation of components
        TESTING: Testing and quality assurance
        INTEGRATION: Integration of components
        DELIVERY: Final project delivery and documentation
    """
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    INTEGRATION = "integration"
    DELIVERY = "delivery"
    
    @classmethod
    def validate(cls, value: str) -> 'ProjectPhase':
        """Validate and convert string to ProjectPhase."""
        try:
            return cls(value)
        except ValueError as e:
            logger.error(f"Invalid project phase: {value}")
            raise ValueError(f"Invalid project phase. Must be one of {[p.value for p in cls]}")

@trace_class
class AccessLevel(Enum):
    """
    Access control levels for shared memories.
    
    Attributes:
        PRIVATE: Only accessible to the creating agent
        SHARED: Accessible to specific agents
        TEAM: Accessible to all agents on the team
        PUBLIC: Accessible to all, including external systems
    """
    PRIVATE = "private"
    SHARED = "shared"
    TEAM = "team"
    PUBLIC = "public"
    
    @classmethod
    def validate(cls, value: str) -> 'AccessLevel':
        """Validate and convert string to AccessLevel."""
        try:
            return cls(value)
        except ValueError as e:
            logger.error(f"Invalid access level: {value}")
            raise ValueError(f"Invalid access level. Must be one of {[l.value for l in cls]}")

@trace_class
class RelationType(Enum):
    """
    Types of relationships between memory entries.
    
    Attributes:
        DEPENDS_ON: Current entry depends on the related entry
        PART_OF: Current entry is part of the related entry
        REFERENCES: Current entry references the related entry
        DERIVED_FROM: Current entry is derived from the related entry
        SUCCESSOR: Current entry succeeds the related entry
    """
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    SUCCESSOR = "successor"

@trace_class
class DeliverableType(Enum):
    """
    Types of deliverables that can be stored.
    
    Attributes:
        CODE: Source code file
        CONFIGURATION: Configuration file
        DOCUMENTATION: Documentation file
        DESIGN: Design specification
        TEST: Test case or test code
        DATA: Data file or structured information
    """
    CODE = "code"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    DESIGN = "design"
    TEST = "test"
    DATA = "data"

@trace_class
class RelationshipInfo(BaseModel):
    """
    Model for representing relationships between memory entries.
    
    Attributes:
        relation_type: Type of relationship
        target_id: ID of the related memory entry
        metadata: Optional additional information about the relationship
    """
    relation_type: RelationType
    target_id: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True

@trace_class
class MemoryEntry(BaseModel):
    """
    Base model for memory entries.
    
    Attributes:
        timestamp: Time when the memory was created
        memory_type: Type of memory (SHORT_TERM, WORKING, LONG_TERM, etc.)
        agent_id: Unique identifier for the agent
        content: Main memory content
        metadata: Optional metadata about the memory
        project_id: Optional identifier for the associated project
        task_id: Optional identifier for the associated task
        version: Optional version information for tracking changes
        access_level: Access control level for this memory
        accessible_by: Set of agent IDs that can access this memory if SHARED
        relationships: List of relationships to other memory entries
        phase: Optional project phase this memory belongs to
        deliverable_type: Optional type if this is a deliverable memory
        parent_id: Optional ID of a parent memory (for hierarchical memories)
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    memory_type: MemoryType
    agent_id: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    # New fields for multi-agent support
    project_id: Optional[str] = Field(default=None)
    task_id: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default="1.0")
    access_level: AccessLevel = Field(default=AccessLevel.PRIVATE)
    accessible_by: Optional[Set[str]] = Field(default=None)
    relationships: List[RelationshipInfo] = Field(default_factory=list)
    phase: Optional[ProjectPhase] = Field(default=None)
    deliverable_type: Optional[DeliverableType] = Field(default=None)
    parent_id: Optional[str] = Field(default=None)
    
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
    
    @root_validator
    def validate_access_level(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate access_level and accessible_by consistency."""
        access_level = values.get('access_level')
        accessible_by = values.get('accessible_by')
        
        if access_level == AccessLevel.SHARED and not accessible_by:
            logger.error("SHARED access level requires accessible_by to be specified")
            raise ValueError("When access_level is SHARED, accessible_by must be specified")
            
        if access_level != AccessLevel.SHARED and accessible_by:
            # Auto-correct by removing accessible_by for non-SHARED memory
            logger.warning(f"Removing accessible_by for non-SHARED memory (access_level: {access_level})")
            values['accessible_by'] = None
            
        return values
    
    @root_validator
    def validate_deliverable_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deliverable_type if memory_type is DELIVERABLE."""
        memory_type = values.get('memory_type')
        deliverable_type = values.get('deliverable_type')
        
        if memory_type == MemoryType.DELIVERABLE and not deliverable_type:
            logger.error("DELIVERABLE memory type requires deliverable_type to be specified")
            raise ValueError("When memory_type is DELIVERABLE, deliverable_type must be specified")
            
        if memory_type != MemoryType.DELIVERABLE and deliverable_type:
            # Auto-correct by removing deliverable_type for non-DELIVERABLE memory
            logger.warning(f"Removing deliverable_type for non-DELIVERABLE memory")
            values['deliverable_type'] = None
            
        return values

    def can_access(self, agent_id: str) -> bool:
        """
        Check if an agent can access this memory entry.
        
        Args:
            agent_id: ID of the agent requesting access
            
        Returns:
            bool: True if the agent can access, False otherwise
        """
        # The agent that created the memory can always access it
        if agent_id == self.agent_id:
            return True
            
        # Check access level
        if self.access_level == AccessLevel.PRIVATE:
            return False
        elif self.access_level == AccessLevel.SHARED:
            return self.accessible_by is not None and agent_id in self.accessible_by
        elif self.access_level == AccessLevel.TEAM:
            return True  # All team members can access
        elif self.access_level == AccessLevel.PUBLIC:
            return True  # Everyone can access
            
        return False
    
    def add_relationship(self, relation_type: RelationType, target_id: str, 
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a relationship to another memory entry.
        
        Args:
            relation_type: Type of relationship
            target_id: ID of the related memory entry
            metadata: Optional metadata about the relationship
        """
        relationship = RelationshipInfo(
            relation_type=relation_type,
            target_id=target_id,
            metadata=metadata
        )
        self.relationships.append(relationship)
    
    def update_version(self, new_version: Optional[str] = None) -> None:
        """
        Update the version of this memory entry.
        
        Args:
            new_version: Optional explicit new version, otherwise increments automatically
        """
        if new_version:
            self.version = new_version
        else:
            # Auto-increment version (simple scheme: 1.0, 1.1, 1.2, etc.)
            try:
                major, minor = self.version.split('.')
                new_minor = int(minor) + 1
                self.version = f"{major}.{new_minor}"
            except (ValueError, AttributeError):
                # If current version is not in the expected format, reset to 1.0
                self.version = "1.0"

@trace_class
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
            
        Note:
            Default implementation that can be overridden by specific memory classes
            for more efficient implementation.
        """
        self.logger.info(f"Retrieving shared memories accessible to agent {agent_id}")
        
        # Default implementation - filter after retrieval
        all_entries = await self.retrieve(agent_id, query)
        
        # Filter for only shared entries accessible to this agent
        shared_entries = [
            entry for entry in all_entries
            if entry.agent_id != agent_id and entry.can_access(agent_id)
        ]
        
        return shared_entries
    
    async def retrieve_by_project(self,
                                agent_id: str,
                                project_id: str,
                                query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memory entries for a specific project.
        
        Args:
            agent_id: Unique identifier for the agent
            project_id: Unique identifier for the project
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of project-related memory entries
        """
        self.logger.info(f"Retrieving project {project_id} memories for agent {agent_id}")
        
        # Combine project_id with the existing query
        combined_query = query or {}
        combined_query["project_id"] = project_id
        
        return await self.retrieve(agent_id, combined_query)
    
    async def retrieve_by_task(self,
                             agent_id: str,
                             task_id: str,
                             query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memory entries for a specific task.
        
        Args:
            agent_id: Unique identifier for the agent
            task_id: Unique identifier for the task
            query: Optional query parameters to filter results
            
        Returns:
            List[MemoryEntry]: List of task-related memory entries
        """
        self.logger.info(f"Retrieving task {task_id} memories for agent {agent_id}")
        
        # Combine task_id with the existing query
        combined_query = query or {}
        combined_query["task_id"] = task_id
        
        return await self.retrieve(agent_id, combined_query)
    
    async def retrieve_deliverables(self,
                                 agent_id: str,
                                 deliverable_type: Optional[DeliverableType] = None) -> List[MemoryEntry]:
        """
        Retrieve deliverable memory entries.
        
        Args:
            agent_id: Unique identifier for the agent
            deliverable_type: Optional filter for specific deliverable type
            
        Returns:
            List[MemoryEntry]: List of deliverable memory entries
        """
        self.logger.info(f"Retrieving deliverables for agent {agent_id}")
        
        # Create query for deliverable type
        query = {"memory_type": MemoryType.DELIVERABLE.value}
        
        if deliverable_type:
            query["deliverable_type"] = deliverable_type.value
        
        return await self.retrieve(agent_id, query)

logger.info("Memory base module initialized successfully")