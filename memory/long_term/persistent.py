import json
import asyncpg
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from ..base import BaseMemory, MemoryEntry, MemoryType

logger = logging.getLogger(__name__)

class LongTermMemory(BaseMemory):
    """
    Implementation of long-term memory using PostgreSQL for persistent storage.
    Supports complex queries, metadata, and efficient retrieval of memories.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        logger.info("Long-term memory system initialized")
    
    @classmethod
    async def create(cls, dsn: str) -> 'LongTermMemory':
        """
        Create a new LongTermMemory instance with its own connection pool.
        
        Args:
            dsn: Database connection string
            
        Returns:
            LongTermMemory: Initialized long-term memory instance
        """
        try:
            # Create connection pool
            pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Initialize instance
            instance = cls(pool)
            
            # Initialize database schema
            await instance._init_database()
            
            logger.info("Successfully created long-term memory system")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create long-term memory: {str(e)}")
            raise
    
    async def _init_database(self):
        """Initialize database schema and indexes"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                -- Create memories table if it doesn't exist
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
                    access_count INTEGER DEFAULT 0
                );
                
                -- Create indexes for efficient querying
                CREATE INDEX IF NOT EXISTS idx_memories_agent_lookup 
                ON agent_memories(agent_id, memory_type);
                
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp 
                ON agent_memories(timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_memories_importance 
                ON agent_memories(importance DESC);
                
                CREATE INDEX IF NOT EXISTS idx_memories_content 
                ON agent_memories USING gin(content jsonb_path_ops);
                
                -- Create table for memory relationships
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
            logger.info("Database schema initialized successfully")
    
    async def store(self, entry: MemoryEntry) -> bool:
        """
        Store a new memory entry in long-term storage
        
        Args:
            entry: Memory entry to store
            
        Returns:
            bool: Success status of the store operation
        """
        try:
            async with self.pool.acquire() as conn:
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
                
                logger.info(f"Successfully stored memory {result} for agent {entry.agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    async def retrieve(self,
                      agent_id: str,
                      query: Optional[Dict[str, Any]] = None,
                      sort_by: str = "timestamp",
                      limit: int = 100) -> List[MemoryEntry]:
        """
        Retrieve memories matching the specified criteria
        
        Args:
            agent_id: Agent identifier
            query: Query parameters
            sort_by: Field to sort by ("timestamp", "importance", "access_count")
            limit: Maximum number of memories to return
            
        Returns:
            List[MemoryEntry]: Matching memory entries
        """
        try:
            async with self.pool.acquire() as conn:
                # Build query
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
                base_query += f" ORDER BY {sort_mapping.get(sort_by, 'timestamp DESC')}"
                
                # Add limit
                base_query += f" LIMIT {limit}"
                
                # Execute query
                rows = await conn.fetch(base_query, *params)
                
                # Update access statistics
                if rows:
                    await conn.execute("""
                        UPDATE agent_memories 
                        SET access_count = access_count + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        WHERE id = ANY($1::int[])
                    """, [row['id'] for row in rows])
                
                # Convert to memory entries
                return [
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
                
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
    async def update(self,
                    agent_id: str,
                    query: Dict[str, Any],
                    update_data: Dict[str, Any]) -> bool:
        """
        Update existing memories matching the query
        
        Args:
            agent_id: Agent identifier
            query: Query to identify memories to update
            update_data: New data to update
            
        Returns:
            bool: Success status of the update operation
        """
        try:
            async with self.pool.acquire() as conn:
                # Build update query
                base_query = """
                    UPDATE agent_memories 
                    SET content = content || $1::jsonb,
                        timestamp = CURRENT_TIMESTAMP
                    WHERE agent_id = $2
                """
                
                params = [json.dumps(update_data), agent_id]
                param_idx = 3
                
                # Add query conditions
                for key, value in query.items():
                    if isinstance(value, (dict, list)):
                        base_query += f" AND content @> ${param_idx}::jsonb"
                        params.append(json.dumps({key: value}))
                    else:
                        base_query += f" AND content->>${param_idx} = ${param_idx + 1}"
                        params.extend([key, str(value)])
                    param_idx += 2
                
                result = await conn.execute(base_query, *params)
                success = "UPDATE" in result
                
                if success:
                    logger.info(f"Successfully updated memories for agent {agent_id}")
                else:
                    logger.warning(f"No memories found to update for agent {agent_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error updating memories: {str(e)}")
            return False
    
    async def add_relationship(self,
                             source_id: int,
                             target_id: int,
                             relationship_type: str,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a relationship between two memories
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            relationship_type: Type of relationship
            metadata: Optional relationship metadata
            
        Returns:
            bool: Success status
        """
        try:
            async with self.pool.acquire() as conn:
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
            logger.error(f"Error adding relationship: {str(e)}")
            return False
    
    async def update_importance(self,
                              memory_id: int,
                              importance: float) -> bool:
        """
        Update the importance score of a memory
        
        Args:
            memory_id: ID of the memory
            importance: New importance score (0.0 to 1.0)
            
        Returns:
            bool: Success status
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_memories
                    SET importance = $2
                    WHERE id = $1
                """,
                    memory_id,
                    importance
                )
                return True
                
        except Exception as e:
            logger.error(f"Error updating importance: {str(e)}")
            return False
    
    async def clear(self, agent_id: str) -> bool:
        """
        Clear all memories for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: Success status
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM agent_memories 
                    WHERE agent_id = $1
                """, agent_id)
                
                logger.info(f"Cleared all memories for agent {agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            return False
    
    async def cleanup_old_memories(self,
                                 max_age_days: int = 90,
                                 min_importance: float = 0.5) -> bool:
        """
        Clean up old, low-importance memories
        
        Args:
            max_age_days: Maximum age of memories to keep
            min_importance: Minimum importance score to keep
            
        Returns:
            bool: Success status
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM agent_memories
                    WHERE timestamp < CURRENT_TIMESTAMP - interval '1 day' * $1
                    AND importance < $2
                """,
                    max_age_days,
                    min_importance
                )
                
                deleted_count = int(result.split()[1])
                logger.info(f"Cleaned up {deleted_count} old memories")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {str(e)}")
            return False