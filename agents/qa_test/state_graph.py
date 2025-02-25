from typing import TypedDict, Dict, List, Any, Optional
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("qa_test.state_graph")

@trace_class
class QATestGraphState(TypedDict):
    """
    Defines the state structure for QA/Test Agent's workflow.
    
    Attributes:
        input (str): Raw project description/requirements
        code (Dict[str, Any]): Code to be tested, organized by components
        specifications (Dict[str, Any]): Technical specifications from Solution Architect
        test_requirements (Dict[str, Any]): Analyzed test requirements
        test_plan (Dict[str, Any]): Test planning details
        test_cases (Dict[str, Any]): Generated test cases
        status (str): Current workflow status
    """
    input: str
    code: Dict[str, Any]
    specifications: Dict[str, Any]
    test_requirements: Dict[str, Any]
    test_plan: Dict[str, Any]
    test_cases: Dict[str, Any]
    test_code: Dict[str, str]
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
            "initialized": ["input", "code", "specifications", "status"],
            "analyzing_requirements": ["input", "code", "specifications", "status"],
            "planning_tests": ["input", "code", "specifications", "test_requirements", "status"],
            "generating_test_cases": ["input", "code", "specifications", "test_requirements", "test_plan", "status"],
            "completed": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "status"]
        }
        
        # Get current stage from status
        current_stage = state.get("status", "initialized")
        required_keys = stage_requirements.get(current_stage, ["input", "code", "specifications", "status"])
        
        # Check for required keys
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise KeyError(f"Missing required keys for stage {current_stage}: {missing_keys}")
        
        # Validate types based on stage
        if "input" in state and not isinstance(state["input"], str):
            raise TypeError("'input' must be a string")
            
        if "code" in state and not isinstance(state["code"], dict):
            raise TypeError("'code' must be a dictionary")
            
        if "specifications" in state and not isinstance(state["specifications"], dict):
            raise TypeError("'specifications' must be a dictionary")
            
        if "test_requirements" in state and not isinstance(state["test_requirements"], dict):
            raise TypeError("'test_requirements' must be a dictionary")
            
        if "test_plan" in state and not isinstance(state["test_plan"], dict):
            raise TypeError("'test_plan' must be a dictionary")
            
        if "test_cases" in state and not isinstance(state["test_cases"], dict):
            raise TypeError("'test_cases' must be a dictionary")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(input_description: str, code: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        input_description: Initial project description
        code: Code to be tested
        specifications: Technical specifications
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": input_description,
            "code": code,
            "specifications": specifications,
            "test_requirements": {},
            "test_plan": {},
            "test_cases": {},
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
        "analyzing_requirements": "planning_tests",
        "planning_tests": "generating_test_cases",
        "generating_test_cases": "completed"
    }
    
    return stage_flow.get(current_stage, "completed")