from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AgentConfig:
    name: str
    description: str
    expertise: List[str]
    tools: List[str]
    
# Default configurations
MECHATRONIC_AGENT_CONFIG = AgentConfig(
    name="Mechatronic Engineer",
    description="Expert in hardware design and engineering",
    expertise=["robotics", "electronics", "mechanical systems", "control systems"],
    tools=["vector_store", "web_search"]
)

PYTHON_AGENT_CONFIG = AgentConfig(
    name="Python Coder",
    description="Expert in Python programming and software development",
    expertise=["python", "algorithms", "data structures", "software design"],
    tools=["vector_store", "web_search"]
)

SUPERVISING_AGENT_CONFIG = AgentConfig(
    name="Supervisor",
    description="Routes queries to appropriate specialized agents",
    expertise=["query analysis", "task routing"],
    tools=["llm"]
)