from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from uuid import UUID
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_method, trace_class
from chat_api.models.message import MessageRole, MessageType
from chat_api.adapters.memory_adapter import MemoryAdapter
from sqlalchemy.orm import Session

# Initialize logger
logger = setup_logger("chat_api.utils.context_builder")


@trace_class
class ContextBuilder:
    """
    Utility class for building conversation context from memory for AI agents.
    Extracts relevant information from both database and memory system,
    then formats it appropriately for each agent type.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter, db_session: Optional[Session] = None):
        """
        Initialize the context builder with memory adapter and optional db session.
        
        Args:
            memory_adapter: Adapter for the memory system
            db_session: Optional SQLAlchemy database session
        """
        self.logger = setup_logger("chat_api.utils.context_builder.instance")
        self.logger.info("Initializing ContextBuilder with hybrid data retrieval")
        self.memory_adapter = memory_adapter
        self.db = db_session
    
    @trace_method
    @monitor_operation(operation_type="context_building")
    async def build_context(self, 
                          session_id: UUID,
                          message_id: Optional[UUID] = None,
                          time_window: Optional[int] = None,
                          max_messages: int = 20,
                          system_prompt: Optional[str] = None,
                          user_info: Optional[Dict[str, Any]] = None,
                          additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build a comprehensive context for an agent based on conversation history.
        Retrieves data from both database and the memory system.
        
        Args:
            session_id: ID of the conversation session
            message_id: Optional ID of the current message
            time_window: Optional time window in seconds for context
            max_messages: Maximum number of messages to include
            system_prompt: Optional system instructions or prompt
            user_info: Optional user information
            additional_context: Optional additional context data
            
        Returns:
            Dict[str, Any]: Structured context for the agent
        """
        self.logger.info(f"Building context for session {session_id}")
        
        try:
            # Get conversation history from database if available
            db_conversation = []
            if self.db:
                db_conversation = await self._get_conversation_from_db(
                    session_id=session_id,
                    time_window=time_window,
                    max_messages=max_messages
                )
            
            # Fall back to memory system if database retrieval failed
            conversation_history = db_conversation
            if not conversation_history:
                conversation_history = await self._get_conversation_from_memory(
                    session_id=session_id,
                    time_window=time_window,
                    max_messages=max_messages
                )
            
            # Get session information from database or memory
            session_info = await self._get_session_info(session_id)
            
            # Get working state from memory system
            working_state = await self._get_working_state(session_id)
            
            # Get long-term context from memory system
            long_term_context = await self._get_long_term_context(
                session_id=session_id
            )
            
            # Combine components into complete context
            context = {
                "session_id": str(session_id),
                "message_id": str(message_id) if message_id else None,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_history": conversation_history,
                "session_info": session_info,
                "working_state": working_state,
                "long_term_context": long_term_context,
                "system_prompt": system_prompt,
                "user_info": user_info or {},
                "additional_context": additional_context or {}
            }
            
            self.logger.info(f"Context built successfully with {len(conversation_history)} conversation messages")
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {str(e)}", exc_info=True)
            # Return minimal context on error
            return {
                "session_id": str(session_id),
                "message_id": str(message_id) if message_id else None,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "session_info": {},
                "working_state": {},
                "long_term_context": {},
                "system_prompt": system_prompt,
                "user_info": user_info or {},
                "additional_context": additional_context or {}
            }
    
    @trace_method
    async def _get_conversation_from_db(self,
                                      session_id: UUID,
                                      time_window: Optional[int] = None,
                                      max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Get conversation history from the database.
        
        Args:
            session_id: ID of the conversation session
            time_window: Optional time window in seconds
            max_messages: Maximum number of messages to include
            
        Returns:
            List[Dict[str, Any]]: List of formatted conversation messages
        """
        self.logger.debug(f"Getting conversation from database for session {session_id}")
        
        try:
            from chat_api.models.message import MessageModel
            from chat_api.models.artifact import ArtifactModel
            
            # Build query for messages
            query = self.db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            )
            
            # Apply time filter if specified
            if time_window:
                time_threshold = datetime.utcnow() - timedelta(seconds=time_window)
                query = query.filter(MessageModel.created_at >= time_threshold)
            
            # Order by timestamp and limit results
            query = query.order_by(MessageModel.created_at.desc()).limit(max_messages)
            
            # Execute query
            messages = query.all()
            
            # Format messages
            formatted_messages = []
            for message in messages:
                # Get artifacts for this message
                artifacts = self.db.query(ArtifactModel).filter(
                    ArtifactModel.message_id == message.id
                ).all()
                
                formatted_artifacts = [
                    {
                        "artifact_id": str(artifact.id),
                        "type": artifact.type,
                        "title": artifact.title,
                        "language": artifact.language,
                        "metadata": artifact.metadata
                    }
                    for artifact in artifacts
                ]
                
                formatted_message = {
                    "message_id": str(message.id),
                    "role": message.role,
                    "content": message.content,
                    "type": message.type,
                    "timestamp": message.created_at.isoformat(),
                    "artifacts": formatted_artifacts,
                    "metadata": message.metadata
                }
                
                formatted_messages.append(formatted_message)
            
            # Reverse to get chronological order
            formatted_messages.reverse()
            
            self.logger.debug(f"Retrieved {len(formatted_messages)} messages from database")
            return formatted_messages
            
        except Exception as e:
            self.logger.error(f"Error getting conversation from database: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def _get_conversation_from_memory(self,
                                         session_id: UUID,
                                         time_window: Optional[int] = None,
                                         max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Get conversation history from the memory system.
        
        Args:
            session_id: ID of the conversation session
            time_window: Optional time window in seconds
            max_messages: Maximum number of messages to include
            
        Returns:
            List[Dict[str, Any]]: List of formatted conversation messages
        """
        self.logger.debug(f"Getting conversation from memory for session {session_id}")
        
        try:
            # Build query
            query = {"metadata.content_type": "message"}
            
            if time_window:
                # Calculate the timestamp threshold
                time_threshold = datetime.utcnow() - timedelta(seconds=time_window)
                query["timestamp"] = {"$gt": time_threshold.isoformat()}
            
            # Retrieve from memory
            memory_entries = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id),
                query=query,
                sort_by="timestamp",
                limit=max_messages
            )
            
            # Format memory entries into conversation messages
            formatted_messages = []
            for entry in memory_entries:
                content = entry.get("content", {})
                message = content.get("message", {})
                
                if message:
                    formatted_message = {
                        "message_id": message.get("message_id", ""),
                        "role": message.get("role", "user"),
                        "content": message.get("content", ""),
                        "timestamp": message.get("timestamp", ""),
                        "artifacts": message.get("artifacts", []),
                        "metadata": entry.get("metadata", {})
                    }
                    
                    formatted_messages.append(formatted_message)
            
            # Sort by timestamp
            formatted_messages.sort(key=lambda x: x.get("timestamp", ""))
            
            self.logger.debug(f"Retrieved {len(formatted_messages)} messages from memory")
            return formatted_messages
            
        except Exception as e:
            self.logger.error(f"Error getting conversation from memory: {str(e)}", exc_info=True)
            return []
    
    @trace_method
    async def _get_session_info(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get session information from database or memory system.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict[str, Any]: Session information
        """
        self.logger.debug(f"Getting session info for session {session_id}")
        
        try:
            # Try to get session info from database first
            if self.db:
                from chat_api.models.session import SessionModel
                session = self.db.query(SessionModel).filter(
                    SessionModel.id == session_id
                ).first()
                
                if session:
                    return {
                        "session_id": str(session.id),
                        "title": session.title,
                        "status": session.status,
                        "session_type": session.session_type,
                        "primary_agent": session.primary_agent,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat(),
                        "message_count": session.message_count,
                        "settings": session.settings,
                        "metadata": session.metadata
                    }
            
            # Fall back to memory system
            query = {"metadata.content_type": "session_info"}
            sessions = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id),
                query=query,
                sort_by="timestamp",
                limit=1
            )
            
            if sessions:
                content = sessions[0].get("content", {})
                session_info = content.get("session_info", {})
                return session_info
            
            # Return minimal info if not found
            return {
                "session_id": str(session_id),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session info: {str(e)}", exc_info=True)
            return {
                "session_id": str(session_id),
                "created_at": datetime.utcnow().isoformat()
            }
    
    @trace_method
    async def _get_working_state(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get current working state from the memory system.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict[str, Any]: Current working state
        """
        self.logger.debug(f"Getting working state for session {session_id}")
        
        try:
            # Get working state from working memory
            working_entries = await self.memory_adapter.retrieve_working(
                agent_id=str(session_id)
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
    async def _get_long_term_context(self, session_id: UUID) -> Dict[str, Any]:
        """
        Extract relevant long-term context for the current session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict[str, Any]: Structured long-term context
        """
        self.logger.debug(f"Getting long-term context for session {session_id}")
        
        try:
            # Get high-importance memories except messages and session info
            query = {
                "metadata.importance": {"$gt": 0.7},  # High importance memories
                "metadata.content_type": {"$nin": ["message", "session_info"]} 
            }
            
            long_term_entries = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id),
                query=query,
                sort_by="metadata.importance",
                limit=20
            )
            
            # Extract artifacts and key information
            artifacts = []
            insights = []
            decisions = []
            key_information = {}
            
            for entry in long_term_entries:
                content = entry.get("content", {})
                metadata = entry.get("metadata", {})
                content_type = metadata.get("content_type", "")
                
                # Handle different content types
                if "artifact" in content:
                    artifact = content["artifact"]
                    artifacts.append({
                        "artifact_id": artifact.get("artifact_id", ""),
                        "type": artifact.get("type", ""),
                        "title": artifact.get("title", ""),
                        "summary": artifact.get("summary", ""),
                        "metadata": metadata
                    })
                
                elif content_type == "insight":
                    insights.append({
                        "content": content.get("insight", ""),
                        "source": metadata.get("source", ""),
                        "timestamp": entry.get("timestamp", "")
                    })
                
                elif content_type == "decision":
                    decisions.append({
                        "content": content.get("decision", ""),
                        "rationale": content.get("rationale", ""),
                        "timestamp": entry.get("timestamp", "")
                    })
                
                # Add to key information for other types
                elif "key_information" in content:
                    key_information.update(content["key_information"])
            
            long_term_context = {
                "artifacts": artifacts,
                "insights": insights,
                "decisions": decisions,
                "key_information": key_information
            }
            
            self.logger.debug(f"Built long-term context with {len(artifacts)} artifacts, "
                            f"{len(insights)} insights, and {len(decisions)} decisions")
            return long_term_context
            
        except Exception as e:
            self.logger.error(f"Error getting long-term context: {str(e)}", exc_info=True)
            return {"artifacts": [], "insights": [], "decisions": [], "key_information": {}}
    
    @trace_method
    @monitor_operation(operation_type="context_format")
    async def format_for_agent(self, context: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """
        Format context for a specific agent type.
        
        Args:
            context: Built context
            agent_type: Type of agent (project_manager, solution_architect, etc.)
            
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
                "timestamp": context["timestamp"],
                "system_prompt": context.get("system_prompt", "")
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
                # Add any artifacts as references
                artifact_text = ""
                artifacts = message.get("artifacts", [])
                if artifacts:
                    artifact_text = "\n[References: " + ", ".join(
                        f"{a.get('title', 'Unnamed')}" for a in artifacts
                    ) + "]"
                
                formatted_text += f"{role}: {content}{artifact_text}\n\n"
        
        return formatted_text
    
    def _format_for_project_manager(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context specifically for Project Manager agent.
        
        Args:
            context: Complete context
            
        Returns:
            Dict[str, Any]: Project Manager specific context
        """
        working_state = context.get("working_state", {})
        long_term_context = context.get("long_term_context", {})
        
        # Extract project plan from working state if available
        project_plan = working_state.get("project_plan", {})
        if not project_plan:
            # Look for project plan in long-term context
            project_plan = long_term_context.get("key_information", {}).get("project_plan", {})
        
        # Extract requirements analysis
        requirements_analysis = working_state.get("requirement_analysis", {})
        if not requirements_analysis:
            requirements_analysis = long_term_context.get("key_information", {}).get("requirement_analysis", {})
        
        # Extract decisions that might impact project management
        decisions = long_term_context.get("decisions", [])
        project_decisions = [d for d in decisions if "project" in d.get("content", "").lower()]
        
        return {
            "project_plan": project_plan,
            "requirements_analysis": requirements_analysis,
            "project_decisions": project_decisions,
            "artifacts": long_term_context.get("artifacts", [])
        }
    
    def _format_for_solution_architect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context specifically for Solution Architect agent.
        
        Args:
            context: Complete context
            
        Returns:
            Dict[str, Any]: Solution Architect specific context
        """
        working_state = context.get("working_state", {})
        long_term_context = context.get("long_term_context", {})
        
        # Extract project plan from project manager if available
        project_plan = working_state.get("project_plan", {})
        
        # Extract architecture design
        architecture_design = working_state.get("architecture_design", {})
        if not architecture_design:
            architecture_design = long_term_context.get("key_information", {}).get("architecture_design", {})
        
        # Extract requirements analysis
        requirements_analysis = working_state.get("requirement_analysis", {})
        
        # Extract technical insights
        insights = long_term_context.get("insights", [])
        technical_insights = [i for i in insights if "technical" in i.get("source", "").lower()]
        
        # Extract architecture artifacts
        artifacts = long_term_context.get("artifacts", [])
        architecture_artifacts = [
            a for a in artifacts if "architecture" in a.get("title", "").lower() 
            or "design" in a.get("title", "").lower()
        ]
        
        return {
            "project_plan": project_plan,
            "requirements_analysis": requirements_analysis,
            "architecture_design": architecture_design,
            "technical_insights": technical_insights,
            "architecture_artifacts": architecture_artifacts
        }
    
    def _format_for_developer(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context specifically for Full Stack Developer agent.
        
        Args:
            context: Complete context
            
        Returns:
            Dict[str, Any]: Developer specific context
        """
        working_state = context.get("working_state", {})
        long_term_context = context.get("long_term_context", {})
        
        # Extract architecture design from solution architect
        architecture_design = working_state.get("architecture_design", {})
        
        # Extract solution design
        solution_design = working_state.get("solution_design", {})
        if not solution_design:
            solution_design = long_term_context.get("key_information", {}).get("solution_design", {})
        
        # Extract tech stack
        tech_stack = working_state.get("tech_stack", {})
        if not tech_stack:
            tech_stack = long_term_context.get("key_information", {}).get("tech_stack", {})
        
        # Extract code artifacts
        artifacts = long_term_context.get("artifacts", [])
        code_artifacts = [
            a for a in artifacts if "code" in a.get("type", "").lower() 
            or "implementation" in a.get("title", "").lower()
        ]
        
        return {
            "architecture_design": architecture_design,
            "solution_design": solution_design,
            "tech_stack": tech_stack,
            "code_artifacts": code_artifacts,
            "generated_code": working_state.get("generated_code", {})
        }
    
    def _format_for_qa_test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context specifically for QA/Test agent.
        
        Args:
            context: Complete context
            
        Returns:
            Dict[str, Any]: QA/Test specific context
        """
        working_state = context.get("working_state", {})
        long_term_context = context.get("long_term_context", {})
        
        # Extract code from developer
        code = working_state.get("generated_code", {})
        
        # Extract specifications
        specifications = working_state.get("specifications", {})
        if not specifications:
            specifications = long_term_context.get("key_information", {}).get("specifications", {})
        
        # Extract test requirements
        test_requirements = working_state.get("test_requirements", {})
        if not test_requirements:
            test_requirements = long_term_context.get("key_information", {}).get("test_requirements", {})
        
        # Extract test artifacts
        artifacts = long_term_context.get("artifacts", [])
        test_artifacts = [
            a for a in artifacts if "test" in a.get("title", "").lower() 
            or "qa" in a.get("title", "").lower()
        ]
        
        return {
            "code": code,
            "specifications": specifications,
            "test_requirements": test_requirements,
            "test_artifacts": test_artifacts,
            "test_plan": working_state.get("test_plan", {}),
            "test_cases": working_state.get("test_cases", {})
        }