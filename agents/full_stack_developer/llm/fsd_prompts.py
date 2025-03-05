from typing import List, Dict, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("full_stack_developer.llm.prompts")
logger.info("Initializing Full Stack Developer LLM prompts module")

@trace_method
def format_requirements_analysis_prompt(task_specification: str) -> str:
    """
    Format the prompt for analyzing task requirements.
    
    Args:
        task_specification: Raw task specification from user
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting requirements analysis prompt")
    try:
        logger.debug(f"Task specification length: {len(task_specification)} chars")
        logger.debug(f"Task specification preview: {task_specification[:100]}...")

        formatted_prompt = f"""
        You are a senior full-stack developer with extensive experience in web and application development.
        Your task is to analyze the following requirement specification and extract key development requirements:

        TASK SPECIFICATION:
        "{task_specification}"

        Based on this specification, please provide:

        1. A structured analysis of the features required
        2. The technical constraints to consider
        3. Dependencies between components
        4. Technology recommendations for frontend, backend, and database
        5. Potential challenges and considerations

        Format your response as a JSON object with the following structure:
        {{
            "features": [
                {{
                    "name": "Feature name",
                    "description": "Brief description",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "technical_constraints": [
                {{
                    "constraint": "Description of constraint",
                    "impact": "How it affects development"
                }}
            ],
            "dependencies": [
                {{
                    "source": "Component that depends on another",
                    "target": "Component being depended on",
                    "description": "Nature of dependency"
                }}
            ],
            "technology_recommendations": {{
                "frontend": ["Technology 1", "Technology 2"],
                "backend": ["Technology 1", "Technology 2"],
                "database": ["Technology 1", "Technology 2"]
            }},
            "challenges": [
                {{
                    "challenge": "Potential challenge",
                    "mitigation": "Possible solution or approach"
                }}
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Requirements analysis prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting requirements analysis prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_solution_design_prompt(
    task_specification: str,
    requirements: Dict[str, Any],
    component: str  # "frontend", "backend", or "database"
) -> str:
    """
    Format the prompt for designing a specific component solution.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        component: Which component to design ("frontend", "backend", or "database")
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug(f"Formatting {component} solution design prompt")
    try:
        # Extract relevant information from requirements
        features = requirements.get("features", [])
        tech_recommendations = requirements.get("technology_recommendations", {})
        component_tech = tech_recommendations.get(component, [])
        
        # Format features list for prompt
        features_text = ""
        for idx, feature in enumerate(features, 1):
            features_text += f"""
            {idx}. {feature.get('name', 'Unnamed Feature')}
               Description: {feature.get('description', 'No description provided')}
               Priority: {feature.get('priority', 'MEDIUM')}
            """
        
        # Component-specific instructions
        if component == "frontend":
            component_instructions = """
            Please design the frontend architecture with:
            1. Component structure
            2. State management approach
            3. UI/UX considerations
            4. Routing structure
            5. Key libraries and frameworks
            6. Integration with backend
            """
            result_structure = """
            {
                "architecture": "Overall architecture pattern",
                "components": [
                    {
                        "name": "Component name",
                        "purpose": "Component purpose",
                        "subcomponents": ["Subcomponent 1", "Subcomponent 2"]
                    }
                ],
                "state_management": {
                    "approach": "Approach description",
                    "stores": ["Store 1", "Store 2"]
                },
                "routing": [
                    {
                        "path": "Route path",
                        "component": "Component to render",
                        "purpose": "Purpose of this route"
                    }
                ],
                "ui_frameworks": ["Framework 1", "Framework 2"],
                "api_integration": {
                    "approach": "Approach description",
                    "endpoints": ["Endpoint 1", "Endpoint 2"]
                },
                "file_structure": [
                    {
                        "path": "Path to file or directory",
                        "purpose": "Purpose of file or directory"
                    }
                ]
            }
            """
        elif component == "backend":
            component_instructions = """
            Please design the backend architecture with:
            1. API structure and endpoints
            2. Business logic organization
            3. Middleware components
            4. Authentication and authorization approach
            5. Key libraries and frameworks
            6. Data access layer
            """
            result_structure = """
            {
                "architecture": "Overall architecture pattern",
                "api_endpoints": [
                    {
                        "path": "Endpoint path",
                        "method": "HTTP method",
                        "purpose": "Purpose of endpoint",
                        "request_params": ["Param 1", "Param 2"],
                        "response_format": "Response description"
                    }
                ],
                "business_logic": {
                    "approach": "Approach description",
                    "modules": ["Module 1", "Module 2"]
                },
                "middleware": [
                    {
                        "name": "Middleware name",
                        "purpose": "Middleware purpose"
                    }
                ],
                "auth_approach": {
                    "strategy": "Authentication strategy",
                    "implementation": "Implementation details"
                },
                "frameworks": ["Framework 1", "Framework 2"],
                "data_access": {
                    "approach": "Approach description",
                    "models": ["Model 1", "Model 2"]
                },
                "file_structure": [
                    {
                        "path": "Path to file or directory",
                        "purpose": "Purpose of file or directory"
                    }
                ]
            }
            """
        else:  # database
            component_instructions = """
            Please design the database architecture with:
            1. Data models and schema
            2. Relationships between entities
            3. Indexing strategy
            4. Query optimization approach
            5. Migration and seeding strategy
            6. Database choice justification
            """
            result_structure = """
            {
                "database_type": "Type of database",
                "models": [
                    {
                        "name": "Model name",
                        "attributes": [
                            {
                                "name": "Attribute name",
                                "type": "Data type",
                                "constraints": ["Constraint 1", "Constraint 2"]
                            }
                        ]
                    }
                ],
                "relationships": [
                    {
                        "source": "Source model",
                        "target": "Target model",
                        "type": "Relationship type",
                        "description": "Relationship description"
                    }
                ],
                "indexing_strategy": [
                    {
                        "model": "Model name",
                        "fields": ["Field 1", "Field 2"],
                        "purpose": "Purpose of index"
                    }
                ],
                "optimization": {
                    "strategies": ["Strategy 1", "Strategy 2"],
                    "considerations": ["Consideration 1", "Consideration 2"]
                },
                "migrations": {
                    "approach": "Migration approach",
                    "tooling": "Migration tooling"
                },
                "schema_diagram": "Textual representation of schema"
            }
            """

        formatted_prompt = f"""
        You are a senior full-stack developer with extensive experience in {component} development.
        Your task is to design the {component} component based on the following specifications:

        TASK SPECIFICATION:
        "{task_specification}"

        REQUIRED FEATURES:
        {features_text}

        RECOMMENDED TECHNOLOGIES:
        {', '.join(component_tech) if component_tech else 'No specific recommendations, choose appropriate technologies'}

        {component_instructions}

        Format your response as a JSON object with the following structure:
        {result_structure}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info(f"{component.capitalize()} solution design prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting {component} solution design prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_code_generation_prompt(
    task_specification: str,
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any],
    component: str  # "frontend", "backend", or "database"
) -> str:
    """
    Format the prompt for generating code for a specific component.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Design details for the component
        component: Which component to generate code for
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug(f"Formatting {component} code generation prompt")
    try:
        # Extract component-specific design
        component_design = solution_design.get(component, {})
        
        if component == "frontend":
            file_types = """
            1. Component files (e.g., React components, Vue components)
            2. Styling files (CSS, SCSS, styled-components)
            3. State management files (store, reducers, actions)
            4. Routing configuration
            5. Utility/helper functions
            6. API integration services
            """
            
            result_format = """
            {
                "file_path/name.ext": "Complete file content",
                "another/path/file.ext": "Complete file content",
                ...
            }
            """
            
        elif component == "backend":
            file_types = """
            1. Server setup and configuration
            2. API route handlers
            3. Controller/service files
            4. Middleware implementation
            5. Authentication modules
            6. Database access modules
            7. Utility/helper functions
            """
            
            result_format = """
            {
                "file_path/name.ext": "Complete file content",
                "another/path/file.ext": "Complete file content",
                ...
            }
            """
            
        else:  # database
            file_types = """
            1. Database schema definitions
            2. Migration files
            3. Seed data files
            4. Database configuration
            5. ORM models (if applicable)
            """
            
            result_format = """
            {
                "file_path/name.ext": "Complete file content",
                "another/path/file.ext": "Complete file content",
                ...
            }
            """

        formatted_prompt = f"""
        You are a senior full-stack developer with extensive experience in {component} development.
        Your task is to generate code for the {component} component based on the provided design:

        TASK SPECIFICATION:
        "{task_specification}"

        {component.upper()} DESIGN:
        {component_design}

        Generate production-quality code for all necessary files according to the design.
        Include the following file types as needed:
        {file_types}

        Each file should be complete, well-structured, and include appropriate:
        1. Comments and documentation
        2. Error handling
        3. Best practices for the selected technologies
        4. Proper imports and dependencies

        Format your response as a JSON object where keys are file paths and values are the complete file content:
        {result_format}

        Make sure each file is complete and can be used directly in a production environment.
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info(f"{component.capitalize()} code generation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting {component} code generation prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_documentation_generation_prompt(
    task_specification: str,
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any],
    generated_code: Dict[str, Dict[str, str]]
) -> str:
    """
    Format the prompt for generating project documentation.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Design details for all components
        generated_code: Generated code files
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting documentation generation prompt")
    try:
        # Extract key information for documentation
        features = requirements.get("features", [])
        tech_recommendations = requirements.get("technology_recommendations", {})
        
        # Count files by type
        file_counts = {}
        for component, files in generated_code.items():
            file_counts[component] = len(files)
        
        # Create file list summary (limited to avoid token limits)
        file_list = ""
        file_count = 0
        for component, files in generated_code.items():
            file_list += f"\n{component.upper()} FILES:\n"
            for file_path in list(files.keys())[:5]:  # Limit to 5 files per component
                file_list += f"- {file_path}\n"
                file_count += 1
            if len(files) > 5:
                file_list += f"- ... {len(files)-5} more files\n"

        formatted_prompt = f"""
        You are a senior full-stack developer with excellent technical documentation skills.
        Your task is to create comprehensive documentation for a software project based on the following information:

        TASK SPECIFICATION:
        "{task_specification}"

        PROJECT OVERVIEW:
        - Features: {len(features)} features implemented
        - Technologies: {', '.join([tech for techs in tech_recommendations.values() for tech in techs[:3]])}
        - Components: Frontend, Backend, Database
        - Total files: {sum(file_counts.values())} files across {len(file_counts)} components

        KEY FILES:
        {file_list}

        Create the following documentation:
        
        1. README.md - Project overview, setup instructions, and usage guide
        2. API.md - API documentation with endpoints, parameters, and responses
        3. ARCHITECTURE.md - System architecture explanation
        
        Each document should be comprehensive, well-structured, and follow best practices for technical documentation.

        Format your response as a JSON object where keys are document names and values are the complete document content:
        {{
            "README.md": "Complete markdown content",
            "API.md": "Complete markdown content",
            "ARCHITECTURE.md": "Complete markdown content"
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Documentation generation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting documentation generation prompt: {str(e)}", exc_info=True)
        raise

logger.info("Full Stack Developer LLM prompts module initialized successfully")