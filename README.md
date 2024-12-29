# VITA

## Multi-Agent System with LangChain

A specialized multi-agent system built with LangChain that routes queries to appropriate expert agents for processing.

## Architecture Overview

The system consists of three main components:
1. **Supervising Agent**: Routes queries to specialized agents
2. **Specialized Agents**: 
   - Python Agent: Handles programming-related queries
   - Mechatronic Agent: Handles hardware and engineering queries
3. **Core Components**:
   - Vector Store-based RAG
   - Web Search capability
   - Document grading
   - Query rephrasing

## Key Features

- **Query Routing**: Intelligent routing of queries to specialized agents
- **RAG Implementation**: Retrieval-Augmented Generation with document grading
- **Fallback Mechanisms**: Web search when local documents aren't sufficient
- **Async Processing**: Efficient handling of concurrent operations
- **Comprehensive Logging**: Detailed logging at all levels

## Project Structure

```
project/
├── configs/              # Configuration files
├── data/                 # Agent-specific document storage
├── src/                  # Source code
│   ├── agents/          # Agent implementations
│   ├── chains/          # LangChain processing chains
│   ├── prompts/         # System prompts
│   ├── retrievers/      # Retrieval implementations
│   └── utils/           # Utility functions
├── tests/               # Test suites
└── vector_stores/       # Vector embeddings storage
```

## Key Design Patterns Used

1. **Singleton Pattern**:
   - LLMManager: Manages LLM instances
   - RetrieverManager: Manages retriever instances

2. **Factory Pattern**:
   - RetrievalFactory: Creates different types of retrievers

3. **Abstract Base Classes**:
   - BaseAgent: Template for specialized agents

4. **Async/Await**:
   - Used in agents for concurrent operations
   - Web search and document processing

## Setup and Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize vector stores:
```bash
python -m src.utils.vector_stores_initz
```

## Usage

Basic usage example:
```python
from src.agents.supervising_agent import SupervisingAgent
from src.agents.python_agent import PythonAgent
from src.agents.mechatronic_agent import MechatronicAgent

# Initialize agents
python_agent = PythonAgent()
mechatronic_agent = MechatronicAgent()
supervising_agent = SupervisingAgent([python_agent, mechatronic_agent])

# Process query
response = await supervising_agent.process("How do I implement a binary search tree?")
```

## Core Components Documentation

See detailed documentation for each component:
- [Agents Documentation](docs/agents.md)
- [Chains Documentation](docs/chains.md)
- [Retrievers Documentation](docs/retrievers.md)
- [Utilities Documentation](docs/utils.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[License Type] - See LICENSE file for details

## Contact

rohithma05@gmail.com