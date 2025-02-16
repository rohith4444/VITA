# Quick Start Guide for Development Continuation

## Initial Setup

### 1. Required Files
Upload these files to continue development:
```
Core Files:
- agents/core/project_manager/agent.py
- agents/core/llm/service.py
- agents/core/monitoring/*.py
- memory/*.py
- tools/project_manager/*.py
- backend/config.py

Documentation:
- Updated Project State Document
- Monitoring System Overview
- Monitoring TODO List
```

### 2. Environment Configuration
Ensure these environment variables are set:
```bash
# Core Configuration
OPENAI_API_KEY=your_openai_key
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=your_db_host
POSTGRES_PORT=your_db_port

# Monitoring Configuration
MONITORING_ENABLED=true
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=your_project_name
LANGCHAIN_TRACING_V2=true
```

### 3. Dependencies
Ensure these packages are installed:
```bash
pip install langsmith>=0.0.69
pip install langchain>=0.1.0
```

## Development Workflow

### 1. Documentation Reference
- Check Project State Document for current status
- Review component-specific documentation
- Consult monitoring overview for instrumentation

### 2. Component Development
Current focus areas:
1. Project Manager Agent workflow
2. Monitoring system expansion
3. Memory system optimization
4. Tool enhancements

### 3. Monitoring Integration
When developing new features:
1. Add appropriate monitoring decorators
2. Include relevant metadata
3. Ensure proper error handling
4. Verify metric collection

## Best Practices

### 1. Code Organization
- Follow existing project structure
- Maintain consistent file organization
- Use type hints and documentation

### 2. Monitoring
- Use appropriate decorators
- Include relevant metadata
- Handle errors gracefully
- Log important events

### 3. Documentation
- Update project state document
- Maintain component documentation
- Document new monitoring metrics

## Common Tasks

### 1. Adding New Agent Operations
```python
@monitor_operation(
    operation_type="operation_name",
    metadata={
        "phase": "phase_name",
        "memory_operations": {...},
        "tools_used": [...]
    }
)
async def new_operation(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
    # Implementation
```

### 2. Adding LLM Operations
```python
@monitor_llm(
    run_name="operation_name",
    metadata={
        "operation_details": {
            "prompt_template": "template_name",
            "max_tokens": token_limit,
            "temperature": temp_value
        }
    }
)
async def llm_operation(self, input_data: str) -> Dict[str, Any]:
    # Implementation
```

### 3. Adding New Tools
1. Create tool in tools/project_manager/
2. Add monitoring in agent implementation
3. Update documentation

## Troubleshooting

### 1. Monitoring Issues
- Verify environment variables
- Check LangSmith connectivity
- Review monitoring service logs

### 2. Development Issues
- Consult project state document
- Review component documentation
- Check existing implementations

## Next Steps

1. Review current project state
2. Choose component to work on
3. Upload necessary files
4. Configure environment
5. Begin development