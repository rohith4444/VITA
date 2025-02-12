# agents/core/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.logging.logger import setup_logger

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.created_at = datetime.utcnow()
        self.status = "initialized"
        self.current_task = None
        self.memory = {
            "short_term": [],
            "working": {},
            "episodic": []
        }
        # Initialize logger with agent name
        self.logger = setup_logger(f"agent.{self.name.lower()}")
        self.logger.info(f"Initializing agent: {self.name} (ID: {self.agent_id})")

    @abstractmethod
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results."""
        pass

    @abstractmethod
    async def reflect(self) -> Dict[str, Any]:
        """Perform self-reflection and analysis."""
        pass

    async def update_memory(self, memory_type: str, data: Any) -> None:
        """Update agent's memory."""
        self.logger.debug(f"Updating {memory_type} memory")
        try:
            if memory_type == "short_term":
                # Keep only recent items in short-term memory
                self.memory["short_term"].append({
                    "timestamp": datetime.utcnow(),
                    "data": data
                })
                # Maintain only last 10 items
                self.memory["short_term"] = self.memory["short_term"][-10:]
                self.logger.debug(f"Short-term memory updated, size: {len(self.memory['short_term'])}")
            
            elif memory_type == "working":
                # Update working memory with current state
                self.memory["working"].update(data)
                self.logger.debug("Working memory updated with new data")
            
            elif memory_type == "episodic":
                # Add to episodic memory with timestamp
                self.memory["episodic"].append({
                    "timestamp": datetime.utcnow(),
                    "data": data
                })
                self.logger.debug("Added new entry to episodic memory")
        except Exception as e:
            self.logger.error(f"Error updating {memory_type} memory: {str(e)}")
            raise

    async def get_memory(self, memory_type: str) -> Any:
        """Retrieve data from agent's memory."""
        self.logger.debug(f"Retrieving {memory_type} memory")
        try:
            return self.memory.get(memory_type)
        except Exception as e:
            self.logger.error(f"Error retrieving {memory_type} memory: {str(e)}")
            raise

    async def update_status(self, status: str) -> None:
        """Update agent's current status."""
        self.logger.info(f"Status update: {self.status} -> {status}")
        self.status = status
        await self.update_memory("working", {"status": status})

    @abstractmethod
    async def generate_report(self) -> Dict[str, Any]:
        """Generate report of agent's activities and findings."""
        pass