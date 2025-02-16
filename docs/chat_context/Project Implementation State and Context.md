# Agent Development Reference Guide

## Project Overview
- AI Agent Development Platform using LangChain and LangGraph
- Three-tier memory architecture
- Monitoring system with LangSmith
- PostgreSQL for persistent storage

## Core Components

### 1. Memory System Architecture
```
memory/
├── base.py                  # Base memory types & classes
├── memory_manager.py        # Central coordination
├── short_term/             # Temporary storage
├── working/                # Active state
└── long_term/              # PostgreSQL storage
```

Memory Types:
- Short-term: Automatic decay, temporary storage
- Working: Active processing state
- Long-term: PostgreSQL persistent storage

### 2. Monitoring System
```
core/monitoring/
├── service.py           # Monitoring service
├── metrics.py          # Metric definitions
├── decorators.py       # Operation decorators
└── constants.py        # Configuration
```

Monitored Components:
- LLM operations
- Agent operations
- State transitions
- Performance metrics
- Cost calculation

### 3. Agent Structure
```
agents/core/
├── base_agent.py           # Base agent class
└── [agent_name]/
    ├── agent.py           # Main agent implementation
    ├── state_graph.py     # State management
    └── tools/            # Agent-specific tools
```

### 4. Tool Integration
Standard tool implementation includes:
- Logging
- Error handling
- Type hints
- Documentation
- Monitoring integration

## Environment Setup

### 1. Database Configuration
```python
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vita_db',
    'user': 'vita_user',
    'password': 'your_password'
}
```

### 2. Required Environment Variables
```bash
# Core Configuration
OPENAI_API_KEY=your_openai_key
POSTGRES_DB=vita_db
POSTGRES_USER=vita_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Monitoring Configuration
MONITORING_ENABLED=true
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=your_project_name
LANGCHAIN_TRACING_V2=true
```

## Agent Implementation Guide

### 1. Base Structure
```python
class NewAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.llm_service = LLMService()

    def add_graph_nodes(self, graph: StateGraph) -> None:
        # Define processing nodes
        graph.add_node("start", self.initial_node)
        # Add more nodes and edges
        graph.set_entry_point("start")
```

### 2. Node Implementation Pattern
```python
@monitor_operation(
    operation_type="node_name",
    metadata={
        "phase": "phase_name",
        "memory_operations": {"type": "read_write"},
        "tools_used": ["tool_list"]
    }
)
async def node_method(self, state: GraphState) -> Dict[str, Any]:
    try:
        # Memory operations
        # Tool usage
        # State updates
        return {"status": "next_state", "data": result}
    except Exception as e:
        self.logger.error(f"Error in node: {str(e)}")
        raise
```

### 3. Memory Integration
```python
# Store in memory
await self.memory_manager.store(
    agent_id=self.agent_id,
    memory_type=MemoryType.WORKING,
    content=data
)

# Retrieve from memory
result = await self.memory_manager.retrieve(
    agent_id=self.agent_id,
    memory_type=MemoryType.LONG_TERM,
    query=query_params
)
```

## Running Agents

### Basic Run Script
```python
async def run_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Initialize Memory Manager
    memory_manager = await MemoryManager.create(Config.database_url())
    
    # Initialize Agent
    agent = NewAgent(
        agent_id=f"agent_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        name="Agent Name",
        memory_manager=memory_manager
    )
    
    # Execute workflow
    result = await agent.run(input_data)
    return result

# Run the agent
result = await run_agent({"input": "task description"})
```

## Best Practices

### 1. Memory Management
- Store initial input in short-term memory
- Use working memory for active processing
- Store important results in long-term memory
- Implement proper memory cleanup

### 2. Monitoring
- Monitor all LLM operations
- Track operation durations
- Log memory usage
- Monitor tool execution
- Track costs

### 3. Error Handling
- Implement proper error handling in each node
- Log errors with context
- Maintain state consistency
- Clean up resources on failure

### 4. Testing
- Test each node independently
- Verify memory operations
- Test tool integrations
- Validate state transitions

## Development Process
1. Define agent workflow and states
2. Implement required tools
3. Create agent class and nodes
4. Add memory integration
5. Implement monitoring
6. Add error handling
7. Create run script
8. Test and validate

Remember to reference this guide when implementing new agents to maintain consistency and ensure all required integrations are included.