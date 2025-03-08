from typing import TypedDict, Dict, List, Any, Optional, Union
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("full_stack_developer.state_graph")

@trace_class
class FullStackDeveloperGraphState(TypedDict):
    """
    Defines the state structure for FullStackDeveloper's workflow.
    
    Attributes:
        input: Raw task specification
        requirements: Analyzed requirements and technical constraints
        solution_design: Design details for frontend, backend, and database
        generated_code: Code generated for each component
        documentation: Generated documentation
        status: Current workflow status
        
        # New fields for Team Lead coordination
        task_id: ID of the assigned task from Team Lead
        team_lead_id: ID of the Team Lead agent
        instructions: Detailed instructions from Team Lead
        deliverables: Packaged deliverables ready for submission
        feedback: Feedback received on deliverables
        revision_requests: Specific revision requests to address
        coordination_state: Current coordination state with Team Lead
        status_reports: History of status reports sent to Team Lead
    """
    input: str
    requirements: Dict[str, Any]
    solution_design: Dict[str, Any]
    generated_code: Dict[str, Dict[str, str]]
    documentation: Dict[str, str]
    status: str
    
    # New fields for Team Lead coordination
    task_id: Optional[str]
    team_lead_id: Optional[str]
    instructions: Optional[Dict[str, Any]]
    deliverables: Dict[str, Any]
    feedback: List[Dict[str, Any]]
    revision_requests: List[Dict[str, Any]]
    coordination_state: str
    status_reports: List[Dict[str, Any]]

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
        # Required keys at different stages
        stage_requirements = {
            "initialized": ["input", "status"],
            "analyzing_requirements": ["input", "status"],
            "designing_solution": ["input", "requirements", "status"],
            "generating_code": ["input", "requirements", "solution_design", "status"],
            "preparing_documentation": ["input", "requirements", "solution_design", "generated_code", "status"],
            "completed": ["input", "requirements", "solution_design", "generated_code", "documentation", "status"],
            
            # New coordination stages
            "awaiting_instructions": ["input", "status", "task_id", "team_lead_id"],
            "processing_instructions": ["input", "status", "task_id", "team_lead_id", "instructions"],
            "reporting_status": ["input", "status", "task_id", "team_lead_id", "status_reports"],
            "packaging_deliverables": ["input", "status", "task_id", "generated_code", "documentation"],
            "awaiting_feedback": ["input", "status", "task_id", "team_lead_id", "deliverables"],
            "processing_feedback": ["input", "status", "task_id", "team_lead_id", "feedback", "revision_requests"],
            "implementing_revisions": ["input", "status", "task_id", "team_lead_id", "revision_requests"],
        }
        
        # Get current stage from status
        current_stage = state.get("status", "initialized")
        required_keys = stage_requirements.get(current_stage, ["input", "status"])
        
        # Check for required keys
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise KeyError(f"Missing required keys for stage {current_stage}: {missing_keys}")
        
        # Validate types based on stage
        if "input" in state and not isinstance(state["input"], str):
            raise TypeError("'input' must be a string")
            
        if "requirements" in state and not isinstance(state["requirements"], dict):
            raise TypeError("'requirements' must be a dictionary")
            
        if "solution_design" in state and not isinstance(state["solution_design"], dict):
            raise TypeError("'solution_design' must be a dictionary")
            
        if "generated_code" in state and not isinstance(state["generated_code"], dict):
            raise TypeError("'generated_code' must be a dictionary")
            
        if "documentation" in state and not isinstance(state["documentation"], dict):
            raise TypeError("'documentation' must be a dictionary")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
        
        # Validate new coordination fields if present
        if "task_id" in state and state["task_id"] is not None and not isinstance(state["task_id"], str):
            raise TypeError("'task_id' must be a string or None")
            
        if "team_lead_id" in state and state["team_lead_id"] is not None and not isinstance(state["team_lead_id"], str):
            raise TypeError("'team_lead_id' must be a string or None")
            
        if "instructions" in state and state["instructions"] is not None and not isinstance(state["instructions"], dict):
            raise TypeError("'instructions' must be a dictionary or None")
            
        if "deliverables" in state and not isinstance(state["deliverables"], dict):
            raise TypeError("'deliverables' must be a dictionary")
            
        if "feedback" in state and not isinstance(state["feedback"], list):
            raise TypeError("'feedback' must be a list")
            
        if "revision_requests" in state and not isinstance(state["revision_requests"], list):
            raise TypeError("'revision_requests' must be a list")
            
        if "coordination_state" in state and not isinstance(state["coordination_state"], str):
            raise TypeError("'coordination_state' must be a string")
            
        if "status_reports" in state and not isinstance(state["status_reports"], list):
            raise TypeError("'status_reports' must be a list")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(task_specification: str, task_id: Optional[str] = None, team_lead_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        task_specification: Initial task specification
        task_id: Optional task ID from Team Lead
        team_lead_id: Optional Team Lead agent ID
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": task_specification,
            "requirements": {},
            "solution_design": {},
            "generated_code": {},
            "documentation": {},
            "status": "initialized",
            
            # Initialize coordination fields
            "task_id": task_id,
            "team_lead_id": team_lead_id,
            "instructions": None if task_id is None else {},
            "deliverables": {},
            "feedback": [],
            "revision_requests": [],
            "coordination_state": "independent" if task_id is None else "awaiting_instructions",
            "status_reports": []
        }
        
        # Validate initial state
        validate_state(state)
        
        logger.debug(f"Created initial state: {state}")
        return state
        
    except Exception as e:
        logger.error(f"Failed to create initial state: {str(e)}", exc_info=True)
        raise

def get_next_stage(current_stage: str) -> str:
    """
    Determines the next stage in the workflow.
    
    Args:
        current_stage: Current workflow stage
        
    Returns:
        str: Next stage name
    """
    # Standard workflow progression
    stage_flow = {
        "initialized": "analyzing_requirements",
        "analyzing_requirements": "designing_solution",
        "designing_solution": "generating_code",
        "generating_code": "preparing_documentation",
        "preparing_documentation": "packaging_deliverables",  # Updated to include deliverable packaging
        "packaging_deliverables": "completed",
        
        # Coordination workflow progression
        "awaiting_instructions": "processing_instructions",
        "processing_instructions": "analyzing_requirements",
        "reporting_status": current_stage,  # Returns to same stage (stateless update)
        "packaging_deliverables": "awaiting_feedback",
        "awaiting_feedback": "processing_feedback",
        "processing_feedback": "implementing_revisions",
        "implementing_revisions": "analyzing_requirements"  # Loop back to start of workflow
    }
    
    return stage_flow.get(current_stage, "completed")

def get_coordination_state(workflow_state: str) -> str:
    """
    Maps workflow state to coordination state.
    
    Args:
        workflow_state: Current workflow state
        
    Returns:
        str: Corresponding coordination state
    """
    coordination_mapping = {
        "initialized": "ready",
        "analyzing_requirements": "working",
        "designing_solution": "working",
        "generating_code": "working",
        "preparing_documentation": "working",
        "packaging_deliverables": "delivering",
        "awaiting_feedback": "waiting",
        "processing_feedback": "revising",
        "implementing_revisions": "revising",
        "completed": "complete"
    }
    
    return coordination_mapping.get(workflow_state, "unknown")

def can_process_teamlead_message(state: Dict[str, Any]) -> bool:
    """
    Determines if the agent can process a Team Lead message in its current state.
    
    Args:
        state: Current state dictionary
        
    Returns:
        bool: True if the agent can process a Team Lead message
    """
    # States where the agent can accept new instructions or feedback
    receptive_states = [
        "initialized",
        "awaiting_instructions",
        "awaiting_feedback",
        "completed"
    ]
    
    # The agent can also receive status update requests in any state
    current_state = state.get("status", "initialized")
    return current_state in receptive_states