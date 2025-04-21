from typing import List
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("llm.prompts")
logger.info("Initializing LLM prompts module")

@trace_method
def format_requirement_analysis_prompt(project_description: str) -> str:
    """
    Format the prompt for analyzing and restructuring user input.
    
    Args:
        project_description: Raw project description from user
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting requirement analysis prompt")
    try:
        logger.debug(f"Project description length: {len(project_description)} chars")
        logger.debug(f"Project description preview: {project_description[:100]}...")

        formatted_prompt = f"""
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
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Requirement analysis prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting requirement analysis prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_project_plan_prompt(problem_statement: str, features: List[str]) -> str:
    """
    Format the prompt for generating a milestone-based project plan.
    
    Args:
        problem_statement: Structured problem description
        features: List of key project features
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting project plan prompt")
    try:
        logger.debug(f"Problem statement length: {len(problem_statement)} chars")
        logger.debug(f"Number of features: {len(features)}")
        
        formatted_prompt = f"""
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
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Project plan prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting project plan prompt: {str(e)}", exc_info=True)
        raise

logger.info("LLM prompts module initialized successfully")