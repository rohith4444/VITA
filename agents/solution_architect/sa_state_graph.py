from typing import TypedDict, Dict, Any, List, Optional
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
    """
    input: str
    project_plan: Dict[str, Any]
    tech_stack: Dict[str, List[str]]
    architecture_design: Dict[str, Any]
    validation_results: Dict[str, Any]
    specifications: Dict[str, Any]
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
            "initialized": ["input", "project_plan", "status"],
            "analyzing_requirements": ["input", "project_plan", "status"],
            "selecting_tech_stack": ["input", "project_plan", "status"],
            "designing_architecture": ["input", "project_plan", "tech_stack", "status"],
            "validating_architecture": ["input", "project_plan", "tech_stack", "architecture_design", "status"],
            "generating_specifications": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "status"],
            "completed": ["input", "project_plan", "tech_stack", "architecture_design", "validation_results", "specifications", "status"]
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
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(project_description: str, project_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        project_description: Initial project description
        project_plan: Project plan from Project Manager
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": project_description,
            "project_plan": project_plan,
            "tech_stack": {},
            "architecture_design": {},
            "validation_results": {},
            "specifications": {},
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
        "analyzing_requirements": "selecting_tech_stack",
        "selecting_tech_stack": "designing_architecture",
        "designing_architecture": "validating_architecture", 
        "validating_architecture": "generating_specifications",
        "generating_specifications": "completed"
    }
    
    return stage_flow.get(current_stage, "completed")