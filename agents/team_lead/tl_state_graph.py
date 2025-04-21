from typing import TypedDict, Dict, List, Any, Optional
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("team_lead.state_graph")

@trace_class
class TeamLeadGraphState(TypedDict):
    """
    Defines the state structure for TeamLead's workflow.
    
    Attributes:
        input (str): Raw project description/requirements
        project_plan (Dict[str, Any]): Project plan from Project Manager
        tasks (List[Dict[str, Any]]): Broken down atomic tasks
        execution_plan (Dict[str, Any]): Coordinated execution plan for the project
        agent_assignments (Dict[str, List[Dict[str, Any]]]): Tasks assigned to specific agents
        progress (Dict[str, Any]): Current progress tracking information
        deliverables (Dict[str, Any]): Collected deliverables from agents
        compilation_result (Dict[str, Any]): Final compiled project result
        status (str): Current workflow status
        user_feedback (Optional[Dict[str, Any]]): Feedback received from user via Scrum Master
        milestone_delivery (Optional[Dict[str, Any]]): Milestone data prepared for user presentation
        user_query (Optional[Dict[str, Any]]): User question that needs technical response
    """
    input: str
    project_plan: Dict[str, Any]
    tasks: List[Dict[str, Any]]
    execution_plan: Dict[str, Any]
    agent_assignments: Dict[str, List[Dict[str, Any]]]
    progress: Dict[str, Any]
    deliverables: Dict[str, Any]
    compilation_result: Dict[str, Any]
    status: str
    user_feedback: Optional[Dict[str, Any]]
    milestone_delivery: Optional[Dict[str, Any]]
    user_query: Optional[Dict[str, Any]]

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
            "analyzing_tasks": ["input", "project_plan", "status"],
            "planning_execution": ["input", "project_plan", "tasks", "status"],
            "assigning_agents": ["input", "project_plan", "tasks", "execution_plan", "status"],
            "monitoring_progress": ["input", "project_plan", "tasks", "execution_plan", "agent_assignments", "progress", "status"],
            "collecting_deliverables": ["input", "project_plan", "tasks", "execution_plan", "agent_assignments", "progress", "deliverables", "status"],
            "compiling_results": ["input", "project_plan", "tasks", "execution_plan", "agent_assignments", "progress", "deliverables", "status"],
            "completed": ["input", "project_plan", "tasks", "execution_plan", "agent_assignments", "progress", "deliverables", "compilation_result", "status"],
            
            # New states for Scrum Master interaction
            "receive_user_feedback": ["input", "project_plan", "tasks", "user_feedback", "status"],
            "prepare_milestone_delivery": ["input", "project_plan", "tasks", "execution_plan", "progress", "milestone_delivery", "status"],
            "respond_to_user_query": ["input", "project_plan", "tasks", "user_query", "status"]
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
            
        if "tasks" in state and not isinstance(state["tasks"], list):
            raise TypeError("'tasks' must be a list")
            
        if "execution_plan" in state and not isinstance(state["execution_plan"], dict):
            raise TypeError("'execution_plan' must be a dictionary")
            
        if "agent_assignments" in state and not isinstance(state["agent_assignments"], dict):
            raise TypeError("'agent_assignments' must be a dictionary")
            
        if "progress" in state and not isinstance(state["progress"], dict):
            raise TypeError("'progress' must be a dictionary")
            
        if "deliverables" in state and not isinstance(state["deliverables"], dict):
            raise TypeError("'deliverables' must be a dictionary")
            
        if "compilation_result" in state and not isinstance(state["compilation_result"], dict):
            raise TypeError("'compilation_result' must be a dictionary")
            
        if not isinstance(state["status"], str):
            raise TypeError("'status' must be a string")
            
        # Validate new Scrum Master interaction states
        if "user_feedback" in state and state["user_feedback"] is not None and not isinstance(state["user_feedback"], dict):
            raise TypeError("'user_feedback' must be a dictionary")
            
        if "milestone_delivery" in state and state["milestone_delivery"] is not None and not isinstance(state["milestone_delivery"], dict):
            raise TypeError("'milestone_delivery' must be a dictionary")
            
        if "user_query" in state and state["user_query"] is not None and not isinstance(state["user_query"], dict):
            raise TypeError("'user_query' must be a dictionary")
            
        logger.info(f"State validation successful for stage: {current_stage}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(input_description: str, project_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates initial state for the workflow.
    
    Args:
        input_description: Initial project description
        project_plan: Project plan from Project Manager
        
    Returns:
        Dict[str, Any]: Initial state dictionary
    """
    logger.info("Creating initial state")
    
    try:
        state = {
            "input": input_description,
            "project_plan": project_plan,
            "tasks": [],
            "execution_plan": {},
            "agent_assignments": {},
            "progress": {
                "timestamp": datetime.utcnow().isoformat(),
                "completion_percentage": 0,
                "milestone_progress": [],
                "task_summary": {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "pending": 0
                }
            },
            "deliverables": {},
            "compilation_result": {},
            "status": "initialized",
            
            # Initialize new Scrum Master interaction fields
            "user_feedback": None,
            "milestone_delivery": None,
            "user_query": None
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
        "initialized": "analyzing_tasks",
        "analyzing_tasks": "planning_execution",
        "planning_execution": "assigning_agents",
        "assigning_agents": "monitoring_progress",
        "monitoring_progress": "collecting_deliverables",
        "collecting_deliverables": "compiling_results",
        "compiling_results": "completed",
        
        # New state flows for Scrum Master interaction
        "receive_user_feedback": "monitoring_progress",  # After processing feedback, return to monitoring
        "prepare_milestone_delivery": "monitoring_progress",  # After preparing milestone, return to monitoring
        "respond_to_user_query": "monitoring_progress"  # After responding to query, return to monitoring
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
        if current_stage == "monitoring_progress" and target_stage == "collecting_deliverables":
            # Check if there's enough progress to move to collecting deliverables
            progress = state.get("progress", {})
            completion_percentage = progress.get("completion_percentage", 0)
            
            # Allow transition if at least 50% complete
            return completion_percentage >= 50
            
        # Can always restart task analysis
        if target_stage == "analyzing_tasks":
            return True
            
        # Allow returning to progress monitoring from deliverable collection
        if current_stage == "collecting_deliverables" and target_stage == "monitoring_progress":
            return True
        
        # Scrum Master interaction state transitions
        # Can transition to receive user feedback from monitoring or collecting
        if target_stage == "receive_user_feedback" and current_stage in [
            "monitoring_progress", "collecting_deliverables"
        ]:
            return True
            
        # Can transition to prepare milestone delivery from monitoring or collecting
        if target_stage == "prepare_milestone_delivery" and current_stage in [
            "monitoring_progress", "collecting_deliverables"
        ]:
            return True
            
        # Can transition to respond to user query from any active state
        if target_stage == "respond_to_user_query" and current_stage not in [
            "initialized", "completed"
        ]:
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
        progress = state.get("progress", {})
        
        metadata = {
            "current_stage": current_stage,
            "next_stage": get_next_stage(current_stage),
            "completion_percentage": progress.get("completion_percentage", 0),
            "task_count": len(state.get("tasks", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if "agent_assignments" in state:
            metadata["assigned_agents"] = list(state["agent_assignments"].keys())
            
        if "deliverables" in state:
            metadata["deliverable_count"] = len(state["deliverables"])
            
        # Add metadata for Scrum Master interactions
        if "user_feedback" in state and state["user_feedback"]:
            metadata["has_user_feedback"] = True
            metadata["feedback_type"] = state["user_feedback"].get("type", "general")
            
        if "milestone_delivery" in state and state["milestone_delivery"]:
            metadata["has_milestone_delivery"] = True
            metadata["milestone_id"] = state["milestone_delivery"].get("id")
            
        if "user_query" in state and state["user_query"]:
            metadata["has_user_query"] = True
            metadata["query_type"] = state["user_query"].get("type", "general")
            
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting state metadata: {str(e)}", exc_info=True)
        return {
            "current_stage": state.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }