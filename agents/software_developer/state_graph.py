from typing import TypedDict, List
from core.logging.logger import setup_logger

# Initialize logger at module level
logger = setup_logger("software_developer_state_graph")
logger.info("Initializing Software Developer State Graph module")

class SoftwareDeveloperGraphState(TypedDict):
    """A dictionary representing the state of a software developer in the state graph."""

    project_description: str
    input: str
    requirements: dict
    tech_stack: dict
    front_end: List[dict]
    back_end: List[dict]
    database: List[dict]
    status: str

def validate_state(state: SoftwareDeveloperGraphState) -> bool:
    """
    Validates the state dictionary structure and types.
    
    Args:
        state: The state dictionary to validate.
        
    Returns:
        bool: True if valid, raises exception if invalid.
    """
    logger.debug("Starting state validation")
    try:
        required_keys = {'project_description', 'input', 'requirements', 'tech_stack', 'front_end', 
                        'back_end', 'database', 'status'}
        
        # Check for missing keys
        missing_keys = required_keys - set(state.keys())
        if missing_keys:
            logger.error(f"State validation failed: missing keys {missing_keys}")
            raise KeyError(f"Missing required keys: {missing_keys}")
        
        # Type validation
        type_checks = [
            ('project_description', str),
            ('input', str),
            ('requirements', dict),
            ('tech_stack', dict),
            ('front_end', list),
            ('back_end', list),
            ('database', list),
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