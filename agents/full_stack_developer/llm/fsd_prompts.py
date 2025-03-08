from typing import List, Dict, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("full_stack_developer.llm.prompts")
logger.info("Initializing Full Stack Developer LLM prompts module")

@trace_method
def format_requirements_analysis_prompt(task_specification: str, project_structure: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the prompt for analyzing task requirements.
    
    Args:
        task_specification: Raw task specification from user
        project_structure: Optional project structure context from Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting requirements analysis prompt")
    try:
        logger.debug(f"Task specification length: {len(task_specification)} chars")
        logger.debug(f"Task specification preview: {task_specification[:100]}...")

        # Add project structure context if available
        project_structure_text = ""
        if project_structure:
            project_structure_text = """
            PROJECT STRUCTURE CONTEXT:
            This task is part of a larger project with the following structure:
            """
            
            # Add directory structure if available
            if "directories" in project_structure:
                project_structure_text += "\nDirectory Structure:\n"
                for directory in project_structure.get("directories", []):
                    project_structure_text += f"- {directory.get('path', '')}: {directory.get('purpose', '')}\n"
            
            # Add component relationships if available
            if "components" in project_structure:
                project_structure_text += "\nRelated Components:\n"
                for component in project_structure.get("components", []):
                    project_structure_text += f"- {component.get('name', '')}: {component.get('description', '')}\n"

        formatted_prompt = f"""
        You are a senior full-stack developer with extensive experience in web and application development.
        Your task is to analyze the following requirement specification and extract key development requirements:

        TASK SPECIFICATION:
        "{task_specification}"
        
        {project_structure_text}

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
            ],
            "project_structure_considerations": [
                "Consideration for integrating with project structure"
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
    component: str,  # "frontend", "backend", or "database"
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for designing a specific component solution.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        component: Which component to design ("frontend", "backend", or "database")
        project_structure: Optional project structure context from Team Lead
        
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
        
        # Add project structure context if available
        project_structure_text = ""
        if project_structure:
            project_structure_text = """
            PROJECT STRUCTURE CONSIDERATIONS:
            This component must integrate with the larger project structure:
            """
            
            # Add component-specific structure information
            if component == "frontend" and "frontend" in project_structure:
                structure_info = project_structure.get("frontend", {})
                project_structure_text += f"\nFrontend Structure:\n"
                for item in structure_info.get("components", []):
                    project_structure_text += f"- {item.get('name', '')}: {item.get('purpose', '')}\n"
                    
            elif component == "backend" and "backend" in project_structure:
                structure_info = project_structure.get("backend", {})
                project_structure_text += f"\nBackend Structure:\n"
                for item in structure_info.get("components", []):
                    project_structure_text += f"- {item.get('name', '')}: {item.get('purpose', '')}\n"
                    
            elif component == "database" and "database" in project_structure:
                structure_info = project_structure.get("database", {})
                project_structure_text += f"\nDatabase Structure:\n"
                for item in structure_info.get("models", []):
                    project_structure_text += f"- {item.get('name', '')}: {item.get('purpose', '')}\n"

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
                ],
                "project_integration": [
                    "How this component integrates with the project structure"
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
                ],
                "project_integration": [
                    "How this component integrates with the project structure"
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
                "schema_diagram": "Textual representation of schema",
                "project_integration": [
                    "How this database integrates with the project structure"
                ]
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

        {project_structure_text}

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
    component: str,  # "frontend", "backend", or "database"
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating code for a specific component.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Design details for the component
        component: Which component to generate code for
        project_structure: Optional project structure context from Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug(f"Formatting {component} code generation prompt")
    try:
        # Extract component-specific design
        component_design = solution_design.get(component, {})
        
        # Add project structure context if available
        project_structure_text = ""
        if project_structure:
            project_structure_text = """
            PROJECT STRUCTURE REQUIREMENTS:
            The code must follow these file naming and location conventions:
            """
            
            # Add file structure conventions
            if "file_naming" in project_structure:
                project_structure_text += "\nFile Naming Conventions:\n"
                for convention in project_structure.get("file_naming", []):
                    project_structure_text += f"- {convention}\n"
                    
            # Add directory structure requirements
            if "directory_structure" in project_structure:
                project_structure_text += "\nDirectory Structure:\n"
                for directory in project_structure.get("directory_structure", []):
                    path = directory.get("path", "")
                    purpose = directory.get("purpose", "")
                    project_structure_text += f"- {path}: {purpose}\n"
        
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
        
        {project_structure_text}

        Generate production-quality code for all necessary files according to the design.
        Include the following file types as needed:
        {file_types}

        Each file should be complete, well-structured, and include appropriate:
        1. Comments and documentation
        2. Error handling
        3. Best practices for the selected technologies
        4. Proper imports and dependencies
        5. Metadata comments indicating purpose and relationship to other components

        Format your response as a JSON object where keys are file paths and values are the complete file content:
        {result_format}

        Make sure each file is complete and can be used directly in a production environment.
        Follow any project structure requirements provided to ensure proper integration.
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
    generated_code: Dict[str, Dict[str, str]],
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating project documentation.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Design details for all components
        generated_code: Generated code files
        project_structure: Optional project structure context from Team Lead
        
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
        
        # Add project structure context if available
        project_structure_text = ""
        if project_structure:
            project_structure_text = """
            DOCUMENTATION STRUCTURE REQUIREMENTS:
            The documentation should follow these conventions and be placed in these locations:
            """
            
            # Add documentation guidelines
            if "documentation" in project_structure:
                doc_guidelines = project_structure.get("documentation", {})
                for doc_type, guidelines in doc_guidelines.items():
                    project_structure_text += f"\n{doc_type} Documentation:\n"
                    project_structure_text += f"- Location: {guidelines.get('location', '')}\n"
                    project_structure_text += f"- Format: {guidelines.get('format', '')}\n"
                    project_structure_text += f"- Required Sections: {', '.join(guidelines.get('sections', []))}\n"

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
        
        {project_structure_text}

        Create the following documentation:
        
        1. README.md - Project overview, setup instructions, and usage guide
        2. API.md - API documentation with endpoints, parameters, and responses
        3. ARCHITECTURE.md - System architecture explanation
        4. COMPONENT_GUIDE.md - Guide to individual components and their integrations
        
        Each document should be comprehensive, well-structured, and follow best practices for technical documentation.
        Include metadata comments at the top of each document indicating its purpose and relationship to the project.

        Format your response as a JSON object where keys are document names and values are the complete document content:
        {{
            "README.md": "Complete markdown content",
            "API.md": "Complete markdown content",
            "ARCHITECTURE.md": "Complete markdown content",
            "COMPONENT_GUIDE.md": "Complete markdown content"
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Documentation generation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting documentation generation prompt: {str(e)}", exc_info=True)
        raise


# New prompts for Team Lead coordination

@trace_method
def format_instruction_processing_prompt(
    instruction: Dict[str, Any],
    task_id: str,
    team_lead_id: str
) -> str:
    """
    Format prompt for processing instructions from the Team Lead.
    
    Args:
        instruction: Instruction from Team Lead
        task_id: ID of the task
        team_lead_id: ID of the Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting instruction processing prompt")
    try:
        # Extract instruction details
        task_name = instruction.get("task_name", "Unnamed Task")
        task_description = instruction.get("description", "No description provided")
        priority = instruction.get("priority", "MEDIUM")
        dependencies = instruction.get("dependencies", {})
        
        # Format dependencies for readability
        dependencies_text = ""
        if dependencies:
            dependencies_text = "\nDEPENDENCIES:\n"
            predecessors = dependencies.get("predecessors", [])
            if predecessors:
                dependencies_text += "Predecessors:\n"
                for pred in predecessors:
                    dependencies_text += f"- Task {pred.get('task_id', '')}: {pred.get('agent', '')}\n"
            
            is_blocked = dependencies.get("is_blocked", False)
            dependencies_text += f"\nBlocked: {is_blocked}\n"
        
        # Format context information
        context = instruction.get("context", {})
        context_text = "\nCONTEXT:\n"
        for key, value in context.items():
            context_text += f"- {key}: {value}\n"

        formatted_prompt = f"""
        You are a senior full-stack developer tasked with processing instructions from your Team Lead.
        Please analyze the following task instructions and break them down into actionable work items:

        TASK ID: {task_id}
        TEAM LEAD ID: {team_lead_id}

        TASK NAME: {task_name}
        PRIORITY: {priority}

        TASK DESCRIPTION:
        {task_description}
        
        {dependencies_text}
        {context_text}

        Analyze these instructions to:
        1. Identify the core objectives and deliverables
        2. Determine the scope of the requested work
        3. Identify any constraints or special requirements
        4. Understand how this task fits into the project structure
        5. Plan your approach to implementing this task

        Format your response as a JSON object with the following structure:
        {{
            "task_analysis": "Detailed analysis of the task",
            "core_objectives": [
                "Objective 1",
                "Objective 2"
            ],
            "deliverables": [
                "Deliverable 1",
                "Deliverable 2"
            ],
            "dependencies_assessment": "Assessment of how dependencies affect this task",
            "implementation_approach": "Planned approach to implementation",
            "clarification_needed": [
                "Question 1",
                "Question 2"
            ],
            "estimated_effort": "LOW/MEDIUM/HIGH"
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Instruction processing prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting instruction processing prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_deliverable_packaging_prompt(
    task_id: str,
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any],
    generated_code: Dict[str, Dict[str, str]],
    documentation: Dict[str, str]
) -> str:
    """
    Format prompt for packaging deliverables for submission to Team Lead.
    
    Args:
        task_id: ID of the task
        requirements: Analyzed requirements
        solution_design: Design details for all components
        generated_code: Generated code files
        documentation: Generated documentation
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting deliverable packaging prompt")
    try:
        # Count files by type
        code_counts = {}
        for component, files in generated_code.items():
            code_counts[component] = len(files)
        
        # Extract key information
        feature_count = len(requirements.get("features", []))
        doc_count = len(documentation)
        
        # Format file list (sample of files)
        file_list = ""
        for component, files in generated_code.items():
            file_list += f"\n{component.upper()} FILES (sample):\n"
            for file_path in list(files.keys())[:3]:  # Limit to 3 files per component
                file_list += f"- {file_path}\n"
            if len(files) > 3:
                file_list += f"- ... and {len(files)-3} more files\n"

        formatted_prompt = f"""
        You are a senior full-stack developer preparing to submit your completed work to your Team Lead.
        Your task is to package your deliverables with appropriate metadata for integration:

        TASK ID: {task_id}

        PROJECT OVERVIEW:
        - Features Implemented: {feature_count}
        - Code Components: {", ".join(generated_code.keys())}
        - Total Code Files: {sum(code_counts.values())}
        - Documentation Files: {doc_count}

        SAMPLE FILES:
        {file_list}

        Create a structured packaging of all deliverables with proper metadata to:
        1. Organize files by component type
        2. Add appropriate headers and descriptions to files
        3. Highlight integration points between components
        4. Include a summary of implementation details
        5. Document any known limitations or future improvements

        Format your response as a JSON object with the following structure:
        {{
            "summary": "Executive summary of the implementation",
            "components": [
                {{
                    "name": "Component name",
                    "type": "frontend/backend/database/documentation",
                    "files": [
                        {{
                            "path": "Path to file",
                            "purpose": "Purpose of this file",
                            "integration_points": ["Component X", "Component Y"]
                        }}
                    ],
                    "key_features": ["Feature 1", "Feature 2"]
                }}
            ],
            "integration_guide": "Guide to integrating these components",
            "test_strategy": "Approach to testing these components",
            "known_limitations": ["Limitation 1", "Limitation 2"],
            "future_improvements": ["Improvement 1", "Improvement 2"],
            "metadata": {{
                "task_id": "{task_id}",
                "complexity": "LOW/MEDIUM/HIGH",
                "component_dependencies": ["Component X depends on Component Y"],
                "external_dependencies": ["External dependency 1", "External dependency 2"]
            }}
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Deliverable packaging prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting deliverable packaging prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_feedback_processing_prompt(
    task_id: str,
    feedback: Dict[str, Any],
    deliverables: Dict[str, Any],
    team_lead_id: str
) -> str:
    """
    Format prompt for processing feedback from the Team Lead.
    
    Args:
        task_id: ID of the task
        feedback: Feedback from Team Lead
        deliverables: The deliverables that received feedback
        team_lead_id: ID of the Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting feedback processing prompt")
    try:
        # Extract feedback details
        feedback_message = feedback.get("feedback_message", "No feedback message provided")
        positive_aspects = feedback.get("positive_aspects", [])
        improvement_areas = feedback.get("improvement_areas", [])
        revision_instructions = feedback.get("revision_instructions", "No specific revision instructions provided")
        
        # Format positive aspects for readability
        positive_text = "\nPOSITIVE ASPECTS:\n"
        for aspect in positive_aspects:
            positive_text += f"- {aspect}\n"
        
        # Format improvement areas for readability
        improvement_text = "\nIMPROVEMENT AREAS:\n"
        for area in improvement_areas:
            area_name = area.get("area", "Unnamed area")
            suggestion = area.get("suggestion", "No suggestion provided")
            priority = area.get("priority", "MEDIUM")
            improvement_text += f"- {area_name} ({priority}): {suggestion}\n"
        
        # Format deliverables summary
        deliverables_text = "\nDELIVERABLES SUMMARY:\n"
        for component_name, component in deliverables.get("components", {}).items():
            deliverables_text += f"- {component_name}: {len(component.get('files', []))} files\n"

        formatted_prompt = f"""
        You are a senior full-stack developer who has received feedback on your work from your Team Lead.
        Please analyze this feedback to create a detailed revision plan:

        TASK ID: {task_id}
        TEAM LEAD ID: {team_lead_id}

        FEEDBACK MESSAGE:
        {feedback_message}
        
        {positive_text}
        {improvement_text}
        
        REVISION INSTRUCTIONS:
        {revision_instructions}
        
        {deliverables_text}

        Analyze this feedback to:
        1. Identify specific areas that need revision
        2. Determine the scope of required changes
        3. Create a prioritized action plan for revisions
        4. Identify any clarification needed

        Format your response as a JSON object with the following structure:
        {{
            "feedback_analysis": "Overall analysis of the feedback",
            "revision_plan": [
                {{
                    "area": "Area to revise",
                    "changes_needed": "Description of required changes",
                    "priority": "HIGH/MEDIUM/LOW",
                    "affected_files": ["file/path1.ext", "file/path2.ext"]
                }}
            ],
            "clarification_needed": [
                "Question 1",
                "Question 2"
            ],
            "revision_approach": "Overall approach to making these revisions",
            "estimated_effort": "LOW/MEDIUM/HIGH",
            "completion_estimate": "Estimated time to complete revisions"
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Feedback processing prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting feedback processing prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_quality_check_prompt(
    task_id: str,
    component: str,  # "frontend", "backend", "database", or "documentation"
    content: Dict[str, str],
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format prompt for performing a self-check on the quality of generated output.
    
    Args:
        task_id: ID of the task
        component: Which component to check
        content: Content to check (e.g., generated code or documentation)
        project_structure: Optional project structure context from Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug(f"Formatting quality check prompt for {component}")
    try:
        # Format file list
        file_list = "\nFILES TO CHECK:\n"
        for file_path in list(content.keys())[:10]:  # Limit to 10 files for token limit
            file_list += f"- {file_path}\n"
        if len(content) > 10:
            file_list += f"- ... and {len(content)-10} more files\n"
        
        # Component-specific quality criteria
        if component == "frontend":
            criteria = """
            QUALITY CRITERIA:
            1. User Interface/Experience
               - Consistency of UI elements
               - Responsive design principles
               - Accessibility considerations
            2. Component Structure
               - Proper component hierarchy
               - Reusability of components
               - Clear separation of concerns
            3. State Management
               - Appropriate state management approach
               - Efficient data flow
               - Minimal state duplication
            4. Performance
               - Optimized render cycles
               - Efficient component updates
               - Proper handling of large datasets
            5. Integration with Backend
               - Clear API integration
               - Proper error handling
               - Loading state management
            """
        elif component == "backend":
            criteria = """
            QUALITY CRITERIA:
            1. API Design
               - RESTful principles
               - Consistent endpoint structure
               - Clear request/response formats
            2. Business Logic
               - Separation of concerns
               - Maintainable code structure
               - Clear domain modeling
            3. Performance
               - Efficient algorithms
               - Optimized database queries
               - Proper caching strategies
            4. Security
               - Input validation
               - Authentication/authorization
               - Protection against common vulnerabilities
            5. Error Handling
               - Comprehensive error cases
               - Proper logging
               - Informative error responses
            """
        elif component == "database":
            criteria = """
            QUALITY CRITERIA:
            1. Schema Design
               - Normalization principles
               - Appropriate data types
               - Efficient relationships
            2. Query Efficiency
               - Proper indexing
               - Optimized query patterns
               - Consideration of large datasets
            3. Data Integrity
               - Appropriate constraints
               - Consistent relationships
               - Transaction management
            4. Migration Strategy
               - Clean migration paths
               - Backward compatibility
               - Data preservation
            5. Security
               - Access control
               - Protection of sensitive data
               - SQL injection prevention
            """
        else:  # documentation
            criteria = """
            QUALITY CRITERIA:
            1. Completeness
               - Covers all major components
               - Includes all APIs and interfaces
               - Addresses setup and usage
            2. Clarity
               - Clear explanations
               - Appropriate examples
               - Consistent terminology
            3. Structure
               - Logical organization
               - Proper headings and sections
               - Table of contents
            4. Accuracy
               - Matches implemented functionality
               - Up-to-date information
               - Correct code examples
            5. Usability
               - Easily navigable
               - Search-friendly
               - Addresses common questions
            """

        formatted_prompt = f"""
        You are a senior full-stack developer conducting a quality assessment of your work before submission.
        Please thoroughly evaluate the {component} component against industry best practices:

        TASK ID: {task_id}
        
        {file_list}
        
        {criteria}

        Perform a comprehensive quality check and provide:
        1. An overall assessment of quality
        2. Identification of issues or improvements
        3. Specific recommendations for each issue
        4. An assessment of alignment with project structure (if provided)

        Format your response as a JSON object with the following structure:
        {{
            "overall_quality": "Assessment on a scale of 1-10",
            "summary": "Summary of quality assessment",
            "issues": [
                {{
                    "issue": "Description of issue",
                    "location": "File or component where issue exists",
                    "severity": "HIGH/MEDIUM/LOW",
                    "recommendation": "Specific fix recommendation"
                }}
            ],
            "strengths": [
                "Strength 1",
                "Strength 2"
            ],
            "alignment_with_structure": "Assessment of alignment with project structure",
            "pass_quality_check": true/false,
            "recommended_improvements": [
                "Improvement 1",
                "Improvement 2"
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info(f"{component.capitalize()} quality check prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting quality check prompt: {str(e)}", exc_info=True)
        raise


@trace_method
def format_status_report_prompt(
    task_id: str,
    team_lead_id: str,
    current_stage: str,
    progress_details: Dict[str, Any]
) -> str:
    """
    Format prompt for generating a status report for the Team Lead.
    
    Args:
        task_id: ID of the task
        team_lead_id: ID of the Team Lead
        current_stage: Current stage of the workflow
        progress_details: Details about current progress
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting status report prompt")
    try:
        # Map stage to more readable format
        stage_mapping = {
            "analyzing_requirements": "Analyzing Requirements",
            "designing_solution": "Designing Solution",
            "generating_code": "Generating Code",
            "preparing_documentation": "Preparing Documentation",
            "awaiting_instructions": "Awaiting Instructions",
            "processing_instructions": "Processing Instructions",
            "awaiting_feedback": "Awaiting Feedback",
            "processing_feedback": "Processing Feedback",
            "implementing_revisions": "Implementing Revisions",
            "completed": "Task Completed"
        }
        
        readable_stage = stage_mapping.get(current_stage, current_stage)
        
        # Extract progress details
        completion_percentage = progress_details.get("completion_percentage", 0)
        completed_steps = progress_details.get("completed_steps", [])
        current_activity = progress_details.get("current_activity", "Unknown")
        started_at = progress_details.get("started_at", "Unknown")
        estimated_completion = progress_details.get("estimated_completion", "Unknown")
        
        # Format completed steps for readability
        steps_text = "\nCOMPLETED STEPS:\n"
        for step in completed_steps:
            steps_text += f"- {step}\n"

        formatted_prompt = f"""
        You are a senior full-stack developer providing a status report to your Team Lead.
        Create a clear, concise status update on your current progress:

        TASK ID: {task_id}
        TEAM LEAD ID: {team_lead_id}
        CURRENT STAGE: {readable_stage}
        COMPLETION: {completion_percentage}%
        STARTED AT: {started_at}
        ESTIMATED COMPLETION: {estimated_completion}
        
        CURRENT ACTIVITY:
        {current_activity}
        
        {steps_text}

        Generate a professional status report that:
        1. Clearly communicates current progress
        2. Highlights accomplishments
        3. Identifies any challenges or blockers
        4. Provides a realistic timeline for next steps
        5. Requests any needed guidance or resources

        Format your response as a JSON object with the following structure:
        {{
            "status_summary": "Brief summary of current status",
            "current_stage": "{readable_stage}",
            "progress_percentage": {completion_percentage},
            "accomplishments": [
                "Accomplishment 1",
                "Accomplishment 2"
            ],
            "challenges": [
                {{
                    "challenge": "Description of challenge",
                    "impact": "Impact on progress",
                    "mitigation": "Approach to resolving"
                }}
            ],
            "next_steps": [
                {{
                    "step": "Next step description",
                    "timeline": "Expected timeline"
                }}
            ],
            "questions_or_requests": [
                "Question or request for Team Lead"
            ],
            "updated_completion_estimate": "Updated estimate of completion time"
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Status report prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting status report prompt: {str(e)}", exc_info=True)
        raise

logger.info("Full Stack Developer LLM prompts module initialized successfully")