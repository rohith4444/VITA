from typing import TypedDict, Dict, Any, List, Optional, Union
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("solution_architect.state_graph")

@trace_class
class SolutionArchitectGraphState(TypedDict):
    """
    Defines the state structure for SolutionArchitect's workflow.
    
    Attributes:
        input (str): Raw project description/requirements
        project_plan (Dict[str, Any]): Project plan from Project Manager
        tech_stack (Dict[str, List[str]]): Selected technologies for each layer
        architecture_design (Dict[str, Any]): System architecture design
        validation_results (Dict[str, Any]): Architecture validation results
        specifications (Dict[str, Any]): Technical specifications
        status (str): Current workflow status
        
        # Coordination attributes
        task_id (str): ID of the current task from Team Lead
        task_priority (str): Priority level of the current task
        assigned_by (str): ID of the agent that assigned this task
        due_time (str): Due time for the current task
        deliverables (Dict[str, Any]): Deliverables being prepared for Team Lead
        feedback (Dict[str, Any]): Feedback received from Team Lead
        coordination_metadata (Dict[str, Any]): Additional metadata for coordination
        awaiting_feedback (bool): Flag indicating if waiting for Team Lead feedback
    """
    input: str
    project_plan: Dict[str, Any]
    tech_stack: Dict[str, List[str]]
    architecture_design: Dict[str, Any]
    validation_results: Dict[str, Any]
    specifications: Dict[str, Any]
    status: str
    
    # Coordination attributes (added for Team Lead integration)
    task_id: Optional[str]
    task_priority: Optional[str]
    assigned_by: Optional[str]
    due_time: Optional[str]
    deliverables: Dict[str, Any]
    feedback: Dict[str, Any]
    coordination_metadata: Dict[str, Any]
    awaiting_feedback: bool

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
            "initialized": ["input", "project_plan", "status"],
            "analyzing_requirements": ["input", "project_plan", "status"],
            "selecting_tech_stack": ["input", "project_plan", "status"],
            "designing_architecture": ["input", "project_plan", "tech_stack", "status"],
            "validating_architecture": ["input", "project_plan", "tech_stack", "architecture_design", "status"],
            "generating_specifications": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "status"],
            "packaging_deliverables": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "specifications", "deliverables", "status"],
            "awaiting_feedback": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "specifications", "deliverables", "awaiting_feedback", "status"],
            "applying_feedback": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "specifications", "deliverables", "feedback", "status"],
            "completed": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "specifications", "deliverables", "status"]
        }
        
        # Get current stage from status
        current_stage = state.get("status", "initialized")
        required_keys = stage_requirements.get(current_stage, ["input", "project_plan", "status"])
        
        # Check for required keys
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise KeyError(f"Missing required keys for stage {current_stage}: {missing_keys}")
        
        # Validate types based on stage
        if "input" in state and not isinstance(state["input"], str):
            raise TypeError("'input' must be a string")
            
        if "project_plan" in state and not isinstance(state["project_plan"], dict):
            raise TypeError("'project_plan' must be a dictionary")
            
        if "tech_stack" in state and not isinstance(state["tech_stack"], dict):
            raise TypeError("'tech_stack' must be a dictionary")
            
        if "architecture_design" in state and not isinstance(state["architecture_design"], dict):
            raise TypeError("'architecture_design' must be a dictionary")
            
        if "validation_results" in state and not isinstance(state["validation_results"], dict):
            raise TypeError("'validation_results' must be a dictionary")
            
        if "specifications" in state and not isinstance(state["specifications"], dict):
            raise TypeError("'specifications' must be a dictionary")
            
        # Validate coordination fields if present
        if "deliverables" in state and not isinstance(state["deliverables"], dict):
            raise TypeError("'deliverables' must be a dictionary")
            
        if "feedback" in state and not isinstance(state["feedback"], dict):
            raise TypeError("'feedback' must be a dictionary")
            
        if "coordination_metadata" in state and not isinstance(state["coordination_metadata"], dict):
            raise TypeError("'coordination_metadata' must be a dictionary")
            
        if "awaiting_feedback" in state and not isinstance(state["awaiting_feedback"], bool):
            raise TypeError("'awaiting_feedback' must be a boolean")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(project_description: str, project_plan: Dict[str, Any], task_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        project_description: Initial project description
        project_plan: Project plan from Project Manager
        task_info: Optional task information from Team Lead
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        # Extract task information if provided
        task_id = None
        task_priority = None
        assigned_by = None
        due_time = None
        
        if task_info:
            task_id = task_info.get("task_id")
            task_priority = task_info.get("priority", "MEDIUM")
            assigned_by = task_info.get("assigned_by")
            due_time = task_info.get("due_time")
        
        state = {
            "input": project_description,
            "project_plan": project_plan,
            "tech_stack": {},
            "architecture_design": {},
            "validation_results": {},
            "specifications": {},
            "status": "initialized",
            
            # Coordination fields
            "task_id": task_id,
            "task_priority": task_priority,
            "assigned_by": assigned_by,
            "due_time": due_time,
            "deliverables": {},
            "feedback": {},
            "coordination_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            },
            "awaiting_feedback": False
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
    stage_flow = {
        "initialized": "analyzing_requirements",
        "analyzing_requirements": "selecting_tech_stack",
        "selecting_tech_stack": "designing_architecture",
        "designing_architecture": "validating_architecture", 
        "validating_architecture": "generating_specifications",
        "generating_specifications": "packaging_deliverables",
        "packaging_deliverables": "awaiting_feedback",
        "awaiting_feedback": "applying_feedback",
        "applying_feedback": "completed"
    }
    
    return stage_flow.get(current_stage, "completed")

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
        
        # Check if target is the next stage in the normal flow
        if get_next_stage(current_stage) == target_stage:
            return True
        
        # Special case transitions for coordination
        
        # Can receive feedback while awaiting feedback
        if current_stage == "awaiting_feedback" and target_stage == "applying_feedback":
            return True
            
        # Can go back to any previous stage from applying_feedback
        if current_stage == "applying_feedback":
            previous_stages = [
                "analyzing_requirements", 
                "selecting_tech_stack", 
                "designing_architecture", 
                "validating_architecture", 
                "generating_specifications"
            ]
            if target_stage in previous_stages:
                return True
        
        # Can be instructed to revise architecture at any point
        if target_stage == "designing_architecture" and state.get("architecture_design"):
            return True
        
        # Can be instructed to revise specifications at any point
        if target_stage == "generating_specifications" and state.get("specifications"):
            return True
        
        # Can be instructed to revise tech stack at any point
        if target_stage == "selecting_tech_stack" and state.get("tech_stack"):
            return True
        
        # Can skip to packaging if Team Lead requests early delivery
        if target_stage == "packaging_deliverables" and state.get("architecture_design"):
            return True
            
        logger.info(f"Invalid transition from {current_stage} to {target_stage}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking transition: {str(e)}", exc_info=True)
        return False

def get_state_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts metadata about the current state for reporting purposes.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Dict[str, Any]: State metadata
    """
    try:
        current_stage = state.get("status", "initialized")
        
        metadata = {
            "current_stage": current_stage,
            "next_stage": get_next_stage(current_stage),
            "timestamp": datetime.utcnow().isoformat(),
            "has_architecture": bool(state.get("architecture_design")),
            "has_specifications": bool(state.get("specifications")),
            "has_tech_stack": bool(state.get("tech_stack")),
            "awaiting_feedback": state.get("awaiting_feedback", False),
            "task_id": state.get("task_id"),
            "task_priority": state.get("task_priority")
        }
        
        if "deliverables" in state and state["deliverables"]:
            metadata["deliverables_count"] = len(state["deliverables"])
            metadata["deliverables_ready"] = any(
                deliverable.get("status") == "ready" 
                for deliverable in state["deliverables"].values()
            )
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting state metadata: {str(e)}", exc_info=True)
        return {
            "current_stage": state.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

def update_coordination_metadata(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates coordination metadata in the state.
    
    Args:
        state: Current state dictionary
        updates: New metadata values to update
        
    Returns:
        Dict[str, Any]: Updated state dictionary
    """
    try:
        # Make a copy of the state to avoid modifying the original
        updated_state = state.copy()
        
        # Ensure coordination_metadata exists
        if "coordination_metadata" not in updated_state:
            updated_state["coordination_metadata"] = {}
        
        # Update metadata
        updated_state["coordination_metadata"].update(updates)
        
        # Always update the last_updated timestamp
        updated_state["coordination_metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error updating coordination metadata: {str(e)}", exc_info=True)
        return state  # Return original state if update fails