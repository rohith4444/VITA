from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

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
        if memory_type == "short_term":
            # Keep only recent items in short-term memory
            self.memory["short_term"].append({
                "timestamp": datetime.utcnow(),
                "data": data
            })
            # Maintain only last 10 items
            self.memory["short_term"] = self.memory["short_term"][-10:]
        
        elif memory_type == "working":
            # Update working memory with current state
            self.memory["working"].update(data)
        
        elif memory_type == "episodic":
            # Add to episodic memory with timestamp
            self.memory["episodic"].append({
                "timestamp": datetime.utcnow(),
                "data": data
            })

    async def get_memory(self, memory_type: str) -> Any:
        """Retrieve data from agent's memory."""
        return self.memory.get(memory_type)

    async def update_status(self, status: str) -> None:
        """Update agent's current status."""
        self.status = status
        await self.update_memory("working", {"status": status})

    @abstractmethod
    async def generate_report(self) -> Dict[str, Any]:
        """Generate report of agent's activities and findings."""
        pass