from typing import Dict, Any, List, Optional
from uuid import UUID

from chat_api.adapters.agent_adapter import AgentAdapter
from chat_api.services.memory_service import MemoryService
from chat_api.utils.response_formatter import ResponseFormatter
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

class AgentService:
    """
    Service for interacting with the agent system.
    """
    
    def __init__(
        self, 
        agent_adapter: AgentAdapter, 
        memory_service: MemoryService,
        response_formatter: ResponseFormatter
    ):
        """
        Initialize the agent service.
        
        Args:
            agent_adapter: Adapter for agent operations
            memory_service: Service for memory operations
            response_formatter: Utility for formatting responses
        """
        self.agent_adapter = agent_adapter
        self.memory_service = memory_service
        self.response_formatter = response_formatter
    
    async def process_message(
        self, 
        session_id: UUID, 
        message_content: str,
        system_prompt: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate an agent response.
        
        Args:
            session_id: ID of the session
            message_content: Content of the user message
            system_prompt: Optional system prompt
            user_info: Optional user information
            additional_context: Optional additional context
            
        Returns:
            Dict[str, Any]: Result from the agent execution
        """
        try:
            # Build context from memory
            context = await self.memory_service.build_context(
                session_id=session_id,
                system_prompt=system_prompt,
                user_info=user_info,
                additional_context=additional_context
            )
            
            # Add the current message to context
            context["current_message"] = message_content
            
            # Call the agent to generate a response
            logger.info(f"Sending message to agent for session {session_id}")
            agent_response = await self.agent_adapter.generate_response(context)
            
            # Format the response
            formatted_response = self.response_formatter.format_response(agent_response)
            
            logger.info(f"Received and formatted agent response for session {session_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {str(e)}")
            raise Exception(f"Failed to process message: {str(e)}")
    
    async def generate_title(self, session_id: UUID, first_message: str) -> str:
        """
        Generate a title for a chat session based on the first message.
        
        Args:
            session_id: ID of the session
            first_message: First message in the session
            
        Returns:
            str: Generated title
        """
        try:
            logger.info(f"Generating title for session {session_id}")
            title = await self.agent_adapter.generate_title(first_message)
            return title
        except Exception as e:
            logger.error(f"Error generating title for session {session_id}: {str(e)}")
            # Return a default title instead of raising an exception
            return "New Chat"
    
    async def process_feedback(
        self, 
        session_id: UUID, 
        message_id: UUID, 
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user feedback on a response.
        
        Args:
            session_id: ID of the session
            message_id: ID of the message receiving feedback
            feedback: Feedback data
            
        Returns:
            Dict[str, Any]: Status of the feedback processing
        """
        try:
            # Get the message context
            context = await self.memory_service.build_context(session_id=session_id)
            
            # Add feedback context
            context["feedback"] = {
                "message_id": str(message_id),
                "feedback_data": feedback
            }
            
            # Send feedback to agent
            logger.info(f"Sending feedback to agent for message {message_id} in session {session_id}")
            result = await self.agent_adapter.process_feedback(context)
            
            return result
        except Exception as e:
            logger.error(f"Error processing feedback for message {message_id} in session {session_id}: {str(e)}")
            raise Exception(f"Failed to process feedback: {str(e)}")
    
    async def execute_tool(
        self, 
        session_id: UUID, 
        tool_name: str, 
        tool_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool via the agent.
        
        Args:
            session_id: ID of the session
            tool_name: Name of the tool to execute
            tool_params: Parameters for the tool
            
        Returns:
            Dict[str, Any]: Tool execution results
        """
        try:
            # Get the session context
            context = await self.memory_service.build_context(session_id=session_id)
            
            # Add tool execution context
            context["tool"] = {
                "name": tool_name,
                "params": tool_params
            }
            
            # Execute the tool
            logger.info(f"Executing tool {tool_name} in session {session_id}")
            result = await self.agent_adapter.execute_tool(context)
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name} in session {session_id}: {str(e)}")
            raise Exception(f"Failed to execute tool: {str(e)}")
            
    async def get_agent_types(self) -> Dict[str, str]:
        """
        Get a list of available agent types with descriptions.
        
        Returns:
            Dict[str, str]: Map of agent type names to descriptions
        """
        try:
            return await self.agent_adapter.get_agent_types()
        except Exception as e:
            logger.error(f"Error retrieving agent types: {str(e)}")
            # Return basic types on error
            return {
                "project_manager": "Project planning and management",
                "solution_architect": "System architecture design",
                "full_stack_developer": "Implementation of components",
                "qa_test": "Testing and quality assurance"
            }
            
    async def generate_report(self, session_id: UUID) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict[str, Any]: Generated report
        """
        try:
            logger.info(f"Generating report for session {session_id}")
            report = await self.agent_adapter.generate_report(str(session_id))
            
            # Format report if needed
            formatted_report = self.response_formatter.format_report(report)
            
            return formatted_report
        except Exception as e:
            logger.error(f"Error generating report for session {session_id}: {str(e)}")
            # Return basic report on error
            return {
                "status": "error",
                "message": f"Failed to generate report: {str(e)}",
                "session_id": str(session_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def cleanup_session_agents(self, session_id: UUID) -> bool:
        """
        Clean up agent resources for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Cleaning up agents for session {session_id}")
            success = await self.agent_adapter.cleanup_agent(str(session_id))
            return success
        except Exception as e:
            logger.error(f"Error cleaning up agents for session {session_id}: {str(e)}")
            return False