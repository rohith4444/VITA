from core.logging.logger import setup_logger
from typing import Dict, List, Any, Optional
from core.tracing.service import trace_method
from agents.solution_architect.llm.sa_service import LLMService

# Initialize logger
logger = setup_logger("tools.solution_architect.architecture_validator")

# Architecture validation criteria
VALIDATION_CRITERIA = {
    "security": [
        "Authentication mechanism specified",
        "Authorization approach defined",
        "Data protection measures included",
        "Secure communication specified"
    ],
    "performance": [
        "Performance requirements specified",
        "Potential bottlenecks identified",
        "Caching strategy defined",
        "Resource utilization considered"
    ],
    "scalability": [
        "Scalability approach specified",
        "Load balancing strategy defined",
        "Database scaling considered",
        "Stateless design where appropriate"
    ],
    "reliability": [
        "Error handling approach defined",
        "Redundancy mechanisms included",
        "Backup strategy specified",
        "Monitoring approach defined"
    ],
    "maintainability": [
        "Modularity in design",
        "Clear component boundaries",
        "Documentation requirements",
        "Testing approach"
    ]
}

@trace_method
async def validate_architecture(
    architecture_design: Dict[str, Any],
    requirements: Dict[str, Any],
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Validate the architecture design against requirements and best practices.
    
    Args:
        architecture_design: System architecture design
        requirements: Structured requirements
        llm_service: LLM service for validation
        
    Returns:
        Dict[str, Any]: Validation results with scores and recommendations
    """
    logger.info("Starting architecture validation")
    
    try:
        # Perform LLM-based validation
        validation_results = await llm_service.validate_architecture_design(
            architecture_design=architecture_design,
            requirements=requirements
        )
        
        logger.debug(f"LLM validation results: {validation_results}")
        
        # Enhance validation with structured checks
        #validation_results = enhance_validation(validation_results, architecture_design, requirements)
        logger.debug(f"Enhanced validation results: {validation_results}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating architecture: {str(e)}", exc_info=True)
        # Return basic validation if LLM validation fails
        return perform_basic_validation(architecture_design, requirements)

@trace_method
def enhance_validation(
    validation_results: Dict[str, Any],
    architecture_design: Dict[str, Any],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance LLM validation with additional structured checks.
    
    Args:
        validation_results: Initial validation results from LLM
        architecture_design: Architecture design
        requirements: Project requirements
        
    Returns:
        Dict[str, Any]: Enhanced validation results
    """
    logger.info("Enhancing validation results")
    
    try:
        # Check requirement coverage
        requirement_coverage = validate_requirement_coverage(
            validation_results.get("requirement_coverage", []),
            architecture_design,
            requirements
        )
        
        # If LLM didn't provide coverage, use our own
        if not validation_results.get("requirement_coverage"):
            validation_results["requirement_coverage"] = requirement_coverage
        
        # Check security aspects
        security_assessment = validate_security(
            validation_results.get("security_assessment", {}),
            architecture_design
        )
        
        # If LLM didn't provide security assessment, use our own
        if not validation_results.get("security_assessment"):
            validation_results["security_assessment"] = security_assessment
            
        # Add architecture completeness check
        validation_results["architecture_completeness"] = check_architecture_completeness(architecture_design)
        
        # Generate overall validation summary if not present
        if not validation_results.get("validation_summary"):
            validation_results["validation_summary"] = generate_validation_summary(validation_results)
            
        logger.info("Validation enhancement completed")
        return validation_results
        
    except Exception as e:
        logger.error(f"Error enhancing validation: {str(e)}", exc_info=True)
        return validation_results

@trace_method
def validate_requirement_coverage(
    existing_coverage: List[Dict[str, Any]],
    architecture_design: Dict[str, Any],
    requirements: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Validate that architecture covers all requirements.
    
    Args:
        existing_coverage: Existing requirement coverage results
        architecture_design: Architecture design
        requirements: Project requirements
        
    Returns:
        List[Dict[str, Any]]: Requirement coverage assessment
    """
    logger.info("Validating requirement coverage")
    
    try:
        # If we already have coverage data, use it
        if existing_coverage:
            return existing_coverage
            
        coverage_results = []
        
        # Extract all functional requirements
        functional_reqs = requirements.get("functional_requirements", [])
        
        # Check each requirement
        for req in functional_reqs:
            req_id = req.get("id", "unknown")
            req_desc = req.get("description", "")
            
            # Simple keyword matching to check if requirement is addressed
            req_keywords = extract_keywords(req_desc)
            covered = check_keyword_coverage(req_keywords, architecture_design)
            
            coverage_results.append({
                "requirement_id": req_id,
                "covered": covered,
                "comments": "Requirement appears to be addressed in the architecture design" if covered else "Requirement may not be fully addressed"
            })
            
        logger.info(f"Validated coverage for {len(coverage_results)} requirements")
        return coverage_results
        
    except Exception as e:
        logger.error(f"Error validating requirement coverage: {str(e)}", exc_info=True)
        return existing_coverage

@trace_method
def validate_security(
    existing_assessment: Dict[str, Any],
    architecture_design: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate security aspects of the architecture.
    
    Args:
        existing_assessment: Existing security assessment
        architecture_design: Architecture design
        
    Returns:
        Dict[str, Any]: Security assessment
    """
    logger.info("Validating security aspects")
    
    try:
        # If we already have security assessment, use it
        if existing_assessment and "overall" in existing_assessment:
            return existing_assessment
            
        # Extract security architecture
        security_architecture = architecture_design.get("security_architecture", {})
        
        findings = []
        recommendations = []
        
        # Check for required security aspects
        security_aspects = [
            "authentication",
            "authorization",
            "data_protection",
            "secure_communication"
        ]
        
        for aspect in security_aspects:
            if aspect not in security_architecture or not security_architecture[aspect]:
                findings.append(f"Missing or inadequate {aspect} specification")
                recommendations.append(f"Define a clear {aspect} approach")
                
        # Determine overall assessment
        if not findings:
            overall = "Strong"
        elif len(findings) <= 2:
            overall = "Adequate"
        else:
            overall = "Concerning"
            
        security_assessment = {
            "overall": overall,
            "findings": findings,
            "recommendations": recommendations
        }
        
        logger.info(f"Security validation completed: {overall} with {len(findings)} findings")
        return security_assessment
        
    except Exception as e:
        logger.error(f"Error validating security: {str(e)}", exc_info=True)
        return existing_assessment or {"overall": "Unknown", "findings": [], "recommendations": []}

@trace_method
def check_architecture_completeness(architecture_design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the architecture design is complete.
    
    Args:
        architecture_design: Architecture design
        
    Returns:
        Dict[str, Any]: Completeness assessment
    """
    logger.info("Checking architecture completeness")
    
    try:
        missing_elements = []
        recommendations = []
        
        # Required architecture elements
        required_elements = [
            "system_components",
            "component_relationships",
            "data_flows",
            "api_interfaces",
            "database_schema",
            "security_architecture",
            "deployment_architecture"
        ]
        
        for element in required_elements:
            if element not in architecture_design or not architecture_design[element]:
                missing_elements.append(element)
                recommendations.append(f"Add {element.replace('_', ' ')} to the architecture design")
                
        # Determine overall assessment
        if not missing_elements:
            overall = "Complete"
        elif len(missing_elements) <= 2:
            overall = "Mostly complete"
        else:
            overall = "Incomplete"
            
        completeness_assessment = {
            "overall": overall,
            "missing_elements": missing_elements,
            "recommendations": recommendations
        }
        
        logger.info(f"Completeness check: {overall} with {len(missing_elements)} missing elements")
        return completeness_assessment
        
    except Exception as e:
        logger.error(f"Error checking architecture completeness: {str(e)}", exc_info=True)
        return {"overall": "Unknown", "missing_elements": [], "recommendations": []}

@trace_method
def generate_validation_summary(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an overall validation summary.
    
    Args:
        validation_results: Detailed validation results
        
    Returns:
        Dict[str, Any]: Validation summary
    """
    logger.info("Generating validation summary")
    
    try:
        # Extract assessments from various sections
        security_overall = validation_results.get("security_assessment", {}).get("overall", "Unknown")
        completeness_overall = validation_results.get("architecture_completeness", {}).get("overall", "Unknown")
        
        # Count requirement coverage
        req_coverage = validation_results.get("requirement_coverage", [])
        covered_count = sum(1 for req in req_coverage if req.get("covered", False))
        total_count = len(req_coverage)
        coverage_percentage = (covered_count / total_count * 100) if total_count > 0 else 0
        
        # Collect strengths and concerns
        strengths = []
        concerns = []
        
        if security_overall == "Strong":
            strengths.append("Strong security architecture")
        elif security_overall == "Concerning":
            concerns.append("Security architecture needs improvement")
            
        if completeness_overall == "Complete":
            strengths.append("Complete architecture design")
        elif completeness_overall == "Incomplete":
            concerns.append("Incomplete architecture design")
            
        if coverage_percentage >= 90:
            strengths.append("Excellent requirement coverage")
        elif coverage_percentage < 70:
            concerns.append("Inadequate requirement coverage")
            
        # Determine overall assessment
        if len(concerns) == 0:
            overall_assessment = "Strong"
            score = 9
        elif len(concerns) <= 1:
            overall_assessment = "Adequate"
            score = 7
        else:
            overall_assessment = "Concerning"
            score = 5
            
        # Generate risks
        risks = []
        if security_overall == "Concerning":
            risks.append("Security vulnerabilities")
        if completeness_overall == "Incomplete":
            risks.append("Missing architecture elements")
        if coverage_percentage < 70:
            risks.append("Unaddressed requirements")
            
        validation_summary = {
            "overall_assessment": overall_assessment,
            "score": score,
            "strengths": strengths,
            "concerns": concerns,
            "risks": risks
        }
        
        logger.info(f"Generated validation summary: {overall_assessment} with score {score}")
        return validation_summary
        
    except Exception as e:
        logger.error(f"Error generating validation summary: {str(e)}", exc_info=True)
        return {
            "overall_assessment": "Unknown",
            "score": 5,
            "strengths": [],
            "concerns": ["Unable to generate proper validation summary"],
            "risks": ["Incomplete validation"]
        }

@trace_method
def perform_basic_validation(
    architecture_design: Dict[str, Any],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform basic architecture validation when LLM validation fails.
    
    Args:
        architecture_design: Architecture design
        requirements: Project requirements
        
    Returns:
        Dict[str, Any]: Basic validation results
    """
    logger.info("Performing basic validation")
    
    try:
        # Check requirement coverage
        requirement_coverage = validate_requirement_coverage([], architecture_design, requirements)
        
        # Check security aspects
        security_assessment = validate_security({}, architecture_design)
        
        # Check architecture completeness
        completeness_assessment = check_architecture_completeness(architecture_design)
        
        # Generate validation summary
        validation_summary = generate_validation_summary({
            "requirement_coverage": requirement_coverage,
            "security_assessment": security_assessment,
            "architecture_completeness": completeness_assessment
        })
        
        # Compile results
        validation_results = {
            "validation_summary": validation_summary,
            "requirement_coverage": requirement_coverage,
            "security_assessment": security_assessment,
            "architecture_completeness": completeness_assessment
        }
        
        logger.info("Basic validation completed")
        return validation_results
        
    except Exception as e:
        logger.error(f"Error performing basic validation: {str(e)}", exc_info=True)
        return {
            "validation_summary": {
                "overall_assessment": "Unknown",
                "score": 5,
                "strengths": [],
                "concerns": ["Validation failed"],
                "risks": ["Incomplete validation"]
            }
        }

# Helper functions

def extract_keywords(text: str) -> List[str]:
    """Extract key words from text."""
    # Simple implementation - in a real system, use NLP
    words = text.lower().split()
    return [w for w in words if len(w) > 3 and w not in ["the", "and", "for", "with"]]

def check_keyword_coverage(keywords: List[str], architecture_design: Dict[str, Any]) -> bool:
    """Check if keywords are covered in architecture design."""
    # Convert architecture to string for simple matching
    architecture_text = str(architecture_design).lower()
    
    # Check if at least half of the keywords are present
    matches = sum(1 for kw in keywords if kw in architecture_text)
    return matches >= len(keywords) / 2 if keywords else True