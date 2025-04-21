from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.qa_test.llm.qat_service import QATestLLMService

# Initialize logger
logger = setup_logger("tools.qa_test.test_analyzer")

@trace_method
async def analyze_test_requirements(
    code: Dict[str, Any], 
    specifications: Dict[str, Any],
    input_description: str,
    llm_service: QATestLLMService
) -> Dict[str, Any]:
    """
    Analyze code and specifications to determine test requirements.
    
    Args:
        code: Code to be tested
        specifications: Technical specifications
        input_description: Project description
        llm_service: QA-specific LLM service
        
    Returns:
        Dict[str, Any]: Analyzed test requirements
    """
    logger.info("Starting test requirements analysis")
    
    try:
        # Call LLM service to analyze test requirements
        requirements = await llm_service.analyze_test_requirements(
            code=code,
            specifications=specifications,
            input_description=input_description
        )
        
        # Enhance the LLM response with additional analysis
        #requirements = enhance_test_requirements(requirements, code, specifications)
        
        logger.info(f"Test requirements analysis completed with {len(requirements.get('functional_test_requirements', []))} functional requirements")
        return requirements
        
    except Exception as e:
        logger.error(f"Error analyzing test requirements: {str(e)}", exc_info=True)
        return {
            "functional_test_requirements": [],
            "integration_test_requirements": [],
            "security_test_requirements": [],
            "performance_test_requirements": []
        }

@trace_method
def enhance_test_requirements(
    requirements: Dict[str, Any], 
    code: Dict[str, Any],
    specifications: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance the LLM-generated test requirements with additional analysis.
    
    Args:
        requirements: Initial test requirements from LLM
        code: Code to be tested
        specifications: Technical specifications
        
    Returns:
        Dict[str, Any]: Enhanced test requirements
    """
    logger.info("Enhancing test requirements")
    
    try:
        enhanced = requirements.copy()
        
        # Check if key test categories are present
        required_categories = [
            "functional_test_requirements",
            "integration_test_requirements",
            "security_test_requirements",
            "performance_test_requirements"
        ]
        
        for category in required_categories:
            if category not in enhanced or not enhanced[category]:
                logger.warning(f"Missing or empty category: {category}")
                enhanced[category] = []
        
        # Check for API testing requirements if APIs are in specifications
        if "api_specifications" in specifications and specifications["api_specifications"]:
            api_test_requirements = generate_api_test_requirements(specifications["api_specifications"])
            
            # Add API test requirements to functional requirements
            for api_req in api_test_requirements:
                if api_req not in enhanced["functional_test_requirements"]:
                    enhanced["functional_test_requirements"].append(api_req)
            
            logger.debug(f"Added {len(api_test_requirements)} API test requirements")
        
        # Add database test requirements if database specifications exist
        if "database_specifications" in specifications and specifications["database_specifications"]:
            db_test_requirements = generate_database_test_requirements(specifications["database_specifications"])
            
            # Add database test requirements to functional requirements
            for db_req in db_test_requirements:
                if db_req not in enhanced["functional_test_requirements"]:
                    enhanced["functional_test_requirements"].append(db_req)
            
            logger.debug(f"Added {len(db_test_requirements)} database test requirements")
        
        # Add security test requirements based on code analysis
        if not enhanced["security_test_requirements"]:
            security_test_reqs = generate_basic_security_test_requirements(code)
            enhanced["security_test_requirements"] = security_test_reqs
            logger.debug(f"Added {len(security_test_reqs)} basic security test requirements")
        
        # Add performance test requirements if not present
        if not enhanced["performance_test_requirements"]:
            perf_test_reqs = generate_basic_performance_test_requirements(code)
            enhanced["performance_test_requirements"] = perf_test_reqs
            logger.debug(f"Added {len(perf_test_reqs)} basic performance test requirements")
        
        logger.info("Test requirements enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing test requirements: {str(e)}", exc_info=True)
        return requirements

@trace_method
def generate_api_test_requirements(api_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate test requirements for APIs based on specifications.
    
    Args:
        api_specs: API specifications
        
    Returns:
        List[Dict[str, Any]]: API test requirements
    """
    logger.debug("Generating API test requirements")
    
    api_test_requirements = []
    
    try:
        for api in api_specs:
            api_name = api.get("api_name", "Unknown API")
            
            for endpoint in api.get("endpoints", []):
                path = endpoint.get("path", "")
                method = endpoint.get("method", "")
                description = endpoint.get("description", "")
                
                # Create test requirement for this endpoint
                requirement = {
                    "component": f"{api_name} API",
                    "functionality": f"{method} {path}",
                    "expected_behavior": f"API should {description}",
                    "priority": "HIGH",
                    "potential_edge_cases": [
                        "Invalid input parameters",
                        "Authentication failure",
                        "Server error handling"
                    ]
                }
                
                api_test_requirements.append(requirement)
        
        logger.debug(f"Generated {len(api_test_requirements)} API test requirements")
        return api_test_requirements
        
    except Exception as e:
        logger.error(f"Error generating API test requirements: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_database_test_requirements(db_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate test requirements for databases based on specifications.
    
    Args:
        db_specs: Database specifications
        
    Returns:
        List[Dict[str, Any]]: Database test requirements
    """
    logger.debug("Generating database test requirements")
    
    db_test_requirements = []
    
    try:
        for db in db_specs:
            db_name = db.get("database", "Unknown Database")
            db_type = db.get("type", "")
            
            # Create general database test requirement
            general_req = {
                "component": f"{db_name} Database",
                "functionality": "Database connection and basic operations",
                "expected_behavior": f"Should connect to {db_type} database and perform CRUD operations",
                "priority": "HIGH",
                "potential_edge_cases": [
                    "Connection failure",
                    "Transaction rollback",
                    "Concurrent access"
                ]
            }
            
            db_test_requirements.append(general_req)
            
            # Add entity-specific test requirements
            for entity in db.get("entities", []):
                entity_name = entity.get("name", "Unknown Entity")
                
                entity_req = {
                    "component": f"{db_name} Database - {entity_name}",
                    "functionality": f"{entity_name} data management",
                    "expected_behavior": f"Should create, read, update, and delete {entity_name} records",
                    "priority": "MEDIUM",
                    "potential_edge_cases": [
                        "Invalid data",
                        "Missing required fields",
                        "Relationship constraints"
                    ]
                }
                
                db_test_requirements.append(entity_req)
        
        logger.debug(f"Generated {len(db_test_requirements)} database test requirements")
        return db_test_requirements
        
    except Exception as e:
        logger.error(f"Error generating database test requirements: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_basic_security_test_requirements(code: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate basic security test requirements based on code analysis.
    
    Args:
        code: Code to be tested
        
    Returns:
        List[Dict[str, Any]]: Basic security test requirements
    """
    logger.debug("Generating basic security test requirements")
    
    # Default security test requirements
    security_reqs = [
        {
            "component": "Authentication",
            "vulnerability_type": "Authentication bypass",
            "test_approach": "Test for authentication validation, session management, and token validation",
            "priority": "HIGH"
        },
        {
            "component": "API Endpoints",
            "vulnerability_type": "Injection attacks",
            "test_approach": "Test for SQL injection, XSS, and CSRF vulnerabilities",
            "priority": "HIGH"
        },
        {
            "component": "Data Storage",
            "vulnerability_type": "Data exposure",
            "test_approach": "Verify proper encryption of sensitive data",
            "priority": "MEDIUM"
        },
        {
            "component": "Input Validation",
            "vulnerability_type": "Input validation bypass",
            "test_approach": "Test with malformed, boundary, and unexpected inputs",
            "priority": "MEDIUM"
        }
    ]
    
    # Check for component-specific security requirements
    for component, content in code.items():
        # Check for authentication components
        if "auth" in component.lower() or "login" in component.lower():
            auth_req = {
                "component": component,
                "vulnerability_type": "Authentication vulnerabilities",
                "test_approach": "Test for weak passwords, brute force protection, and account lockout",
                "priority": "HIGH"
            }
            security_reqs.append(auth_req)
        
        # Check for API components
        if "api" in component.lower() or "endpoint" in component.lower():
            api_req = {
                "component": component,
                "vulnerability_type": "API security",
                "test_approach": "Test for proper authentication, authorization, and input validation",
                "priority": "HIGH"
            }
            security_reqs.append(api_req)
    
    logger.debug(f"Generated {len(security_reqs)} basic security test requirements")
    return security_reqs

@trace_method
def generate_basic_performance_test_requirements(code: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate basic performance test requirements based on code analysis.
    
    Args:
        code: Code to be tested
        
    Returns:
        List[Dict[str, Any]]: Basic performance test requirements
    """
    logger.debug("Generating basic performance test requirements")
    
    # Default performance test requirements
    perf_reqs = [
        {
            "component": "API Endpoints",
            "performance_aspect": "Response time",
            "benchmark": "API responses should be within 200ms under normal load",
            "priority": "HIGH"
        },
        {
            "component": "Database Operations",
            "performance_aspect": "Query performance",
            "benchmark": "Database queries should complete within 100ms",
            "priority": "MEDIUM"
        },
        {
            "component": "Overall System",
            "performance_aspect": "Load testing",
            "benchmark": "System should handle 100 concurrent users with acceptable response times",
            "priority": "MEDIUM"
        },
        {
            "component": "Resource Usage",
            "performance_aspect": "Memory and CPU usage",
            "benchmark": "Application should maintain stable resource utilization under normal load",
            "priority": "LOW"
        }
    ]
    
    # Check for component-specific performance requirements
    for component, content in code.items():
        # Check for database components
        if "database" in component.lower() or "db" in component.lower():
            db_req = {
                "component": component,
                "performance_aspect": "Database performance",
                "benchmark": "Database operations should be optimized for performance",
                "priority": "HIGH"
            }
            perf_reqs.append(db_req)
        
        # Check for frontend components
        if "ui" in component.lower() or "frontend" in component.lower():
            ui_req = {
                "component": component,
                "performance_aspect": "UI rendering",
                "benchmark": "UI should render within 300ms",
                "priority": "MEDIUM"
            }
            perf_reqs.append(ui_req)
    
    logger.debug(f"Generated {len(perf_reqs)} basic performance test requirements")
    return perf_reqs