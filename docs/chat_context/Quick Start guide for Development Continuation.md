# VITA Agent Development Quick Start Guide

## Introduction

This guide provides essential information for developing agents within the VITA AI Agent Development Platform. It covers common patterns and agent-specific implementations.

## System Architecture

### Agent Structure
```
agents/
├── core/                    # Core components
│   ├── base_agent.py       # Base agent class
│   ├── llm/                # Shared LLM components
│   └── monitoring/         # Monitoring system
├── project_manager/        # Project Manager implementation
│   ├── agent.py
│   └── state_graph.py
└── solution_architect/     # Solution Architect implementation
    ├── agent.py
    ├── state_graph.py
    └── llm/                # Agent-specific LLM components
        ├── prompts.py
        └── service.py
```

### Common Components
- Memory System (Three-tier storage)
- Monitoring System (LangSmith integration)
- Base LLM Service
- Logging System
- Tracing System

## Agent Development Guide

### 1. Define Agent State
Each agent needs a TypedDict defining its state structure:

```python
# Example: Project Manager State
class ProjectManagerGraphState(TypedDict):
    input: str
    status: str
    project_plan: Dict[str, Any]

# Example: Solution Architect State
class SolutionArchitectGraphState(TypedDict):
    input: str
    project_plan: Dict[str, Any]
    tech_stack: Dict[str, List[str]]
    architecture_design: Dict[str, Any]
    validation_results: Dict[str, Any]
    specifications: Dict[str, Any]
    status: str
```

### 2. Build Agent Workflow

Each agent implements its workflow using LangGraph:

```python
def _build_graph(self) -> StateGraph:
    graph = StateGraph(AgentGraphState)
    
    # Add nodes for workflow steps
    graph.add_node("start", self.receive_input)
    # Add agent-specific nodes
    
    # Add edges for workflow flow
    graph.add_edge("start", "next_step")
    # Add agent-specific edges
    
    return graph.compile()
```

### 3. LLM Integration Options

#### Option 1: Use Core LLM Service
For simple agents with standard LLM needs:
```python
from agents.core.llm.service import LLMService

class SimpleAgent(BaseAgent):
    def __init__(self):
        self.llm_service = LLMService()
```

#### Option 2: Agent-Specific LLM Service
For agents needing specialized LLM handling:
```python
agents/solution_architect/llm/
├── prompts.py      # Agent-specific prompts
└── service.py      # Specialized LLM methods
```

### 4. Tool Organization

Tools should be organized by agent and functionality:
```
tools/
├── project_manager/
│   ├── task_breakdown.py
│   └── resource_allocator.py
└── solution_architect/
    ├── technology_selector.py
    ├── architecture_validator.py
    └── specification_generator.py
```

## Agent-Specific Implementations

### Project Manager Agent
Focus: Project planning and management
```python
class ProjectManagerAgent(BaseAgent):
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow:
        1. Receive project input
        2. Analyze requirements
        3. Generate project plan
        """
```

### Solution Architect Agent
Focus: Technical architecture and specifications
```python
class SolutionArchitectAgent(BaseAgent):
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow:
        1. Analyze technical requirements
        2. Select technology stack
        3. Design architecture
        4. Validate architecture
        5. Generate specifications
        """
```

## Key Differences Between Agents

### State Management
- **Project Manager**: Focuses on project structure and resource allocation
- **Solution Architect**: Maintains complex technical state including tech stack and architecture

### LLM Integration
- **Project Manager**: Uses core LLM service
- **Solution Architect**: Has specialized LLM service with custom prompts

### Tool Usage
- **Project Manager**: Tools for project breakdown and resource management
- **Solution Architect**: Tools for tech selection and architecture validation

## Best Practices

### 1. State Design
- Keep state minimal but complete
- Use TypedDict for type safety
- Document state fields

### 2. Error Handling
```python
try:
    result = await operation()
    return result
except Exception as e:
    self.logger.error(f"Operation failed: {str(e)}", exc_info=True)
    return fallback_result()
```

### 3. Memory Usage
```python
# Store important results
await self.memory_manager.store(
    agent_id=self.agent_id,
    memory_type=MemoryType.LONG_TERM,
    content=result,
    importance=0.8
)
```

### 4. Monitoring
```python
@monitor_operation(
    operation_type="process_data",
    metadata={"phase": "processing"}
)
async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
```

## Testing and Deployment

1. Test agent in isolation
2. Verify memory operations
3. Check monitoring metrics
4. Validate error handling
5. Test integration with other agents

## Common Issues and Solutions

1. **Empty LLM Responses**
   - Implement retry logic
   - Return empty JSON instead of None
   - Log response content for debugging

2. **Memory Management**
   - Clear obsolete data
   - Use appropriate memory types
   - Handle retrieval failures

3. **State Transitions**
   - Validate state before transitions
   - Handle incomplete states
   - Log state changes

## Next Steps

1. Choose agent type based on responsibility
2. Follow appropriate implementation pattern
3. Implement required components
4. Test thoroughly
5. Document agent capabilities