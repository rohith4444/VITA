from core.logging.logger import setup_logger
from typing import Dict, Any, List

logger = setup_logger("resource_allocator")

AGENTS = {
    "Solution Architect": ["architecture", "database design"],
    "Full Stack Developer": ["backend", "frontend", "API development"],
    "QA/Test Agent": ["test", "quality assurance"]
}

def allocate_resources(milestones: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Assign tasks to the most suitable agents."""
    logger.info("Allocating resources to tasks")

    allocation = {agent: [] for agent in AGENTS.keys()}

    for milestone in milestones:
        for task in milestone["tasks"]:
            for agent, skills in AGENTS.items():
                if any(skill in task["name"].lower() for skill in skills):
                    allocation[agent].append(task["id"])
                    break  # Assign only once

    logger.debug(f"Resource Allocation: {allocation}")
    return allocation
