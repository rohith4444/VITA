from typing import TypedDict, Dict, List, Any, Optional, Union
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("qa_test.state_graph")

@trace_class
class QATestGraphState(TypedDict):
    """
    Defines the state structure for QA/Test Agent's workflow with Team Lead coordination.
    
    Attributes:
        input (str): Raw project description/requirements
        code (Dict[str, Any]): Code to be tested, organized by components
        specifications (Dict[str, Any]): Technical specifications from Solution Architect
        test_requirements (Dict[str, Any]): Analyzed test requirements
        test_plan (Dict[str, Any]): Test planning details
        test_cases (Dict[str, Any]): Generated test cases
        test_code (Dict[str, str]): Generated executable test code
        
        # Team Lead coordination attributes
        task_id (str): ID of the task assigned by Team Lead
        task_priority (str): Priority level assigned by Team Lead (HIGH/MEDIUM/LOW)
        components_to_test (Dict[str, Any]): Specific components that need testing
        dependencies (Dict[str, List[str]]): Component dependencies for integration testing
        coordination_metadata (Dict[str, Any]): Additional directives from Team Lead
        status_report (Dict[str, Any]): Progress report for Team Lead
        feedback (Dict[str, Any]): Feedback received from Team Lead
        
        status (str): Current workflow status
    """
    input: str
    code: Dict[str, Any]
    specifications: Dict[str, Any]
    test_requirements: Dict[str, Any]
    test_plan: Dict[str, Any]
    test_cases: Dict[str, Any]
    test_code: Dict[str, str]
    
    # Team Lead coordination fields
    task_id: str
    task_priority: str
    components_to_test: Dict[str, Any]
    dependencies: Dict[str, List[str]]
    coordination_metadata: Dict[str, Any]
    status_report: Dict[str, Any]
    feedback: Dict[str, Any]
    
    # Workflow status
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
            # Original workflow stages
            "initialized": ["input", "code", "specifications", "status"],
            "analyzing_requirements": ["input", "code", "specifications", "status"],
            "planning_tests": ["input", "code", "specifications", "test_requirements", "status"],
            "generating_test_cases": ["input", "code", "specifications", "test_requirements", "test_plan", "status"],
            "generating_test_code": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "status"],
            "completed": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "test_code", "status"],
            
            # Team Lead coordination stages
            "receiving_task": ["input", "code", "specifications", "task_id", "task_priority", "components_to_test", "status"],
            "processing_feedback": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "feedback", "status"],
            "reporting_results": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "test_code", "status_report", "status"],
            "awaiting_approval": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "test_code", "status_report", "status"],
            "updating_tests": ["input", "code", "specifications", "test_requirements", "test_plan", "test_cases", "feedback", "status"]
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
            
        if "test_code" in state and not isinstance(state["test_code"], dict):
            raise TypeError("'test_code' must be a dictionary")
            
        # Validate Team Lead coordination fields
        if "task_id" in state and not isinstance(state["task_id"], str):
            raise TypeError("'task_id' must be a string")
            
        if "task_priority" in state and not isinstance(state["task_priority"], str):
            raise TypeError("'task_priority' must be a string")
            
        if "components_to_test" in state and not isinstance(state["components_to_test"], dict):
            raise TypeError("'components_to_test' must be a dictionary")
            
        if "dependencies" in state and not isinstance(state["dependencies"], dict):
            raise TypeError("'dependencies' must be a dictionary")
            
        if "coordination_metadata" in state and not isinstance(state["coordination_metadata"], dict):
            raise TypeError("'coordination_metadata' must be a dictionary")
            
        if "status_report" in state and not isinstance(state["status_report"], dict):
            raise TypeError("'status_report' must be a dictionary")
            
        if "feedback" in state and not isinstance(state["feedback"], dict):
            raise TypeError("'feedback' must be a dictionary")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(
    input_description: str,
    code: Dict[str, Any],
    specifications: Dict[str, Any],
    task_id: Optional[str] = None,
    task_priority: Optional[str] = None,
    components_to_test: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates initial state for the workflow, with optional Team Lead directives.
    
    Args:
        input_description: Initial project description
        code: Code to be tested
        specifications: Technical specifications
        task_id: Optional task ID from Team Lead
        task_priority: Optional priority from Team Lead
        components_to_test: Optional specific components to test
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        # Determine initial status based on whether we're receiving from Team Lead
        initial_status = "receiving_task" if task_id else "initialized"
        
        state = {
            # Core testing fields
            "input": input_description,
            "code": code,
            "specifications": specifications,
            "test_requirements": {},
            "test_plan": {},
            "test_cases": {},
            "test_code": {},
            
            # Team Lead coordination fields with defaults
            "task_id": task_id or "",
            "task_priority": task_priority or "MEDIUM",
            "components_to_test": components_to_test or {},
            "dependencies": {},
            "coordination_metadata": {
                "received_timestamp": datetime.utcnow().isoformat(),
                "source": "team_lead" if task_id else "direct",
                "coordination_status": "active" if task_id else "independent"
            },
            "status_report": {},
            "feedback": {},
            
            # Workflow status
            "status": initial_status
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
    # Define workflow transitions including Team Lead coordination paths
    stage_flow = {
        # Original workflow path
        "initialized": "analyzing_requirements",
        "analyzing_requirements": "planning_tests",
        "planning_tests": "generating_test_cases",
        "generating_test_cases": "generating_test_code",
        "generating_test_code": "reporting_results",  # Changed to reporting instead of completed
        
        # Team Lead coordination paths
        "receiving_task": "analyzing_requirements",
        "processing_feedback": "updating_tests",
        "updating_tests": "generating_test_cases",
        "reporting_results": "awaiting_approval",
        "awaiting_approval": "completed"  # Terminal state
    }
    
    return stage_flow.get(current_stage, "completed")

def can_transition(state: Dict[str, Any], target_stage: str) -> bool:
    """
    Checks if transition to target stage is valid from current state.
    
    Args:
        state: Current state dictionary
        target_stage: Target stage to transition to
        
    Returns:
        bool: True if transition is valid, False otherwise
    """
    current_stage = state.get("status", "initialized")
    
    # Standard workflow transition check
    if get_next_stage(current_stage) == target_stage:
        return True
    
    # Special case transitions for coordination
    
    # Can go to processing_feedback from almost any stage if feedback received
    if target_stage == "processing_feedback" and state.get("feedback"):
        # Can only process feedback after initial requirements analysis
        return current_stage not in ["initialized", "receiving_task"]
    
    # Can go to reporting_results after test code is generated
    if target_stage == "reporting_results" and state.get("test_code"):
        return True
    
    # Can restart analysis due to changed requirements or feedback
    if target_stage == "analyzing_requirements" and state.get("feedback"):
        return True
    
    return False

def get_priority_factor(state: Dict[str, Any]) -> float:
    """
    Calculates a priority factor to adjust workflow based on task priority.
    
    Args:
        state: Current state dictionary
        
    Returns:
        float: Priority factor (higher means more thorough testing)
    """
    priority = state.get("task_priority", "MEDIUM")
    
    if priority == "HIGH":
        return 1.5  # More thorough testing
    elif priority == "LOW":
        return 0.8  # More focused, limited testing
    else:  # MEDIUM
        return 1.0  # Standard testing
        
def format_status_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats a status report for Team Lead based on current state.
    
    Args:
        state: Current state dictionary
        
    Returns:
        Dict[str, Any]: Formatted status report
    """
    # Extract progress information
    test_requirements = state.get("test_requirements", {})
    test_plan = state.get("test_plan", {})
    test_cases = state.get("test_cases", {})
    test_code = state.get("test_code", {})
    
    # Calculate completion metrics
    requirements_done = len(test_requirements.get("functional_test_requirements", [])) > 0
    plan_done = len(test_plan.get("unit_tests", [])) > 0
    cases_done = len(test_cases.get("unit_test_cases", [])) > 0
    code_done = len(test_code) > 0
    
    # Calculate overall completion percentage
    completion_steps = [requirements_done, plan_done, cases_done, code_done]
    completion_percentage = sum(1 for step in completion_steps if step) / len(completion_steps) * 100
    
    # Create report
    status_report = {
        "task_id": state.get("task_id", ""),
        "timestamp": datetime.utcnow().isoformat(),
        "completion_percentage": completion_percentage,
        "phase_status": {
            "requirements_analysis": "completed" if requirements_done else "pending",
            "test_planning": "completed" if plan_done else "pending",
            "test_case_generation": "completed" if cases_done else "pending",
            "test_code_generation": "completed" if code_done else "pending"
        },
        "metrics": {
            "functional_requirements": len(test_requirements.get("functional_test_requirements", [])),
            "integration_requirements": len(test_requirements.get("integration_test_requirements", [])),
            "unit_tests": len(test_plan.get("unit_tests", [])),
            "integration_tests": len(test_plan.get("integration_tests", [])),
            "unit_test_cases": len(test_cases.get("unit_test_cases", [])),
            "integration_test_cases": len(test_cases.get("integration_test_cases", [])),
            "test_files": len(test_code)
        },
        "issues": [],  # To be filled by agent
        "recommendations": []  # To be filled by agent
    }
    
    return status_report