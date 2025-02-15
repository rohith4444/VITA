from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from core.logging.logger import setup_logger
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from langgraph.graph import StateGraph, END

class BaseAgent(ABC):
    """Abstract base class for all agents using LangGraph."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        self.logger = setup_logger(f"base_agent.{name.lower()}")
        self.logger.info(f"Initializing base agent: {name} (ID: {agent_id})")
        
        try:
            self.agent_id = agent_id
            self.name = name
            self.created_at = datetime.utcnow()
            self.status = "initialized"
            self.memory_manager = memory_manager
            
            self.logger.debug(f"Agent created at: {self.created_at}")
            self.logger.debug(f"Initial status: {self.status}")

            # Initialize processing graph
            self.logger.info("Building agent state graph")
            self.graph = self._build_graph()
            self.logger.info("Agent initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize base agent: {str(e)}", exc_info=True)
            raise
    
    def _build_graph(self) -> StateGraph:
        """Builds the LangGraph-based execution flow for this agent."""
        self.logger.debug("Building agent graph")
        try:
            graph = StateGraph(dict)
            
            # Add agent-specific nodes
            self.logger.debug("Adding agent-specific nodes")
            self.add_graph_nodes(graph)
            
            # Define entry point
            self.logger.debug("Setting graph entry point to 'start'")
            graph.set_entry_point("start")
            
            # Compile graph
            self.logger.debug("Compiling agent graph")
            compiled_graph = graph.compile()
            self.logger.info("Graph built successfully")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build agent graph: {str(e)}", exc_info=True)
            raise
    
    @abstractmethod
    def add_graph_nodes(self, graph: StateGraph) -> None:
        """Each agent defines its own processing nodes."""
        pass

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the agent's workflow using LangGraph."""
        self.logger.info("Starting agent workflow execution")
        try:
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            result = self.graph.invoke({"input": input_data, "status": self.status})
            self.logger.info("Agent workflow completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
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
    async def generate_report(self) -> Dict[str, Any]:
        """Generate a report of the agent's activities and findings."""
        pass