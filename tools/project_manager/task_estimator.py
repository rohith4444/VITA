from core.logging.logger import setup_logger
from typing import Literal
from core.tracing.service import trace_method


logger = setup_logger("tools.project_manager.task_estimator")

EffortLevel = Literal["LOW", "MEDIUM", "HIGH"]


@trace_method
def estimate_task_complexity(task_name: str) -> EffortLevel:
    """
    Determine task complexity based on heuristics.
    
    Args:
        task_name: Name of the task
        
    Returns:
        EffortLevel: Estimated complexity level
    """
    logger.info(f"Estimating complexity for task: {task_name}")
    
    if not task_name:
        logger.warning("Empty task name provided")
        return "LOW"

    try:
        task_lower = task_name.lower()
        
        if any(keyword in task_lower for keyword in ["authentication", "database", "security"]):
            logger.debug(f"Task '{task_name}' estimated as HIGH complexity")
            return "HIGH"
        elif any(keyword in task_lower for keyword in ["ui", "frontend", "api"]):
            logger.debug(f"Task '{task_name}' estimated as MEDIUM complexity")
            return "MEDIUM"
        else:
            logger.debug(f"Task '{task_name}' estimated as LOW complexity")
            return "LOW"
            
    except Exception as e:
        logger.error(f"Error estimating task complexity: {str(e)}", exc_info=True)
        return "LOW"