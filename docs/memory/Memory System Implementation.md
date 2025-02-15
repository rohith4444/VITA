# Memory System Implementation

## Base Components

### MemoryType Enum
```python
class MemoryType(Enum):
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
```

### MemoryEntry Model
```python
class MemoryEntry(BaseModel):
    timestamp: datetime
    memory_type: MemoryType
    agent_id: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
```

## Memory Implementations

### Short-term Memory
RAM-based storage with automatic decay.

#### Key Methods:
- `store()`: Add new memory entry
- `retrieve()`: Get recent memories
- `update()`: Modify existing memories
- `clear()`: Remove all memories
- `_cleanup_loop()`: Automatic cleanup process

#### Features:
- Automatic decay after configurable period
- In-memory storage for fast access
- Temporary context maintenance
- Access tracking

### Working Memory
Active state storage with quick access.

#### Key Methods:
- `store()`: Store current state
- `retrieve()`: Get active state
- `update()`: Modify state
- `clear()`: Reset state
- `get_working_state()`: Get complete state
- `clear_if_inactive()`: Clean inactive states

#### Features:
- Key-value storage
- Quick state access
- Current context management
- Inactivity cleanup

### Long-term Memory
PostgreSQL-based persistent storage.

#### Key Methods:
- `store()`: Store permanent memory
- `retrieve()`: Complex memory retrieval
- `update()`: Update stored memories
- `add_relationship()`: Create memory links
- `update_importance()`: Modify importance
- `cleanup_old_memories()`: Maintenance

#### Features:
- Persistent storage
- Complex querying
- Relationship tracking
- Importance scoring
- Access statistics

## Database Schema

### agent_memories Table
```sql
CREATE TABLE agent_memories (
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
```

### memory_relationships Table
```sql
CREATE TABLE memory_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES agent_memories(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES agent_memories(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relationship_type)
);
```

## Usage Examples

### Storing Memories
```python
# Short-term memory
await memory_manager.store(
    agent_id="agent1",
    memory_type=MemoryType.SHORT_TERM,
    content={"conversation": "current context"}
)

# Working memory
await memory_manager.store(
    agent_id="agent1",
    memory_type=MemoryType.WORKING,
    content={"active_task": "current task"}
)

# Long-term memory
await memory_manager.store(
    agent_id="agent1",
    memory_type=MemoryType.LONG_TERM,
    content={"project": "completed project"},
    importance=0.8
)
```

### Retrieving Memories
```python
# Get recent conversations
recent_memories = await memory_manager.retrieve(
    agent_id="agent1",
    memory_type=MemoryType.SHORT_TERM
)

# Get current state
current_state = await memory_manager.retrieve(
    agent_id="agent1",
    memory_type=MemoryType.WORKING
)

# Query long-term memory
project_memories = await memory_manager.retrieve(
    agent_id="agent1",
    memory_type=MemoryType.LONG_TERM,
    query={"type": "project"},
    sort_by="timestamp",
    limit=10
)
```