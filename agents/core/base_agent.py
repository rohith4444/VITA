from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.logging.logger import setup_logger
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from langgraph.graph import StateGraph, END

class BaseAgent(ABC):
    """Abstract base class for all agents using LangGraph."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        self.agent_id = agent_id
        self.name = name
        self.created_at = datetime.utcnow()
        self.status = "initialized"
        self.memory_manager = memory_manager  # ✅ Integrated MemoryManager
        
        # Initialize logger
        self.logger = setup_logger(f"agent.{self.name.lower()}")
        self.logger.info(f"Initializing agent: {self.name} (ID: {self.agent_id})")

        # Initialize processing graph
        self.logger.info("Building agent state graph")
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Builds the LangGraph-based execution flow for this agent."""
        graph = StateGraph(dict)

        # Add agent-specific nodes (to be overridden in child classes)
        self.add_graph_nodes(graph)

        # Define the entry point
        graph.set_entry_point("start")
        
        # Compile the execution graph
        return graph.compile()
    
    @abstractmethod
    def add_graph_nodes(self, graph: StateGraph) -> None:
        """Each agent defines its own processing nodes."""
        pass

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the agent's workflow using LangGraph."""
        self.logger.info(f"Running agent process with input: {input_data}")
        result = self.graph.invoke({"input": input_data, "status": self.status})
        self.logger.info("Agent processing completed.")
        return result

    async def update_memory(self, memory_type: str, data: Any) -> None:
        """Update agent's memory using MemoryManager."""
        self.logger.debug(f"Updating {memory_type} memory")
        try:
            await self.memory_manager.store(self.agent_id, MemoryType[memory_type.upper()], data)
        except Exception as e:
            self.logger.error(f"Error updating memory: {str(e)}")
    
    async def get_memory(self, memory_type: str) -> Any:
        """Retrieve data from agent's memory using MemoryManager."""
        self.logger.debug(f"Retrieving {memory_type} memory")
        try:
            return await self.memory_manager.retrieve(self.agent_id, MemoryType[memory_type.upper()])
        except Exception as e:
            self.logger.error(f"Error retrieving memory: {str(e)}")
            return None
    
    async def update_status(self, status: str) -> None:
        """Update agent's current status and store it in working memory."""
        self.logger.info(f"Status update: {self.status} -> {status}")
        self.status = status
        await self.update_memory("working", {"status": status})

    @abstractmethod
    async def generate_report(self) -> Dict[str, Any]:
        """Generate a report of the agent's activities and findings."""
        pass
