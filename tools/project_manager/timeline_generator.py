from core.logging.logger import setup_logger
from typing import Dict, Any, List

logger = setup_logger("timeline_generator")

def estimate_time(milestones: List[Dict[str, Any]], num_developers: int) -> int:
    """Estimate total project time based on workload."""
    total_effort = sum(5 if task["effort"] == "LOW" else 10 if task["effort"] == "MEDIUM" else 15 for milestone in milestones for task in milestone["tasks"])

    estimated_time = total_effort // num_developers
    logger.info(f"Estimated time for {num_developers} developers: {estimated_time} minutes")
    
    return estimated_time
