from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("llm.prompts")
logger.info("Initializing LLM prompts")

def format_analysis_prompt(features, timeline, constraints):
    """Format the requirement analysis prompt."""
    logger.debug(f"Formatting analysis prompt with: features={features}, timeline={timeline}")
    return REQUIREMENT_ANALYSIS_TEMPLATE.format(
        features=features,
        timeline=timeline,
        constraints=constraints
    )

def format_task_prompt(scope, features, constraints):
    """Format the task breakdown prompt."""
    logger.debug(f"Formatting task prompt with: scope={scope}, features={features}")
    return TASK_BREAKDOWN_TEMPLATE.format(
        scope=scope,
        features=features,
        constraints=constraints
    )

# Prompt Templates
REQUIREMENT_ANALYSIS_TEMPLATE = """
Analyze the following project requirements for a task management application:

Features:
{features}

Timeline:
{timeline}

Constraints:
{constraints}

Please provide a structured analysis including:
1. Understanding of core requirements
2. Technical considerations and architecture recommendations
3. Potential risks and challenges
4. Suggested additional features or improvements
5. Resource requirements and skill sets needed
6. Timeline feasibility assessment

Format your response as a JSON object with the following structure:
{
    "understood_requirements": [],
    "technical_considerations": [],
    "potential_risks": [],
    "suggested_features": [],
    "resource_requirements": [],
    "timeline_assessment": {
        "feasible": boolean,
        "concerns": [],
        "recommendations": []
    }
}
"""

TASK_BREAKDOWN_TEMPLATE = """
Based on the following project analysis, provide a detailed task breakdown for a task management application:

Scope:
{scope}

Features:
{features}

Constraints:
{constraints}

Please break down the implementation into detailed tasks, including:
1. Task name and description
2. Estimated duration
3. Dependencies
4. Required skills
5. Priority level
6. Complexity assessment

Format your response as a JSON array of task objects with the following structure:
[
    {
        "id": "string",
        "name": "string",
        "description": "string",
        "duration_days": number,
        "dependencies": ["task_ids"],
        "required_skills": ["skill_names"],
        "priority": "HIGH|MEDIUM|LOW",
        "complexity": "HIGH|MEDIUM|LOW"
    }
]
"""

RISK_ASSESSMENT_TEMPLATE = """
Analyze the potential risks for the following project aspects:

Technical Stack:
{tech_stack}

Features:
{features}

Timeline:
{timeline}

Please provide a comprehensive risk assessment including:
1. Technical risks
2. Timeline risks
3. Resource risks
4. Integration risks
5. Security risks
6. Scalability risks

Format your response as a JSON array of risk objects.
"""

logger.info("LLM prompts initialized successfully")