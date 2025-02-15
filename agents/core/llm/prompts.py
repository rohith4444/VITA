from core.logging.logger import setup_logger
from typing import Dict, Any, List

# Initialize logger
logger = setup_logger("llm.prompts")
logger.info("Initializing LLM prompts")

def format_requirement_analysis_prompt(project_description: str) -> str:
    """Format the prompt for analyzing and restructuring user input."""
    logger.debug(f"Formatting requirement analysis prompt for description: {project_description}")

    return f"""
    The user has provided the following unstructured project request:

    "{project_description}"

    Please rewrite this in a professional and structured way so that AI agents can understand it better.
    Then, extract and list the core features of the project.

    Format the response as a JSON object with:
    {{
        "restructured_requirements": "<professionalized version of user input>",
        "features": ["Feature 1", "Feature 2", ...]
    }}
    """

def format_project_plan_prompt(problem_statement: str, features: List[str]) -> str:
    """Format the prompt for generating a milestone-based project plan."""
    logger.debug(f"Formatting project plan prompt for problem: {problem_statement}, features: {features}")

    return f"""
    Given the following problem statement:

    "{problem_statement}"

    And these key features:
    {features}

    Please generate a structured project plan that includes:
    - A list of major **milestones** required to build the system.
    - Step-by-step **tasks** under each milestone.
    - **Dependencies** between tasks.
    - **Effort level** (LOW, MEDIUM, HIGH) for each task.

    Format the response as a JSON object:
    {{
        "milestones": [
            {{
                "name": "Milestone Name",
                "tasks": [
                    {{"id": "1", "name": "Task Name", "dependencies": ["id"], "effort": "HIGH"}}
                ]
            }}
        ]
    }}
    """

logger.info("LLM prompts initialized successfully")