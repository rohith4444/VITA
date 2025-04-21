import asyncpg, json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from ..base import BaseMemory, MemoryEntry, MemoryType, AccessLevel, ProjectPhase, RelationType, DeliverableType, CleanableResource
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

@trace_class
class LongTermMemory(BaseMemory, CleanableResource):
    """
    Implementation of long-term memory using PostgreSQL for persistent storage.
    Supports complex queries, metadata, and efficient retrieval of memories.
    Enhanced to support multi-agent coordination, project archives, and deliverables.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.logger = setup_logger("memory.long_term")
        self.logger.info("Initializing Long-Term Memory system")
        
        try:
            self.pool = pool
            self.logger.info("Long-term memory system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Long-Term Memory: {str(e)}", exc_info=True)
            raise
    
    @classmethod
    async def create(cls, dsn: str) -> 'LongTermMemory':
        """
        Create a new LongTermMemory instance with its own connection pool.
        
        Args:
            dsn: Database connection string
            
        Returns:
            LongTermMemory: Initialized long-term memory instance
            
        Raises:
            ConnectionError: If database connection fails
            ValueError: If dsn is invalid
        """
        logger = setup_logger("memory.long_term.create")
        logger.info("Creating new Long-Term Memory instance")
        
        if not dsn:
            logger.error("Invalid database connection string")
            raise ValueError("Database connection string cannot be empty")
        
        try:
            from urllib.parse import urlparse

            # Parse the DSN string
            url = urlparse(dsn)
            username = url.username
            password = url.password
            database = url.path[1:]  # Remove leading '/'
            hostname = url.hostname
            port = url.port or 5432

            logger.debug(f"Attempting connection to {hostname}:{port}/{database}")

            # Create connection pool with explicit parameters
            pool = await asyncpg.create_pool(
                user=username,
                password=password,
                database=database,
                host=hostname,
                port=port,
                min_size=5,
                max_size=20,
                command_timeout=60,
                ssl=False
            )
            
            # Initialize instance
            instance = cls(pool)
            
            # Initialize database schema
            await instance._init_database()
            
            logger.info("Successfully created long-term memory system")
            return instance
            
        except asyncpg.PostgresError as e:
            logger.error(f"Database connection error: {str(e)}", exc_info=True)
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create long-term memory: {str(e)}", exc_info=True)
            raise

    async def _init_database(self):
        """
        Initialize database schema and indexes.
        Creates necessary tables and indexes if they don't exist.
        Enhanced to support multi-agent system, projects, and deliverables.
        """
        self.logger.info("Initializing database schema")
        
        try:
            async with self.pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    self.logger.debug("Creating memories table and indexes")
                    
                    # Create main memories table with enhanced fields
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS agent_memories (
                            id SERIAL PRIMARY KEY,
                            agent_id TEXT NOT NULL,
                            memory_type TEXT NOT NULL,
                            content JSONB NOT NULL,
                            metadata JSONB,
                            importance FLOAT DEFAULT 0.0,
                            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            last_accessed TIMESTAMP WITH TIME ZONE,
                            access_count INTEGER DEFAULT 0,
                            
                            -- New fields for multi-agent coordination
                            project_id TEXT,
                            task_id TEXT,
                            version TEXT,
                            access_level TEXT DEFAULT 'private',
                            phase TEXT,
                            deliverable_type TEXT,
                            parent_id TEXT,
                            
                            CHECK (importance >= 0.0 AND importance <= 1.0)
                        );
                    """)
                    
                    # Create indexes for efficient querying
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_memories_agent_lookup ON agent_memories(agent_id, memory_type);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON agent_memories(timestamp DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_importance ON agent_memories(importance DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_content ON agent_memories USING gin(content jsonb_path_ops);",
                        
                        # New indexes for multi-agent coordination
                        "CREATE INDEX IF NOT EXISTS idx_memories_project ON agent_memories(project_id);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_task ON agent_memories(task_id);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_deliverable_type ON agent_memories(deliverable_type);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_access_level ON agent_memories(access_level);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_phase ON agent_memories(phase);",
                    ]
                    
                    for idx in indexes:
                        await conn.execute(idx)
                        self.logger.debug(f"Created index: {idx[:50]}...")
                    
                    # Create relationships table
                    self.logger.debug("Creating memory relationships table")
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS memory_relationships (
                            id SERIAL PRIMARY KEY,
                            source_id INTEGER REFERENCES agent_memories(id) ON DELETE CASCADE,
                            target_id INTEGER REFERENCES agent_memories(id) ON DELETE CASCADE,
                            relationship_type TEXT NOT NULL,
                            metadata JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(source_id, target_id, relationship_type)
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_memory_relationships 
                        ON memory_relationships(source_id, target_id);
                    """)
                    
                    # Create access control table for shared memories
                    self.logger.debug("Creating memory access control table")
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS memory_access (
                            id SERIAL PRIMARY KEY,
                            memory_id INTEGER REFERENCES agent_memories(id) ON DELETE CASCADE,
                            agent_id TEXT NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(memory_id, agent_id)
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_memory_access 
                        ON memory_access(memory_id, agent_id);
                    """)
                    
                    self.logger.info("Database schema initialized successfully")
                    
        except asyncpg.PostgresError as e:
            self.logger.error(f"Database schema initialization failed: {str(e)}", exc_info=True)
            raise
    
    @trace_method
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a new memory entry in long-term storage.
        Enhanced to support project-specific data, access control, and deliverables.
        
        Args:
            entry: Memory entry to store
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If entry is invalid
            RuntimeError: If storage operation fails
        """
        self.logger.info(f"Storing {entry.memory_type.value} memory for agent {entry.agent_id}")
        
        # Validate entry
        if not entry.content:
            self.logger.error("Attempted to store empty content")
            raise ValueError("Cannot store empty content")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Calculate importance from metadata
                    importance = entry.metadata.get('importance', 0.0) if entry.metadata else 0.0
                    
                    # Extract additional fields from enhanced MemoryEntry
                    project_id = entry.project_id
                    task_id = entry.task_id
                    version = entry.version
                    access_level = entry.access_level.value if entry.access_level else AccessLevel.PRIVATE.value
                    phase = entry.phase.value if entry.phase else None
                    deliverable_type = entry.deliverable_type.value if entry.deliverable_type else None
                    parent_id = entry.parent_id
                    
                    self.logger.debug(
                        f"Storing memory with project_id={project_id}, task_id={task_id}, "
                        f"access_level={access_level}, deliverable_type={deliverable_type}"
                    )
                    
                    # Store the memory
                    result = await conn.fetchval("""
                        INSERT INTO agent_memories 
                        (agent_id, memory_type, content, metadata, importance, timestamp,
                         project_id, task_id, version, access_level, phase, deliverable_type, parent_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        RETURNING id
                    """,
                        entry.agent_id,
                        entry.memory_type.value,
                        json.dumps(entry.content),
                        json.dumps(entry.metadata) if entry.metadata else None,
                        importance,
                        entry.timestamp,
                        project_id,
                        task_id,
                        version,
                        access_level,
                        phase,
                        deliverable_type,
                        parent_id
                    )
                    
                    # Handle access control for shared memories
                    if access_level == AccessLevel.SHARED.value and entry.accessible_by:
                        for agent_id in entry.accessible_by:
                            await conn.execute("""
                                INSERT INTO memory_access (memory_id, agent_id)
                                VALUES ($1, $2)
                                ON CONFLICT (memory_id, agent_id) DO NOTHING
                            """, result, agent_id)
                        
                        self.logger.debug(f"Added access for {len(entry.accessible_by)} agents")
                    
                    # Handle relationships if present
                    if entry.relationships:
                        for rel in entry.relationships:
                            await self._store_relationship(
                                conn,
                                result,  # new memory id
                                rel.target_id,
                                rel.relation_type.value,
                                rel.metadata
                            )
                        
                        self.logger.debug(f"Stored {len(entry.relationships)} relationships")
                    
                    self.logger.info(f"Successfully stored memory {result}")
                    return True
                    
        except asyncpg.UniqueViolationError:
            self.logger.warning(f"Duplicate memory entry detected for agent {entry.agent_id}")
            return False
        except asyncpg.PostgresError as e:
            self.logger.error(f"Database error storing memory: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to store memory: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error storing memory: {str(e)}", exc_info=True)
            raise

    async def _store_relationship(self, 
                                conn: asyncpg.Connection,
                                source_id: int,
                                target_id: int,
                                relationship_type: str,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Helper method to store memory relationships.
        
        Args:
            conn: Database connection
            source_id: ID of the source memory
            target_id: ID of the target memory
            relationship_type: Type of relationship
            metadata: Optional relationship metadata
            
        Returns:
            bool: Success status
        """
        try:
            await conn.execute("""
                INSERT INTO memory_relationships
                (source_id, target_id, relationship_type, metadata)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (source_id, target_id, relationship_type)
                DO UPDATE SET metadata = EXCLUDED.metadata
            """,
                source_id,
                target_id,
                relationship_type,
                json.dumps(metadata) if metadata else None
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error storing relationship {relationship_type} between {source_id} and {target_id}: {str(e)}"
            )
            return False
        
    @trace_method
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve memories matching the specified criteria.
        Enhanced to support project filtering, access control, and deliverables.
        
        Args:
            agent_id: Agent identifier
            query: Query parameters for filtering
            sort_by: Field to sort by ("timestamp", "importance", "access_count")
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryEntry]: Matching memory entries
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If retrieval operation fails
        """
        self.logger.info(f"Retrieving memories for agent {agent_id}")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        valid_sort_fields = {"timestamp", "importance", "access_count"}
        if sort_by not in valid_sort_fields:
            self.logger.error(f"Invalid sort field: {sort_by}")
            raise ValueError(f"sort_by must be one of {valid_sort_fields}")
        
        try:
            async with self.pool.acquire() as conn:
                # Build base query
                base_query = """
                    SELECT 
                        m.*,
                        array_agg(DISTINCT jsonb_build_object(
                            'relationship_type', r.relationship_type,
                            'target_id', r.target_id,
                            'metadata', r.metadata
                        )) as relationships,
                        array_agg(DISTINCT ma.agent_id) FILTER (WHERE ma.agent_id IS NOT NULL) as accessible_by
                    FROM 
                        agent_memories m
                    LEFT JOIN 
                        memory_relationships r ON m.id = r.source_id
                    LEFT JOIN 
                        memory_access ma ON m.id = ma.memory_id
                    WHERE 
                        (m.agent_id = $1
                        OR m.access_level = 'team'
                        OR m.access_level = 'public'
                        OR (m.access_level = 'shared' AND 
                            EXISTS (SELECT 1 FROM memory_access WHERE memory_id = m.id AND agent_id = $1)))
                """
                
                params = [agent_id]
                param_idx = 2
                
                # Add memory type filter
                if query and "memory_type" in query:
                    base_query += f" AND m.memory_type = ${param_idx}"
                    params.append(query["memory_type"])
                    param_idx += 1
                    
                # Add project filter
                if query and "project_id" in query:
                    base_query += f" AND m.project_id = ${param_idx}"
                    params.append(query["project_id"])
                    param_idx += 1
                    
                # Add task filter
                if query and "task_id" in query:
                    base_query += f" AND m.task_id = ${param_idx}"
                    params.append(query["task_id"])
                    param_idx += 1
                    
                # Add phase filter
                if query and "phase" in query:
                    base_query += f" AND m.phase = ${param_idx}"
                    params.append(query["phase"])
                    param_idx += 1
                    
                # Add deliverable type filter
                if query and "deliverable_type" in query:
                    base_query += f" AND m.deliverable_type = ${param_idx}"
                    params.append(query["deliverable_type"])
                    param_idx += 1
                
                # Add content/metadata filters
                if query:
                    self.logger.debug(f"Applying query filters: {query}")
                    for key, value in query.items():
                        # Skip already handled keys
                        if key in ["memory_type", "project_id", "task_id", "phase", "deliverable_type"]:
                            continue
                            
                        if isinstance(value, (dict, list)):
                            # Handle JSON queries
                            base_query += f" AND m.content @> ${param_idx}::jsonb"
                            params.append(json.dumps({key: value}))
                        else:
                            # Handle simple key-value queries
                            base_query += f" AND m.content->>${param_idx} = ${param_idx + 1}"
                            params.extend([key, str(value)])
                        param_idx += 2
                
                # Add grouping
                base_query += " GROUP BY m.id"
                
                # Add sorting
                sort_mapping = {
                    "timestamp": "m.timestamp DESC",
                    "importance": "m.importance DESC",
                    "access_count": "m.access_count DESC"
                }
                base_query += f" ORDER BY {sort_mapping[sort_by]}"
                
                # Add limit
                base_query += f" LIMIT {limit}"
                
                self.logger.debug(f"Executing query with {len(params)} parameters")
                
                # Execute query
                rows = await conn.fetch(base_query, *params)
                
                # Update access statistics
                if rows:
                    await self._update_access_stats(conn, [row['id'] for row in rows])
                
                # Convert to memory entries
                memories = []
                for row in rows:
                    # Parse accessible_by list
                    accessible_by = set(row['accessible_by']) if row['accessible_by'] and row['accessible_by'][0] is not None else None
                    
                    # Parse relationships
                    relationships = []
                    if row['relationships'] and row['relationships'][0] is not None:
                        for rel in row['relationships']:
                            if rel:
                                # Convert each relationship to RelationshipInfo
                                relationships.append({
                                    "relation_type": rel['relationship_type'],
                                    "target_id": rel['target_id'],
                                    "metadata": json.loads(rel['metadata']) if rel['metadata'] else None
                                })
                    
                    # Determine memory type
                    try:
                        memory_type = MemoryType(row['memory_type'])
                    except ValueError:
                        memory_type = MemoryType.LONG_TERM
                        
                    # Determine access level
                    try:
                        access_level = AccessLevel(row['access_level']) if row['access_level'] else AccessLevel.PRIVATE
                    except ValueError:
                        access_level = AccessLevel.PRIVATE
                        
                    # Determine phase
                    phase = None
                    if row['phase']:
                        try:
                            phase = ProjectPhase(row['phase'])
                        except ValueError:
                            pass
                            
                    # Determine deliverable type
                    deliverable_type = None
                    if row['deliverable_type']:
                        try:
                            deliverable_type = DeliverableType(row['deliverable_type'])
                        except ValueError:
                            pass
                    
                    # Create memory entry
                    entry = MemoryEntry(
                        agent_id=row['agent_id'],
                        memory_type=memory_type,
                        content=json.loads(row['content']),
                        metadata={
                            **(json.loads(row['metadata']) if row['metadata'] else {}),
                            'importance': row['importance'],
                            'access_count': row['access_count'],
                            'last_accessed': row['last_accessed'].isoformat() if row['last_accessed'] else None,
                            'memory_id': str(row['id']),
                            'relationships': relationships
                        },
                        timestamp=row['timestamp'],
                        project_id=row['project_id'],
                        task_id=row['task_id'],
                        version=row['version'],
                        access_level=access_level,
                        accessible_by=accessible_by,
                        phase=phase,
                        deliverable_type=deliverable_type,
                        parent_id=row['parent_id']
                    )
                    
                    memories.append(entry)
                
                self.logger.info(f"Retrieved {len(memories)} memories")
                return memories
                
        except asyncpg.PostgresError as e:
            self.logger.error(f"Database error retrieving memories: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve memories: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving memories: {str(e)}", exc_info=True)
            raise

    @trace_method
    async def retrieve_shared(self,
                            agent_id: str,
                            query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]:
        """
        Retrieve memories shared with the specified agent.
        
        Args:
            agent_id: Agent identifier
            query: Query parameters for filtering
            
        Returns:
            List[MemoryEntry]: Shared memory entries
        """
        self.logger.info(f"Retrieving shared memories for agent {agent_id}")
        
        try:
            async with self.pool.acquire() as conn:
                # Build base query for shared memories
                base_query = """
                    SELECT 
                        m.*,
                        array_agg(DISTINCT jsonb_build_object(
                            'relationship_type', r.relationship_type,
                            'target_id', r.target_id,
                            'metadata', r.metadata
                        )) as relationships,
                        array_agg(DISTINCT ma.agent_id) FILTER (WHERE ma.agent_id IS NOT NULL) as accessible_by
                    FROM 
                        agent_memories m
                    LEFT JOIN 
                        memory_relationships r ON m.id = r.source_id
                    LEFT JOIN 
                        memory_access ma ON m.id = ma.memory_id
                    WHERE 
                        m.agent_id != $1
                        AND (m.access_level = 'team'
                            OR m.access_level = 'public'
                            OR (m.access_level = 'shared' AND 
                                EXISTS (SELECT 1 FROM memory_access WHERE memory_id = m.id AND agent_id = $1)))
                """
                
                params = [agent_id]
                param_idx = 2
                
                # Add memory type filter
                if query and "memory_type" in query:
                    base_query += f" AND m.memory_type = ${param_idx}"
                    params.append(query["memory_type"])
                    param_idx += 1
                    
                # Add project filter
                if query and "project_id" in query:
                    base_query += f" AND m.project_id = ${param_idx}"
                    params.append(query["project_id"])
                    param_idx += 1
                
                # Add other content filters
                if query:
                    for key, value in query.items():
                        # Skip already handled keys
                        if key in ["memory_type", "project_id"]:
                            continue
                            
                        if isinstance(value, (dict, list)):
                            # Handle JSON queries
                            base_query += f" AND m.content @> ${param_idx}::jsonb"
                            params.append(json.dumps({key: value}))
                        else:
                            # Handle simple key-value queries
                            base_query += f" AND m.content->>${param_idx} = ${param_idx + 1}"
                            params.extend([key, str(value)])
                        param_idx += 2
                
                # Add grouping and sort by recency
                base_query += " GROUP BY m.id ORDER BY m.timestamp DESC LIMIT 100"
                
                # Execute query
                rows = await conn.fetch(base_query, *params)
                
                # Convert to memory entries (reuse code from retrieve method)
                memories = []
                for row in rows:
                    # Parse accessible_by list
                    accessible_by = set(row['accessible_by']) if row['accessible_by'] and row['accessible_by'][0] is not None else None
                    
                    # Parse relationships
                    relationships = []
                    if row['relationships'] and row['relationships'][0] is not None:
                        for rel in row['relationships']:
                            if rel:
                                relationships.append({
                                    "relation_type": rel['relationship_type'],
                                    "target_id": rel['target_id'],
                                    "metadata": json.loads(rel['metadata']) if rel['metadata'] else None
                                })
                    
                    # Determine memory type, access level, etc.
                    try:
                        memory_type = MemoryType(row['memory_type'])
                    except ValueError:
                        memory_type = MemoryType.LONG_TERM
                        
                    try:
                        access_level = AccessLevel(row['access_level']) if row['access_level'] else AccessLevel.PRIVATE
                    except ValueError:
                        access_level = AccessLevel.PRIVATE
                        
                    phase = None
                    if row['phase']:
                        try:
                            phase = ProjectPhase(row['phase'])
                        except ValueError:
                            pass
                            
                    deliverable_type = None
                    if row['deliverable_type']:
                        try:
                            deliverable_type = DeliverableType(row['deliverable_type'])
                        except ValueError:
                            pass
                    
                    # Create memory entry
                    entry = MemoryEntry(
                        agent_id=row['agent_id'],
                        memory_type=memory_type,
                        content=json.loads(row['content']),
                        metadata={
                            **(json.loads(row['metadata']) if row['metadata'] else {}),
                            'importance': row['importance'],
                            'memory_id': str(row['id']),
                            'relationships': relationships
                        },
                        timestamp=row['timestamp'],
                        project_id=row['project_id'],
                        task_id=row['task_id'],
                        version=row['version'],
                        access_level=access_level,
                        accessible_by=accessible_by,
                        phase=phase,
                        deliverable_type=deliverable_type,
                        parent_id=row['parent_id']
                    )
                    
                    memories.append(entry)
                
                self.logger.info(f"Retrieved {len(memories)} shared memories")
                return memories
                
        except Exception as e:
            self.logger.error(f"Error retrieving shared memories: {str(e)}", exc_info=True)
            return []

    @trace_method
    async def retrieve_deliverables(self,
                                  agent_id: str,
                                  project_id: Optional[str] = None,
                                  deliverable_type: Optional[DeliverableType] = None) -> List[MemoryEntry]:
        """
        Retrieve deliverable memories.
        
        Args:
            agent_id: Agent identifier
            project_id: Optional project filter
            deliverable_type: Optional deliverable type filter
            
        Returns:
            List[MemoryEntry]: Deliverable memory entries
        """
        self.logger.info(f"Retrieving deliverables for agent {agent_id}")
        
        # Build query
        query = {"memory_type": MemoryType.DELIVERABLE.value}
        
        if project_id:
            query["project_id"] = project_id
            
        if deliverable_type:
            query["deliverable_type"] = deliverable_type.value
        
        # Use main retrieve method with DELIVERABLE filter
        return await self.retrieve(agent_id, query)

    @trace_method
    async def retrieve_by_project(self,
                                agent_id: str,
                                project_id: str,
                                memory_type: Optional[MemoryType] = None) -> List[MemoryEntry]:
        """
        Retrieve memories for a specific project.
        
        Args:
            agent_id: Agent identifier
            project_id: Project identifier
            memory_type: Optional memory type filter
            
        Returns:
            List[MemoryEntry]: Project-related memory entries
        """
        self.logger.info(f"Retrieving project memories for project {project_id}")
        
        # Build query
        query = {"project_id": project_id}
        
        if memory_type:
            query["memory_type"] = memory_type.value
        
        # Use main retrieve method with project filter
        return await self.retrieve(agent_id, query)

    @trace_method
    async def _update_access_stats(self, conn: asyncpg.Connection, memory_ids: List[int]):
        """
        Update access statistics for retrieved memories.
        
        Args:
            conn: Database connection
            memory_ids: List of memory IDs to update
        """
        try:
            await conn.execute("""
                UPDATE agent_memories 
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = ANY($1::int[])
            """, memory_ids)
            
            self.logger.debug(f"Updated access stats for {len(memory_ids)} memories")
            
        except Exception as e:
            self.logger.error(f"Error updating access stats: {str(e)}")
            # Don't raise - this is a non-critical operation

    @trace_method
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing memories.
        Enhanced to handle project-specific updates.
        
        Args:
            agent_id: Agent identifier
            query: Query to identify memories to update
            update_data: Data to update
            
        Returns:
            bool: Success status
            
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
            # First retrieve memories matching the query
            matching_memories = await self.retrieve(agent_id, query)
            
            if not matching_memories:
                self.logger.warning(f"No memories found matching query for update")
                return False
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    updated_count = 0
                    
                    for memory in matching_memories:
                        memory_id = memory.metadata.get('memory_id')
                        if not memory_id:
                            continue
                        
                        # Update memory content
                        updated_content = {**memory.content, **update_data}
                        
                        # Update the memory in database
                        await conn.execute("""
                            UPDATE agent_memories 
                            SET content = $1,
                                timestamp = $2
                            WHERE id = $3
                        """,
                            json.dumps(updated_content),
                            datetime.utcnow(),
                            int(memory_id)
                        )
                        
                        updated_count += 1
                    
                    self.logger.info(f"Updated {updated_count} memories for agent {agent_id}")
                    return updated_count > 0
                    
        except Exception as e:
            self.logger.error(f"Error updating memories: {str(e)}", exc_info=True)
            return False
    @trace_method
    async def clear(self, agent_id: str) -> bool:
        """
        Clear operation for long-term memory.
        Only clears memories owned by the specified agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: Success status
            
        Raises:
            ValueError: If agent_id is invalid
        """
        self.logger.warning(f"Clearing memories for agent {agent_id} - this operation is irreversible")
        
        if not agent_id or not agent_id.strip():
            self.logger.error("Invalid agent_id provided")
            raise ValueError("agent_id cannot be empty")
            
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM agent_memories 
                    WHERE agent_id = $1
                """, agent_id)
                
                self.logger.info(f"Cleared memories for agent {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error clearing memories: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def update_version(self,
                           agent_id: str,
                           memory_id: str,
                           new_content: Dict[str, Any],
                           new_version: Optional[str] = None) -> bool:
        """
        Update a memory entry with a new version.
        
        Args:
            agent_id: Agent identifier
            memory_id: ID of the memory to update
            new_content: New content for the memory
            new_version: Optional explicit new version
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Updating version for memory {memory_id}")
        
        try:
            async with self.pool.acquire() as conn:
                # Get current memory entry
                row = await conn.fetchrow("""
                    SELECT * FROM agent_memories WHERE id = $1
                """, int(memory_id))
                
                if not row:
                    self.logger.warning(f"Memory {memory_id} not found")
                    return False
                
                # Check if agent is authorized to update this memory
                if row['agent_id'] != agent_id and row['access_level'] != 'team' and row['access_level'] != 'public':
                    self.logger.warning(f"Agent {agent_id} not authorized to update memory {memory_id}")
                    return False
                
                # Calculate new version
                if not new_version:
                    current_version = row['version'] or "1.0"
                    try:
                        major, minor = current_version.split('.')
                        new_version = f"{major}.{int(minor) + 1}"
                    except (ValueError, AttributeError):
                        new_version = "1.1"
                
                # Update the memory
                await conn.execute("""
                    UPDATE agent_memories 
                    SET content = $1,
                        version = $2,
                        timestamp = $3
                    WHERE id = $4
                """,
                    json.dumps(new_content),
                    new_version,
                    datetime.utcnow(),
                    int(memory_id)
                )
                
                self.logger.info(f"Updated memory {memory_id} to version {new_version}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating memory version: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def share_memory(self,
                         agent_id: str,
                         memory_id: str,
                         share_with: Set[str]) -> bool:
        """
        Share a memory with specific agents.
        
        Args:
            agent_id: Agent sharing the memory
            memory_id: ID of the memory to share
            share_with: Set of agent IDs to share with
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Sharing memory {memory_id} with {len(share_with)} agents")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if agent can share this memory
                    row = await conn.fetchrow("""
                        SELECT agent_id, access_level FROM agent_memories WHERE id = $1
                    """, int(memory_id))
                    
                    if not row:
                        self.logger.warning(f"Memory {memory_id} not found")
                        return False
                    
                    # Only the owner or team_lead can share a memory
                    if row['agent_id'] != agent_id and agent_id != "team_lead":
                        self.logger.warning(f"Agent {agent_id} not authorized to share memory {memory_id}")
                        return False
                    
                    # Update access level to shared if not already
                    if row['access_level'] != 'shared' and row['access_level'] != 'team' and row['access_level'] != 'public':
                        await conn.execute("""
                            UPDATE agent_memories SET access_level = 'shared' WHERE id = $1
                        """, int(memory_id))
                    
                    # Add access for each agent
                    for share_agent_id in share_with:
                        await conn.execute("""
                            INSERT INTO memory_access (memory_id, agent_id)
                            VALUES ($1, $2)
                            ON CONFLICT (memory_id, agent_id) DO NOTHING
                        """, int(memory_id), share_agent_id)
                    
                    self.logger.info(f"Successfully shared memory {memory_id} with {len(share_with)} agents")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error sharing memory: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    async def get_project_archives(self,
                                 agent_id: str,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get a list of available project archives.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of projects to return
            
        Returns:
            List[Dict[str, Any]]: List of project summaries
        """
        self.logger.info(f"Retrieving project archives for agent {agent_id}")
        
        try:
            async with self.pool.acquire() as conn:
                # Get distinct projects with summary info
                rows = await conn.fetch("""
                    SELECT 
                        project_id,
                        MIN(timestamp) as start_date,
                        MAX(timestamp) as last_updated,
                        COUNT(*) as memory_count,
                        COUNT(DISTINCT agent_id) as agent_count,
                        COUNT(DISTINCT task_id) as task_count
                    FROM 
                        agent_memories
                    WHERE 
                        project_id IS NOT NULL
                        AND (agent_id = $1
                             OR access_level = 'team'
                             OR access_level = 'public'
                             OR (access_level = 'shared' AND 
                                 EXISTS (SELECT 1 FROM memory_access WHERE memory_id = agent_memories.id AND agent_id = $1)))
                    GROUP BY 
                        project_id
                    ORDER BY 
                        MAX(timestamp) DESC
                    LIMIT $2
                """, agent_id, limit)
                
                project_archives = []
                for row in rows:
                    project_archives.append({
                        "project_id": row['project_id'],
                        "start_date": row['start_date'].isoformat(),
                        "last_updated": row['last_updated'].isoformat(),
                        "memory_count": row['memory_count'],
                        "agent_count": row['agent_count'],
                        "task_count": row['task_count']
                    })
                
                self.logger.info(f"Retrieved {len(project_archives)} project archives")
                return project_archives
                
        except Exception as e:
            self.logger.error(f"Error retrieving project archives: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def cleanup(self) -> None:
        """
        Cleanup resources before shutdown.
        Closes the database connection pool.
        """
        self.logger.info("Cleaning up Long-Term Memory resources")
        
        try:
            if self.pool:
                await self.pool.close()
                self.logger.info("Closed database connection pool")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            raise