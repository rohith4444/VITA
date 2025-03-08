from typing import List, Dict, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("llm.prompts.solution_architect")

@trace_method
def format_architecture_requirements_prompt(project_description: str, features: List[str], task_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the prompt for analyzing architecture requirements.
    
    Args:
        project_description: The project description
        features: List of project features
        task_context: Optional context from Team Lead task assignment
    """
    logger.debug("Formatting architecture requirements analysis prompt")
    
    try:
        logger.debug(f"Project description length: {len(project_description)} chars")
        logger.debug(f"Number of features: {len(features)}")

        # Format features as bullet points
        formatted_features = "\n".join(f"- {feature}" for feature in features)

        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            """

        formatted_prompt = f"""
        As a Solution Architect, analyze the following project:

        PROJECT DESCRIPTION:
        "{project_description}"

        KEY FEATURES:
        {formatted_features}
        {task_context_section}

        Analyze the architecture requirements for this project. Consider:
        1. Functional requirements
        2. Non-functional requirements (performance, scalability, security, etc.)
        3. System constraints
        4. Integration requirements
        5. Data management needs
        6. Project structure implications for other team members

        Format your response as a JSON object with:
        {{
            "functional_requirements": [
                {{
                    "id": "FR1",
                    "description": "Requirement description",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "non_functional_requirements": [
                {{
                    "id": "NFR1",
                    "type": "Performance/Security/Scalability/etc.",
                    "description": "Requirement description",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "constraints": [
                {{
                    "id": "C1",
                    "description": "Constraint description"
                }}
            ],
            "integration_points": [
                {{
                    "id": "IP1",
                    "description": "Integration point description"
                }}
            ],
            "data_requirements": [
                {{
                    "id": "DR1",
                    "description": "Data requirement description",
                    "data_type": "User data/Transaction data/etc."
                }}
            ],
            "project_structure_considerations": [
                {{
                    "aspect": "Directory organization/Module structure/etc.",
                    "recommendation": "Structure recommendation",
                    "rationale": "Why this structure is recommended"
                }}
            ]
        }}
        """
        
        logger.info("Architecture requirements prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting architecture requirements prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_tech_stack_prompt(project_description: str, requirements: Dict[str, Any], task_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the prompt for technology stack selection.
    
    Args:
        project_description: The project description
        requirements: Structured requirements
        task_context: Optional context from Team Lead task assignment
    """
    logger.debug("Formatting tech stack selection prompt")
    
    try:
        # Format functional requirements
        functional_reqs = requirements.get("functional_requirements", [])
        formatted_functional = "\n".join(
            f"- {req['id']}: {req['description']}" 
            for req in functional_reqs
        )

        # Format non-functional requirements
        non_functional_reqs = requirements.get("non_functional_requirements", [])
        formatted_non_functional = "\n".join(
            f"- {req['id']} ({req['type']}): {req['description']}" 
            for req in non_functional_reqs
        )

        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            Tech Constraints: {task_context.get('tech_constraints', 'No specific constraints provided')}
            """

        formatted_prompt = f"""
        As a Solution Architect, recommend a technology stack for the following project:

        PROJECT DESCRIPTION:
        "{project_description}"

        KEY FUNCTIONAL REQUIREMENTS:
        {formatted_functional}

        KEY NON-FUNCTIONAL REQUIREMENTS:
        {formatted_non_functional}
        {task_context_section}

        Recommend a comprehensive technology stack for this project. Include:
        1. Frontend technologies
        2. Backend technologies
        3. Database technologies
        4. Infrastructure/Cloud technologies
        5. DevOps tools
        6. Additional tools and libraries

        Provide justification for each recommendation based on the requirements.
        Ensure your recommendations will integrate well with the work of other team members.

        Format your response as a JSON object with:
        {{
            "frontend": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "backend": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "database": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "infrastructure": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "devops": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "additional": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"],
                    "version": "Recommended version",
                    "integration_notes": "Notes for integration with other technologies"
                }}
            ],
            "directory_structure_recommendations": {
                "approach": "Monorepo/Multi-repo/etc.",
                "project_organization": "Recommended organization structure",
                "rationale": "Reasoning for this structure"
            }
        }}
        """
        
        logger.info("Tech stack prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting tech stack prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_architecture_design_prompt(
    project_description: str,
    tech_stack: Dict[str, List[Dict[str, Any]]],
    requirements: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for architecture design generation.
    
    Args:
        project_description: The project description
        tech_stack: Selected technology stack
        requirements: Structured requirements
        task_context: Optional context from Team Lead task assignment
    """
    logger.debug("Formatting architecture design prompt")
    
    try:
        # Format tech stack
        tech_categories = []
        for category, techs in tech_stack.items():
            tech_list = ", ".join(tech["technology"] for tech in techs)
            tech_categories.append(f"{category.upper()}: {tech_list}")
        
        formatted_tech_stack = "\n".join(tech_categories)
        
        # Format requirements
        functional_reqs = requirements.get("functional_requirements", [])
        non_functional_reqs = requirements.get("non_functional_requirements", [])
        
        formatted_functional = "\n".join(
            f"- {req['id']}: {req['description']}" 
            for req in functional_reqs
        )
        formatted_non_functional = "\n".join(
            f"- {req['id']} ({req['type']}): {req['description']}" 
            for req in non_functional_reqs
        )

        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            Architecture Focus: {task_context.get('architecture_focus', 'No specific focus provided')}
            Integration Requirements: {task_context.get('integration_requirements', 'No specific requirements provided')}
            """

        formatted_prompt = f"""
        As a Solution Architect, design a detailed system architecture for the following project:

        PROJECT DESCRIPTION:
        "{project_description}"

        TECHNOLOGY STACK:
        {formatted_tech_stack}

        KEY FUNCTIONAL REQUIREMENTS:
        {formatted_functional}

        KEY NON-FUNCTIONAL REQUIREMENTS:
        {formatted_non_functional}
        {task_context_section}

        Design a comprehensive system architecture that addresses all requirements and leverages the selected technology stack.
        Your architecture should provide clear guidance for other team members who will implement it.
        Be specific about project structure and component organization.

        Format your response as a JSON object with:
        {{
            "system_components": [
                {{
                    "name": "Component name",
                    "description": "Component description",
                    "responsibilities": ["Responsibility 1", "Responsibility 2"],
                    "technologies": ["Technology 1", "Technology 2"],
                    "file_structure": "Recommended file/directory structure for this component",
                    "dependencies": ["Other component it depends on"]
                }}
            ],
            "component_relationships": [
                {{
                    "source": "Source component",
                    "target": "Target component",
                    "relationship_type": "uses/calls/depends on/etc.",
                    "description": "Description of relationship",
                    "interface_details": "API/interface details"
                }}
            ],
            "data_flows": [
                {{
                    "source": "Source component/actor",
                    "target": "Target component/actor",
                    "data": "Data being transferred",
                    "description": "Description of data flow",
                    "format": "JSON/XML/Binary/etc."
                }}
            ],
            "api_interfaces": [
                {{
                    "name": "API name",
                    "type": "REST/GraphQL/SOAP/etc.",
                    "endpoints": [
                        {{
                            "path": "/example/path",
                            "method": "GET/POST/etc.",
                            "description": "Endpoint description",
                            "request_format": "Request format details",
                            "response_format": "Response format details"
                        }}
                    ],
                    "responsible_component": "Component implementing this API"
                }}
            ],
            "database_schema": [
                {{
                    "entity": "Entity name",
                    "description": "Entity description",
                    "attributes": ["Attribute 1", "Attribute 2"],
                    "relationships": ["Relationship 1", "Relationship 2"],
                    "table_structure": "SQL table definition or NoSQL structure"
                }}
            ],
            "security_architecture": {{
                "authentication": "Authentication mechanism",
                "authorization": "Authorization approach",
                "data_protection": "Data protection measures",
                "secure_communication": "Communication security",
                "component_responsibility": "Which component handles security"
            }},
            "deployment_architecture": {{
                "environments": ["Development", "Staging", "Production"],
                "infrastructure": "Infrastructure description",
                "scaling_strategy": "Scaling approach",
                "deployment_process": "Process for deployment"
            }},
            "project_structure": {{
                "root_directories": ["Directory 1", "Directory 2"],
                "directory_organization": "Description of directory organization",
                "module_organization": "Description of module organization",
                "file_naming_conventions": "Naming conventions for files",
                "rationale": "Reasoning behind this structure"
            }}
        }}
        """
        
        logger.info("Architecture design prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting architecture design prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_architecture_validation_prompt(
    architecture_design: Dict[str, Any],
    requirements: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for architecture validation.
    
    Args:
        architecture_design: Architecture design
        requirements: Structured requirements
        task_context: Optional context from Team Lead task assignment
    """
    logger.debug("Formatting architecture validation prompt")
    
    try:
        # Format requirements
        functional_reqs = requirements.get("functional_requirements", [])
        non_functional_reqs = requirements.get("non_functional_requirements", [])
        
        formatted_functional = "\n".join(
            f"- {req['id']}: {req['description']}" 
            for req in functional_reqs
        )
        formatted_non_functional = "\n".join(
            f"- {req['id']} ({req['type']}): {req['description']}" 
            for req in non_functional_reqs
        )
        
        # Convert architecture design to formatted string
        import json
        architecture_json = json.dumps(architecture_design, indent=2)

        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            Validation Focus: {task_context.get('validation_focus', 'No specific focus provided')}
            """

        formatted_prompt = f"""
        As a Solution Architect, validate the following system architecture against the project requirements:

        SYSTEM ARCHITECTURE:
        {architecture_json}

        FUNCTIONAL REQUIREMENTS:
        {formatted_functional}

        NON-FUNCTIONAL REQUIREMENTS:
        {formatted_non_functional}
        {task_context_section}

        Perform a comprehensive validation of the architecture design. Evaluate:
        1. Requirement coverage
        2. Component completeness
        3. Security aspects
        4. Scalability
        5. Performance
        6. Maintainability
        7. Technology alignment
        8. Integration potential with other team members' work
        9. Project structure and organization clarity

        Format your response as a JSON object with:
        {{
            "validation_summary": {{
                "overall_assessment": "Strong/Adequate/Concerning",
                "score": "1-10 score",
                "strengths": ["Strength 1", "Strength 2"],
                "concerns": ["Concern 1", "Concern 2"],
                "risks": ["Risk 1", "Risk 2"]
            }},
            "requirement_coverage": [
                {{
                    "requirement_id": "Requirement ID",
                    "covered": true/false,
                    "comments": "Comments on coverage"
                }}
            ],
            "component_assessment": [
                {{
                    "component": "Component name",
                    "assessment": "Assessment notes",
                    "improvements": ["Improvement 1", "Improvement 2"]
                }}
            ],
            "security_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "scalability_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "performance_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "potential_bottlenecks": ["Bottleneck 1", "Bottleneck 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "maintainability_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "technology_alignment": {{
                "overall": "Strong/Adequate/Concerning",
                "misalignments": ["Misalignment 1", "Misalignment 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "integration_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }},
            "structure_assessment": {{
                "overall": "Strong/Adequate/Concerning",
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
        }}
        """
        
        logger.info("Architecture validation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting architecture validation prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_specifications_prompt(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    validation_results: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for technical specifications generation.
    
    Args:
        architecture_design: Architecture design
        tech_stack: Selected technology stack
        validation_results: Validation results
        task_context: Optional context from Team Lead task assignment
    """
    logger.debug("Formatting specifications prompt")
    
    try:
        # Format tech stack
        tech_categories = []
        for category, techs in tech_stack.items():
            tech_list = ", ".join(tech["technology"] for tech in techs)
            tech_categories.append(f"{category.upper()}: {tech_list}")
        
        formatted_tech_stack = "\n".join(tech_categories)
        
        # Convert architecture design and validation results to formatted strings
        import json
        architecture_json = json.dumps(architecture_design, indent=2)
        validation_json = json.dumps(validation_results, indent=2)

        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            Specification Focus: {task_context.get('specification_focus', 'No specific focus provided')}
            """

        formatted_prompt = f"""
        As a Solution Architect, generate detailed technical specifications based on the following:

        SYSTEM ARCHITECTURE:
        {architecture_json}

        TECHNOLOGY STACK:
        {formatted_tech_stack}

        VALIDATION RESULTS:
        {validation_json}
        {task_context_section}

        Generate comprehensive technical specifications that would guide the development team. Include:
        1. Component specifications
        2. API specifications
        3. Database specifications
        4. Security specifications
        5. Integration specifications
        6. Performance requirements
        7. Deployment specifications
        8. Project structure specifications

        Address any concerns or recommendations from the validation results.
        Ensure specifications provide clear guidance for other team members.

        Format your response as a JSON object with:
        {{
            "component_specifications": [
                {{
                    "component": "Component name",
                    "purpose": "Component purpose",
                    "functionality": ["Function 1", "Function 2"],
                    "technical_requirements": ["Requirement 1", "Requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"],
                    "implementation_guidelines": "Guidelines for implementation",
                    "file_structure": "Recommended file/directory structure"
                }}
            ],
            "api_specifications": [
                {{
                    "api_name": "API name",
                    "description": "API description",
                    "endpoints": [
                        {{
                            "path": "/path",
                            "method": "HTTP method",
                            "parameters": ["Parameter 1", "Parameter 2"],
                            "request_format": "Request format",
                            "response_format": "Response format",
                            "description": "Endpoint description",
                            "error_handling": "Error handling approach"
                        }}
                    ],
                    "authentication": "Authentication method",
                    "rate_limiting": "Rate limiting approach",
                    "implementation_guidelines": "Guidelines for implementation"
                }}
            ],
            "database_specifications": [
                {{
                    "database": "Database name",
                    "type": "Database type",
                    "purpose": "Database purpose",
                    "entities": [
                        {{
                            "name": "Entity name",
                            "attributes": ["Attribute 1: Type", "Attribute 2: Type"],
                            "relationships": ["Relationship 1", "Relationship 2"],
                            "constraints": ["Constraint 1", "Constraint 2"],
                            "indexes": ["Index 1", "Index 2"]
                        }}
                    ],
                    "indexing_strategy": "Indexing approach",
                    "scaling_strategy": "Scaling approach",
                    "implementation_guidelines": "Guidelines for implementation"
                }}
            ],
            "security_specifications": {{
                "authentication": "Authentication details",
                "authorization": "Authorization details",
                "data_protection": "Data protection details",
                "secure_communication": "Communication security details",
                "security_monitoring": "Security monitoring approach",
                "implementation_guidelines": "Guidelines for implementation"
            }},
            "integration_specifications": [
                {{
                    "integration_point": "Integration point",
                    "integration_type": "Integration type",
                    "communication_protocol": "Protocol",
                    "data_format": "Data format",
                    "frequency": "Integration frequency",
                    "error_handling": "Error handling approach",
                    "implementation_guidelines": "Guidelines for implementation"
                }}
            ],
            "performance_specifications": {{
                "response_time_requirements": "Response time details",
                "throughput_requirements": "Throughput details",
                "scalability_requirements": "Scalability details",
                "resource_usage_limits": "Resource usage details",
                "optimization_recommendations": "Optimization recommendations"
            }},
            "deployment_specifications": {{
                "environments": ["Environment 1", "Environment 2"],
                "infrastructure_requirements": ["Requirement 1", "Requirement 2"],
                "deployment_process": "Deployment process",
                "monitoring_approach": "Monitoring approach",
                "rollback_strategy": "Rollback strategy",
                "implementation_guidelines": "Guidelines for implementation"
            }},
            "project_structure_specifications": {{
                "directory_organization": "Directory organization",
                "file_naming_conventions": "File naming conventions",
                "module_organization": "Module organization",
                "code_organization_principles": ["Principle 1", "Principle 2"],
                "implementation_guidelines": "Guidelines for implementation"
            }}
        }}
        """
        
        logger.info("Specifications prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting specifications prompt: {str(e)}", exc_info=True)
        raise

# New prompts for Team Lead coordination

@trace_method
def format_task_instruction_prompt(task_instruction: Dict[str, Any]) -> str:
    """
    Format the prompt for processing task instructions from Team Lead.
    
    Args:
        task_instruction: Task instruction from Team Lead
        
    Returns:
        str: Formatted prompt for processing instructions
    """
    logger.debug("Formatting task instruction prompt")
    
    try:
        # Extract task details
        task_id = task_instruction.get("task_id", "Unknown")
        task_name = task_instruction.get("task_name", "Unknown task")
        description = task_instruction.get("description", "No description provided")
        priority = task_instruction.get("priority", "MEDIUM")
        due_time = task_instruction.get("due_time", "Not specified")
        
        # Format dependencies if any
        dependencies_text = ""
        dependencies = task_instruction.get("dependencies", {})
        predecessors = dependencies.get("predecessors", [])
        if predecessors:
            dependencies_text = "Dependencies:\n"
            for dep in predecessors:
                dep_id = dep.get("task_id", "Unknown")
                dep_agent = dep.get("agent", "Unknown")
                dependencies_text += f"- Task {dep_id} by {dep_agent}\n"
        
        formatted_prompt = f"""
        As a Solution Architect, analyze the following task instruction from the Team Lead:

        TASK INFORMATION:
        Task ID: {task_id}
        Task Name: {task_name}
        Description: {description}
        Priority: {priority}
        Due Time: {due_time}
        {dependencies_text}

        Determine the following:
        1. The type of task being requested (requirements analysis, tech stack selection, architecture design, validation, or specifications)
        2. The specific requirements or constraints for this task
        3. The expected deliverables
        4. The specific areas to focus on
        5. How this task integrates with the work of other team members

        Format your response as a JSON object with:
        {{
            "task_type": "requirements_analysis/tech_stack_selection/architecture_design/validation/specifications",
            "interpretation": "Your interpretation of what is being requested",
            "key_requirements": ["Requirement 1", "Requirement 2"],
            "constraints": ["Constraint 1", "Constraint 2"],
            "focus_areas": ["Area 1", "Area 2"],
            "expected_deliverables": ["Deliverable 1", "Deliverable 2"],
            "integration_points": ["Integration point 1", "Integration point 2"],
            "clarification_questions": ["Question 1", "Question 2"]
        }}
        """
        
        logger.info("Task instruction prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting task instruction prompt: {str(e)}", exc_info=True)
        return f"""
        As a Solution Architect, analyze the task instruction and determine what is being requested.
        Format your response as a JSON object with the task type, interpretation, and expected deliverables.
        """

@trace_method
def format_feedback_processing_prompt(feedback: Dict[str, Any], original_deliverable: Dict[str, Any]) -> str:
    """
    Format the prompt for processing feedback from Team Lead.
    
    Args:
        feedback: Feedback from Team Lead
        original_deliverable: Original deliverable that received feedback
        
    Returns:
        str: Formatted prompt for processing feedback
    """
    logger.debug("Formatting feedback processing prompt")
    
    try:
        # Extract feedback details
        feedback_message = feedback.get("message", "No feedback message provided")
        feedback_points = feedback.get("points", [])
        feedback_summary = feedback.get("summary", "No summary provided")
        
        # Format feedback points as bullet points
        formatted_points = "\n".join(f"- {point}" for point in feedback_points)
        
        # Convert original deliverable to formatted string
        import json
        deliverable_json = json.dumps(original_deliverable, indent=2)

        formatted_prompt = f"""
        As a Solution Architect, analyze the following feedback from the Team Lead:

        FEEDBACK MESSAGE:
        {feedback_message}

        FEEDBACK POINTS:
        {formatted_points}

        FEEDBACK SUMMARY:
        {feedback_summary}

        ORIGINAL DELIVERABLE:
        {deliverable_json}

        Determine the following:
        1. The specific areas that need revision
        2. The nature of the changes requested
        3. The priority of each change
        4. How to best implement the requested changes

        Format your response as a JSON object with:
        {{
            "revision_areas": [
                {{
                    "area": "Area needing revision",
                    "current_state": "Current state description",
                    "requested_change": "Change requested",
                    "priority": "HIGH/MEDIUM/LOW",
                    "implementation_approach": "How to implement this change"
                }}
            ],
            "misunderstandings": [
                {{
                    "point": "Point of misunderstanding",
                    "clarification": "Clarification"
                }}
            ],
            "revision_plan": {{
                "steps": ["Step 1", "Step 2"],
                "stage_to_revisit": "The workflow stage to return to",
                "estimated_effort": "LOW/MEDIUM/HIGH"
            }},
            "clarification_questions": ["Question 1", "Question 2"]
        }}
        """
        
        logger.info("Feedback processing prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting feedback processing prompt: {str(e)}", exc_info=True)
        return f"""
        As a Solution Architect, analyze the feedback from the Team Lead and determine what revisions are needed.
        Format your response as a JSON object with revision areas, misunderstandings, and a revision plan.
        """

@trace_method
def format_deliverable_packaging_prompt(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    specifications: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for packaging deliverables for Team Lead.
    
    Args:
        architecture_design: Architecture design
        tech_stack: Selected technology stack
        specifications: Technical specifications
        task_context: Optional context from Team Lead task assignment
        
    Returns:
        str: Formatted prompt for packaging deliverables
    """
    logger.debug("Formatting deliverable packaging prompt")
    
    try:
        # Convert components to formatted strings
        import json
        architecture_json = json.dumps(architecture_design, indent=2)
        tech_stack_json = json.dumps(tech_stack, indent=2)
        specifications_json = json.dumps(specifications, indent=2)
        
        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            Instructions: {task_context.get('instructions', 'No specific instructions provided')}
            Expected Deliverables: {task_context.get('expected_deliverables', 'No specific deliverables requested')}
            """

        formatted_prompt = f"""
        As a Solution Architect, prepare comprehensive deliverables for the Team Lead based on the following:

        ARCHITECTURE DESIGN:
        {architecture_json}

        TECHNOLOGY STACK:
        {tech_stack_json}

        TECHNICAL SPECIFICATIONS:
        {specifications_json}
        {task_context_section}

        Package these components into clear, well-structured deliverables that can be used by other team members.
        Focus on creating deliverables that:
        1. Provide clear direction for development teams
        2. Organize information in a structured, accessible way
        3. Include all necessary metadata for traceability and integration
        4. Follow standardized formats for consistency across the project
        5. Highlight project structure and organization recommendations

        Format your response as a JSON object with:
        {{
            "deliverables": [
                {{
                    "id": "Deliverable ID",
                    "name": "Deliverable name",
                    "type": "Architecture/TechStack/Specifications/Structure",
                    "description": "Description of deliverable",
                    "content": {{
                        // The actual structured content of the deliverable
                    }},
                    "format": "JSON/Markdown/Diagram",
                    "intended_audience": ["Development team", "Project manager", "QA team"],
                    "usage_instructions": "How to use this deliverable"
                }}
            ],
            "project_structure_recommendation": {{
                "root_directories": ["Directory 1", "Directory 2"],
                "directory_organization": "Description of directory organization",
                "component_placement": [
                    {{
                        "component": "Component name",
                        "file_path": "Path relative to project root",
                        "purpose": "Purpose of this placement"
                    }}
                ],
                "naming_conventions": {{
                    "files": "File naming convention",
                    "directories": "Directory naming convention",
                    "components": "Component naming convention"
                }}
            }},
            "integration_points": [
                {{
                    "component": "Component name",
                    "interfaces_with": ["Other component 1", "Other component 2"],
                    "interface_type": "API/File/Database/etc.",
                    "responsible_agent": "Agent responsible for implementation"
                }}
            ],
            "deliverable_summary": "Executive summary of all deliverables"
        }}
        """
        
        logger.info("Deliverable packaging prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting deliverable packaging prompt: {str(e)}", exc_info=True)
        return f"""
        As a Solution Architect, package your work into clear deliverables for the Team Lead.
        Include architecture design, tech stack, specifications, and project structure recommendations.
        Format your response as a JSON object with deliverables and a project structure recommendation.
        """

@trace_method
def format_status_report_prompt(
    current_state: Dict[str, Any],
    progress: Dict[str, Any],
    task_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating a status report for Team Lead.
    
    Args:
        current_state: Current state of the Solution Architect
        progress: Progress information
        task_context: Optional context from Team Lead task assignment
        
    Returns:
        str: Formatted prompt for status report generation
    """
    logger.debug("Formatting status report prompt")
    
    try:
        # Extract status information
        current_stage = current_state.get("status", "Unknown")
        completion_percentage = progress.get("completion_percentage", 0)
        milestones_completed = progress.get("milestones_completed", [])
        milestones_pending = progress.get("milestones_pending", [])
        issues = progress.get("issues", [])
        
        # Format milestones as bullet points
        completed_milestones_text = "\n".join(f"- {milestone}" for milestone in milestones_completed)
        pending_milestones_text = "\n".join(f"- {milestone}" for milestone in milestones_pending)
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        # Add task context if provided
        task_context_section = ""
        if task_context:
            task_context_section = f"""
            TASK CONTEXT FROM TEAM LEAD:
            Task ID: {task_context.get('task_id', 'Not specified')}
            Priority: {task_context.get('priority', 'Not specified')}
            Due Time: {task_context.get('due_time', 'Not specified')}
            """

        formatted_prompt = f"""
        As a Solution Architect, generate a status report for the Team Lead:

        CURRENT STATE:
        Current Stage: {current_stage}
        Completion Percentage: {completion_percentage}%

        MILESTONES COMPLETED:
        {completed_milestones_text if completed_milestones_text else "None yet"}

        PENDING MILESTONES:
        {pending_milestones_text if pending_milestones_text else "None"}

        ISSUES/BLOCKERS:
        {issues_text if issues_text else "None at this time"}
        {task_context_section}

        Generate a comprehensive status report that clearly communicates:
        1. Current progress and achievements
        2. Upcoming work and priorities
        3. Any issues or blockers requiring attention
        4. Resource needs or dependencies
        5. Timeline projections

        Format your response as a JSON object with:
        {{
            "status_summary": "Brief summary of current status",
            "current_stage": "Current workflow stage",
            "completion_percentage": percentage,
            "achievements": [
                {{
                    "description": "Achievement description",
                    "significance": "Why this is important"
                }}
            ],
            "pending_work": [
                {{
                    "description": "Pending work item",
                    "priority": "HIGH/MEDIUM/LOW",
                    "estimated_completion": "Estimated completion date/time"
                }}
            ],
            "issues": [
                {{
                    "description": "Issue description",
                    "impact": "Impact of this issue",
                    "mitigation": "Mitigation strategy",
                    "assistance_needed": "Help needed from Team Lead"
                }}
            ],
            "dependencies": [
                {{
                    "description": "Dependency description",
                    "dependent_on": "Who/what this depends on",
                    "status": "Status of this dependency"
                }}
            ],
            "timeline_projection": {{
                "on_track": true/false,
                "expected_completion": "Expected completion date/time",
                "variance": "Ahead/behind schedule"
            }},
            "next_update": "When the next status update will be provided"
        }}
        """
        
        logger.info("Status report prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting status report prompt: {str(e)}", exc_info=True)
        return f"""
        As a Solution Architect, generate a status report for the Team Lead.
        Include current progress, achievements, pending work, and any issues or blockers.
        Format your response as a JSON object with a status summary and detailed sections.
        """