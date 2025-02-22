from core.logging.logger import setup_logger
from typing import Dict, List, Any
from core.tracing.service import trace_method
from agents.solution_architect.llm.service import LLMService

# Initialize logger
logger = setup_logger("tools.solution_architect.technology_selector")

# Common technology stacks for reference
DEFAULT_TECH_STACKS = {
    "web_application": {
        "frontend": ["React", "Next.js", "TypeScript"],
        "backend": ["Node.js", "Express", "Python", "FastAPI"],
        "database": ["PostgreSQL", "MongoDB"],
        "infrastructure": ["AWS", "Docker", "Kubernetes"]
    },
    "mobile_application": {
        "frontend": ["React Native", "Flutter"],
        "backend": ["Node.js", "Express", "Python", "FastAPI"],
        "database": ["PostgreSQL", "MongoDB", "Firebase"],
        "infrastructure": ["AWS", "Google Cloud"]
    },
    "data_intensive": {
        "backend": ["Python", "FastAPI", "Django"],
        "database": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
        "infrastructure": ["AWS", "Docker", "Kubernetes"]
    }
}

@trace_method
async def select_tech_stack(
    project_description: str, 
    requirements: Dict[str, Any],
    llm_service: LLMService
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Select appropriate technology stack based on project requirements.
    
    Args:
        project_description: Project description
        requirements: Structured requirements
        llm_service: LLM service for recommendations
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Selected technology stack with justifications
    """
    logger.info("Starting technology stack selection")
    
    try:
        # Get recommendations from LLM
        tech_stack = await llm_service.select_technology_stack(
            project_description=project_description,
            requirements=requirements
        )
        
        logger.debug(f"Received technology stack recommendations: {tech_stack}")
        
        # Validate and enhance recommendations
        validated_stack = validate_tech_stack(tech_stack)
        logger.debug(f"Validated technology stack: {validated_stack}")
        
        # Check compatibility
        compatibility_issues = check_compatibility(validated_stack)
        logger.debug(f"Compatibility issues: {compatibility_issues}")
        
        if compatibility_issues:
            logger.warning(f"Found {len(compatibility_issues)} compatibility issues")
            # Resolve compatibility issues
            resolved_stack = resolve_compatibility_issues(validated_stack, compatibility_issues)
            logger.debug(f"Resolved technology stack: {resolved_stack}")
            return resolved_stack
        
        return validated_stack
        
    except Exception as e:
        logger.error(f"Error selecting technology stack: {str(e)}", exc_info=True)
        # Fallback to a default stack if necessary
        return get_default_tech_stack(project_description)

@trace_method
def validate_tech_stack(tech_stack: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Validate and enhance technology stack recommendations.
    
    Args:
        tech_stack: Recommended technology stack
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Validated technology stack
    """
    logger.info("Validating technology stack")
    
    validated = {}
    required_categories = ["frontend", "backend", "database", "infrastructure"]
    
    try:
        # Ensure all required categories are present
        for category in required_categories:
            if category not in tech_stack or not tech_stack[category]:
                logger.warning(f"Missing or empty category: {category}")
                tech_stack[category] = default_for_category(category)
                
        # Validate each entry has required fields
        for category, technologies in tech_stack.items():
            validated[category] = []
            for tech in technologies:
                if not isinstance(tech, dict):
                    logger.warning(f"Invalid technology entry in {category}: {tech}")
                    continue
                    
                valid_tech = {
                    "technology": tech.get("technology", "Unknown"),
                    "justification": tech.get("justification", "Recommended by system"),
                    "alternatives": tech.get("alternatives", [])
                }
                validated[category].append(valid_tech)
                
        # Add any missing categories
        for category in tech_stack:
            if category not in validated:
                validated[category] = []
                
        logger.info("Technology stack validation completed")
        return validated
        
    except Exception as e:
        logger.error(f"Error validating technology stack: {str(e)}", exc_info=True)
        # Return original if validation fails
        return tech_stack

@trace_method
def check_compatibility(tech_stack: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Check for compatibility issues between selected technologies.
    
    Args:
        tech_stack: Technology stack to check
        
    Returns:
        List[Dict[str, Any]]: List of compatibility issues found
    """
    logger.info("Checking technology compatibility")
    
    compatibility_issues = []
    
    try:
        # Known incompatibility rules
        incompatible_pairs = [
            {"tech1": "React", "tech2": "Angular", "reason": "Different frontend frameworks, choose one"},
            {"tech1": "MongoDB", "tech2": "Mongoose", "category1": "database", "category2": "additional", "reason": "Mongoose is an ODM for MongoDB, not a separate database"},
            {"tech1": "Flask", "tech2": "Django", "category1": "backend", "category2": "backend", "reason": "Different Python web frameworks, choose one for the same application component"}
        ]
        
        # Find all technologies
        all_techs = {}
        for category, technologies in tech_stack.items():
            for tech in technologies:
                tech_name = tech["technology"]
                if tech_name not in all_techs:
                    all_techs[tech_name] = {"categories": []}
                all_techs[tech_name]["categories"].append(category)
        
        # Check for incompatibilities
        for rule in incompatible_pairs:
            tech1, tech2 = rule["tech1"], rule["tech2"]
            
            if tech1 in all_techs and tech2 in all_techs:
                # Check category constraints if specified
                if "category1" in rule and "category2" in rule:
                    cat1, cat2 = rule["category1"], rule["category2"]
                    if cat1 in all_techs[tech1]["categories"] and cat2 in all_techs[tech2]["categories"]:
                        compatibility_issues.append({
                            "tech1": tech1,
                            "tech2": tech2,
                            "reason": rule["reason"]
                        })
                else:
                    # No category constraints, just report the incompatibility
                    compatibility_issues.append({
                        "tech1": tech1,
                        "tech2": tech2,
                        "reason": rule["reason"]
                    })
        
        logger.info(f"Found {len(compatibility_issues)} compatibility issues")
        return compatibility_issues
        
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}", exc_info=True)
        return []

@trace_method
def resolve_compatibility_issues(
    tech_stack: Dict[str, List[Dict[str, Any]]],
    issues: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Resolve compatibility issues in the technology stack.
    
    Args:
        tech_stack: Technology stack with issues
        issues: List of compatibility issues
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Resolved technology stack
    """
    logger.info("Resolving compatibility issues")
    
    resolved_stack = {category: technologies.copy() for category, technologies in tech_stack.items()}
    
    try:
        for issue in issues:
            tech1, tech2 = issue["tech1"], issue["tech2"]
            
            # Simple resolution strategy: remove the second technology
            for category, technologies in resolved_stack.items():
                resolved_stack[category] = [
                    tech for tech in technologies if tech["technology"] != tech2
                ]
            
            logger.debug(f"Resolved compatibility issue between {tech1} and {tech2} by removing {tech2}")
        
        logger.info("Compatibility issues resolved")
        return resolved_stack
        
    except Exception as e:
        logger.error(f"Error resolving compatibility issues: {str(e)}", exc_info=True)
        return tech_stack

@trace_method
def default_for_category(category: str) -> List[Dict[str, Any]]:
    """
    Get default technologies for a category.
    
    Args:
        category: Technology category
        
    Returns:
        List[Dict[str, Any]]: Default technologies for the category
    """
    logger.debug(f"Getting defaults for category: {category}")
    
    defaults = {
        "frontend": [
            {"technology": "React", "justification": "Popular and widely supported frontend library", "alternatives": ["Vue.js", "Angular"]}
        ],
        "backend": [
            {"technology": "Node.js", "justification": "Versatile backend runtime", "alternatives": ["Python/FastAPI", "Java/Spring"]}
        ],
        "database": [
            {"technology": "PostgreSQL", "justification": "Reliable and feature-rich relational database", "alternatives": ["MongoDB", "MySQL"]}
        ],
        "infrastructure": [
            {"technology": "AWS", "justification": "Comprehensive cloud platform", "alternatives": ["Azure", "Google Cloud"]}
        ],
        "devops": [
            {"technology": "Docker", "justification": "Standard containerization technology", "alternatives": ["Podman"]}
        ],
        "additional": [
            {"technology": "Redis", "justification": "High-performance caching", "alternatives": ["Memcached"]}
        ]
    }
    
    return defaults.get(category, [{"technology": "Generic", "justification": "Default option", "alternatives": []}])

@trace_method
def get_default_tech_stack(project_description: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a default technology stack based on the project description.
    
    Args:
        project_description: Project description
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Default technology stack
    """
    logger.info("Selecting default technology stack")
    
    # Simple heuristic to determine project type
    project_type = "web_application"  # Default
    
    project_desc_lower = project_description.lower()
    if "mobile" in project_desc_lower or "android" in project_desc_lower or "ios" in project_desc_lower:
        project_type = "mobile_application"
    elif "data" in project_desc_lower or "analytics" in project_desc_lower or "dashboard" in project_desc_lower:
        project_type = "data_intensive"
    
    logger.debug(f"Determined project type: {project_type}")
    
    # Get the default stack for the project type
    default_stack = DEFAULT_TECH_STACKS.get(project_type, DEFAULT_TECH_STACKS["web_application"])
    
    # Convert to the expected format
    formatted_stack = {}
    for category, technologies in default_stack.items():
        formatted_stack[category] = []
        for tech in technologies:
            formatted_stack[category].append({
                "technology": tech,
                "justification": f"Default {category} technology for {project_type}",
                "alternatives": []
            })
    
    logger.info(f"Selected default tech stack for project type: {project_type}")
    return formatted_stack