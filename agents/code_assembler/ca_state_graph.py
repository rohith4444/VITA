from typing import TypedDict, Dict, List, Any, Optional
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("code_assembler.state_graph")

@trace_class
class CodeAssemblerGraphState(TypedDict):
    """
    Defines the state structure for CodeAssembler's workflow.
    
    Attributes:
        input (Dict[str, Any]): Initial input containing project details and collected components
        components (Dict[str, Dict[str, Any]]): Dictionary of collected components by ID
        dependency_graph (Dict[str, Any]): Graph of component dependencies
        file_structure (Dict[str, Any]): Planned file and directory structure
        validation_results (Dict[str, Any]): Results of structure validation
        integration_plan (Dict[str, Any]): Plan for integrating components
        compiled_project (Dict[str, Any]): Final compiled project information
        config_files (Dict[str, Any]): Generated configuration files
        output_location (str): Location of the assembled project
        status (str): Current workflow status
    """
    input: Dict[str, Any]
    components: Dict[str, Dict[str, Any]]
    dependency_graph: Dict[str, Any]
    file_structure: Dict[str, Any]
    validation_results: Dict[str, Any]
    integration_plan: Dict[str, Any]
    compiled_project: Dict[str, Any]
    config_files: Dict[str, Any]
    output_location: str
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
            "initialized": ["input", "components", "status"],
            "analyzing_dependencies": ["input", "components", "status"],
            "planning_structure": ["input", "components", "dependency_graph", "status"],
            "validating_structure": ["input", "components", "dependency_graph", "file_structure", "status"],
            "integrating_components": ["input", "components", "dependency_graph", "file_structure", "validation_results", "status"],
            "generating_configs": ["input", "components", "dependency_graph", "file_structure", "validation_results", "integration_plan", "status"],
            "compiling_project": ["input", "components", "dependency_graph", "file_structure", "validation_results", "integration_plan", "config_files", "status"],
            "completed": ["input", "components", "dependency_graph", "file_structure", "validation_results", "integration_plan", "config_files", "compiled_project", "output_location", "status"]
        }
        
        # Get current stage from status
        current_stage = state.get("status", "initialized")
        required_keys = stage_requirements.get(current_stage, ["input", "components", "status"])
        
        # Check for required keys
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise KeyError(f"Missing required keys for stage {current_stage}: {missing_keys}")
        
        # Validate types based on stage
        if "input" in state and not isinstance(state["input"], dict):
            raise TypeError("'input' must be a dictionary")
            
        if "components" in state and not isinstance(state["components"], dict):
            raise TypeError("'components' must be a dictionary")
            
        if "dependency_graph" in state and not isinstance(state["dependency_graph"], dict):
            raise TypeError("'dependency_graph' must be a dictionary")
            
        if "file_structure" in state and not isinstance(state["file_structure"], dict):
            raise TypeError("'file_structure' must be a dictionary")
            
        if "validation_results" in state and not isinstance(state["validation_results"], dict):
            raise TypeError("'validation_results' must be a dictionary")
            
        if "integration_plan" in state and not isinstance(state["integration_plan"], dict):
            raise TypeError("'integration_plan' must be a dictionary")
            
        if "compiled_project" in state and not isinstance(state["compiled_project"], dict):
            raise TypeError("'compiled_project' must be a dictionary")
            
        if "config_files" in state and not isinstance(state["config_files"], dict):
            raise TypeError("'config_files' must be a dictionary")
            
        if "output_location" in state and not isinstance(state["output_location"], str):
            raise TypeError("'output_location' must be a string")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        input_data: Initial input containing project details and collected components
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": input_data,
            "components": input_data.get("components", {}),
            "dependency_graph": {},
            "file_structure": {},
            "validation_results": {},
            "integration_plan": {},
            "compiled_project": {},
            "config_files": {},
            "output_location": "",
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
        "initialized": "analyzing_dependencies",
        "analyzing_dependencies": "planning_structure",
        "planning_structure": "validating_structure",
        "validating_structure": "integrating_components",
        "integrating_components": "generating_configs",
        "generating_configs": "compiling_project",
        "compiling_project": "completed"
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
            
        # Special case transitions
        if current_stage == "validating_structure" and target_stage == "planning_structure":
            # Allow going back to planning if validation failed
            validation_results = state.get("validation_results", {})
            has_errors = validation_results.get("has_errors", False)
            
            # Allow transition if there are validation errors
            return has_errors
            
        # Can always restart dependency analysis
        if target_stage == "analyzing_dependencies":
            return True
            
        # Allow returning to integration from config generation if needed
        if current_stage == "generating_configs" and target_stage == "integrating_components":
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
        components = state.get("components", {})
        
        metadata = {
            "current_stage": current_stage,
            "next_stage": get_next_stage(current_stage),
            "component_count": len(components),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add validation status if available
        if "validation_results" in state:
            validation_results = state["validation_results"]
            metadata["validation_status"] = {
                "has_errors": validation_results.get("has_errors", False),
                "error_count": validation_results.get("error_count", 0),
                "warning_count": validation_results.get("warning_count", 0)
            }
            
        # Add compilation status if available
        if "compiled_project" in state and state["compiled_project"]:
            metadata["is_compiled"] = True
            metadata["output_location"] = state.get("output_location", "")
            
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting state metadata: {str(e)}", exc_info=True)
        return {
            "current_stage": state.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }