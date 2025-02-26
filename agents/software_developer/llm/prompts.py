from typing import List
from core.logging.logger import setup_logger

# Initialize module logger
logger = setup_logger("llm.prompts")
logger.info("Initializing LLM prompts module")

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

def format_tech_stack_prompt(problem_statement: str) -> str:
    logger.debug("Formating tech stack query")
    try:
        formatted_prompt = f"""
        The following is a user-provided project request:

            "{problem_statement}"

            Please analyze and **rewrite it in a structured, professional format** suitable for technical development.

            Then, **extract and list** all core features, breaking them into logical components.

            Additionally, identify:
            - **Tech Stack Preferences** (if mentioned)
            - **Key Functionalities** (what the project should do)
            - **Dependencies & Constraints** (e.g., database, APIs, frameworks)

            Format the response as a **JSON object**:
            {
                "structured_requirements": "<Professional version of the project request>",
                "features": ["Feature 1", "Feature 2", ...],
                "tech_stack": {
                    "frontend": "<If specified>",
                    "backend": "<If specified>",
                    "database": "<If specified>",
                    "other": ["Any other relevant technologies"]
                }
            }
        """
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Requirement analysis prompt formatted successfully")
    except Exception as e:
        logger.error(f"Error formatting requirement analysis prompt: {str(e)}", exc_info=True)
        raise

def format_frontend_prompt(requirements: list, tech_stack: str) -> str:
    logger.debug("Formating frontend query")
    try:
        return f"""
        The following is a list of user-provided project requirements:

        "{requirements}"

        Each requirement describes a **feature** that needs a frontend implementation using **"{tech_stack}"**.

        ### **Task:**
        1. **Analyze and structure** each requirement into a professional and development-ready format.
        2. **Generate a frontend component** for each feature using {tech_stack}.
        3. **Ensure modularity**, following best practices for reusable and maintainable UI components.
        4. **Include relevant hooks, event handlers, and state management logic** if applicable.

        ### **Response Format (JSON)**
        {
            "structured_requirements": [
                {
                    "requirement": "<Professionalized version of requirement>",
                    "component_name": "<Suggested component name>",
                    "frontend_code": "<Generated code using {frontend_technology}>"
                },
                ...
            ]
        }
        """
    except Exception as e:
        logger.error(f"Error formatting requirement analysis prompt: {str(e)}", exc_info=True)
        raise

def format_backend_prompt(requirements: list, tech_stack: str) -> str:
    logger.debug("Formating backend query")
    try:
        return f"""
            The following is a list of user-provided project requirements:

            {requirements}

            Each requirement describes a **feature** that needs a corresponding **backend service** using the specified technology stack:

            **Tech Stack:**
            - **Framework:** {tech_stack}
            - **Database:** mysql
            - **Authentication (if required):** JWT authentication

            ### **Task:**
            1. **Analyze and structure** each requirement into a professional and development-ready format.
            2. **Define API endpoints** for the backend service, including request and response formats.
            3. **Implement business logic and service methods** based on the requirement.
            4. **Ensure best practices** for security, scalability, and error handling.
            5. **If authentication is required, integrate it using JWT authentication**.

            ### **Response Format (JSON)**
            {
                "structured_requirements": [
                    {
                        "requirement": "<Professionalized version of requirement>",
                        "service_name": "<Suggested service name>",
                        "api_endpoints": [
                            {
                                "method": "<GET/POST/PUT/DELETE>",
                                "endpoint": "<API route>",
                                "request_body": "<Expected request structure>",
                                "response_body": "<Expected response structure>"
                            }
                        ],
                        "service_code": "<Generated service code using {tech_stack}>"
                    },
                    ...
                ]
            }
            """

    except Exception as e:
        logger.error(f"Error formatting requirement analysis prompt: {str(e)}", exc_info=True)
        raise

def format_database_prompt(requirements: list, tech_stack: str) -> str:
    logger.debug("Formating database query")
    try:
        return f"""
            The following is a list of user-provided project requirements:

            {requirements}

            Each requirement describes a **feature** that needs a corresponding **database service** using **{tech_stack}**.

            ### **Task:**
            1. **Analyze and structure** each requirement into a professional and development-ready format.
            2. **Design the database schema** for storing and managing the required data.
            3. **Generate database service code** for CRUD operations using {tech_stack}.
            4. **Ensure best practices** for indexing, relationships, transactions, and security.

            ### **Response Format (JSON)**
            {
                "structured_requirements": [
                    {
                        "requirement": "<Professionalized version of requirement>",
                        "table_name": "<Suggested table/collection name>",
                        "schema": "<Database schema definition>",
                        "service_code": "<Generated service code using {tech_stack}>"
                    },
                    ...
                ]
            }
        """
    except Exception as e:
        logger.error(f"Error formatting requirement analysis prompt: {str(e)}", exc_info=True)
        raise

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