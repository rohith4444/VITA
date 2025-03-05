from typing import TypedDict, Dict, List, Any, Optional
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
    """
    input: str
    requirements: Dict[str, Any]
    solution_design: Dict[str, Any]
    generated_code: Dict[str, Dict[str, str]]
    documentation: Dict[str, str]
    status: str

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
            "completed": ["input", "requirements", "solution_design", "generated_code", "documentation", "status"]
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
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(task_specification: str) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        task_specification: Initial task specification
        
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
        "analyzing_requirements": "designing_solution",
        "designing_solution": "generating_code",
        "generating_code": "preparing_documentation",
        "preparing_documentation": "completed"
    }
    
    return stage_flow.get(current_stage, "completed")