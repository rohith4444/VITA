from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from core.logging.logger import setup_logger
from core.tracing.service import  trace_class
from memory.memory_manager import MemoryManager
from memory.base import MemoryType

@trace_class
class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        self.logger = setup_logger(f"base_agent.{name.lower()}")
        self.logger.info(f"Initializing base agent: {name} (ID: {agent_id})")
        
        try:
            self.agent_id = agent_id
            self.name = name
            self.created_at = datetime.utcnow()
            self.status = "initialized"
            self.memory_manager = memory_manager
            self.logger.info("Base agent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize base agent: {str(e)}", exc_info=True)
            raise

    async def update_memory(self, memory_type: str, data: Any) -> None:
        """Update agent's memory using MemoryManager."""
        self.logger.debug(f"Updating {memory_type} memory")
        try:
            await self.memory_manager.store(
                self.agent_id, 
                MemoryType[memory_type.upper()], 
                data
            )
            self.logger.debug(f"Successfully updated {memory_type} memory")
            
        except Exception as e:
            self.logger.error(f"Failed to update {memory_type} memory: {str(e)}", exc_info=True)
            raise
    
    async def get_memory(self, memory_type: str) -> Any:
        """Retrieve data from agent's memory using MemoryManager."""
        self.logger.debug(f"Retrieving {memory_type} memory")
        try:
            result = await self.memory_manager.retrieve(
                self.agent_id, 
                MemoryType[memory_type.upper()]
            )
            self.logger.debug(f"Successfully retrieved {memory_type} memory")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve {memory_type} memory: {str(e)}", exc_info=True)
            return None
    
    async def update_status(self, status: str) -> None:
        """Update agent's current status and store it in working memory."""
        self.logger.info(f"Updating agent status: {self.status} -> {status}")
        try:
            self.status = status
            await self.update_memory("working", {"status": status})
            self.logger.debug("Status updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {str(e)}", exc_info=True)
            raise

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's workflow."""
        pass

    @abstractmethod
    async def generate_report(self) -> Dict[str, Any]:
        """Generate a report of the agent's activities."""
        pass