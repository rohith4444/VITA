from typing import TypedDict, Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime
from enum import Enum, auto
from core.logging.logger import setup_logger
from core.tracing.service import trace_class, trace_method

# Initialize logger
logger = setup_logger("scrum_master.state_graph")

class RequestType(Enum):
    """Enum representing the types of user requests the Scrum Master can handle."""
    NEW_PROJECT = "new_project"                  # User wants to create a new project
    FEEDBACK = "feedback"                        # User is providing feedback
    TECHNICAL_QUESTION = "technical_question"    # User has a technical question
    STATUS_INQUIRY = "status_inquiry"            # User wants a progress update
    CLARIFICATION = "clarification"              # User wants clarification
    MILESTONE_APPROVAL = "milestone_approval"    # User is reviewing a milestone
    REQUIREMENT_CHANGE = "requirement_change"    # User wants to change requirements
    GENERAL_INQUIRY = "general_inquiry"          # General questions about the project
    EMERGENCY = "emergency"                      # Critical/urgent issue
    OTHER = "other"                              # Fallback for unclassified requests

class FeedbackType(Enum):
    """Enum representing the types of feedback a user can provide."""
    BUG_REPORT = "bug_report"                    # Reporting a bug or issue
    FEATURE_REQUEST = "feature_request"          # Requesting a new feature
    IMPROVEMENT = "improvement"                  # Suggesting an improvement
    USABILITY = "usability"                      # Feedback on usability
    CLARIFICATION = "clarification"              # Asking for clarification
    GENERAL = "general"                          # General feedback
    TECHNICAL = "technical"                      # Technical feedback
    REQUIREMENT_CHANGE = "requirement_change"    # Change to requirements

class UserTechnicalLevel(Enum):
    """Enum representing the technical expertise level of a user."""
    BEGINNER = "beginner"                        # Limited technical knowledge
    INTERMEDIATE = "intermediate"                # Some technical knowledge
    ADVANCED = "advanced"                        # Advanced technical knowledge
    EXPERT = "expert"                            # Expert technical knowledge

class MilestoneAction(Enum):
    """Enum representing possible actions for milestone management."""
    APPROVE = "approve"                          # Approve milestone as is
    APPROVE_WITH_FEEDBACK = "approve_with_feedback" # Approve but with feedback
    REQUEST_CHANGES = "request_changes"          # Request specific changes
    REJECT = "reject"                            # Reject the milestone
    DEFER = "defer"                              # Defer decision
    REQUEST_MORE_INFO = "request_more_info"      # Request additional information

class AgentType(Enum):
    """Enum representing the types of agents in the system."""
    TEAM_LEAD = "team_lead"                      # Team Lead Agent
    SOLUTION_ARCHITECT = "solution_architect"    # Solution Architect Agent
    FULL_STACK_DEVELOPER = "full_stack_developer" # Full Stack Developer Agent
    QA_TEST = "qa_test"                          # QA/Test Agent
    PROJECT_MANAGER = "project_manager"          # Project Manager Agent
    SCRUM_MASTER = "scrum_master"                # Scrum Master Agent
    CODE_ASSEMBLER = "code_assembler"            # Code Assembler Agent

class Priority(Enum):
    """Enum representing priority levels for requests and tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    USER_INITIATED = "user_initiated"            # Special priority for user-initiated requests

@trace_class
class ScrumMasterGraphState(TypedDict):
    """
    Defines the state structure for ScrumMaster's workflow.
    
    Attributes:
        input (str): Raw user input/request
        request_type (str): Classified request type (new_project, feedback, question, etc.)
        user_id (str): Identifier for the user making the request
        project_id (Optional[str]): Identifier for the project (if applicable)
        pm_response (Optional[Dict[str, Any]]): Response from Project Manager agent
        team_lead_response (Optional[Dict[str, Any]]): Response from Team Lead agent
        milestone_data (Optional[Dict[str, Any]]): Milestone data for presentation
        user_feedback (Optional[Dict[str, Any]]): Processed user feedback
        technical_question (Optional[Dict[str, Any]]): Processed technical question
        status_report (Optional[Dict[str, Any]]): Generated status report
        user_preferences (Optional[Dict[str, Any]]): Tracked user preferences
        output (Optional[Dict[str, Any]]): Output to be presented to user
        clarification_questions (Optional[List[str]]): Questions to ask user for clarification
        agent_routing (Optional[Dict[str, Any]]): Information about routing to specific agents
        milestone_actions (Optional[Dict[str, Any]]): Actions related to milestone approvals
        conversation_history (Optional[List[Dict[str, Any]]]): History of the conversation
        error_info (Optional[Dict[str, Any]]): Information about errors encountered
        status (str): Current workflow status
        metadata (Dict[str, Any]): Additional metadata about the state
        transition_history (List[Dict[str, Any]]): History of state transitions
    """
    input: str
    request_type: str
    user_id: str
    project_id: Optional[str]
    pm_response: Optional[Dict[str, Any]]
    team_lead_response: Optional[Dict[str, Any]]
    milestone_data: Optional[Dict[str, Any]]
    user_feedback: Optional[Dict[str, Any]]
    technical_question: Optional[Dict[str, Any]]
    status_report: Optional[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    clarification_questions: Optional[List[str]]
    agent_routing: Optional[Dict[str, Any]]
    milestone_actions: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]]
    error_info: Optional[Dict[str, Any]]
    status: str
    metadata: Dict[str, Any]
    transition_history: List[Dict[str, Any]]

@trace_method
def validate_state(state: Dict[str, Any]) -> bool:
    """
    Validates state dictionary structure based on current workflow stage.
    
    Args:
        state: State dictionary to validate
        
    Returns:
        bool: True if valid, raises exception if invalid
    """
    logger.debug("Validating state")
    
    try:
        # Required keys that must be present in all states
        global_required_keys = ["input", "user_id", "status", "metadata", "transition_history"]
        for key in global_required_keys:
            if key not in state:
                raise KeyError(f"Missing required global key: {key}")
        
        # Required keys at different stages
        stage_requirements = {
            "initialized": [],  # No additional requirements beyond global
            "analyzing_request": ["request_type"],
            "routing_to_pm": ["request_type"],
            "awaiting_pm_response": ["request_type"],
            "processing_pm_response": ["request_type", "pm_response"],
            "routing_to_team_lead": ["request_type"],
            "awaiting_team_lead_response": ["request_type"],
            "processing_team_lead_response": ["request_type", "team_lead_response"],
            "need_clarification": ["request_type", "clarification_questions"],
            "presenting_to_user": ["output"],
            "processing_feedback": ["user_feedback"],
            "preparing_milestone": ["milestone_data"],
            "awaiting_milestone_approval": ["milestone_data"],
            "processing_milestone_decision": ["milestone_data", "milestone_actions"],
            "handling_technical_question": ["technical_question"],
            "generating_status_report": ["project_id"],
            "error_handling": ["error_info"],
            "completed": []  # No additional requirements beyond global
        }
        
        # Get current stage from status
        current_stage = state.get("status", "initialized")
        stage_required_keys = stage_requirements.get(current_stage, [])
        
        # Check for stage-specific required keys
        for key in stage_required_keys:
            if key not in state or state[key] is None:
                raise KeyError(f"Missing required key for stage {current_stage}: {key}")
        
        # Validate types based on stage
        if "input" in state and not isinstance(state["input"], str):
            raise TypeError("'input' must be a string")
            
        if "user_id" in state and not isinstance(state["user_id"], str):
            raise TypeError("'user_id' must be a string")
            
        if "request_type" in state and not isinstance(state["request_type"], str):
            raise TypeError("'request_type' must be a string")
            
        if "project_id" in state and state["project_id"] is not None and not isinstance(state["project_id"], str):
            raise TypeError("'project_id' must be a string or None")
            
        if "transition_history" in state and not isinstance(state["transition_history"], list):
            raise TypeError("'transition_history' must be a list")
            
        if "metadata" in state and not isinstance(state["metadata"], dict):
            raise TypeError("'metadata' must be a dictionary")
            
        if "status" in state and not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
        
        # Validate request type if present
        if "request_type" in state and state["request_type"] not in [rt.value for rt in RequestType]:
            # Allow string values that match RequestType values
            if isinstance(state["request_type"], str) and state["request_type"] not in RequestType.__members__:
                # Check if it's at least in the list of allowed values
                allowed_values = [rt.value for rt in RequestType]
                if state["request_type"] not in allowed_values:
                    logger.warning(f"Unknown request_type: {state['request_type']}, allowed values: {allowed_values}")
        
        # Validate special state combinations
        if current_stage == "processing_feedback" and "user_feedback" in state:
            if not isinstance(state["user_feedback"], dict):
                raise TypeError("'user_feedback' must be a dictionary")
            
            # Check for required feedback fields
            required_feedback_fields = ["content", "feedback_type"]
            for field in required_feedback_fields:
                if field not in state["user_feedback"]:
                    raise KeyError(f"Missing required field in user_feedback: {field}")
        
        # Validate milestone data if present
        if current_stage in ["preparing_milestone", "awaiting_milestone_approval", "processing_milestone_decision"] and "milestone_data" in state:
            if not isinstance(state["milestone_data"], dict):
                raise TypeError("'milestone_data' must be a dictionary")
            
            # Check for required milestone fields
            required_milestone_fields = ["id", "name", "completion_percentage"]
            for field in required_milestone_fields:
                if field not in state["milestone_data"]:
                    raise KeyError(f"Missing required field in milestone_data: {field}")
        
        # Validate technical question if present
        if current_stage == "handling_technical_question" and "technical_question" in state:
            if not isinstance(state["technical_question"], dict):
                raise TypeError("'technical_question' must be a dictionary")
            
            # Check for required question fields
            required_question_fields = ["question", "context"]
            for field in required_question_fields:
                if field not in state["technical_question"]:
                    raise KeyError(f"Missing required field in technical_question: {field}")
        
        # Validate error info if in error handling state
        if current_stage == "error_handling" and "error_info" in state:
            if not isinstance(state["error_info"], dict):
                raise TypeError("'error_info' must be a dictionary")
            
            # Check for required error fields
            required_error_fields = ["error_message", "error_type"]
            for field in required_error_fields:
                if field not in state["error_info"]:
                    raise KeyError(f"Missing required field in error_info: {field}")
        
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

@trace_method
def create_initial_state(user_input: str, user_id: str) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        user_input: Initial user input
        user_id: User identifier
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        current_time = datetime.utcnow().isoformat()
        
        state = {
            "input": user_input,
            "request_type": "unknown",
            "user_id": user_id,
            "project_id": None,
            "pm_response": None,
            "team_lead_response": None,
            "milestone_data": None,
            "user_feedback": None,
            "technical_question": None,
            "status_report": None,
            "user_preferences": None,
            "output": None,
            "clarification_questions": None,
            "agent_routing": None,
            "milestone_actions": None,
            "conversation_history": [
                {
                    "role": "user",
                    "content": user_input,
                    "timestamp": current_time
                }
            ],
            "error_info": None,
            "status": "initialized",
            "metadata": {
                "created_at": current_time,
                "updated_at": current_time
            },
            "transition_history": [
                {
                    "from_state": None,
                    "to_state": "initialized",
                    "timestamp": current_time,
                    "reason": "Initial state creation"
                }
            ]
        }
        
        # Validate initial state
        validate_state(state)
        
        logger.debug(f"Created initial state for user {user_id}")
        return state
        
    except Exception as e:
        logger.error(f"Failed to create initial state: {str(e)}", exc_info=True)
        # Create minimal valid state with error info
        current_time = datetime.utcnow().isoformat()
        return {
            "input": user_input,
            "request_type": "unknown",
            "user_id": user_id,
            "project_id": None,
            "pm_response": None,
            "team_lead_response": None,
            "milestone_data": None,
            "user_feedback": None,
            "technical_question": None,
            "status_report": None,
            "user_preferences": None,
            "output": None,
            "clarification_questions": None,
            "agent_routing": None,
            "milestone_actions": None,
            "conversation_history": [
                {
                    "role": "user",
                    "content": user_input,
                    "timestamp": current_time
                }
            ],
            "error_info": {
                "error_message": f"Error creating initial state: {str(e)}",
                "error_type": "initialization_error",
                "timestamp": current_time
            },
            "status": "error_handling",
            "metadata": {
                "created_at": current_time,
                "updated_at": current_time
            },
            "transition_history": [
                {
                    "from_state": None,
                    "to_state": "error_handling",
                    "timestamp": current_time,
                    "reason": f"Error during initialization: {str(e)}"
                }
            ]
        }

@trace_method
def get_next_stage(current_stage: str, state: Optional[Dict[str, Any]] = None) -> str:
    """
    Determines the next stage in the workflow based on current stage and state.
    
    Args:
        current_stage: Current workflow stage
        state: Optional current state for context-aware decisions
        
    Returns:
        str: Next stage name
    """
    # Default stage progression for simple flows
    standard_flow = {
        "initialized": "analyzing_request",
        "analyzing_request": "routing_request",
        "routing_request": "processing_request",
        "routing_to_pm": "awaiting_pm_response",
        "awaiting_pm_response": "processing_pm_response",
        "processing_pm_response": "presenting_to_user",
        "routing_to_team_lead": "awaiting_team_lead_response",
        "awaiting_team_lead_response": "processing_team_lead_response",
        "processing_team_lead_response": "presenting_to_user",
        "need_clarification": "presenting_to_user",
        "processing_feedback": "routing_to_team_lead",
        "preparing_milestone": "awaiting_milestone_approval",
        "awaiting_milestone_approval": "processing_milestone_decision",
        "processing_milestone_decision": "routing_to_team_lead",
        "handling_technical_question": "presenting_to_user",
        "generating_status_report": "presenting_to_user",
        "error_handling": "presenting_to_user",
        "presenting_to_user": "completed"
    }
    
    # If no state is provided, use standard flow
    if state is None:
        return standard_flow.get(current_stage, "completed")
    
    # Context-aware routing based on state and current stage
    if current_stage == "analyzing_request":
        request_type = state.get("request_type", "unknown")
        
        # Route based on request type
        if request_type == RequestType.NEW_PROJECT.value:
            return "routing_to_pm"
        elif request_type == RequestType.FEEDBACK.value:
            return "processing_feedback"
        elif request_type == RequestType.TECHNICAL_QUESTION.value:
            return "handling_technical_question"
        elif request_type == RequestType.STATUS_INQUIRY.value:
            return "generating_status_report"
        elif request_type == RequestType.MILESTONE_APPROVAL.value:
            return "preparing_milestone"
        elif request_type == RequestType.CLARIFICATION.value:
            return "need_clarification"
        elif request_type == RequestType.EMERGENCY.value:
            # Emergency goes directly to Team Lead
            return "routing_to_team_lead"
        elif request_type == "unknown":
            # If we couldn't classify, ask for clarification
            return "need_clarification"
        else:
            # Default routing for other types
            return "routing_request"
    
    elif current_stage == "routing_request":
        # Determine where to route based on request details
        request_type = state.get("request_type", "unknown")
        
        if request_type in [
            RequestType.NEW_PROJECT.value, 
            RequestType.REQUIREMENT_CHANGE.value
        ]:
            return "routing_to_pm"
        elif request_type in [
            RequestType.FEEDBACK.value,
            RequestType.TECHNICAL_QUESTION.value,
            RequestType.STATUS_INQUIRY.value,
            RequestType.EMERGENCY.value
        ]:
            return "routing_to_team_lead"
        else:
            # For other types, try to handle directly
            return "presenting_to_user"
    
    elif current_stage == "processing_feedback":
        feedback = state.get("user_feedback", {})
        feedback_type = feedback.get("feedback_type", "")
        
        # Route critical feedback directly to Team Lead
        if feedback.get("priority", "") == Priority.CRITICAL.value:
            return "routing_to_team_lead"
        
        # Handle different feedback types
        if feedback_type in [
            FeedbackType.BUG_REPORT.value,
            FeedbackType.TECHNICAL.value
        ]:
            return "routing_to_team_lead"
        elif feedback_type == FeedbackType.REQUIREMENT_CHANGE.value:
            return "routing_to_pm"
        else:
            # For other feedback, process and present to user first
            return "presenting_to_user"
    
    elif current_stage == "processing_milestone_decision":
        # Get the milestone action
        actions = state.get("milestone_actions", {})
        decision = actions.get("decision", "")
        
        # Route based on decision
        if decision in [
            MilestoneAction.APPROVE.value,
            MilestoneAction.APPROVE_WITH_FEEDBACK.value,
            MilestoneAction.REQUEST_CHANGES.value,
            MilestoneAction.REJECT.value
        ]:
            # Forward decision to Team Lead
            return "routing_to_team_lead"
        elif decision == MilestoneAction.REQUEST_MORE_INFO.value:
            # Need more information about the milestone
            return "routing_to_team_lead"
        else:
            # For defer or other actions, go back to user
            return "presenting_to_user"
    
    # For all other cases, use the standard flow
    return standard_flow.get(current_stage, "completed")

@trace_method
def can_transition(state: Dict[str, Any], target_stage: str) -> bool:
    """
    Checks if a transition to the target stage is valid from the current state.
    
    Args:
        state: Current state dictionary
        target_stage: Target stage to transition to
        
    Returns:
        bool: True if transition is valid, False otherwise
    """
    logger.debug(f"Checking transition from {state.get('status', 'unknown')} to {target_stage}")
    
    try:
        current_stage = state.get("status", "initialized")
        
        # Always allow transition to error_handling
        if target_stage == "error_handling":
            return True
        
        # Check if target is the next stage in the flow given the current state
        next_stage = get_next_stage(current_stage, state)
        if next_stage == target_stage:
            return True
            
        # Special case transitions
        
        # Allow restarting request analysis from most states
        if target_stage == "analyzing_request":
            return True
            
        # Can always go to presenting_to_user from most states
        if target_stage == "presenting_to_user" and current_stage not in [
            "initialized", "analyzing_request", "awaiting_pm_response", 
            "awaiting_team_lead_response"
        ]:
            return True
            
        # Can transition to need_clarification from many states
        if target_stage == "need_clarification" and current_stage not in [
            "initialized", "awaiting_pm_response", "awaiting_team_lead_response",
            "completed"
        ]:
            return True
            
        # Allow routing to team lead from various states
        if target_stage == "routing_to_team_lead" and current_stage in [
            "processing_feedback", "processing_milestone_decision", 
            "handling_technical_question"
        ]:
            return True
            
        # Handle unexpected user input by going back to analyzing_request
        if current_stage == "presenting_to_user" and target_stage == "analyzing_request":
            return True
            
        # Allow skipping PM for certain request types
        if current_stage == "routing_to_pm" and target_stage == "routing_to_team_lead":
            # Check request type to see if PM can be skipped
            request_type = state.get("request_type", "unknown")
            if request_type in [
                RequestType.FEEDBACK.value, RequestType.TECHNICAL_QUESTION.value,
                RequestType.STATUS_INQUIRY.value, RequestType.EMERGENCY.value
            ]:
                return True
        
        logger.info(f"Invalid transition from {current_stage} to {target_stage}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking transition: {str(e)}", exc_info=True)
        return False

@trace_method
def transition_state(
    state: Dict[str, Any], 
    target_stage: str, 
    reason: str = "", 
    updates: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Transition the state to a new stage with validation and history tracking.
    
    Args:
        state: Current state dictionary
        target_stage: Target stage to transition to
        reason: Reason for the transition
        updates: Optional dictionary of state updates to apply during transition
        
    Returns:
        Dict[str, Any]: Updated state after transition
    """
    logger.info(f"Transitioning from {state.get('status', 'unknown')} to {target_stage}")
    
    try:
        # Check if transition is valid
        if not can_transition(state, target_stage):
            error_msg = f"Invalid transition from {state.get('status', 'unknown')} to {target_stage}"
            logger.error(error_msg)
            
            # Instead of failing, create error_info and go to error_handling
            current_time = datetime.utcnow().isoformat()
            new_state = state.copy()
            new_state["error_info"] = {
                "error_message": error_msg,
                "error_type": "invalid_transition",
                "timestamp": current_time,
                "attempted_target": target_stage
            }
            
            # Record the failed transition attempt
            from_state = state.get("status", "unknown")
            new_state["transition_history"] = new_state.get("transition_history", []) + [
                {
                    "from_state": from_state,
                    "to_state": "error_handling",
                    "timestamp": current_time,
                    "reason": f"Invalid transition attempt to {target_stage}: {reason}"
                }
            ]
            
            new_state["status"] = "error_handling"
            new_state["metadata"]["updated_at"] = current_time
            
            # Don't apply any other updates when going to error_handling
            return new_state
        
        # Copy the state to avoid modifying the original
        new_state = state.copy()
        current_time = datetime.utcnow().isoformat()
        
        # Record transition in history
        from_state = state.get("status", "unknown")
        new_state["transition_history"] = new_state.get("transition_history", []) + [
            {
                "from_state": from_state,
                "to_state": target_stage,
                "timestamp": current_time,
                "reason": reason
            }
        ]
        
        # Update status
        new_state["status"] = target_stage
        
        # Update metadata
        new_state["metadata"] = new_state.get("metadata", {}).copy()
        new_state["metadata"]["updated_at"] = current_time
        
        # Apply additional updates if provided
        if updates:
            for key, value in updates.items():
                if key not in ["status", "transition_history", "metadata"]:  # Don't overwrite these
                    new_state[key] = value
        
        # Special handling for certain transitions
        if target_stage == "presenting_to_user" and "output" not in updates:
            # Ensure there's an output for presenting to user
            new_state["output"] = new_state.get("output") or {
                "content": "I'm processing your request.",
                "type": "text",
                "generated_at": current_time
            }
        
        # Validate the new state
        validate_state(new_state)
        
        logger.info(f"Successfully transitioned to {target_stage}")
        return new_state
        
    except Exception as e:
        logger.error(f"Error during state transition: {str(e)}", exc_info=True)
        
        # Create error state
        current_time = datetime.utcnow().isoformat()
        error_state = state.copy()
        error_state["error_info"] = {
            "error_message": f"Error during transition to {target_stage}: {str(e)}",
            "error_type": "transition_error",
            "timestamp": current_time,
            "attempted_target": target_stage
        }
        
        # Record the failed transition
        from_state = state.get("status", "unknown")
        error_state["transition_history"] = error_state.get("transition_history", []) + [
            {
                "from_state": from_state,
                "to_state": "error_handling",
                "timestamp": current_time,
                "reason": f"Error during transition: {str(e)}"
            }
        ]
        
        error_state["status"] = "error_handling"
        error_state["metadata"] = error_state.get("metadata", {}).copy()
        error_state["metadata"]["updated_at"] = current_time
        
        return error_state

@trace_method
def determine_request_type(user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Determine the type of user request from input text and context.
    This is a placeholder for more sophisticated request classification.
    In a real system, this would call the LLM service for accurate classification.
    
    Args:
        user_input: User input text
        context: Optional additional context including conversation history
        
    Returns:
        str: Determined request type from RequestType enum values
    """
    """
    Determine the type of user request from input text and context.
    This is a placeholder for more sophisticated request classification.
    
    Args:
        user_input: User input text
        context: Optional additional context
        
    Returns:
        str: Determined request type
    """
    # This is a simplified implementation - in practice, would use LLM service
    user_input_lower = user_input.lower()
    
    # Check for project creation requests
    if any(phrase in user_input_lower for phrase in [
        "create a project", "new project", "start a project", "build",
        "develop a", "make a"
    ]):
        return RequestType.NEW_PROJECT.value
    
    # Check for feedback
    if any(phrase in user_input_lower for phrase in [
        "feedback", "suggestion", "improve", "change", "bug", "issue",
        "doesn't work", "not working", "problem"
    ]):
        return RequestType.FEEDBACK.value
    
    # Check for technical questions
    if any(phrase in user_input_lower for phrase in [
        "how does", "why is", "explain", "what is", "tell me about",
        "technical", "architecture", "code", "implementation"
    ]) or "?" in user_input:
        return RequestType.TECHNICAL_QUESTION.value
    
    # Check for status inquiries
    if any(phrase in user_input_lower for phrase in [
        "status", "progress", "update", "how is", "where are we",
        "timeline", "when will", "completed", "finished"
    ]):
        return RequestType.STATUS_INQUIRY.value
    
    # Check for milestone approvals
    if any(phrase in user_input_lower for phrase in [
        "approve", "review", "milestone", "deliverable", "accept",
        "reject", "changes needed"
    ]):
        return RequestType.MILESTONE_APPROVAL.value
    
    # Check for clarification requests
    if any(phrase in user_input_lower for phrase in [
        "clarify", "clarification", "confused", "don't understand",
        "more detail", "explain"
    ]):
        return RequestType.CLARIFICATION.value
    
    # Check for requirement changes
    if any(phrase in user_input_lower for phrase in [
        "change requirement", "update requirement", "modify requirement",
        "new requirement", "requirement change"
    ]):
        return RequestType.REQUIREMENT_CHANGE.value
    
    # Check for emergency situations
    if any(phrase in user_input_lower for phrase in [
        "urgent", "emergency", "critical", "asap", "immediately",
        "blocker", "blocked", "show stopper"
    ]):
        return RequestType.EMERGENCY.value
    
    # Check for general inquiries
    if any(phrase in user_input_lower for phrase in [
        "help", "info", "information", "general", "overview",
        "guide", "documentation"
    ]):
        return RequestType.GENERAL_INQUIRY.value
    
    # Default to other if no clear type is determined
    return RequestType.OTHER.value

@trace_method
def resolve_optimal_agent_routing(
    state: Dict[str, Any],
    available_agents: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Determine the optimal agent to handle a specific request based on request type,
    content, priority, and available agents.
    
    Args:
        state: Current state dictionary
        available_agents: Optional set of available agent IDs
        
    Returns:
        Dict[str, Any]: Routing information including target agent, priority, and context
    """
    logger.info("Resolving optimal agent routing")
    
    try:
        request_type = state.get("request_type", "unknown")
        user_id = state.get("user_id", "")
        input_content = state.get("input", "")
        
        # Default routing is to Team Lead
        default_routing = {
            "target_agent_id": AgentType.TEAM_LEAD.value,
            "routing_reason": "Default routing to Team Lead",
            "priority": Priority.MEDIUM.value,
            "context": {
                "request_type": request_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # If no available agents specified, assume all are available
        if available_agents is None:
            available_agents = {agent.value for agent in AgentType}
        
        # Check if Team Lead is available for default routing
        if AgentType.TEAM_LEAD.value not in available_agents:
            logger.warning("Team Lead not available, adjusting routing")
            # Fall back to PROJECT_MANAGER if Team Lead unavailable
            if AgentType.PROJECT_MANAGER.value in available_agents:
                default_routing["target_agent_id"] = AgentType.PROJECT_MANAGER.value
                default_routing["routing_reason"] = "Team Lead unavailable, routing to Project Manager"
        
        # Route based on request type
        if request_type == RequestType.NEW_PROJECT.value:
            # New projects go to Project Manager first
            if AgentType.PROJECT_MANAGER.value in available_agents:
                return {
                    "target_agent_id": AgentType.PROJECT_MANAGER.value,
                    "routing_reason": "New project request routed to Project Manager",
                    "priority": Priority.HIGH.value,
                    "context": {
                        "request_type": request_type,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "requires_planning": True
                    }
                }
            
        elif request_type == RequestType.FEEDBACK.value:
            # Process user feedback
            feedback = state.get("user_feedback", {})
            feedback_type = feedback.get("feedback_type", "")
            priority = feedback.get("priority", Priority.MEDIUM.value)
            
            # Technical feedback goes to Team Lead or appropriate specialist
            if feedback_type in [FeedbackType.BUG_REPORT.value, FeedbackType.TECHNICAL.value]:
                # Critical bugs go directly to Team Lead with high priority
                if priority == Priority.CRITICAL.value:
                    return {
                        "target_agent_id": AgentType.TEAM_LEAD.value,
                        "routing_reason": "Critical technical feedback routed to Team Lead",
                        "priority": Priority.CRITICAL.value,
                        "context": {
                            "request_type": request_type,
                            "feedback_type": feedback_type,
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "requires_immediate_attention": True
                        }
                    }
                # Non-critical bugs can go to QA/Test if available
                elif AgentType.QA_TEST.value in available_agents:
                    return {
                        "target_agent_id": AgentType.QA_TEST.value,
                        "routing_reason": "Bug report routed to QA/Test agent",
                        "priority": priority,
                        "context": {
                            "request_type": request_type,
                            "feedback_type": feedback_type,
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
            
            # Feature requests or improvements go to Solution Architect if available
            elif feedback_type in [FeedbackType.FEATURE_REQUEST.value, FeedbackType.IMPROVEMENT.value]:
                if AgentType.SOLUTION_ARCHITECT.value in available_agents:
                    return {
                        "target_agent_id": AgentType.SOLUTION_ARCHITECT.value,
                        "routing_reason": f"{feedback_type} routed to Solution Architect",
                        "priority": priority,
                        "context": {
                            "request_type": request_type,
                            "feedback_type": feedback_type,
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
            
            # Requirement changes go to Project Manager
            elif feedback_type == FeedbackType.REQUIREMENT_CHANGE.value:
                if AgentType.PROJECT_MANAGER.value in available_agents:
                    return {
                        "target_agent_id": AgentType.PROJECT_MANAGER.value,
                        "routing_reason": "Requirement change routed to Project Manager",
                        "priority": priority,
                        "context": {
                            "request_type": request_type,
                            "feedback_type": feedback_type,
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
        
        elif request_type == RequestType.TECHNICAL_QUESTION.value:
            # Technical questions can be routed based on content
            question = state.get("technical_question", {})
            question_content = question.get("question", input_content)
            
            # Check for architecture-related questions
            if any(term in question_content.lower() for term in [
                "architecture", "design", "structure", "system", "framework"
            ]) and AgentType.SOLUTION_ARCHITECT.value in available_agents:
                return {
                    "target_agent_id": AgentType.SOLUTION_ARCHITECT.value, 
                    "routing_reason": "Architecture-related question routed to Solution Architect",
                    "priority": Priority.MEDIUM.value,
                    "context": {
                        "request_type": request_type,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "question_type": "architecture"
                    }
                }
            
            # Check for implementation-related questions
            elif any(term in question_content.lower() for term in [
                "code", "implementation", "programming", "function", "class", "method"
            ]) and AgentType.FULL_STACK_DEVELOPER.value in available_agents:
                return {
                    "target_agent_id": AgentType.FULL_STACK_DEVELOPER.value,
                    "routing_reason": "Implementation-related question routed to Developer",
                    "priority": Priority.MEDIUM.value,
                    "context": {
                        "request_type": request_type,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "question_type": "implementation"
                    }
                }
            
            # Check for testing-related questions
            elif any(term in question_content.lower() for term in [
                "test", "quality", "qa", "bug", "issue", "verification"
            ]) and AgentType.QA_TEST.value in available_agents:
                return {
                    "target_agent_id": AgentType.QA_TEST.value,
                    "routing_reason": "Testing-related question routed to QA/Test agent",
                    "priority": Priority.MEDIUM.value,
                    "context": {
                        "request_type": request_type,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "question_type": "testing"
                    }
                }
        
        elif request_type == RequestType.MILESTONE_APPROVAL.value:
            # Milestone approvals are processed and then routed to Team Lead
            return {
                "target_agent_id": AgentType.TEAM_LEAD.value,
                "routing_reason": "Milestone approval decision routed to Team Lead",
                "priority": Priority.HIGH.value,
                "context": {
                    "request_type": request_type,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "milestone_id": state.get("milestone_data", {}).get("id"),
                    "decision": state.get("milestone_actions", {}).get("decision")
                }
            }
        
        elif request_type == RequestType.EMERGENCY.value:
            # Emergencies always go to Team Lead with critical priority
            return {
                "target_agent_id": AgentType.TEAM_LEAD.value,
                "routing_reason": "Emergency request routed directly to Team Lead",
                "priority": Priority.CRITICAL.value,
                "context": {
                    "request_type": request_type,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "requires_immediate_attention": True
                }
            }
        
        # For all other cases, use default routing
        logger.info(f"Using default routing to {default_routing['target_agent_id']} for request type {request_type}")
        return default_routing
        
    except Exception as e:
        logger.error(f"Error in optimal agent routing: {str(e)}", exc_info=True)
        # Fall back to Team Lead in case of error
        return {
            "target_agent_id": AgentType.TEAM_LEAD.value,
            "routing_reason": f"Error in routing resolution: {str(e)}",
            "priority": Priority.HIGH.value,
            "context": {
                "request_type": state.get("request_type", "unknown"),
                "user_id": state.get("user_id", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        }

@trace_method
def prepare_state_context_for_llm(
    state: Dict[str, Any],
    context_type: str = "general"
) -> Dict[str, Any]:
    """
    Prepare and extract relevant context from the state for LLM calls.
    Tailors the context based on the specific LLM operation being performed.
    
    Args:
        state: Current state dictionary
        context_type: Type of context to prepare (general, feedback, technical, milestone, etc.)
        
    Returns:
        Dict[str, Any]: Prepared context for LLM
    """
    logger.info(f"Preparing {context_type} context for LLM call")
    
    try:
        # Base context included in all types
        base_context = {
            "user_id": state.get("user_id", ""),
            "request_type": state.get("request_type", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add project context if available
        if state.get("project_id"):
            base_context["project_id"] = state["project_id"]
        
        # Add user preferences if available
        if state.get("user_preferences"):
            base_context["user_preferences"] = {
                "technical_level": state["user_preferences"].get("technical_level", UserTechnicalLevel.BEGINNER.value),
                "detail_preference": state["user_preferences"].get("detail_preference", "medium"),
                "communication_style": state["user_preferences"].get("communication_style", "friendly")
            }
        
        # Add conversation history summary if available
        if state.get("conversation_history"):
            # Only include last 3 exchanges to keep context concise
            recent_history = state["conversation_history"][-6:] if len(state["conversation_history"]) > 6 else state["conversation_history"]
            base_context["conversation_history"] = recent_history
        
        # Customize context based on type
        if context_type == "feedback":
            # Context for feedback processing
            feedback_context = {
                **base_context,
                "feedback_content": state.get("user_feedback", {}).get("content", ""),
                "feedback_type": state.get("user_feedback", {}).get("feedback_type", ""),
                "feedback_priority": state.get("user_feedback", {}).get("priority", ""),
                "feedback_sentiment": state.get("user_feedback", {}).get("sentiment", "")
            }
            return feedback_context
            
        elif context_type == "technical_question":
            # Context for answering technical questions
            question_context = {
                **base_context,
                "question": state.get("technical_question", {}).get("question", ""),
                "question_context": state.get("technical_question", {}).get("context", {}),
                "user_technical_level": base_context.get("user_preferences", {}).get("technical_level", UserTechnicalLevel.BEGINNER.value)
            }
            return question_context
            
        elif context_type == "milestone":
            # Context for milestone presentation
            milestone_context = {
                **base_context,
                "milestone_id": state.get("milestone_data", {}).get("id", ""),
                "milestone_name": state.get("milestone_data", {}).get("name", ""),
                "milestone_completion": state.get("milestone_data", {}).get("completion_percentage", 0),
                "requires_approval": state.get("milestone_data", {}).get("requires_approval", True)
            }
            return milestone_context
            
        elif context_type == "status_report":
            # Context for status reporting
            status_context = {
                **base_context,
                "project_status": state.get("status_report", {}),
                "report_type": state.get("metadata", {}).get("report_type", "standard")
            }
            return status_context
            
        elif context_type == "clarification":
            # Context for generating clarification questions
            clarification_context = {
                **base_context,
                "original_input": state.get("input", ""),
                "unclear_aspects": state.get("clarification_questions", []),
                "request_analysis": {
                    "request_type": state.get("request_type", "unknown"),
                    "clarification_needed": True
                }
            }
            return clarification_context
        
        # Default to general context
        return base_context
        
    except Exception as e:
        logger.error(f"Error preparing context for LLM: {str(e)}", exc_info=True)
        # Return minimal context in case of error
        return {
            "user_id": state.get("user_id", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "context_error": str(e)
        }

@trace_method
def extract_state_visualization_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract data from the state for visualization purposes.
    Formats the state graph data for use in visualization tools.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Dict[str, Any]: Formatted visualization data
    """
    logger.info("Extracting state visualization data")
    
    try:
        # Extract basic state information
        viz_data = {
            "current_state": state.get("status", "unknown"),
            "request_type": state.get("request_type", "unknown"),
            "user_id": state.get("user_id", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": state.get("project_id")
        }
        
        # Extract transition history for graph visualization
        if state.get("transition_history"):
            # Format transitions for visualization
            transitions = []
            for transition in state["transition_history"]:
                transitions.append({
                    "from": transition.get("from_state"),
                    "to": transition.get("to_state"),
                    "timestamp": transition.get("timestamp"),
                    "reason": transition.get("reason", "")
                })
            
            viz_data["transitions"] = transitions
            
            # Calculate state durations
            state_durations = {}
            for i in range(len(transitions) - 1):
                current_state = transitions[i]["to"]
                start_time = datetime.fromisoformat(transitions[i]["timestamp"])
                end_time = datetime.fromisoformat(transitions[i+1]["timestamp"])
                duration = (end_time - start_time).total_seconds()
                
                if current_state in state_durations:
                    state_durations[current_state] += duration
                else:
                    state_durations[current_state] = duration
            
            viz_data["state_durations"] = state_durations
        
        # Add node data for each possible state
        all_states = [
            "initialized", "analyzing_request", "routing_to_pm", "awaiting_pm_response",
            "processing_pm_response", "routing_to_team_lead", "awaiting_team_lead_response",
            "processing_team_lead_response", "need_clarification", "presenting_to_user",
            "processing_feedback", "preparing_milestone", "awaiting_milestone_approval",
            "processing_milestone_decision", "handling_technical_question",
            "generating_status_report", "error_handling", "completed"
        ]
        
        nodes = []
        for node_state in all_states:
            # Check if this state has been visited
            visited = any(t.get("to_state") == node_state for t in state.get("transition_history", []))
            
            # Determine if this is the current state
            is_current = state.get("status") == node_state
            
            # Add node data
            nodes.append({
                "id": node_state,
                "visited": visited,
                "current": is_current,
                "duration": viz_data.get("state_durations", {}).get(node_state, 0),
                "type": _get_node_type(node_state)
            })
        
        viz_data["nodes"] = nodes
        
        # Add current state details
        viz_data["current_state_details"] = _get_state_details(state)
        
        return viz_data
        
    except Exception as e:
        logger.error(f"Error extracting visualization data: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "current_state": state.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }

def _get_node_type(state_name: str) -> str:
    """Helper function to categorize state nodes by type."""
    if state_name in ["initialized", "completed"]:
        return "terminal"
    elif state_name in ["error_handling"]:
        return "error"
    elif state_name in ["awaiting_pm_response", "awaiting_team_lead_response", "awaiting_milestone_approval"]:
        return "waiting"
    elif state_name in ["processing_feedback", "processing_pm_response", "processing_team_lead_response", "processing_milestone_decision"]:
        return "processing"
    elif state_name in ["presenting_to_user", "need_clarification"]:
        return "user_interaction"
    elif state_name in ["analyzing_request", "routing_to_pm", "routing_to_team_lead"]:
        return "routing"
    else:
        return "standard"

def _get_state_details(state: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to extract relevant details for the current state."""
    current_state = state.get("status", "unknown")
    
    details = {
        "state": current_state,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add state-specific details
    if current_state == "processing_feedback":
        details["feedback"] = state.get("user_feedback", {})
    elif current_state == "preparing_milestone":
        details["milestone"] = state.get("milestone_data", {})
    elif current_state == "handling_technical_question":
        details["question"] = state.get("technical_question", {})
    elif current_state == "error_handling":
        details["error"] = state.get("error_info", {})
    elif current_state == "presenting_to_user":
        details["output"] = state.get("output", {})
    
    return details