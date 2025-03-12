from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
from datetime import datetime
import json, uuid
import os
import logging

from core.logging.logger import setup_logger
from core.tracing.service import trace_method, trace_class
from agents.core.base_agent import BaseAgent
from agents.scrum_master.llm.sm_service import ScrumMasterLLMService
from agents.scrum_master.sm_state_graph import (
    ScrumMasterGraphState, RequestType, FeedbackType, UserTechnicalLevel, 
    MilestoneAction, AgentType, Priority, validate_state, 
    create_initial_state, get_next_stage, transition_state,
    determine_request_type, resolve_optimal_agent_routing,
    prepare_state_context_for_llm, extract_state_visualization_data
)

from tools.scrum_master.feedback_processor import (
    process_feedback, translate_feedback_for_technical_team,
    track_feedback_status, add_response_to_feedback,
    prepare_feedback_for_user
)

from tools.scrum_master.checkpoint_manager import (
    create_checkpoint, track_checkpoint_status,
    process_user_approval, process_user_rejection,
    add_user_feedback, notify_team_lead
)

from tools.team_lead.agent_communicator import (
    AgentCommunicator, MessageType, MessagePriority, 
    DeliverableType, UserFeedbackType
)

from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from agents.core.monitoring.decorators import monitor_operation

# Initialize logger
logger = setup_logger("scrum_master.agent")

@trace_class
class ScrumMasterAgent(BaseAgent):
    """
    Scrum Master Agent responsible for human-AI collaboration, handling user feedback,
    and translating between technical agents and users.
    
    Attributes:
        agent_id (str): Unique identifier for this agent instance
        name (str): Display name for the agent
        memory_manager (MemoryManager): Memory management system
        llm_service (ScrumMasterLLMService): LLM service for user communication
        agent_communicator (AgentCommunicator): Tool for agent communication
        registered_agents (Dict[str, Dict[str, Any]]): Information about available agents
        user_preferences (Dict[str, Dict[str, Any]]): User preferences by user ID
        active_conversations (Dict[str, Dict[str, Any]]): Currently active conversations
    """
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        """
        Initialize the Scrum Master Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            name: Display name for the agent
            memory_manager: Memory management system
        """
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"scrum_master.{agent_id}")
        self.logger.info(f"Initializing ScrumMasterAgent with ID: {agent_id}")
        
        try:
            # Initialize LLM service
            self.llm_service = ScrumMasterLLMService()
            
            # Initialize communication tools
            self.agent_communicator = AgentCommunicator()
            
            # Register self with agent communicator
            self.agent_communicator.register_agent(agent_id)
            
            # Initialize agent registry and user preferences
            self.registered_agents = {}
            self.user_preferences = {}
            self.active_conversations = {}
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("ScrumMasterAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ScrumMasterAgent: {str(e)}", exc_info=True)
            raise
    
    def _build_graph(self):
        """Build the LangGraph-based execution flow for Scrum Master Agent."""
        self.logger.info("Building ScrumMaster processing graph")
        try:
            # Initialize graph builder
            from agents.core.graph.graph_builder import WorkflowGraphBuilder
            builder = WorkflowGraphBuilder(ScrumMasterGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes (primary state handlers)
            self.logger.debug("Adding graph nodes")
            builder.add_node("receive_user_input", self.receive_user_input)
            builder.add_node("analyze_request", self.analyze_request)
            builder.add_node("need_clarification", self.need_clarification)
            builder.add_node("route_to_pm", self.route_to_pm)
            builder.add_node("route_to_team_lead", self.route_to_team_lead)
            builder.add_node("process_feedback", self.process_feedback)
            builder.add_node("prepare_milestone", self.prepare_milestone)
            builder.add_node("awaiting_milestone_approval", self.awaiting_milestone_approval)
            builder.add_node("processing_milestone_decision", self.processing_milestone_decision)
            builder.add_node("handling_technical_question", self.handling_technical_question)
            builder.add_node("generating_status_report", self.generating_status_report)
            builder.add_node("present_to_user", self.present_to_user)
            builder.add_node("error_handling", self.error_handling)
            builder.add_node("completed", self.complete_workflow)
            
            # Add edges (state transitions)
            self.logger.debug("Adding graph edges")
            builder.add_edge("receive_user_input", "analyze_request")
            builder.add_edge("analyze_request", "need_clarification", 
                             condition=self._needs_clarification)
            builder.add_edge("analyze_request", "route_to_pm", 
                             condition=self._should_route_to_pm)
            builder.add_edge("analyze_request", "route_to_team_lead", 
                             condition=self._should_route_to_team_lead)
            builder.add_edge("analyze_request", "process_feedback", 
                             condition=self._is_feedback)
            builder.add_edge("analyze_request", "prepare_milestone", 
                             condition=self._is_milestone_related)
            builder.add_edge("analyze_request", "handling_technical_question", 
                             condition=self._is_technical_question)
            builder.add_edge("analyze_request", "generating_status_report", 
                             condition=self._is_status_inquiry)
            
            # Clarification edges
            builder.add_edge("need_clarification", "present_to_user")
            
            # PM routing edges
            builder.add_edge("route_to_pm", "present_to_user")
            
            # Team Lead routing edges
            builder.add_edge("route_to_team_lead", "present_to_user")
            
            # Feedback processing edges
            builder.add_edge("process_feedback", "route_to_team_lead", 
                             condition=self._should_forward_feedback)
            builder.add_edge("process_feedback", "present_to_user", 
                             condition=lambda s: not self._should_forward_feedback(s))
            
            # Milestone edges
            builder.add_edge("prepare_milestone", "awaiting_milestone_approval")
            builder.add_edge("awaiting_milestone_approval", "processing_milestone_decision")
            builder.add_edge("processing_milestone_decision", "route_to_team_lead")
            
            # Technical question edges
            builder.add_edge("handling_technical_question", "present_to_user")
            
            # Status report edges
            builder.add_edge("generating_status_report", "present_to_user")
            
            # Present to user edges
            builder.add_edge("present_to_user", "completed")
            
            # Error handling edges
            builder.add_edge("error_handling", "present_to_user")
            
            # Set entry point
            builder.set_entry_point("receive_user_input")
            
            # Compile graph
            compiled_graph = builder.compile()
            self.logger.info("Successfully built and compiled graph")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise
    
    def _get_graph_builder(self):
        """Return the graph builder for visualization."""
        if not hasattr(self, '_graph_builder'):
            self._build_graph()  # This will create and store the builder
        return self._graph_builder
    
    # State transition condition methods
    
    def _needs_clarification(self, state: ScrumMasterGraphState) -> bool:
        """Determine if clarification is needed."""
        return state.get("request_type") == RequestType.CLARIFICATION.value or \
               "unknown" in state.get("request_type", "") or \
               state.get("clarification_questions") is not None
    
    def _should_route_to_pm(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request should be routed to Project Manager."""
        return state.get("request_type") in [
            RequestType.NEW_PROJECT.value, 
            RequestType.REQUIREMENT_CHANGE.value
        ]
    
    def _should_route_to_team_lead(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request should be routed to Team Lead."""
        return state.get("request_type") in [
            RequestType.EMERGENCY.value,
            RequestType.STATUS_INQUIRY.value
        ] or state.get("agent_routing", {}).get("target_agent_id") == AgentType.TEAM_LEAD.value
    
    def _is_feedback(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request is feedback."""
        return state.get("request_type") == RequestType.FEEDBACK.value
    
    def _is_milestone_related(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request is milestone related."""
        return state.get("request_type") == RequestType.MILESTONE_APPROVAL.value
    
    def _is_technical_question(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request is a technical question."""
        return state.get("request_type") == RequestType.TECHNICAL_QUESTION.value
    
    def _is_status_inquiry(self, state: ScrumMasterGraphState) -> bool:
        """Determine if request is a status inquiry."""
        return state.get("request_type") == RequestType.STATUS_INQUIRY.value
    
    def _should_forward_feedback(self, state: ScrumMasterGraphState) -> bool:
        """Determine if feedback should be forwarded to another agent."""
        feedback = state.get("user_feedback", {})
        return feedback.get("priority") in [
            Priority.HIGH.value, Priority.CRITICAL.value, Priority.USER_INITIATED.value
        ] or feedback.get("routing_destination") != AgentType.SCRUM_MASTER.value
    
    # State handler methods
    
    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_user_input(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Handle initial user input and setup.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting receive_user_input phase")
        
        try:
            input_data = state["input"]
            user_id = state["user_id"]
            
            self.logger.debug(f"Received input from user {user_id}: {input_data[:100]}...")
            
            # Store initial request in memory
            memory_entry = {
                "initial_request": input_data,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            # Initialize conversation if new
            if user_id not in self.active_conversations:
                self.active_conversations[user_id] = {
                    "conversation_id": f"conv_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "started_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "message_count": 0,
                    "topics": []
                }
            
            # Update conversation record
            self.active_conversations[user_id]["message_count"] += 1
            self.active_conversations[user_id]["last_activity"] = datetime.utcnow().isoformat()
            
            # Retrieve user preferences if available
            user_preferences = await self._get_user_preferences(user_id)
            if user_preferences:
                state["user_preferences"] = user_preferences
            
            # Add the new message to conversation history
            if "conversation_history" not in state:
                state["conversation_history"] = []
                
            state["conversation_history"].append({
                "role": "user",
                "content": input_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Preliminary request type determination
            request_type = determine_request_type(input_data)
            state["request_type"] = request_type
            
            # Update the status
            await self.update_status("analyzing_request")
            
            state["status"] = "analyzing_request"
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_user_input: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "input_processing_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="analyze_request",
                      metadata={"phase": "request_analysis"})
    async def analyze_request(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Analyze the user's request to determine intent and type.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with analysis results
        """
        self.logger.info("Starting analyze_request phase")
        
        try:
            input_data = state["input"]
            user_id = state["user_id"]
            preliminary_request_type = state["request_type"]
            
            # Prepare context for LLM
            llm_context = prepare_state_context_for_llm(state)
            
            # Call LLM to analyze request
            analysis_result = await self.llm_service.analyze_user_request(
                user_input=input_data,
                user_history=state.get("conversation_history", []),
                context=llm_context
            )
            
            # Update state with analysis results
            state["request_type"] = analysis_result.get("request_type", preliminary_request_type)
            
            # Check if clarification is needed
            if analysis_result.get("clarification_needed", False):
                state["clarification_questions"] = analysis_result.get("clarification_questions", [])
                self.logger.info(f"Clarification needed for user request: {state['clarification_questions']}")
            
            # Determine which agent should handle this request
            routing_info = resolve_optimal_agent_routing(state)
            state["agent_routing"] = routing_info
            
            # Store analysis in working memory
            working_memory_entry = {
                "request_analysis": analysis_result,
                "routing_info": routing_info,
                "request_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # If this is a feedback request, process it
            if state["request_type"] == RequestType.FEEDBACK.value:
                user_feedback = await self._process_user_feedback(
                    user_id=user_id,
                    content=input_data,
                    context=llm_context
                )
                state["user_feedback"] = user_feedback
            
            # If this is a technical question, process it
            if state["request_type"] == RequestType.TECHNICAL_QUESTION.value:
                technical_question = {
                    "question": input_data,
                    "context": {
                        "user_technical_level": state.get("user_preferences", {}).get(
                            "technical_level", UserTechnicalLevel.BEGINNER.value
                        )
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                state["technical_question"] = technical_question
            
            # Update status
            state["status"] = get_next_stage(state["status"], state)
            await self.update_status(state["status"])
            
            self.logger.info(f"Request analyzed as {state['request_type']}, routing to {state['agent_routing'].get('target_agent_id')}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_request: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "request_analysis_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="need_clarification",
                      metadata={"phase": "clarification"})
    async def need_clarification(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Generate clarification questions for ambiguous requests.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with clarification questions
        """
        self.logger.info("Starting need_clarification phase")
        
        try:
            user_id = state["user_id"]
            clarification_questions = state.get("clarification_questions", [])
            
            # Prepare context for LLM
            llm_context = prepare_state_context_for_llm(state, "clarification")
            
            # Generate clarification message
            clarification_result = await self.llm_service.generate_clarification_request(
                questions=clarification_questions,
                context=llm_context
            )
            
            # Prepare output for user
            output = {
                "content": clarification_result.get("message_to_user", "Could you please provide more information?"),
                "type": "clarification_request",
                "requires_response": True,
                "questions": clarification_result.get("specific_questions", clarification_questions),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "presenting_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Generated clarification request for user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in need_clarification: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "clarification_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="route_to_pm",
                      metadata={"phase": "pm_routing"})
    async def route_to_pm(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Route request to Project Manager agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with routing information
        """
        self.logger.info("Starting route_to_pm phase")
        
        try:
            user_id = state["user_id"]
            input_data = state["input"]
            request_type = state["request_type"]
            
            # Format message for Project Manager
            message_content = {
                "request_type": request_type,
                "user_input": input_data,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_response": True
            }
            
            # Add project context if available
            if state.get("project_id"):
                message_content["project_id"] = state["project_id"]
            
            # Determine priority
            priority = MessagePriority.HIGH if request_type == RequestType.NEW_PROJECT.value else MessagePriority.MEDIUM
            
            # Send message to Project Manager
            message_id = self.agent_communicator.send_message(
                source_agent_id=self.agent_id,
                target_agent_id="project_manager",
                content=message_content,
                message_type=MessageType.REQUEST,
                priority=priority,
                user_id=user_id
            )
            
            if not message_id:
                raise Exception("Failed to send message to Project Manager")
            
            # Prepare interim response for user
            output = {
                "content": "I'm working on your request and consulting with our Project Manager. I'll get back to you soon.",
                "type": "interim_response",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Store routing info in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "routed_to": "project_manager",
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "presenting_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Routed request to Project Manager, message ID: {message_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in route_to_pm: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "pm_routing_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="route_to_team_lead",
                      metadata={"phase": "team_lead_routing"})
    async def route_to_team_lead(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Route request to Team Lead agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with routing information
        """
        self.logger.info("Starting route_to_team_lead phase")
        
        try:
            user_id = state["user_id"]
            input_data = state["input"]
            request_type = state["request_type"]
            
            # Prepare message content based on request type
            message_content = {
                "request_type": request_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_response": True
            }
            
            message_type = MessageType.REQUEST
            priority = MessagePriority.MEDIUM
            
            # Customize message based on request type
            if request_type == RequestType.FEEDBACK.value and state.get("user_feedback"):
                feedback = state["user_feedback"]
                routing_dest = feedback.get("routing_destination")
                
                # Create technical-friendly version of the feedback
                tech_feedback = translate_feedback_for_technical_team(
                    feedback=feedback,
                    target_agent=routing_dest
                )
                
                message_content["feedback"] = tech_feedback
                message_type = MessageType.USER_FEEDBACK
                
                if feedback.get("priority") in [Priority.HIGH.value, Priority.CRITICAL.value]:
                    priority = MessagePriority.HIGH
                
            elif request_type == RequestType.TECHNICAL_QUESTION.value and state.get("technical_question"):
                message_content["question"] = state["technical_question"]["question"]
                message_content["context"] = state["technical_question"]["context"]
                
            elif request_type == RequestType.MILESTONE_APPROVAL.value and state.get("milestone_actions"):
                message_content["milestone_id"] = state.get("milestone_data", {}).get("id")
                message_content["decision"] = state.get("milestone_actions", {}).get("decision")
                message_content["feedback"] = state.get("milestone_actions", {}).get("feedback")
                message_type = MessageType.USER_DECISION
                priority = MessagePriority.HIGH
                
            elif request_type == RequestType.EMERGENCY.value:
                message_content["emergency_description"] = input_data
                priority = MessagePriority.CRITICAL
            
            # Add project context if available
            if state.get("project_id"):
                message_content["project_id"] = state["project_id"]
            
            # Send message to Team Lead
            message_id = self.agent_communicator.send_message(
                source_agent_id=self.agent_id,
                target_agent_id="team_lead",
                content=message_content,
                message_type=message_type,
                priority=priority,
                user_id=user_id
            )
            
            if not message_id:
                raise Exception("Failed to send message to Team Lead")
            
            # Prepare response for user
            output_content = "I've forwarded your request to our technical team. I'll update you when I have more information."
            
            if request_type == RequestType.FEEDBACK.value:
                output_content = "Thank you for your feedback. I've shared it with our development team."
                
            elif request_type == RequestType.MILESTONE_APPROVAL.value:
                decision = state.get("milestone_actions", {}).get("decision")
                if decision == MilestoneAction.APPROVE.value:
                    output_content = "Thank you for approving this milestone. The team has been notified and will continue with the next steps."
                else:
                    output_content = "I've forwarded your feedback on this milestone to the development team. They'll address your concerns."
            
            output = {
                "content": output_content,
                "type": "confirmation",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Store routing info in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "routed_to": "team_lead",
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "presenting_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Routed request to Team Lead, message ID: {message_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in route_to_team_lead: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "team_lead_routing_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    # Continuing from the existing implementation

    @monitor_operation(operation_type="process_feedback",
                      metadata={"phase": "feedback_processing"})
    async def process_feedback(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Process user feedback.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with processed feedback
        """
        self.logger.info("Starting process_feedback phase")
        
        try:
            user_id = state["user_id"]
            input_data = state["input"]
            
            # If feedback is already processed, use it
            if state.get("user_feedback"):
                self.logger.debug("Using pre-processed feedback")
                feedback = state["user_feedback"]
            else:
                # Process feedback
                self.logger.debug("Processing new feedback")
                feedback = await self._process_user_feedback(
                    user_id=user_id,
                    content=input_data,
                    context=prepare_state_context_for_llm(state)
                )
                state["user_feedback"] = feedback
            
            # Submit feedback through agent communicator
            feedback_id = self.agent_communicator.submit_user_feedback(
                user_id=user_id,
                content=input_data,
                feedback_type=feedback.get("category", UserFeedbackType.GENERAL.value),
                project_id=state.get("project_id"),
                requires_response=feedback.get("requires_response", False),
                metadata=feedback
            )
            
            if feedback_id:
                self.logger.info(f"Submitted feedback with ID: {feedback_id}")
                state["user_feedback"]["feedback_id"] = feedback_id
            
            # Prepare response for user
            routing_destination = feedback.get("routing_destination", "team_lead")
            
            output_content = "Thank you for your feedback. "
            if feedback.get("priority") in [Priority.HIGH.value, Priority.CRITICAL.value]:
                output_content += "I've prioritized this and forwarded it to our team for immediate attention."
            else:
                output_content += "I've shared it with our team for consideration."
                
            if feedback.get("requires_response", False):
                output_content += " I'll get back to you once we've reviewed it."
            
            output = {
                "content": output_content,
                "type": "feedback_confirmation",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Determine next state based on feedback priority and routing
            if self._should_forward_feedback(state):
                state["status"] = "route_to_team_lead"
            else:
                state["status"] = "present_to_user"
            
            await self.update_status(state["status"])
            
            self.logger.info(f"Processed feedback with priority {feedback.get('priority')}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in process_feedback: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "feedback_processing_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="prepare_milestone",
                      metadata={"phase": "milestone_preparation"})
    async def prepare_milestone(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Prepare milestone data for user presentation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with milestone data
        """
        self.logger.info("Starting prepare_milestone phase")
        
        try:
            user_id = state["user_id"]
            project_id = state.get("project_id")
            
            # If milestone data is provided via agent communication, use it
            if state.get("milestone_data"):
                milestone_data = state["milestone_data"]
            else:
                # Request milestone data from Team Lead
                message_content = {
                    "request_type": "milestone_data",
                    "user_id": user_id,
                    "project_id": project_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "requires_response": True
                }
                
                # Send request to Team Lead
                message_id = self.agent_communicator.send_message(
                    source_agent_id=self.agent_id,
                    target_agent_id="team_lead",
                    content=message_content,
                    message_type=MessageType.REQUEST,
                    priority=MessagePriority.HIGH,
                    user_id=user_id
                )
                
                if not message_id:
                    raise Exception("Failed to request milestone data from Team Lead")
                
                # For now, create placeholder milestone data (normally would wait for response)
                milestone_data = {
                    "id": f"milestone_{uuid.uuid4().hex[:8]}",
                    "name": "Project Milestone",
                    "description": "Important project milestone requiring approval",
                    "completion_percentage": 100,
                    "components": ["component1", "component2"],
                    "requires_approval": True,
                    "technical_details": {
                        "completed_tasks": 10,
                        "total_tasks": 10,
                        "test_coverage": "95%"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                state["milestone_data"] = milestone_data
            
            # Prepare user-friendly milestone presentation
            llm_context = prepare_state_context_for_llm(state, "milestone")
            
            # Generate milestone presentation
            presentation = await self.llm_service.generate_milestone_presentation(
                milestone_data=milestone_data,
                user_preferences=state.get("user_preferences"),
                context=llm_context
            )
            
            # Create checkpoint for approval tracking
            checkpoint = create_checkpoint(
                checkpoint_type="milestone",
                title=milestone_data.get("name", "Project Milestone"),
                description=milestone_data.get("description", ""),
                project_id=project_id,
                milestone_id=milestone_data.get("id"),
                requires_approval=True
            )
            
            # Store checkpoint in state
            milestone_data["checkpoint"] = checkpoint
            state["milestone_data"] = milestone_data
            
            # Store checkpoint in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "checkpoint": checkpoint,
                    "milestone_data": milestone_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Prepare output for user
            output = {
                "content": presentation.get("title", "Milestone Review") + "\n\n" + 
                          presentation.get("summary", "Please review this milestone."),
                "type": "milestone_presentation",
                "milestone": presentation,
                "requires_approval": True,
                "options": [
                    {"id": "approve", "label": "Approve", "description": "Approve this milestone"},
                    {"id": "approve_with_changes", "label": "Approve with Changes", "description": "Approve with requested changes"},
                    {"id": "request_changes", "label": "Request Changes", "description": "Request changes before approval"},
                    {"id": "reject", "label": "Reject", "description": "Reject this milestone"}
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "awaiting_milestone_approval"
            await self.update_status(state["status"])
            
            self.logger.info(f"Prepared milestone presentation for user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in prepare_milestone: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "milestone_preparation_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="awaiting_milestone_approval",
                      metadata={"phase": "milestone_approval"})
    async def awaiting_milestone_approval(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Wait for user approval on milestone.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with user decision
        """
        self.logger.info("Starting awaiting_milestone_approval phase")
        
        try:
            # This state is a placeholder while waiting for user decision
            # The actual decision is processed when user responds
            
            # For simulation, create a milestone decision based on user input
            user_input = state.get("input", "").lower()
            
            decision = MilestoneAction.APPROVE
            feedback = None
            
            if "approve" in user_input:
                if "changes" in user_input or "modify" in user_input:
                    decision = MilestoneAction.APPROVE_WITH_FEEDBACK
                    feedback = "Approved with some suggested changes: " + state.get("input", "")
                else:
                    decision = MilestoneAction.APPROVE
                    feedback = "Approved: " + state.get("input", "")
            elif "reject" in user_input:
                decision = MilestoneAction.REJECT
                feedback = "Rejected: " + state.get("input", "")
            elif "change" in user_input or "modify" in user_input:
                decision = MilestoneAction.REQUEST_CHANGES
                feedback = "Changes requested: " + state.get("input", "")
            elif "more info" in user_input or "additional" in user_input:
                decision = MilestoneAction.REQUEST_MORE_INFO
                feedback = "More information requested: " + state.get("input", "")
            
            # Update milestone actions
            state["milestone_actions"] = {
                "decision": decision.value,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update checkpoint status
            if state.get("milestone_data") and state["milestone_data"].get("checkpoint"):
                checkpoint = state["milestone_data"]["checkpoint"]
                
                if decision in [MilestoneAction.APPROVE, MilestoneAction.APPROVE_WITH_FEEDBACK]:
                    # Process approval
                    updated_checkpoint = process_user_approval(
                        checkpoint=checkpoint,
                        user_id=state["user_id"],
                        approval_notes=feedback
                    )
                else:
                    # Process rejection or change request
                    updated_checkpoint = process_user_rejection(
                        checkpoint=checkpoint,
                        user_id=state["user_id"],
                        rejection_reason=feedback,
                        requires_revision=(decision == MilestoneAction.REQUEST_CHANGES)
                    )
                
                # Update milestone data
                state["milestone_data"]["checkpoint"] = updated_checkpoint
            
            # Update status
            state["status"] = "processing_milestone_decision"
            await self.update_status(state["status"])
            
            self.logger.info(f"Received milestone decision: {decision.value}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in awaiting_milestone_approval: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "milestone_approval_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="processing_milestone_decision",
                      metadata={"phase": "milestone_decision"})
    async def processing_milestone_decision(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Process user decision on milestone.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with processed decision
        """
        self.logger.info("Starting processing_milestone_decision phase")
        
        try:
            user_id = state["user_id"]
            milestone_data = state.get("milestone_data", {})
            milestone_actions = state.get("milestone_actions", {})
            
            decision = milestone_actions.get("decision")
            feedback = milestone_actions.get("feedback")
            
            # Create notification for Team Lead
            if milestone_data.get("checkpoint"):
                notification_type = "approval" if decision in [
                    MilestoneAction.APPROVE.value, 
                    MilestoneAction.APPROVE_WITH_FEEDBACK.value
                ] else "rejection"
                
                notification = notify_team_lead(
                    checkpoint=milestone_data["checkpoint"],
                    notification_type=notification_type,
                    agent_id=self.agent_id
                )
                
                # Store notification in memory
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "notification": notification,
                        "milestone_decision": milestone_actions,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Update status - route decision to Team Lead
            state["status"] = "route_to_team_lead"
            await self.update_status(state["status"])
            
            self.logger.info(f"Processed milestone decision: {decision}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in processing_milestone_decision: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "milestone_decision_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="handling_technical_question",
                      metadata={"phase": "technical_question"})
    async def handling_technical_question(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Handle technical questions from users.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with technical answer
        """
        self.logger.info("Starting handling_technical_question phase")
        
        try:
            user_id = state["user_id"]
            question_data = state.get("technical_question", {})
            question = question_data.get("question", state.get("input", ""))
            
            # Get user technical level from preferences
            user_technical_level = state.get("user_preferences", {}).get(
                "technical_level", UserTechnicalLevel.BEGINNER.value
            )
            
            # Prepare context for LLM
            llm_context = prepare_state_context_for_llm(state, "technical_question")
            
            # For complex technical questions, consider routing to Team Lead
            if self._is_complex_technical_question(question):
                # Route to Team Lead for complex questions
                state["status"] = "route_to_team_lead"
                await self.update_status(state["status"])
                return state
            
            # Generate technical answer
            answer_result = await self.llm_service.answer_technical_question(
                question=question,
                user_technical_level=user_technical_level,
                context=llm_context
            )
            
            # Prepare output for user
            output = {
                "content": answer_result.get("answer", "I'll need to consult with our technical team on this question."),
                "type": "technical_answer",
                "key_points": answer_result.get("key_points", []),
                "technical_level": answer_result.get("technical_level_used", user_technical_level),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "present_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Handled technical question for user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in handling_technical_question: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "technical_question_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    def _is_complex_technical_question(self, question: str) -> bool:
        """Determine if a question is complex enough to route to technical team."""
        # Simple heuristic based on question complexity
        complex_terms = [
            "architecture", "implementation details", "low-level", "internal working",
            "algorithms", "optimization", "code structure", "backend", "database schema",
            "deployment", "infrastructure", "scaling", "performance tuning"
        ]
        
        return any(term in question.lower() for term in complex_terms)
    
    @monitor_operation(operation_type="generating_status_report",
                      metadata={"phase": "status_report"})
    async def generating_status_report(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Generate project status report for user.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with status report
        """
        self.logger.info("Starting generating_status_report phase")
        
        try:
            user_id = state["user_id"]
            project_id = state.get("project_id")
            
            # Request status data from Team Lead
            message_content = {
                "request_type": "status_report",
                "user_id": user_id,
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_response": True
            }
            
            # Send request to Team Lead
            message_id = self.agent_communicator.send_message(
                source_agent_id=self.agent_id,
                target_agent_id="team_lead",
                content=message_content,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.MEDIUM,
                user_id=user_id
            )
            
            if not message_id:
                raise Exception("Failed to request status report from Team Lead")
            
            # For now, create placeholder status data (normally would wait for response)
            status_data = {
                "project_name": "Project",
                "overall_progress": 75,
                "current_phase": "Implementation",
                "milestones": [
                    {"name": "Planning", "status": "completed", "progress": 100},
                    {"name": "Design", "status": "completed", "progress": 100},
                    {"name": "Implementation", "status": "in_progress", "progress": 65},
                    {"name": "Testing", "status": "pending", "progress": 0}
                ],
                "recent_activities": [
                    "Completed user authentication implementation",
                    "Started work on dashboard components",
                    "Resolved database connection issues"
                ],
                "issues": [
                    {"description": "Performance optimization needed", "priority": "medium"}
                ]
            }
            
            # Generate user-friendly status report
            llm_context = prepare_state_context_for_llm(state, "status_report")
            
            # Get report type preference
            report_type = state.get("user_preferences", {}).get("report_type", "standard")
            
            # Generate report
            report_result = await self.llm_service.generate_status_report(
                project_status=status_data,
                report_type=report_type,
                context=llm_context
            )
            
            # Prepare output for user
            output = {
                "content": report_result.get("report_title", "Project Status Report") + "\n\n" + 
                          report_result.get("summary", "Here's the current status of your project."),
                "type": "status_report",
                "report": report_result,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["status_report"] = status_data
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update status
            state["status"] = "present_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Generated status report for user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generating_status_report: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "status_report_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="present_to_user",
                      metadata={"phase": "user_presentation"})
    async def present_to_user(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Present information to the user.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state after presentation
        """
        self.logger.info("Starting present_to_user phase")
        
        try:
            user_id = state["user_id"]
            
            # If output is already prepared, use it
            if state.get("output"):
                output = state["output"]
            else:
                # Generate a default response if no specific output is prepared
                output = {
                    "content": "I've processed your request. Is there anything else you'd like to know?",
                    "type": "default_response",
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                state["output"] = output
            
            # Add to conversation history if not already added
            conversation_history = state.get("conversation_history", [])
            
            # Check if this output is already in the history
            output_in_history = any(
                entry.get("role") == "assistant" and entry.get("content") == output["content"]
                for entry in conversation_history[-3:]  # Check recent entries
            )
            
            if not output_in_history:
                state.setdefault("conversation_history", []).append({
                    "role": "assistant",
                    "content": output["content"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update user activity timestamp
            if user_id in self.active_conversations:
                self.active_conversations[user_id]["last_activity"] = datetime.utcnow().isoformat()
            
            # Store conversation in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "conversation_history": state.get("conversation_history", []),
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Update status
            state["status"] = "completed"
            await self.update_status(state["status"])
            
            self.logger.info(f"Presented information to user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in present_to_user: {str(e)}", exc_info=True)
            state["error_info"] = {
                "error_message": str(e),
                "error_type": "presentation_error",
                "timestamp": datetime.utcnow().isoformat()
            }
            state["status"] = "error_handling"
            return state
    
    @monitor_operation(operation_type="error_handling",
                      metadata={"phase": "error_handling"})
    async def error_handling(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Handle errors during processing.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state after error handling
        """
        self.logger.info("Starting error_handling phase")
        
        try:
            error_info = state.get("error_info", {})
            error_message = error_info.get("error_message", "An unknown error occurred")
            error_type = error_info.get("error_type", "unknown_error")
            
            self.logger.error(f"Handling error: {error_type} - {error_message}")
            
            # Create user-friendly error message
            user_message = "I apologize, but I encountered an issue while processing your request."
            
            if "clarification" in error_type:
                user_message = "I need more information to understand your request. Could you please provide more details?"
            elif "routing" in error_type:
                user_message = "I'm having trouble connecting with the right team member to handle your request. Let's try again."
            elif "feedback" in error_type:
                user_message = "There was an issue processing your feedback. Could you please rephrase it?"
            elif "milestone" in error_type:
                user_message = "I encountered a problem with the milestone information. Let me try to resolve this."
            elif "technical" in error_type:
                user_message = "I'm having difficulty answering your technical question. Let me consult with our technical team."
            
            # Prepare output for user
            output = {
                "content": user_message,
                "type": "error_message",
                "error_type": error_type,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            state["output"] = output
            
            # Add to conversation history
            state.setdefault("conversation_history", []).append({
                "role": "assistant",
                "content": output["content"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Store error in memory for diagnostics
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "error_info": error_info,
                    "user_id": state.get("user_id", "unknown"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={"error": True}
            )
            
            # Update status
            state["status"] = "present_to_user"
            await self.update_status(state["status"])
            
            self.logger.info(f"Handled error: {error_type}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in error_handling (meta-error): {str(e)}", exc_info=True)
            # Create a basic error response
            state["output"] = {
                "content": "I apologize, but I encountered an unexpected issue. Please try again later.",
                "type": "error_message",
                "generated_at": datetime.utcnow().isoformat()
            }
            state["status"] = "present_to_user"
            return state
    
    @monitor_operation(operation_type="complete_workflow",
                      metadata={"phase": "completion"})
    async def complete_workflow(self, state: ScrumMasterGraphState) -> Dict[str, Any]:
        """
        Complete the workflow and perform cleanup.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Final state
        """
        self.logger.info("Starting complete_workflow phase")
        
        try:
            user_id = state.get("user_id", "unknown")
            
            # Add completion timestamp
            state["completion_timestamp"] = datetime.utcnow().isoformat()
            
            # Store final state in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "completed_state": {
                        "request_type": state.get("request_type"),
                        "output": state.get("output"),
                        "timestamp": state["completion_timestamp"]
                    },
                    "user_id": user_id
                },
                metadata={"completed": True}
            )
            
            self.logger.info(f"Workflow completed for user {user_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in complete_workflow: {str(e)}", exc_info=True)
            return state
    
    # Helper methods
    
    async def _process_user_feedback(
        self,
        user_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process user feedback using feedback processor tool."""
        self.logger.debug(f"Processing feedback from user {user_id}")
        
        try:
            # Get project context if available
            project_id = context.get("project_id") if context else None
            
            # Get user context
            user_context = {
                "technical_level": context.get("user_preferences", {}).get("technical_level", "beginner")
            } if context else None
            
            # Process feedback using feedback processor
            feedback_result = process_feedback(
                user_id=user_id,
                content=content,
                project_id=project_id,
                user_context=user_context
            )
            
            # Convert feedback to dictionary
            feedback_dict = feedback_result.to_dict() if hasattr(feedback_result, 'to_dict') else feedback_result
            
            return feedback_dict
            
        except Exception as e:
            self.logger.error(f"Error processing user feedback: {str(e)}", exc_info=True)

    async def _get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences from memory or communicator.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[Dict[str, Any]]: User preferences if found, None otherwise
        """
        self.logger.debug(f"Retrieving preferences for user {user_id}")
        
        try:
            # Check if we have preferences in instance variable
            if user_id in self.user_preferences:
                return self.user_preferences[user_id]
            
            # Check if agent communicator has preferences
            comms_preferences = self.agent_communicator.get_user_preferences(user_id)
            if comms_preferences:
                self.user_preferences[user_id] = comms_preferences
                return comms_preferences
            
            # Check if preferences are in memory
            memory_results = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"user_id": user_id, "type": "preferences"}
            )
            
            if memory_results and len(memory_results) > 0:
                preferences = memory_results[0].content
                # Cache for future use
                self.user_preferences[user_id] = preferences
                return preferences
            
            # If no preferences found, create default
            default_preferences = {
                "technical_level": UserTechnicalLevel.BEGINNER.value,
                "detail_level": "medium",
                "communication_style": "friendly",
                "explanation_detail": "medium",
                "use_analogies": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store default preferences
            self.user_preferences[user_id] = default_preferences
            
            # Store in memory for future sessions
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=default_preferences,
                metadata={"user_id": user_id, "type": "preferences"}
            )
            
            return default_preferences
            
        except Exception as e:
            self.logger.error(f"Error retrieving user preferences: {str(e)}", exc_info=True)
            # Return minimal default preferences
            return {
                "technical_level": UserTechnicalLevel.BEGINNER.value,
                "detail_level": "medium",
                "communication_style": "friendly"
            }
    
    @trace_method
    async def update_user_preferences(
        self, 
        user_id: str, 
        preference_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user preferences and store them.
        
        Args:
            user_id: ID of the user
            preference_updates: Dictionary of preference updates
            
        Returns:
            Dict[str, Any]: Updated preferences
        """
        self.logger.info(f"Updating preferences for user {user_id}")
        
        try:
            # Get current preferences
            current_preferences = await self._get_user_preferences(user_id) or {}
            
            # Update preferences
            updated_preferences = {**current_preferences, **preference_updates}
            updated_preferences["updated_at"] = datetime.utcnow().isoformat()
            
            # Store in instance variable
            self.user_preferences[user_id] = updated_preferences
            
            # Store in communicator
            for key, value in preference_updates.items():
                self.agent_communicator.store_user_preference(
                    user_id=user_id,
                    preference_type=key,
                    preference_value=value
                )
            
            # Store in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=updated_preferences,
                metadata={"user_id": user_id, "type": "preferences"}
            )
            
            self.logger.info(f"Updated preferences for user {user_id}")
            return updated_preferences
            
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {str(e)}", exc_info=True)
            return await self._get_user_preferences(user_id) or {}
    
    @trace_method
    async def detect_preferences_from_input(
        self, 
        user_id: str, 
        input_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze user input to detect preference clues.
        
        Args:
            user_id: ID of the user
            input_text: User input text
            
        Returns:
            Optional[Dict[str, Any]]: Detected preferences if any
        """
        self.logger.debug(f"Detecting preferences from input for user {user_id}")
        
        try:
            preference_updates = {}
            input_lower = input_text.lower()
            
            # Look for technical level clues
            if any(term in input_lower for term in ["expert", "advanced", "developer", "technical", "professional", "engineer"]):
                if "beginner" not in input_lower and "simple" not in input_lower:
                    preference_updates["technical_level"] = UserTechnicalLevel.ADVANCED.value
            elif any(term in input_lower for term in ["beginner", "simple", "explain", "easy", "don't understand", "confused"]):
                preference_updates["technical_level"] = UserTechnicalLevel.BEGINNER.value
            
            # Look for detail preference clues
            if any(term in input_lower for term in ["detail", "comprehensive", "thorough", "in-depth"]):
                preference_updates["detail_level"] = "detailed"
            elif any(term in input_lower for term in ["brief", "short", "quick", "summary", "overview"]):
                preference_updates["detail_level"] = "brief"
            
            # Look for communication style clues
            if any(term in input_lower for term in ["formal", "professional", "business"]):
                preference_updates["communication_style"] = "formal"
            elif any(term in input_lower for term in ["friendly", "casual", "conversational"]):
                preference_updates["communication_style"] = "friendly"
            
            # Look for explanation preference clues
            if "analogy" in input_lower or "like" in input_lower:
                preference_updates["use_analogies"] = True
            
            # Only update if we detected something
            if preference_updates:
                self.logger.info(f"Detected preferences from input: {preference_updates}")
                return await self.update_user_preferences(user_id, preference_updates)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting preferences: {str(e)}", exc_info=True)
            return None
    
    @trace_method
    async def handle_incoming_message(
        self,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle incoming messages from other agents.
        
        Args:
            message: Message to handle
            
        Returns:
            Optional[Dict[str, Any]]: Response if applicable
        """
        self.logger.info(f"Handling incoming message of type {message.get('message_type', 'unknown')}")
        
        try:
            message_type = message.get("message_type")
            content = message.get("content", {})
            source_agent_id = message.get("source_agent_id")
            
            # Handle milestone presentations
            if message_type == MessageType.MILESTONE_PRESENTATION.value:
                return await self._handle_milestone_presentation(content, source_agent_id)
            
            # Handle response to user question
            elif message_type == MessageType.RESPONSE.value:
                return await self._handle_agent_response(content, source_agent_id)
            
            # Handle approval requests
            elif message_type == MessageType.APPROVAL_REQUEST.value:
                return await self._handle_approval_request(content, source_agent_id)
            
            # Handle notifications
            elif message_type == MessageType.NOTIFICATION.value:
                return await self._handle_notification(content, source_agent_id)
            
            # Handle deliverables
            elif message_type == MessageType.DELIVERABLE.value:
                return await self._handle_deliverable(content, source_agent_id)
            
            # Log unhandled message type
            self.logger.warning(f"Unhandled message type: {message_type}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling incoming message: {str(e)}", exc_info=True)
            return None
    
    async def _handle_milestone_presentation(
        self,
        content: Dict[str, Any],
        source_agent_id: str
    ) -> Dict[str, Any]:
        """Handle milestone presentation from another agent."""
        self.logger.info(f"Handling milestone presentation from {source_agent_id}")
        
        try:
            deliverable_id = content.get("deliverable_id")
            
            # Get the deliverable
            if not deliverable_id or deliverable_id not in self.agent_communicator.deliverables:
                raise ValueError(f"Deliverable {deliverable_id} not found")
                
            deliverable = self.agent_communicator.deliverables[deliverable_id]
            
            # Extract milestone data
            milestone_data = deliverable.content
            
            # Create initial state for handling milestone
            user_id = content.get("user_id", "unknown")
            
            initial_state = create_initial_state(
                user_input=f"Please review milestone {milestone_data.get('name', 'Unknown')}",
                user_id=user_id
            )
            
            # Set milestone data and request type
            initial_state["milestone_data"] = milestone_data
            initial_state["request_type"] = RequestType.MILESTONE_APPROVAL.value
            
            # Run the workflow
            result = await self.run(initial_state)
            
            self.logger.info(f"Handled milestone presentation, returning result")
            return result
            
        except Exception as e:
            self.logger.error(f"Error handling milestone presentation: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "message": "Failed to process milestone presentation"
            }
    
    async def _handle_agent_response(
        self,
        content: Dict[str, Any],
        source_agent_id: str
    ) -> Dict[str, Any]:
        """Handle response from another agent."""
        self.logger.info(f"Handling response from {source_agent_id}")
        
        try:
            # Extract response data
            response_content = content.get("response", content)
            user_id = content.get("user_id", "unknown")
            
            # Check if this is for a specific user
            if not user_id or user_id == "unknown":
                self.logger.warning(f"Response without user ID from {source_agent_id}")
                return {"status": "error", "message": "No user ID provided"}
            
            # Create user-friendly version of the response
            user_preferences = await self._get_user_preferences(user_id)
            
            # Translate technical content if needed
            if source_agent_id not in ["scrum_master", "project_manager"]:
                # This is likely technical content that needs translation
                translation_result = await self.llm_service.translate_technical_content(
                    technical_content=response_content,
                    user_technical_level=user_preferences.get("technical_level", UserTechnicalLevel.BEGINNER.value),
                    user_preferences=user_preferences
                )
                
                user_friendly_response = translation_result.get("translated_content", str(response_content))
            else:
                # Already user-friendly
                user_friendly_response = str(response_content)
            
            # Create response state
            response_state = {
                "output": {
                    "content": user_friendly_response,
                    "type": "response",
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_agent": source_agent_id
                },
                "user_id": user_id,
                "status": "completed"
            }
            
            # Update conversation history for this user
            if user_id in self.active_conversations:
                conversation = self.active_conversations[user_id]
                
                # Add response to history if available
                if "conversation_history" in conversation:
                    conversation["conversation_history"].append({
                        "role": "assistant",
                        "content": user_friendly_response,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            self.logger.info(f"Processed response for user {user_id}")
            return response_state
            
        except Exception as e:
            self.logger.error(f"Error handling agent response: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "message": "Failed to process agent response"
            }
    
    async def _handle_approval_request(
        self,
        content: Dict[str, Any],
        source_agent_id: str
    ) -> Dict[str, Any]:
        """Handle approval request from another agent."""
        self.logger.info(f"Handling approval request from {source_agent_id}")
        
        try:
            # Extract approval request data
            approval_request_id = content.get("approval_request_id")
            title = content.get("title", "Approval Request")
            description = content.get("description", "Please review and approve")
            request_content = content.get("content", {})
            user_id = content.get("user_id", "unknown")
            
            # Create initial state for handling approval
            initial_state = create_initial_state(
                user_input=f"Please review and approve: {title}",
                user_id=user_id
            )
            
            # Set approval data
            initial_state["approval_request"] = {
                "id": approval_request_id,
                "title": title,
                "description": description,
                "content": request_content,
                "source_agent_id": source_agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            initial_state["request_type"] = RequestType.MILESTONE_APPROVAL.value
            
            # Run the workflow
            result = await self.run(initial_state)
            
            self.logger.info(f"Handled approval request, returning result")
            return result
            
        except Exception as e:
            self.logger.error(f"Error handling approval request: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "message": "Failed to process approval request"
            }
    
    async def _handle_notification(
        self,
        content: Dict[str, Any],
        source_agent_id: str
    ) -> Dict[str, Any]:
        """Handle notification from another agent."""
        self.logger.info(f"Handling notification from {source_agent_id}")
        
        try:
            # Extract notification data
            notification_type = content.get("notification_type", "general")
            notification_content = content.get("content", content)
            user_id = content.get("user_id")
            
            # Store notification in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "notification": notification_content,
                    "source_agent_id": source_agent_id,
                    "notification_type": notification_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Only forward to user if user_id is specified
            if user_id:
                # Create user-friendly notification
                notification_text = str(notification_content)
                
                if isinstance(notification_content, dict):
                    if "message" in notification_content:
                        notification_text = notification_content["message"]
                    elif "content" in notification_content:
                        notification_text = notification_content["content"]
                
                # Create response state
                response_state = {
                    "output": {
                        "content": f"Update: {notification_text}",
                        "type": "notification",
                        "generated_at": datetime.utcnow().isoformat(),
                        "source_agent": source_agent_id
                    },
                    "user_id": user_id,
                    "status": "completed"
                }
                
                self.logger.info(f"Forwarding notification to user {user_id}")
                return response_state
            
            self.logger.info(f"Processed notification (not forwarded to user)")
            return {"status": "success", "message": "Notification processed"}
            
        except Exception as e:
            self.logger.error(f"Error handling notification: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "message": "Failed to process notification"
            }
    
    async def _handle_deliverable(
        self,
        content: Dict[str, Any],
        source_agent_id: str
    ) -> Dict[str, Any]:
        """Handle deliverable from another agent."""
        self.logger.info(f"Handling deliverable from {source_agent_id}")
        
        try:
            # Extract deliverable data
            deliverable_id = content.get("deliverable_id")
            
            # Get the deliverable
            if not deliverable_id or deliverable_id not in self.agent_communicator.deliverables:
                raise ValueError(f"Deliverable {deliverable_id} not found")
                
            deliverable = self.agent_communicator.deliverables[deliverable_id]
            
            # Check if this is for user presentation
            if deliverable.for_user_presentation:
                # This should be presented to the user
                user_id = content.get("user_id", "unknown")
                
                if user_id == "unknown":
                    self.logger.warning(f"User-targeted deliverable without user ID from {source_agent_id}")
                    return {"status": "error", "message": "No user ID provided for user-targeted deliverable"}
                
                # Create user-friendly version
                user_preferences = await self._get_user_preferences(user_id)
                
                # Format for user based on deliverable type
                deliverable_type = deliverable.deliverable_type
                deliverable_content = deliverable.content
                
                # Prepare output based on type
                if deliverable_type == DeliverableType.USER_PRESENTATION.value:
                    # Already formatted for user
                    output_content = deliverable_content
                    if isinstance(output_content, dict) and "content" in output_content:
                        output_content = output_content["content"]
                else:
                    # Need to format for user
                    output_content = f"I've received a {deliverable_type} from our team. Here's what they've prepared:"
                    
                    if isinstance(deliverable_content, dict):
                        if "title" in deliverable_content:
                            output_content = f"{deliverable_content.get('title', '')}\n\n"
                        if "content" in deliverable_content:
                            output_content += str(deliverable_content["content"])
                        elif "description" in deliverable_content:
                            output_content += str(deliverable_content["description"])
                        else:
                            # Just convert the whole thing to string
                            output_content += str(deliverable_content)
                    else:
                        output_content += str(deliverable_content)
                
                # Create response state
                response_state = {
                    "output": {
                        "content": output_content,
                        "type": "deliverable",
                        "generated_at": datetime.utcnow().isoformat(),
                        "source_agent": source_agent_id,
                        "deliverable_type": deliverable_type
                    },
                    "user_id": user_id,
                    "status": "completed"
                }
                
                self.logger.info(f"Forwarding deliverable to user {user_id}")
                return response_state
            
            # Otherwise just acknowledge receipt
            self.logger.info(f"Processed deliverable (not for user presentation)")
            return {"status": "success", "message": "Deliverable processed"}
            
        except Exception as e:
            self.logger.error(f"Error handling deliverable: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "message": "Failed to process deliverable"
            }
    
    @trace_method
    async def check_for_agent_messages(self) -> List[Dict[str, Any]]:
        """
        Check for incoming messages from other agents.
        
        Returns:
            List[Dict[str, Any]]: List of processed messages
        """
        self.logger.debug("Checking for agent messages")
        
        try:
            # Get messages for this agent
            messages = self.agent_communicator.get_messages(self.agent_id)
            
            if not messages:
                return []
                
            self.logger.info(f"Found {len(messages)} messages to process")
            
            # Process each message
            processed_results = []
            
            for message in messages:
                # Acknowledge message
                self.agent_communicator.acknowledge_message(self.agent_id, message["id"])
                
                # Process message
                result = await self.handle_incoming_message(message)
                
                if result:
                    processed_results.append(result)
                    
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error checking for agent messages: {str(e)}", exc_info=True)
            return []
    
    @monitor_operation(operation_type="run",
                      metadata={"phase": "execution"})
    async def run(self, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the Scrum Master Agent's workflow.
        
        Args:
            input_data: Input string or dictionary containing initial state
            
        Returns:
            Dict[str, Any]: Final results of the scrum master process
        """
        self.logger.info("Starting ScrumMaster workflow execution")
        
        try:
            # Check for messages from other agents first
            agent_messages = await self.check_for_agent_messages()
            
            # Handle string input - create initial state
            if isinstance(input_data, str):
                # Create initial state with user input
                user_id = "user"  # Use default user ID if not specified
                
                initial_state = create_initial_state(input_data, user_id)
                
                # Check for preference clues in input
                await self.detect_preferences_from_input(user_id, input_data)
                
            # Handle dictionary input - use as initial state
            elif isinstance(input_data, dict):
                # If input_data is already a state dictionary, use it
                if "input" in input_data and "user_id" in input_data:
                    initial_state = input_data
                else:
                    # Try to create a state from this dictionary
                    user_id = input_data.get("user_id", "user")
                    user_input = input_data.get("input", input_data.get("content", "Hello"))
                    
                    initial_state = create_initial_state(user_input, user_id)
                    
                    # Add any additional data from input_data
                    for key, value in input_data.items():
                        if key not in initial_state and key not in ["input", "user_id"]:
                            initial_state[key] = value
            else:
                raise ValueError(f"Unsupported input type: {type(input_data)}")
            
            # Validate initial state
            validate_state(initial_state)
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke(initial_state)
            
            # If we processed any agent messages, include in response
            if agent_messages:
                # Only include user-targeted messages
                user_messages = [msg for msg in agent_messages if msg.get("user_id") == result.get("user_id")]
                
                if user_messages:
                    # Add latest agent message to the result
                    latest_message = user_messages[-1]
                    
                    # Only override output if we don't already have one
                    if "output" not in result or not result["output"]:
                        result["output"] = latest_message.get("output")
            
            self.logger.info("Workflow completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            
            # Create error response
            error_response = {
                "status": "error",
                "error": str(e),
                "output": {
                    "content": "I apologize, but I encountered an error while processing your request. Please try again.",
                    "type": "error",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Add user_id if available
            if isinstance(input_data, dict) and "user_id" in input_data:
                error_response["user_id"] = input_data["user_id"]
                
            return error_response
    
    @trace_method
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's work.
        
        Returns:
            Dict[str, Any]: Report data
        """
        self.logger.info("Generating ScrumMaster report")
        
        try:
            # Get active conversations
            conversations = len(self.active_conversations)
            
            # Count messages by type
            message_counts = {}
            for user_id, conversation in self.active_conversations.items():
                history = conversation.get("conversation_history", [])
                message_counts[user_id] = len(history)
            
            # Get recent memory entries
            recent_memories = await self.memory_manager.retrieve_recent(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                limit=10
            )
            
            # Calculate overall statistics
            total_messages = sum(message_counts.values())
            active_users = len(self.active_conversations)
            
            # Build report
            report = {
                "agent_id": self.agent_id,
                "agent_type": "scrum_master",
                "active_conversations": conversations,
                "active_users": active_users,
                "total_messages": total_messages,
                "message_counts_by_user": message_counts,
                "registered_agents": list(self.registered_agents.keys()),
                "recent_activities": [
                    {
                        "timestamp": memory.timestamp,
                        "type": memory.metadata.get("type", "interaction"),
                        "user_id": memory.content.get("user_id", "unknown") if isinstance(memory.content, dict) else "unknown"
                    }
                    for memory in recent_memories
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            self.logger.info("Report generation completed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return {
                "agent_id": self.agent_id,
                "agent_type": "scrum_master",
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }