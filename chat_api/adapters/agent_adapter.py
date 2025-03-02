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
    @monitor_operation(operation_type="agent_response_generation")
    async def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response from the appropriate agent based on session context.
        
        Args:
            context: Context data including session, messages, and other information
            
        Returns:
            Dict[str, Any]: Response from the agent
            
        Raises:
            ValueError: If agent generation fails
        """
        session_id = context.get("session_id")
        if not session_id:
            self.logger.error("Missing session_id in context")
            raise ValueError("Context must include session_id")
            
        self.logger.info(f"Generating response for session {session_id}")
        
        try:
            # Get the agent type from context
            session_info = context.get("session_info", {})
            agent_type = session_info.get("primary_agent", "project_manager")
            
            # Check if agent already exists
            if session_id not in self._active_agents:
                # Create a new agent
                await self.create_agent(
                    session_id=session_id,
                    agent_type=agent_type
                )
            
            agent = self._active_agents[session_id]
            
            # Format input for agent
            current_message = context.get("current_message", "")
            if not current_message:
                self.logger.warning("No current_message in context")
                current_message = "Please help me with this task."
                
            # Create agent input data
            agent_input = {
                "input": current_message,
                "context": context
            }
            
            # Run the agent
            result = await agent.run(agent_input)
            
            # Format the response
            response = {
                "content": result.get("output", "I don't have a specific answer at this moment."),
                "artifacts": result.get("artifacts", []),
                "metadata": {
                    "agent_type": agent_type,
                    "processing_time": result.get("processing_time", 0),
                    "confidence": result.get("confidence", 0.0),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            self.logger.info(f"Generated response for session {session_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return {
                "content": "I encountered an issue processing your request. Please try again.",
                "artifacts": [],
                "metadata": {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    @trace_method
    @monitor_operation(operation_type="agent_title_generation")
    async def generate_title(self, first_message: str) -> str:
        """
        Generate a title for a chat session based on the first message.
        
        Args:
            first_message: First message in the session
            
        Returns:
            str: Generated title
            
        Raises:
            Exception: If title generation fails
        """
        self.logger.info("Generating title for session based on first message")
        
        try:
            # Use ProjectManager agent for title generation
            temp_agent_id = f"title_generator_{uuid4()}"
            
            title_agent = ProjectManagerAgent(
                agent_id=temp_agent_id,
                name="Title Generator",
                memory_manager=self.memory_manager
            )
            
            # Create simplified input for title generation
            title_input = {
                "input": first_message,
                "task": "generate_title",
                "max_length": 50
            }
            
            # Run the agent
            result = await title_agent.run(title_input)
            
            # Extract title from result
            title = result.get("title", "New Chat")
            
            # Clean up title (remove quotes, etc.)
            title = title.strip(' "\'')
            
            # Use default if empty
            if not title:
                title = "New Chat"
                
            self.logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            self.logger.error(f"Error generating title: {str(e)}", exc_info=True)
            return "New Chat"  # Default title on error
    
    @trace_method
    @monitor_operation(operation_type="agent_feedback_processing")
    async def process_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback on a response.
        
        Args:
            context: Context containing feedback data and session information
            
        Returns:
            Dict[str, Any]: Status of the feedback processing
            
        Raises:
            ValueError: If feedback processing fails
        """
        session_id = context.get("session_id")
        if not session_id:
            self.logger.error("Missing session_id in feedback context")
            raise ValueError("Context must include session_id")
            
        feedback_data = context.get("feedback", {})
        if not feedback_data:
            self.logger.error("Missing feedback data in context")
            raise ValueError("Context must include feedback data")
            
        message_id = feedback_data.get("message_id")
        if not message_id:
            self.logger.error("Missing message_id in feedback data")
            raise ValueError("Feedback must include message_id")
            
        self.logger.info(f"Processing feedback for message {message_id} in session {session_id}")
        
        try:
            # Store feedback in memory system for later learning
            # (This would be implemented based on your learning pipeline)
            
            return {
                "status": "success",
                "message": "Feedback recorded successfully",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process feedback: {str(e)}",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @trace_method
    @monitor_operation(operation_type="agent_tool_execution")
    async def execute_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool via the agent.
        
        Args:
            context: Context containing tool information and session data
            
        Returns:
            Dict[str, Any]: Tool execution results
            
        Raises:
            ValueError: If tool execution fails
        """
        session_id = context.get("session_id")
        if not session_id:
            self.logger.error("Missing session_id in tool context")
            raise ValueError("Context must include session_id")
            
        tool_data = context.get("tool", {})
        if not tool_data:
            self.logger.error("Missing tool data in context")
            raise ValueError("Context must include tool data")
            
        tool_name = tool_data.get("name")
        if not tool_name:
            self.logger.error("Missing tool name in tool data")
            raise ValueError("Tool data must include name")
            
        tool_params = tool_data.get("params", {})
        
        self.logger.info(f"Executing tool {tool_name} in session {session_id}")
        
        try:
            if session_id not in self._active_agents:
                # Get the agent type from context
                session_info = context.get("session_info", {})
                agent_type = session_info.get("primary_agent", "project_manager")
                
                # Create a new agent
                await self.create_agent(
                    session_id=session_id,
                    agent_type=agent_type
                )
            
            agent = self._active_agents[session_id]
            
            # Check if agent has the tool
            if not hasattr(agent, "execute_tool"):
                self.logger.error(f"Agent does not support tool execution: {type(agent).__name__}")
                raise ValueError(f"Agent does not support tool execution")
            
            # Execute the tool
            tool_result = await agent.execute_tool(tool_name, tool_params)
            
            self.logger.info(f"Tool {tool_name} executed successfully")
            return {
                "status": "success",
                "tool_name": tool_name,
                "result": tool_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "tool_name": tool_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
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