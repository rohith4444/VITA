# Memory System Overview

## Introduction
The memory system implements a three-tier memory architecture designed for AI agents, providing different types of storage based on duration and importance of information. This modular system enables agents to maintain context, process information, and learn from past experiences.

## Key Components
- **Short-term Memory**: Temporary storage for immediate context
- **Working Memory**: Active processing state storage
- **Long-term Memory**: Persistent storage for important information

## Directory Structure
```
memory/
├── base.py                  # Base classes and types
├── memory_manager.py        # Central memory coordination
├── short_term/
│   └── in_memory.py        # Short-term implementation
├── working/
│   └── working_memory.py   # Working memory implementation
└── long_term/
    ├── __init__.py
    └── persistent.py       # Long-term PostgreSQL implementation
```

## Core Principles
1. **Hierarchical Storage**
   - Different memory types for different purposes
   - Automatic memory management
   - Efficient data retrieval

2. **Data Management**
   - Automatic cleanup of old data
   - Importance-based retention
   - Memory relationships

3. **Integration**
   - Seamless agent integration
   - Consistent API across memory types
   - Transaction support

## Memory Types

### Short-term Memory
- Temporary RAM-based storage
- Automatic decay mechanism
- Recent context maintenance
- Quick access and modification

### Working Memory
- Active state management
- Current task context
- Key-value storage
- Fast retrieval and updates

### Long-term Memory
- PostgreSQL persistent storage
- Complex query capabilities
- Relationship tracking
- Importance scoring
- Historical data maintenance

## Getting Started
1. Initialize memory manager
2. Configure memory types
3. Set up database connection
4. Integrate with agents

## Configuration
- Memory retention periods
- Cleanup intervals
- Database settings
- Memory importance thresholds

## Best Practices
1. Use appropriate memory type for data
2. Implement regular cleanup
3. Monitor memory usage
4. Handle errors gracefully
5. Maintain data consistency