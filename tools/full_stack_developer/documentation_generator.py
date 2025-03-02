from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.full_stack_developer.llm.service import LLMService

# Initialize logger
logger = setup_logger("tools.full_stack_developer.documentation_generator")

@trace_method
async def generate_documentation(
    task_specification: str,
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any],
    generated_code: Dict[str, Dict[str, str]],
    llm_service: LLMService
) -> Dict[str, str]:
    """
    Generate project documentation for the implemented solution.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Technical design for all components
        generated_code: Generated code files
        llm_service: LLM service for documentation generation
        
    Returns:
        Dict[str, str]: Dictionary mapping document names to their content
        
    Raises:
        ValueError: If LLM returns empty documentation
        Exception: If documentation generation fails
    """
    logger.info("Starting documentation generation process")
    
    # Use LLM service to generate documentation
    documentation = await llm_service.generate_documentation(
        task_specification=task_specification,
        requirements=requirements,
        solution_design=solution_design,
        generated_code=generated_code
    )
    
    if not documentation:
        logger.error("LLM returned empty documentation")
        raise ValueError("LLM returned empty documentation")
    
    logger.info(f"Successfully generated {len(documentation)} documentation files")
    return documentation