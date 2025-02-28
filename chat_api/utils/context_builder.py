from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_method
from chat_api.models.message import MessageRole, MessageType
from chat_api.adapters.memory_adapter import MemoryAdapter

# Initialize logger
logger = setup_logger("chat_api.utils.context_builder")


class ContextBuilder:
    """
    Utility class for building conversation context from memory for AI agents.
    Extracts relevant information from different memory tiers and formats it
    for agent consumption.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter):
        """
        Initialize the context builder with a memory adapter.
        
        Args:
            memory_adapter: Adapter for the memory system
        """
        self.logger = setup_logger("chat_api.utils.context_builder.instance")
        self.logger.info("Initializing ContextBuilder")
        self.memory_adapter = memory_adapter
    
    @trace_method
    @monitor_operation(operation_type="context_building")
    async def build_context(self, 
                          agent_id: str,
                          session_id: str,
                          message_id: Optional[str] = None,
                          time_window: Optional[int] = None,
                          max_messages: int = 20) -> Dict[str, Any]:
        """
        Build a comprehensive context for an agent based on conversation history.
        
        Args:
            agent_id: ID of the agent
            session_id: ID of the conversation session
            message_id: Optional ID of the current message
            time_window: Optional time window in seconds for context
            max_messages: Maximum number of messages to include
            
        Returns:
            Dict[str, Any]: Structured context for the agent
        """
        self.logger.info(f"Building context for agent {agent_id} in session {session_id}")
        
        try:
            # Build context components
            conversation_history = await self._build_conversation_history(
                agent_id=agent_id,
                session_id=session_id,
                time_window=time_window,
                max_messages=max_messages
            )
            
            working_state = await self._get_working_state(agent_id)
            
            long_term_context = await self._get_long_term_context(
                agent_id=agent_id,
                session_id=session_id
            )
            
            # Combine components into complete context
            context = {
                "session_id": session_id,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_history": conversation_history,
                "working_state": working_state,
                "long_term_context": long_term_context
            }
            
            self.logger.info(f"Context built successfully with {len(conversation_history)} conversation messages")
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {str(e)}", exc_info=True)
            # Return minimal context on error
            return {
                "session_id": session_id,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "working_state": {},
                "long_term_context": {}
            }
    
    @trace_method
    async def _build_conversation_history(self,
                                        agent_id: str,
                                        session_id: str,
                                        time_window: Optional[int] = None,
                                        max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Build conversation history from short-term memory.
        
        Args:
            agent_id: ID of the agent
            session_id: ID of the conversation session
            time_window: Optional time window in seconds
            max_messages: Maximum number of messages to include
            
        Returns:
            List[Dict[str, Any]]: List of formatted conversation messages
        """
        self.logger.debug(f"Building conversation history for agent {agent_id}")
        
        try:
            # Get conversation history from short-term memory
            query = {"session_id": session_id}
            
            if time_window:
                # Calculate the timestamp threshold
                time_threshold = datetime.utcnow() - timedelta(seconds=time_window)
                query["timestamp"] = {"$gt": time_threshold.isoformat()}
            
            conversation_entries = await self.memory_adapter.retrieve_short_term(
                agent_id=agent_id,
                query=query
            )
            
            # Sort by timestamp and limit to max_messages
            conversation_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            conversation_entries = conversation_entries[:max_messages]
            
            # Format conversation history
            formatted_history = []
            for entry in conversation_entries:
                content = entry.get("content", {})
                if "message" in content:
                    formatted_history.append({
                        "role": content.get("role", MessageRole.USER.value),
                        "content": content.get("message", ""),
                        "message_id": content.get("message_id", ""),
                        "timestamp": content.get("timestamp", "")
                    })
            
            # Reverse to get chronological order
            formatted_history.reverse()
            
            self.logger.debug(f"Built conversation history with {len(formatted_history)} messages")
            return formatted_history
            
        except Exception as e:
            self.logger.error(f"Error building conversation history: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def _get_working_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Retrieve current working state from working memory.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict[str, Any]: Current working state
        """
        self.logger.debug(f"Getting working state for agent {agent_id}")
        
        try:
            # Get working state from working memory
            working_entries = await self.memory_adapter.retrieve_working(
                agent_id=agent_id
            )
            
            # Combine all working entries into a single state
            working_state = {}
            for entry in working_entries:
                content = entry.get("content", {})
                working_state.update(content)
            
            self.logger.debug(f"Retrieved working state with {len(working_state)} fields")
            return working_state
            
        except Exception as e:
            self.logger.error(f"Error getting working state: {str(e)}", exc_info=True)
            return {}
    
    @trace_method
    async def _get_long_term_context(self, agent_id: str, session_id: str) -> Dict[str, Any]:
        """
        Extract relevant long-term context for the current session.
        
        Args:
            agent_id: ID of the agent
            session_id: ID of the conversation session
            
        Returns:
            Dict[str, Any]: Structured long-term context
        """
        self.logger.debug(f"Getting long-term context for agent {agent_id} in session {session_id}")
        
        try:
            # Get high-importance memories for this session
            query = {
                "metadata.session_id": session_id,
                "metadata.importance": {"$gt": 0.7}  # High importance memories
            }
            
            long_term_entries = await self.memory_adapter.retrieve_long_term(
                agent_id=agent_id,
                query=query,
                sort_by="metadata.importance",
                limit=10
            )
            
            # Extract artifacts and key information
            artifacts = []
            key_information = {}
            
            for entry in long_term_entries:
                content = entry.get("content", {})
                
                # Check if it's an artifact
                if "artifact" in content:
                    artifacts.append({
                        "title": content.get("title", "Untitled"),
                        "type": content.get("type", "unknown"),
                        "summary": content.get("summary", ""),
                        "artifact_id": content.get("artifact_id", "")
                    })
                
                # Check if it's key information
                if "key_information" in content:
                    key_information.update(content["key_information"])
            
            long_term_context = {
                "artifacts": artifacts,
                "key_information": key_information
            }
            
            self.logger.debug(f"Built long-term context with {len(artifacts)} artifacts and {len(key_information)} key information items")
            return long_term_context
            
        except Exception as e:
            self.logger.error(f"Error getting long-term context: {str(e)}", exc_info=True)
            return {"artifacts": [], "key_information": {}}
    
    @trace_method
    @monitor_operation(operation_type="context_format")
    async def format_for_agent(self, context: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """
        Format context for a specific agent type.
        
        Args:
            context: Built context
            agent_type: Type of agent
            
        Returns:
            Dict[str, Any]: Agent-specific formatted context
        """
        self.logger.info(f"Formatting context for agent type: {agent_type}")
        
        try:
            # Base formatted context
            formatted_context = {
                "input": self._format_conversation_for_agent(context["conversation_history"]),
                "session_id": context["session_id"],
                "message_id": context["message_id"],
                "timestamp": context["timestamp"]
            }
            
            # Add agent-specific formatting
            if agent_type == "project_manager":
                formatted_context.update(self._format_for_project_manager(context))
            elif agent_type == "solution_architect":
                formatted_context.update(self._format_for_solution_architect(context))
            elif agent_type == "full_stack_developer":
                formatted_context.update(self._format_for_developer(context))
            elif agent_type == "qa_test":
                formatted_context.update(self._format_for_qa_test(context))
            
            self.logger.info(f"Context formatted successfully for {agent_type}")
            return formatted_context
            
        except Exception as e:
            self.logger.error(f"Error formatting context for agent: {str(e)}", exc_info=True)
            
            # Return minimally formatted context on error
            return {
                "input": self._format_conversation_for_agent(context.get("conversation_history", [])),
                "session_id": context.get("session_id", ""),
                "message_id": context.get("message_id", "")
            }
    
    def _format_conversation_for_agent(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Format conversation history as text for agent input.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            str: Formatted conversation text
        """
        formatted_text = ""
        
        for message in conversation_history:
            role = message.get("role", "").upper()
            content = message.get("content", "")
            
            if role and content:
                formatted_text += f"{role}: {content}\n\n"
        
        return formatted_text
    
    def _format_for_project_manager(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format context specifically for Project Manager agent."""
        working_state = context.get("working_state", {})
        project_plan = working_state.get("project_plan", {})
        
        return {
            "project_plan": project_plan
        }
    
    def _format_for_solution_architect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format context specifically for Solution Architect agent."""
        working_state = context.get("working_state", {})
        project_plan = working_state.get("project_plan", {})
        
        return {
            "project_plan": project_plan
        }
    
    def _format_for_developer(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format context specifically for Full Stack Developer agent."""
        working_state = context.get("working_state", {})
        solution_design = working_state.get("solution_design", {})
        
        return {
            "solution_design": solution_design
        }
    
    def _format_for_qa_test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format context specifically for QA/Test agent."""
        working_state = context.get("working_state", {})
        code = working_state.get("code", {})
        specifications = working_state.get("specifications", {})
        
        return {
            "code": code,
            "specifications": specifications
        }