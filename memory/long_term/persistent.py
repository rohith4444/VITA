import json
import asyncpg
import logging
from typing import Dict, List, Any, Optional
from ..base import BaseMemory, MemoryEntry, MemoryType
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class LongTermMemory(BaseMemory):
    """
    Implementation of long-term memory using PostgreSQL for persistent storage.
    Supports complex queries, metadata, and efficient retrieval of memories.
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
        """
        self.logger.info("Initializing database schema")
        
        try:
            async with self.pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    self.logger.debug("Creating memories table and indexes")
                    
                    # Create main memories table
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
                            CHECK (importance >= 0.0 AND importance <= 1.0)
                        );
                    """)
                    
                    # Create indexes for efficient querying
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_memories_agent_lookup ON agent_memories(agent_id, memory_type);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON agent_memories(timestamp DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_importance ON agent_memories(importance DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_memories_content ON agent_memories USING gin(content jsonb_path_ops);",
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
                    
                    self.logger.info("Database schema initialized successfully")
                    
        except asyncpg.PostgresError as e:
            self.logger.error(f"Database schema initialization failed: {str(e)}", exc_info=True)
            raise
    
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a new memory entry in long-term storage.
        
        Args:
            entry: Memory entry to store
            
        Returns:
            bool: Success status of the store operation
            
        Raises:
            ValueError: If entry is invalid
            RuntimeError: If storage operation fails
        """
        self.logger.info(f"Storing memory for agent {entry.agent_id}")
        
        # Validate entry
        if not entry.content:
            self.logger.error("Attempted to store empty content")
            raise ValueError("Cannot store empty content")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Calculate initial importance
                    importance = entry.metadata.get('importance', 0.0) if entry.metadata else 0.0
                    
                    # Store the memory
                    result = await conn.fetchval("""
                        INSERT INTO agent_memories 
                        (agent_id, memory_type, content, metadata, importance, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """,
                        entry.agent_id,
                        entry.memory_type.value,
                        json.dumps(entry.content),
                        json.dumps(entry.metadata) if entry.metadata else None,
                        importance,
                        entry.timestamp
                    )
                    
                    # Handle relationships if present in metadata
                    if entry.metadata and 'relationships' in entry.metadata:
                        for rel in entry.metadata['relationships']:
                            await self._store_relationship(
                                conn,
                                result,  # new memory id
                                rel['target_id'],
                                rel['relationship_type'],
                                rel.get('metadata')
                            )
                    
                    self.logger.info(f"Successfully stored memory {result}")
                    self.logger.debug(f"Memory content size: {len(str(entry.content))} chars")
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
        
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve memories matching the specified criteria.
        
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
                    SELECT m.*, 
                           array_agg(DISTINCT jsonb_build_object(
                               'relationship_type', r.relationship_type,
                               'target_id', r.target_id,
                               'metadata', r.metadata
                           )) as relationships
                    FROM agent_memories m
                    LEFT JOIN memory_relationships r ON m.id = r.source_id
                    WHERE m.agent_id = $1
                """
                
                params = [agent_id]
                param_idx = 2
                
                # Add content/metadata filters
                if query:
                    self.logger.debug(f"Applying query filters: {query}")
                    for key, value in query.items():
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
                memories = [
                    MemoryEntry(
                        agent_id=row['agent_id'],
                        memory_type=MemoryType.LONG_TERM,
                        content=json.loads(row['content']),
                        metadata={
                            **(json.loads(row['metadata']) if row['metadata'] else {}),
                            'importance': row['importance'],
                            'access_count': row['access_count'],
                            'last_accessed': row['last_accessed'].isoformat() if row['last_accessed'] else None,
                            'relationships': [
                                rel for rel in row['relationships'] if rel is not None
                            ]
                        },
                        timestamp=row['timestamp']
                    )
                    for row in rows
                ]
                
                self.logger.info(f"Retrieved {len(memories)} memories")
                return memories
                
        except asyncpg.PostgresError as e:
            self.logger.error(f"Database error retrieving memories: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve memories: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving memories: {str(e)}", exc_info=True)
            raise

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

    async def clear(self) -> bool:
        """
        Clear operation is not supported for long-term memory.
        Returns False since this operation is not applicable.
        
        Returns:
            bool: Always returns False
        """
        self.logger.warning("Attempt to clear long-term memory - operation not supported")
        return False
    
    async def update(self, entry: MemoryEntry) -> bool:
        """
        Update an existing memory entry.
        
        Args:
            entry: Updated memory entry
            
        Returns:
            bool: Success status of the update operation
        """
        self.logger.info(f"Updating memory for agent {entry.agent_id}")
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    result = await conn.execute("""
                        UPDATE agent_memories 
                        SET content = $1,
                            metadata = $2,
                            importance = $3,
                            timestamp = $4
                        WHERE agent_id = $5 
                        AND memory_type = $6
                    """,
                        json.dumps(entry.content),
                        json.dumps(entry.metadata) if entry.metadata else None,
                        entry.metadata.get('importance', 0.0) if entry.metadata else 0.0,
                        entry.timestamp,
                        entry.agent_id,
                        entry.memory_type.value
                    )
                    
                    self.logger.info(f"Successfully updated memory for agent {entry.agent_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error updating memory: {str(e)}", exc_info=True)
            return False