from core.logging.logger import setup_logger
from typing import Dict, Any, List
from core.tracing.service import trace_method


logger = setup_logger("tools.project_manager.timeline")



@trace_method
def estimate_time(milestones: List[Dict[str, Any]], num_developers: int) -> int:
    """
    Estimate total project time based on workload.
    
    Args:
        milestones: List of project milestones with tasks
        num_developers: Number of available developers
        
    Returns:
        int: Estimated time in minutes
    """
    logger.info(f"Estimating timeline for {num_developers} developers")
    
    if not milestones or num_developers < 1:
        logger.error("Invalid input parameters")
        return 0

    try:
        effort_mapping = {"LOW": 5, "MEDIUM": 10, "HIGH": 15}
        total_effort = sum(
            effort_mapping[task["effort"]] 
            for milestone in milestones 
            for task in milestone["tasks"]
        )

        estimated_time = total_effort // num_developers
        logger.info(f"Total effort: {total_effort}, Estimated time: {estimated_time} minutes")
        
        return estimated_time
        
    except Exception as e:
        logger.error(f"Error estimating timeline: {str(e)}", exc_info=True)
        return 0