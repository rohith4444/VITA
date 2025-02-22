from typing import List, Dict, Any
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("llm.prompts.solution_architect")

@trace_method
def format_architecture_requirements_prompt(project_description: str, features: List[str]) -> str:
    """
    Format the prompt for analyzing architecture requirements.
    """
    logger.debug("Formatting architecture requirements analysis prompt")
    
    try:
        logger.debug(f"Project description length: {len(project_description)} chars")
        logger.debug(f"Number of features: {len(features)}")

        # Format features as bullet points
        formatted_features = "\n".join(f"- {feature}" for feature in features)

        formatted_prompt = f"""
        As a Solution Architect, analyze the following project:

        PROJECT DESCRIPTION:
        "{project_description}"

        KEY FEATURES:
        {formatted_features}

        Analyze the architecture requirements for this project. Consider:
        1. Functional requirements
        2. Non-functional requirements (performance, scalability, security, etc.)
        3. System constraints
        4. Integration requirements
        5. Data management needs

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
            ]
        }}
        """
        
        logger.info("Architecture requirements prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting architecture requirements prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_tech_stack_prompt(project_description: str, requirements: Dict[str, Any]) -> str:
    """
    Format the prompt for technology stack selection.
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

        formatted_prompt = f"""
        As a Solution Architect, recommend a technology stack for the following project:

        PROJECT DESCRIPTION:
        "{project_description}"

        KEY FUNCTIONAL REQUIREMENTS:
        {formatted_functional}

        KEY NON-FUNCTIONAL REQUIREMENTS:
        {formatted_non_functional}

        Recommend a comprehensive technology stack for this project. Include:
        1. Frontend technologies
        2. Backend technologies
        3. Database technologies
        4. Infrastructure/Cloud technologies
        5. DevOps tools
        6. Additional tools and libraries

        Provide justification for each recommendation based on the requirements.

        Format your response as a JSON object with:
        {{
            "frontend": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ],
            "backend": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ],
            "database": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ],
            "infrastructure": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ],
            "devops": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ],
            "additional": [
                {{
                    "technology": "Technology name",
                    "justification": "Reasons for selection",
                    "alternatives": ["Alternative 1", "Alternative 2"]
                }}
            ]
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
    requirements: Dict[str, Any]
) -> str:
    """
    Format the prompt for architecture design generation.
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

        Design a comprehensive system architecture that addresses all requirements and leverages the selected technology stack.

        Format your response as a JSON object with:
        {{
            "system_components": [
                {{
                    "name": "Component name",
                    "description": "Component description",
                    "responsibilities": ["Responsibility 1", "Responsibility 2"],
                    "technologies": ["Technology 1", "Technology 2"]
                }}
            ],
            "component_relationships": [
                {{
                    "source": "Source component",
                    "target": "Target component",
                    "relationship_type": "uses/calls/depends on/etc.",
                    "description": "Description of relationship"
                }}
            ],
            "data_flows": [
                {{
                    "source": "Source component/actor",
                    "target": "Target component/actor",
                    "data": "Data being transferred",
                    "description": "Description of data flow"
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
                            "description": "Endpoint description"
                        }}
                    ]
                }}
            ],
            "database_schema": [
                {{
                    "entity": "Entity name",
                    "description": "Entity description",
                    "attributes": ["Attribute 1", "Attribute 2"],
                    "relationships": ["Relationship 1", "Relationship 2"]
                }}
            ],
            "security_architecture": {{
                "authentication": "Authentication mechanism",
                "authorization": "Authorization approach",
                "data_protection": "Data protection measures",
                "secure_communication": "Communication security"
            }},
            "deployment_architecture": {{
                "environments": ["Development", "Staging", "Production"],
                "infrastructure": "Infrastructure description",
                "scaling_strategy": "Scaling approach"
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
    requirements: Dict[str, Any]
) -> str:
    """
    Format the prompt for architecture validation.
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

        formatted_prompt = f"""
        As a Solution Architect, validate the following system architecture against the project requirements:

        SYSTEM ARCHITECTURE:
        {architecture_json}

        FUNCTIONAL REQUIREMENTS:
        {formatted_functional}

        NON-FUNCTIONAL REQUIREMENTS:
        {formatted_non_functional}

        Perform a comprehensive validation of the architecture design. Evaluate:
        1. Requirement coverage
        2. Component completeness
        3. Security aspects
        4. Scalability
        5. Performance
        6. Maintainability
        7. Technology alignment

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
    validation_results: Dict[str, Any]
) -> str:
    """
    Format the prompt for technical specifications generation.
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

        formatted_prompt = f"""
        As a Solution Architect, generate detailed technical specifications based on the following:

        SYSTEM ARCHITECTURE:
        {architecture_json}

        TECHNOLOGY STACK:
        {formatted_tech_stack}

        VALIDATION RESULTS:
        {validation_json}

        Generate comprehensive technical specifications that would guide the development team. Include:
        1. Component specifications
        2. API specifications
        3. Database specifications
        4. Security specifications
        5. Integration specifications
        6. Performance requirements
        7. Deployment specifications

        Address any concerns or recommendations from the validation results.

        Format your response as a JSON object with:
        {{
            "component_specifications": [
                {{
                    "component": "Component name",
                    "purpose": "Component purpose",
                    "functionality": ["Function 1", "Function 2"],
                    "technical_requirements": ["Requirement 1", "Requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"]
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
                            "description": "Endpoint description"
                        }}
                    ],
                    "authentication": "Authentication method",
                    "rate_limiting": "Rate limiting approach"
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
                            "constraints": ["Constraint 1", "Constraint 2"]
                        }}
                    ],
                    "indexing_strategy": "Indexing approach",
                    "scaling_strategy": "Scaling approach"
                }}
            ],
            "security_specifications": {{
                "authentication": "Authentication details",
                "authorization": "Authorization details",
                "data_protection": "Data protection details",
                "secure_communication": "Communication security details",
                "security_monitoring": "Security monitoring approach"
            }},
            "integration_specifications": [
                {{
                    "integration_point": "Integration point",
                    "integration_type": "Integration type",
                    "communication_protocol": "Protocol",
                    "data_format": "Data format",
                    "frequency": "Integration frequency",
                    "error_handling": "Error handling approach"
                }}
            ],
            "performance_specifications": {{
                "response_time_requirements": "Response time details",
                "throughput_requirements": "Throughput details",
                "scalability_requirements": "Scalability details",
                "resource_usage_limits": "Resource usage details"
            }},
            "deployment_specifications": {{
                "environments": ["Environment 1", "Environment 2"],
                "infrastructure_requirements": ["Requirement 1", "Requirement 2"],
                "deployment_process": "Deployment process",
                "monitoring_approach": "Monitoring approach",
                "rollback_strategy": "Rollback strategy"
            }}
        }}
        """
        
        logger.info("Specifications prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting specifications prompt: {str(e)}", exc_info=True)
        raise