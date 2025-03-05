from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.full_stack_developer.llm.fsd_service import LLMService

# Initialize logger
logger = setup_logger("tools.full_stack_developer.requirements_analyzer")

@trace_method
async def analyze_requirements(
    task_specification: str,
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Analyze task specification to extract structured requirements.
    
    Args:
        task_specification: Raw task specification
        llm_service: LLM service for analysis
        
    Returns:
        Dict[str, Any]: Structured requirements analysis
    """
    logger.info("Starting requirements analysis")
    
    try:
        # Use LLM to analyze requirements
        requirements = await llm_service.analyze_requirements(task_specification)
        
        # Validate and enhance the requirements
        enhanced_requirements = enhance_requirements(requirements)
        
        logger.info(f"Requirements analysis completed with {len(enhanced_requirements.get('features', []))} features")
        return enhanced_requirements
        
    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}", exc_info=True)
        return generate_fallback_requirements(task_specification)

def enhance_requirements(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and enhance the LLM-generated requirements.
    
    Args:
        requirements: Initial requirements from LLM
        
    Returns:
        Dict[str, Any]: Enhanced requirements
    """
    logger.debug("Enhancing requirements")
    
    try:
        enhanced = requirements.copy()
        
        # Ensure all required sections are present
        required_sections = [
            "features",
            "technical_constraints",
            "dependencies",
            "technology_recommendations",
            "challenges"
        ]
        
        for section in required_sections:
            if section not in enhanced or not enhanced[section]:
                logger.warning(f"Missing section in requirements: {section}")
                if section in ["features", "technical_constraints", "dependencies", "challenges"]:
                    enhanced[section] = []
                elif section == "technology_recommendations":
                    enhanced[section] = {
                        "frontend": ["React", "TypeScript", "Tailwind CSS"],
                        "backend": ["Node.js", "Express", "MongoDB"],
                        "database": ["MongoDB", "PostgreSQL"]
                    }
        
        # Ensure technology recommendations have all required categories
        tech_rec = enhanced["technology_recommendations"]
        for category in ["frontend", "backend", "database"]:
            if category not in tech_rec or not tech_rec[category]:
                logger.warning(f"Missing technology recommendations for {category}")
                if category == "frontend":
                    tech_rec[category] = ["React", "TypeScript", "Tailwind CSS"]
                elif category == "backend":
                    tech_rec[category] = ["Node.js", "Express"]
                elif category == "database":
                    tech_rec[category] = ["MongoDB", "PostgreSQL"]
        
        # Ensure each feature has required fields
        for feature in enhanced["features"]:
            if "name" not in feature:
                feature["name"] = "Unnamed Feature"
            if "description" not in feature:
                feature["description"] = "No description provided"
            if "priority" not in feature:
                feature["priority"] = "MEDIUM"
                
        # Sort features by priority
        priority_values = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        enhanced["features"] = sorted(
            enhanced["features"],
            key=lambda x: priority_values.get(x.get("priority", "MEDIUM"), 2),
            reverse=True
        )
        
        logger.debug("Requirements enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing requirements: {str(e)}", exc_info=True)
        return requirements

def generate_fallback_requirements(task_specification: str) -> Dict[str, Any]:
    """
    Generate basic requirements when LLM analysis fails.
    
    Args:
        task_specification: Raw task specification
        
    Returns:
        Dict[str, Any]: Basic requirements structure
    """
    logger.info("Generating fallback requirements")
    
    # Extract potential feature names from specification
    words = task_specification.split()
    potential_features = [
        word for word in words 
        if len(word) > 5 and word[0].isupper() and word.isalnum()
    ]
    
    # Create basic features
    features = []
    for i, feature in enumerate(potential_features[:3], 1):
        features.append({
            "name": f"Feature {i}: {feature}",
            "description": f"Implementation of {feature}",
            "priority": "HIGH"
        })
    
    # Add generic feature if none found
    if not features:
        features = [
            {
                "name": "Core Functionality",
                "description": "Main functionality of the application",
                "priority": "HIGH"
            },
            {
                "name": "User Interface",
                "description": "User interface components",
                "priority": "MEDIUM"
            },
            {
                "name": "Data Management",
                "description": "Storage and retrieval of data",
                "priority": "MEDIUM"
            }
        ]
    
    # Create fallback requirements structure
    fallback_requirements = {
        "features": features,
        "technical_constraints": [
            {
                "constraint": "Browser compatibility",
                "impact": "Must work on modern browsers"
            },
            {
                "constraint": "Responsive design",
                "impact": "Must work on mobile and desktop"
            }
        ],
        "dependencies": [
            {
                "source": "Frontend",
                "target": "Backend API",
                "description": "Frontend depends on backend API"
            },
            {
                "source": "Backend API",
                "target": "Database",
                "description": "Backend depends on database"
            }
        ],
        "technology_recommendations": {
            "frontend": ["React", "TypeScript", "Tailwind CSS"],
            "backend": ["Node.js", "Express"],
            "database": ["MongoDB", "PostgreSQL"]
        },
        "challenges": [
            {
                "challenge": "Data synchronization",
                "mitigation": "Implement proper state management"
            },
            {
                "challenge": "Performance optimization",
                "mitigation": "Use efficient algorithms and caching"
            }
        ]
    }
    
    logger.info("Fallback requirements generated successfully")
    return fallback_requirements