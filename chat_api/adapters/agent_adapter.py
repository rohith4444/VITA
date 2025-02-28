from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime
from uuid import uuid4
import json
import importlib
from agents.core.base_agent import BaseAgent
from memory.memory_manager import MemoryManager
from agents.project_manager.agent import ProjectManagerAgent
from agents.solution_architect.agent import SolutionArchitectAgent
from agents.full_stack_developer.agent import FullStackDeveloperAgent
from agents.qa_test.agent import QATestAgent
from agents.core.monitoring.decorators import monitor_operation
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

# Initialize logger
logger = setup_logger("chat_api.adapters.agent")


@trace_class
class AgentAdapter:
    """
    Adapter for the existing agent system.
    Provides an interface to create, run, and manage agents for the chat API.
    """
    
    # Map of agent type names to their implementation classes
    AGENT_TYPES = {
        "project_manager": ProjectManagerAgent,
        "solution_architect": SolutionArchitectAgent,
        "full_stack_developer": FullStackDeveloperAgent,
        "qa_test": QATestAgent
    }
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the agent adapter with a memory manager instance.
        
        Args:
            memory_manager: The memory manager from the existing system
        """
        self.logger = setup_logger("chat_api.adapters.agent.instance")
        self.logger.info("Initializing Agent Adapter")
        self.memory_manager = memory_manager
        self._active_agents = {}  # session_id -> agent instance
    
    @trace_method
    @monitor_operation(operation_type="agent_creation")
    async def create_agent(self, session_id: str, agent_type: str, name: Optional[str] = None) -> str:
        """
        Create a new agent instance for a session.
        
        Args:
            session_id: Unique identifier for the session
            agent_type: Type of agent to create
            name: Optional name for the agent
            
        Returns:
            str: Agent ID
            
        Raises:
            ValueError: If the agent type is invalid or agent creation fails
        """
        self.logger.info(f"Creating agent of type {agent_type} for session {session_id}")
        
        if agent_type not in self.AGENT_TYPES:
            self.logger.error(f"Invalid agent type: {agent_type}")
            raise ValueError(f"Invalid agent type. Must be one of: {list(self.AGENT_TYPES.keys())}")
        
        try:
            # Generate a unique agent ID
            agent_id = f"{agent_type}_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create agent instance
            agent_class = self.AGENT_TYPES[agent_type]
            agent_instance = agent_class(
                agent_id=agent_id,
                name=name or agent_type.replace('_', ' ').title(),
                memory_manager=self.memory_manager
            )
            
            # Store in active agents
            self._active_agents[session_id] = agent_instance
            
            self.logger.info(f"Successfully created agent with ID: {agent_id}")
            return agent_id
            
        except Exception as e:
            self.logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create agent: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="agent_execution")
    async def run_agent(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an agent with the given input data.
        
        Args:
            session_id: Unique identifier for the session
            input_data: Input data for the agent
            
        Returns:
            Dict[str, Any]: Result from the agent execution
            
        Raises:
            ValueError: If the agent is not found or execution fails
        """
        self.logger.info(f"Running agent for session {session_id}")
        
        if session_id not in self._active_agents:
            self.logger.error(f"No active agent found for session {session_id}")
            raise ValueError(f"No active agent found for session {session_id}")
        
        try:
            agent = self._active_agents[session_id]
            
            # Run the agent
            result = await agent.run(input_data)
            
            self.logger.info(f"Agent execution completed for session {session_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error running agent: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to run agent: {str(e)}")
    
    @trace_method
    @monitor_operation(operation_type="agent_report_generation")
    async def generate_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a report from the agent.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Dict[str, Any]: Generated report
            
        Raises:
            ValueError: If the agent is not found or report generation fails
        """
        self.logger.info(f"Generating report for session {session_id}")
        
        if session_id not in self._active_agents:
            self.logger.error(f"No active agent found for session {session_id}")
            raise ValueError(f"No active agent found for session {session_id}")
        
        try:
            agent = self._active_agents[session_id]
            
            # Generate report
            report = await agent.generate_report()
            
            self.logger.info(f"Report generation completed for session {session_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to generate report: {str(e)}")
    
    @trace_method
    async def get_agent_instance(self, session_id: str) -> Optional[BaseAgent]:
        """
        Get the active agent instance for a session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Optional[BaseAgent]: Agent instance if found, None otherwise
        """
        return self._active_agents.get(session_id)
    
    @trace_method
    async def get_agent_types(self) -> Dict[str, str]:
        """
        Get a list of available agent types with descriptions.
        
        Returns:
            Dict[str, str]: Map of agent type names to descriptions
        """
        agent_type_descriptions = {
            "project_manager": "Manages project planning and coordination",
            "solution_architect": "Designs system architecture and technical specifications",
            "full_stack_developer": "Implements frontend and backend components",
            "qa_test": "Creates test plans and validates implementation"
        }
        return agent_type_descriptions
    
    @trace_method
    @monitor_operation(operation_type="agent_cleanup")
    async def cleanup_agent(self, session_id: str) -> bool:
        """
        Clean up resources for an agent.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Cleaning up agent for session {session_id}")
        
        if session_id not in self._active_agents:
            self.logger.warning(f"No active agent found for session {session_id}")
            return False
        
        try:
            agent = self._active_agents[session_id]
            
            # Use context manager to clean up resources
            async with agent:
                pass
            
            # Remove from active agents
            del self._active_agents[session_id]
            
            self.logger.info(f"Agent cleanup completed for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up agent: {str(e)}", exc_info=True)
            return False
    
    @trace_method
    @monitor_operation(operation_type="agent_cleanup_all")
    async def cleanup_all_agents(self) -> bool:
        """
        Clean up resources for all active agents.
        
        Returns:
            bool: Success status
        """
        self.logger.info("Cleaning up all active agents")
        
        if not self._active_agents:
            self.logger.info("No active agents to clean up")
            return True
        
        success = True
        for session_id in list(self._active_agents.keys()):
            try:
                result = await self.cleanup_agent(session_id)
                if not result:
                    success = False
            except Exception as e:
                self.logger.error(f"Error cleaning up agent for session {session_id}: {str(e)}", exc_info=True)
                success = False
        
        self.logger.info("All agent cleanups attempted")
        return success