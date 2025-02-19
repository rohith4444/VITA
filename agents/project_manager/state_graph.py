from typing import TypedDict, List
from core.logging.logger import setup_logger

# Initialize logger at module level
logger = setup_logger("project_manager.state_graph")
logger.info("Initializing Project Manager State Graph module")

class ProjectManagerGraphState(TypedDict):
    """
    Defines the state structure for ProjectManagerAgent's execution in LangGraph.
    
    Attributes:
        project_description (str): The raw project input provided by the user.
        requirements (dict): Structured requirements extracted from the project input.
        milestones (list): List of project milestones and tasks.
        resource_allocation (dict): Assigned resources for task execution.
        timeline_options (list): Different execution timelines for project completion.
        status (str): Current execution status of the project manager.
    """
    project_description: str
    requirements: dict
    milestones: List[dict]
    resource_allocation: dict
    timeline_options: List[dict]
    status: str

def validate_state(state: ProjectManagerGraphState) -> bool:
    """
    Validates the state dictionary structure and types.
    
    Args:
        state: The state dictionary to validate.
        
    Returns:
        bool: True if valid, raises exception if invalid.
    """
    logger.debug("Starting state validation")
    try:
        required_keys = {'project_description', 'requirements', 'milestones', 
                        'resource_allocation', 'timeline_options', 'status'}
        
        # Check for missing keys
        missing_keys = required_keys - set(state.keys())
        if missing_keys:
            logger.error(f"State validation failed: missing keys {missing_keys}")
            raise KeyError(f"Missing required keys: {missing_keys}")
        
        # Type validation
        type_checks = [
            ('project_description', str),
            ('requirements', dict),
            ('milestones', list),
            ('resource_allocation', dict),
            ('timeline_options', list),
            ('status', str)
        ]
        
        for field, expected_type in type_checks:
            if not isinstance(state[field], expected_type):
                logger.error(f"Type validation failed for {field}: expected {expected_type}, got {type(state[field])}")
                raise TypeError(f"'{field}' must be {expected_type}, got {type(state[field])}")
        
        logger.info("State validation successful")
        logger.debug(f"Current state status: {state['status']}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(project_description: str) -> ProjectManagerGraphState:
    """
    Creates an initial state dictionary with default values for ProjectManagerAgent.
    
    Args:
        project_description: The initial project description provided by the user.
        
    Returns:
        ProjectManagerGraphState: Initialized state dictionary.
    """
    logger.info("Creating initial project manager state")
    try:
        logger.debug(f"Initializing state with project description: {project_description[:100]}...")
        
        state: ProjectManagerGraphState = {
            'project_description': project_description,
            'requirements': {},
            'milestones': [],
            'resource_allocation': {},
            'timeline_options': [],
            'status': 'initialized'
        }
        
        # Validate the created state
        validate_state(state)
        
        logger.info("Initial state created and validated successfully")
        return state
        
    except Exception as e:
        logger.error(f"Failed to create initial state: {str(e)}", exc_info=True)
        raise