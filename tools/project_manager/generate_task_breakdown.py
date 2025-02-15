import json
from core.logging.logger import setup_logger
from typing import Dict, Any, List
from agents.core.llm.service import LLMService
from agents.core.llm.prompts import format_project_plan_prompt
from .task_estimator import estimate_task_complexity

logger = setup_logger("generate_task_breakdown")

async def generate_task_breakdown(problem_statement: str, features: List[str], llm_service: LLMService) -> List[Dict[str, Any]]:
    """
    Generate a structured task breakdown using LLM and refine tasks with heuristics.
    """
    logger.info("Generating structured task breakdown using LLM")
    
    try:
        # Step 1: Format the LLM prompt
        prompt = format_project_plan_prompt(problem_statement, features)

        # Step 2: Call LLM to generate milestone-based tasks
        response = await llm_service.generate_project_plan(prompt)
        
        logger.debug(f"LLM Task Breakdown Response: {response}")

        # Step 3: Process LLM response
        plan = json.loads(response)

        milestones = []
        for milestone in plan["milestones"]:
            tasks = []
            for task in milestone["tasks"]:
                tasks.append({
                    "id": task["id"],
                    "name": task["name"],
                    "dependencies": task.get("dependencies", []),
                    "effort": estimate_task_complexity(task["name"]),
                })
            milestones.append({"name": milestone["name"], "tasks": tasks})

        logger.info("Task breakdown successfully generated and refined.")
        return milestones

    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response for task breakdown")
        return []

    except Exception as e:
        logger.error(f"Error generating task breakdown: {str(e)}")
        return []
