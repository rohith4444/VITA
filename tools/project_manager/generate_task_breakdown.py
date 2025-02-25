import json
from core.logging.logger import setup_logger
from typing import Dict, Any, List, Optional
from agents.project_manager.llm.service import LLMService
from agents.project_manager.llm.prompts import format_project_plan_prompt
from .task_estimator import estimate_task_complexity
from core.tracing.service import trace_method



logger = setup_logger("tools.project_manager.task_breakdown")

@trace_method
async def generate_task_breakdown(
    problem_statement: str, 
    features: List[str], 
    llm_service: LLMService
) -> List[Dict[str, Any]]:
    """
    Generate a structured task breakdown using LLM and refine tasks with heuristics.
    
    Args:
        problem_statement: Project description
        features: List of project features
        llm_service: LLM service instance
        
    Returns:
        List[Dict[str, Any]]: List of milestones with tasks
    """
    logger.info("Starting task breakdown generation")
    
    if not problem_statement or not features:
        logger.error("Invalid input: empty problem statement or features")
        return []
    
    try:
        # Step 1: Format the LLM prompt
        prompt = format_project_plan_prompt(problem_statement, features)
        logger.debug(f"Generated prompt length: {len(prompt)}")

        # Step 2: Call LLM to generate milestone-based tasks
        response = await llm_service.generate_project_plan(problem_statement, features)
        logger.debug("Received LLM response")

        # Step 3: Process response - no need for json.loads since response is already a dict
        if isinstance(response, dict) and 'milestones' in response:
            milestones = []
            for milestone in response["milestones"]:
                tasks = []
                for task in milestone["tasks"]:
                    tasks.append({
                        "id": task["id"],
                        "name": task["name"],
                        "dependencies": task.get("dependencies", []),
                        "effort": estimate_task_complexity(task["name"]),
                    })
                milestones.append({
                    "name": milestone["name"], 
                    "tasks": tasks
                })

            logger.info(f"Generated {len(milestones)} milestones with {sum(len(m['tasks']) for m in milestones)} tasks")
            return milestones
        else:
            logger.error("Response missing milestones key or invalid format")
            return []

    except Exception as e:
        logger.error(f"Error generating task breakdown: {str(e)}", exc_info=True)
        return []