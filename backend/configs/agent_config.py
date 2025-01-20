from dataclasses import dataclass
from typing import List, Optional
from src.utils.logger import setup_logger

logger = setup_logger("AgentConfig")

@dataclass
class AgentConfig:
    """Configuration for different types of agents."""
    name: str
    description: str
    expertise: List[str]
    tools: List[str]
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        logger.debug(f"Creating agent config for: {self.name}")
        self._validate_config()
        
    def _validate_config(self):
        """Validate the configuration parameters."""
        try:
            if not self.name:
                raise ValueError("Agent name cannot be empty")
            if not self.expertise:
                raise ValueError(f"Agent {self.name} must have at least one expertise")
            if not self.tools:
                raise ValueError(f"Agent {self.name} must have at least one tool")
                
            logger.debug(f"Agent {self.name} config validated successfully")
        except Exception as e:
            logger.error(f"Invalid config for agent {self.name}: {str(e)}")
            raise

logger.info("Creating default agent configurations")

# Default configurations
MECHATRONIC_AGENT_CONFIG = AgentConfig(
    name="Mechatronic Engineer",
    description="Expert in hardware design and engineering",
    expertise=["robotics", "electronics", "mechanical systems", "control systems"],
    tools=["vector_store", "web_search"]
)
logger.debug("Mechatronic agent config created")

PYTHON_AGENT_CONFIG = AgentConfig(
    name="Python Coder",
    description="Expert in Python programming and software development",
    expertise=["python", "algorithms", "data structures", "software design"],
    tools=["vector_store", "web_search"]
)
logger.debug("Python agent config created")

SUPERVISING_AGENT_CONFIG = AgentConfig(
    name="Supervisor",
    description="Routes queries to appropriate specialized agents",
    expertise=["query analysis", "task routing"],
    tools=["llm"]
)
logger.debug("Supervising agent config created")

logger.info("All default agent configurations created successfully")