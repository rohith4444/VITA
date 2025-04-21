# VITA - AI-Powered Project Development Platform

VITA is an innovative platform where users can bring their project ideas to life through collaboration with specialized AI agents. The platform transforms project development by providing instant access to a team of AI experts who can plan, execute, and deliver projects across various domains.

## 🎯 Core Concept

VITA operates through a multi-agent system with specialized roles:

- **Project Manager**: Plans projects, breaks down tasks, and allocates resources
- **Solution Architect**: Designs system architecture and selects technology stacks
- **Full Stack Developer**: Implements code for frontend, backend, and database components
- **QA/Test Engineer**: Develops test plans and creates test cases to ensure quality
- **Code Assembler**: Organizes and integrates code components
- **Scrum Master**: Manages project progress and facilitates team communication
- **Team Lead**: Coordinates agent activities and compiles results

## 💻 Technical Architecture

### Agent System

The platform is built on a modular agent architecture:

- Each agent has a defined role with specialized tools and LLM integration
- A state-based workflow graph drives agent execution
- Memory systems (short-term, working, and long-term) maintain context
- Monitoring and tracing capabilities track agent operations

### Backend Components

- **FastAPI Backend**: API endpoints, authentication, and database interactions
- **PostgreSQL Database**: Persistent storage for project data
- **Memory Manager**: Manages different memory types for agent context
- **Monitoring**: LangSmith integration for LLM operation tracking
- **Logging**: Comprehensive logging system with socket and file handlers

## 🧠 Agent Capabilities

### Project Manager Agent
- Analyzes project requirements
- Generates task breakdowns and milestones
- Allocates resources and estimates timelines

### Solution Architect Agent
- Analyzes architecture requirements
- Selects appropriate technology stacks
- Designs system architecture
- Validates architecture against requirements
- Generates technical specifications

### Full Stack Developer Agent
- Analyzes technical requirements
- Designs component solutions (frontend, backend, database)
- Generates production-ready code
- Creates project documentation

### QA/Test Agent
- Analyzes test requirements
- Creates test plans
- Generates test cases
- Implements test code

## 🔧 Tools

The system includes specialized tools for each agent:

- **Project Manager Tools**: Task breakdown, resource allocation, timeline estimation
- **Solution Architect Tools**: Technology selection, architecture validation, specification generation
- **Full Stack Developer Tools**: Requirements analysis, solution design, code generation, documentation
- **QA/Test Tools**: Test analysis, test planning, test generation, test code implementation

## 🗄️ Memory Systems

- **Short-Term Memory**: Temporary storage with automatic decay
- **Working Memory**: Active processing state with quick access
- **Long-Term Memory**: PostgreSQL-based persistent storage for important information

## 📊 Monitoring and Tracing

- Comprehensive metrics for LLM operations and agent activities
- LangSmith integration for visualizing agent workflows
- Detailed logging with customizable levels

## 🏗️ Project Structure

The repository follows a modular structure:

```
project/
├── agents/                # Agent implementations
│   ├── core/              # Base agent functionality
│   ├── project_manager/   # Project planning agent
│   ├── solution_architect/# Architecture design agent
│   ├── full_stack_developer/ # Development agent
│   ├── qa_test/           # Testing agent
│   ├── code_assembler/    # Code integration agent
│   ├── scrum_master/      # Project facilitation agent
│   └── team_lead/         # Coordination agent
├── backend/               # API server and configurations
│   ├── chat_api/          # Chat interface API
│   ├── models/            # Database models
│   ├── routes/            # API routes
│   ├── schemas/           # Data validation schemas
│   └── services/          # Business logic services
├── core/                  # Core system components
│   ├── logging/           # Logging functionality
│   └── tracing/           # Execution tracing
├── memory/                # Memory systems
│   ├── long_term/         # Persistent storage
│   ├── short_term/        # Temporary memory
│   └── working/           # Active context memory
└── tools/                 # Specialized agent tools
    ├── project_manager/   # Planning tools
    ├── solution_architect/# Architecture tools
    ├── full_stack_developer/ # Development tools
    └── qa_test/           # Testing tools
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js (for frontend components)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/vita.git
cd vita
```

2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

4. Configure environment variables
```bash
# Create .env file with required settings
# See .env.example for required variables
```

5. Run the logging server
```bash
python -m core.logging.log_server
```

### Running Agents

Use the scripts in the `scripts/` directory to run individual agents:

```bash
# Run project manager agent
python -m scripts.run_project_manager

# Run solution architect agent
python -m scripts.run_solution_architect_agent

# Run full stack developer agent
python -m scripts.run_software_dev_agent

# Run QA/test agent
python -m scripts.run_qa_test_agent
```

## 📝 License

This project is licensed under the MIT License.

## 📧 Contact

For questions and support, please contact: rohithma05@gmail.com