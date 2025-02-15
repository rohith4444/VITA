# Memory System API Reference

## Memory Manager

### Class: MemoryManager

#### Constructor
```python
def __init__(self,
             short_term: ShortTermMemory,
             working: WorkingMemory,
             long_term: LongTermMemory)
```

#### Factory Method
```python
@classmethod
async def create(cls, db_url: str) -> 'MemoryManager'
```
Creates a new MemoryManager instance with all memory subsystems.

#### Core Methods

##### store()
```python
async def store(self,
                agent_id: str,
                memory_type: MemoryType,
                content: Dict[str, Any],
                metadata: Optional[Dict[str, Any]] = None,
                importance: float = 0.0) -> bool
```
Stores information in the specified memory system.

##### retrieve()
```python
async def retrieve(self,
                  agent_id: str,
                  memory_type: MemoryType,
                  query: Optional[Dict[str, Any]] = None,
                  sort_by: str = "timestamp",
                  limit: int = 100) -> List[MemoryEntry]
```
Retrieves information from the specified memory system.

##### update()
```python
async def update(self,
                agent_id: str,
                memory_type: MemoryType,
                query: Dict[str, Any],
                update_data: Dict[str, Any]) -> bool
```
Updates existing information in the specified memory system.

##### consolidate_to_long_term()
```python
async def consolidate_to_long_term(self,
                                 agent_id: str,
                                 importance_threshold: float = 0.5) -> bool
```
Consolidates important short-term memories to long-term storage.

##### cleanup_old_memories()
```python
async def cleanup_old_memories(self,
                             max_age_days: int = 90,
                             min_importance: float = 0.5) -> bool
```
Cleans up old, low-importance memories from long-term storage.

## Memory Implementations

### Short-term Memory

#### Core Methods

##### store()
```python
async def store(self, entry: MemoryEntry) -> bool
```
Stores a memory entry with automatic expiration.

##### retrieve()
```python
async def retrieve(self,
                  agent_id: str,
                  query: Optional[Dict[str, Any]] = None) -> List[MemoryEntry]
```
Retrieves non-expired memory entries.

### Working Memory

#### Core Methods

##### store()
```python
async def store(self, entry: MemoryEntry) -> bool
```
Stores a memory entry in working memory.

##### get_working_state()
```python
async def get_working_state(self, agent_id: str) -> Dict[str, Any]
```
Gets the current working state for an agent.

### Long-term Memory

#### Core Methods

##### store()
```python
async def store(self, entry: MemoryEntry) -> bool
```
Stores a memory entry in long-term storage.

##### add_relationship()
```python
async def add_relationship(self,
                         source_id: int,
                         target_id: int,
                         relationship_type: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool
```
Adds a relationship between two memories.

##### update_importance()
```python
async def update_importance(self,
                          memory_id: int,
                          importance: float) -> bool
```
Updates the importance score of a memory.

## Error Handling

### Common Exceptions
- `ValueError`: Invalid input parameters
- `ConnectionError`: Database connection issues
- `RuntimeError`: General operation failures

### Example Error Handling
```python
try:
    await memory_manager.store(
        agent_id="agent1",
        memory_type=MemoryType.LONG_TERM,
        content=content
    )
except ValueError as e:
    # Handle invalid input
    logger.error(f"Invalid input: {str(e)}")
except ConnectionError as e:
    # Handle database connection issues
    logger.error(f"Database connection error: {str(e)}")
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {str(e)}")
```

## Best Practices

### Memory Selection
- Use short-term for temporary context
- Use working for active processing
- Use long-term for important data

### Performance
- Implement proper error handling
- Use appropriate query limits
- Regular cleanup of old data
- Monitor memory usage

### Data Consistency
- Validate input data
- Use transactions where needed
- Maintain relationship integrity
- Regular data backups