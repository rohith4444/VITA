from typing import TypedDict, List, Dict, Any
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("project_manager.state_graph")

class ProjectManagerGraphState(TypedDict):
    """
    Defines the state structure for ProjectManager's workflow.
    
    Attributes:
        input (str): Raw project description/requirements
        requirements (Dict[str, Any]): Structured requirements after analysis
        project_plan (Dict[str, Any]): Generated project plan
        status (str): Current workflow status
    """
    input: str
    requirements: Dict[str, Any]
    project_plan: Dict[str, Any]
    status: str

def validate_state(state: Dict[str, Any]) -> bool:
    """
    Validates state dictionary structure.
    
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
            "generating_project_plan": ["input", "requirements", "status"],
            "completed": ["input", "requirements", "project_plan", "status"]
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
            
        if "project_plan" in state and not isinstance(state["project_plan"], dict):
            raise TypeError("'project_plan' must be a dictionary")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(project_description: str) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        project_description: Initial project description
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": project_description,
            "status": "initialized"
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
        "analyzing_requirements": "generating_project_plan",
        "generating_project_plan": "completed"
    }
    
    return stage_flow.get(current_stage, "completed")