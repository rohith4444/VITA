from core.logging.logger import setup_logger
from typing import Dict, Any, List
from core.tracing.service import trace_method



logger = setup_logger("tools.project_manager.resource_allocator")

# Define agent capabilities
AGENTS = {
    "Solution Architect": ["architecture", "database design"],
    "Full Stack Developer": ["backend", "frontend", "API development"],
    "QA/Test Agent": ["test", "quality assurance"]
}

@trace_method
def allocate_resources(milestones: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Assign tasks to the most suitable agents.
    
    Args:
        milestones: List of project milestones with tasks
        
    Returns:
        Dict[str, List[str]]: Agent to task ID mappings
    """
    logger.info("Starting resource allocation")
    
    if not milestones:
        logger.warning("No milestones provided for resource allocation")
        return {agent: [] for agent in AGENTS.keys()}

    try:
        allocation = {agent: [] for agent in AGENTS.keys()}
        unassigned_tasks = []

        for milestone in milestones:
            for task in milestone["tasks"]:
                assigned = False
                for agent, skills in AGENTS.items():
                    if any(skill in task["name"].lower() for skill in skills):
                        allocation[agent].append(task["id"])
                        assigned = True
                        break
                
                if not assigned:
                    unassigned_tasks.append(task["id"])

        if unassigned_tasks:
            logger.warning(f"Unassigned tasks: {unassigned_tasks}")

        logger.info(f"Completed resource allocation for {sum(len(tasks) for tasks in allocation.values())} tasks")
        return allocation
        
    except Exception as e:
        logger.error(f"Error during resource allocation: {str(e)}", exc_info=True)
        return {agent: [] for agent in AGENTS.keys()}