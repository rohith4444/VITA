# Utilities Documentation

## Overview

The utilities package provides essential support functions and classes used throughout the system. Key components include logging, environment management, LLM management, web search, and data management.

## Components

### 1. Logger (logger.py)

**Purpose**: Provides consistent logging across the application with custom formatting and levels.

```python
# Usage
logger = setup_logger("ComponentName")
logger.info("Operation started")
logger.debug("Detailed information")
logger.error("Error occurred", exc_info=True)
```

**Features**:
- Custom color formatting
- File and console output
- Log level control
- Exception tracing

### 2. Environment Loader (env_loader.py)

**Purpose**: Manages environment variables and configuration.

```python
# Usage
env_vars = load_env_variables()
```

**Required Variables**:
- OPENAI_API_KEY
- HUGGINGFACEHUB_API_TOKEN
- TAVILY_API_KEY

**Features**:
- Environment validation
- Secure key handling
- Error reporting

### 3. LLM Manager (llm.py)

**Purpose**: Manages LLM instances using singleton pattern.

```python
class LLMManager:
    _instance = None
    _llm_instances = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

**Features**:
- Instance caching
- Configuration management
- Resource optimization

### 4. Web Search Tool (web_search.py)

**Purpose**: Provides web search capabilities using Tavily API.

```python
class WebSearchTool:
    def search(self, query: str) -> List[Document]:
        results = self.searcher.invoke(query)
        return [Document(page_content=result["content"]) 
                for result in results]
```

**Features**:
- Configurable search depth
- Result limiting
- Document conversion

### 5. Data Manager (data_manager.py)

**Purpose**: Manages document loading and vector store operations.

```python
class AgentDataManager:
    def load_and_process_documents(self) -> List[Document]:
        # Load documents
        documents = []
        for file_type, loader in self.loaders.items():
            docs = loader.load()
            documents.extend(docs)
            
        # Split into chunks
        return self.text_splitter.split_documents(documents)
```

**Features**:
- Multiple file type support
- Document chunking
- Vector store management

## Common Patterns

### 1. Singleton Pattern Implementation
```python
@classmethod
def get_instance(cls):
    if cls._instance is None:
        cls._instance = cls()
    return cls._instance
```

### 2. Error Handling Pattern
```python
try:
    # Operation
    logger.info("Operation started")
    result = perform_operation()
    logger.debug("Operation result: {result}")
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise
```

### 3. Resource Management Pattern
```python
class ResourceManager:
    def __init__(self):
        self._resource = None
    
    @property
    def resource(self):
        if self._resource is None:
            self._resource = initialize_resource()
        return self._resource
```

## Best Practices

### 1. Logging
- Use appropriate log levels
- Include context in log messages
- Handle exceptions properly
- Use structured logging where appropriate

### 2. Environment Variables
- Never commit sensitive values
- Validate all required variables
- Provide clear error messages
- Use .env.example for documentation

### 3. Resource Management
- Implement proper cleanup
- Use lazy initialization
- Cache expensive resources
- Monitor resource usage

### 4. Error Handling
- Log all errors with context
- Provide meaningful error messages
- Include stack traces for debugging
- Clean up resources on error

## Usage Examples

### Complete Logging Example
```python
def process_operation(data):
    logger = setup_logger("OperationProcessor")
    logger.info(f"Starting operation with {len(data)} items")
    
    try:
        # Operation steps
        logger.debug("Preprocessing data")
        processed = preprocess(data)
        
        logger.debug("Processing main operation")
        result = main_operation(processed)
        
        logger.info("Operation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}", exc_info=True)
        raise
```

### Environment Loading Example
```python
def initialize_system():
    try:
        env_vars = load_env_variables()
        llm = LLMManager.get_instance().get_llm()
        web_search = WebSearchTool()
        return SystemComponents(llm, web_search)
    except EnvironmentError as e:
        logger.critical(f"Failed to initialize: {str(e)}")
        sys.exit(1)
```

## Troubleshooting

Common issues and their solutions:

1. **Missing Environment Variables**
   - Check .env file exists
   - Verify all required variables
   - Check variable names match

2. **Resource Initialization Failures**
   - Check API keys are valid
   - Verify network connectivity
   - Check resource limits

3. **Performance Issues**
   - Monitor resource usage
   - Check caching effectiveness
   - Review log levels in production

4. **Memory Management**
   - Monitor singleton instances
   - Implement cleanup methods
   - Watch for memory leaks