from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.qa_test.llm.qat_service import QATestLLMService

# Initialize logger
logger = setup_logger("tools.qa_test.test_planner")

# Define common testing tools/frameworks
TESTING_TOOLS = {
    "unit": {
        "python": ["pytest", "unittest"],
        "javascript": ["jest", "mocha", "chai"],
        "java": ["JUnit", "TestNG"]
    },
    "integration": {
        "api": ["Postman", "REST-assured", "Supertest"],
        "database": ["TestContainers", "dbunit"]
    },
    "security": ["OWASP ZAP", "SonarQube", "Snyk"],
    "performance": ["JMeter", "Locust", "Artillery"]
}

@trace_method
async def create_test_plan(
    test_requirements: Dict[str, Any],
    llm_service: QATestLLMService
) -> Dict[str, Any]:
    """
    Create a test plan based on the analyzed test requirements.
    
    Args:
        test_requirements: Analyzed test requirements
        llm_service: QA-specific LLM service
        
    Returns:
        Dict[str, Any]: Test plan with testing approaches and tools
    """
    logger.info("Starting test plan creation")
    
    try:
        # Call LLM service to create the test plan
        test_plan = await llm_service.create_test_plan(test_requirements)
        
        # Enhance the LLM response with additional planning
        # test_plan = enhance_test_plan(test_plan, test_requirements)
        
        logger.info(f"Test plan creation completed with {len(test_plan.get('unit_tests', []))} unit tests and {len(test_plan.get('integration_tests', []))} integration tests")
        return test_plan
       
    except Exception as e:
        logger.error(f"Error creating test plan: {str(e)}", exc_info=True)
        return generate_basic_test_plan(test_requirements)

@trace_method
def enhance_test_plan(
    test_plan: Dict[str, Any],
    test_requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance the LLM-generated test plan with additional planning details.
    
    Args:
        test_plan: Initial test plan from LLM
        test_requirements: Analyzed test requirements
        
    Returns:
        Dict[str, Any]: Enhanced test plan
    """
    logger.info("Enhancing test plan")
    
    try:
        enhanced = test_plan.copy()
        
        # Check if key test categories are present
        required_categories = [
            "unit_tests",
            "integration_tests",
            "security_tests",
            "performance_tests",
            "test_environment",
            "test_sequence"
        ]
        
        for category in required_categories:
            if category not in enhanced or not enhanced[category]:
                logger.warning(f"Missing or empty category: {category}")
                if category == "test_environment":
                    enhanced[category] = {
                        "requirements": ["Development environment"],
                        "configurations": ["Standard configuration"]
                    }
                elif category == "test_sequence":
                    enhanced[category] = ["Unit Tests", "Integration Tests", "Security Tests", "Performance Tests"]
                else:
                    enhanced[category] = []
        
        # Check and enhance testing tools
        for unit_test in enhanced["unit_tests"]:
            if "test_tools" not in unit_test or not unit_test["test_tools"]:
                # Add default unit testing tools
                unit_test["test_tools"] = TESTING_TOOLS["unit"]["python"] + TESTING_TOOLS["unit"]["javascript"]
        
        for integration_test in enhanced["integration_tests"]:
            if "test_tools" not in integration_test or not integration_test["test_tools"]:
                # Add default integration testing tools
                integration_test["test_tools"] = TESTING_TOOLS["integration"]["api"]
        
        # Enhance security tests
        if not enhanced["security_tests"] and "security_test_requirements" in test_requirements:
            for sec_req in test_requirements.get("security_test_requirements", []):
                security_test = {
                    "component": sec_req.get("component", "Unknown"),
                    "test_objective": f"Test for {sec_req.get('vulnerability_type', 'security vulnerabilities')}",
                    "test_approach": sec_req.get("test_approach", "Standard security testing"),
                    "test_tools": TESTING_TOOLS["security"]
                }
                enhanced["security_tests"].append(security_test)
        
        # Enhance performance tests
        if not enhanced["performance_tests"] and "performance_test_requirements" in test_requirements:
            for perf_req in test_requirements.get("performance_test_requirements", []):
                performance_test = {
                    "component": perf_req.get("component", "Unknown"),
                    "test_objective": f"Test {perf_req.get('performance_aspect', 'performance')}",
                    "test_approach": "Load and stress testing",
                    "test_tools": TESTING_TOOLS["performance"],
                    "metrics": ["Response time", "Throughput", "Resource utilization"]
                }
                enhanced["performance_tests"].append(performance_test)
        
        logger.info("Test plan enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing test plan: {str(e)}", exc_info=True)
        return test_plan

@trace_method
def generate_basic_test_plan(test_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a basic test plan when LLM-based plan creation fails.
    
    Args:
        test_requirements: Analyzed test requirements
        
    Returns:
        Dict[str, Any]: Basic test plan
    """
    logger.info("Generating basic test plan")
    
    basic_plan = {
        "unit_tests": [],
        "integration_tests": [],
        "security_tests": [],
        "performance_tests": [],
        "test_environment": {
            "requirements": ["Development environment"],
            "configurations": ["Standard configuration"]
        },
        "test_sequence": [
            "Unit Tests",
            "Integration Tests",
            "Security Tests",
            "Performance Tests"
        ]
    }
    
    try:
        # Generate unit tests from functional requirements
        for req in test_requirements.get("functional_test_requirements", []):
            component = req.get("component", "Unknown")
            functionality = req.get("functionality", "")
            expected_behavior = req.get("expected_behavior", "")
            
            unit_test = {
                "component": component,
                "test_objective": f"Test {functionality}",
                "test_approach": "Black-box and white-box testing",
                "test_tools": TESTING_TOOLS["unit"]["python"] + TESTING_TOOLS["unit"]["javascript"][:1],
                "test_data_requirements": ["Valid inputs", "Invalid inputs", "Edge cases"],
                "dependencies": []
            }
            
            basic_plan["unit_tests"].append(unit_test)
        
        # Generate integration tests from integration requirements
        for req in test_requirements.get("integration_test_requirements", []):
            components = req.get("components", ["Unknown"])
            interaction = req.get("interaction", "")
            expected_behavior = req.get("expected_behavior", "")
            
            integration_test = {
                "components": components,
                "test_objective": f"Test {interaction}",
                "test_approach": "Component integration testing",
                "test_tools": TESTING_TOOLS["integration"]["api"],
                "test_data_requirements": ["Integration test data"],
                "dependencies": []
            }
            
            basic_plan["integration_tests"].append(integration_test)
        
        # Generate security tests from security requirements
        for req in test_requirements.get("security_test_requirements", []):
            component = req.get("component", "Unknown")
            vulnerability_type = req.get("vulnerability_type", "")
            test_approach = req.get("test_approach", "")
            
            security_test = {
                "component": component,
                "test_objective": f"Test for {vulnerability_type}",
                "test_approach": test_approach,
                "test_tools": TESTING_TOOLS["security"]
            }
            
            basic_plan["security_tests"].append(security_test)
        
        # Generate performance tests from performance requirements
        for req in test_requirements.get("performance_test_requirements", []):
            component = req.get("component", "Unknown")
            performance_aspect = req.get("performance_aspect", "")
            benchmark = req.get("benchmark", "")
            
            performance_test = {
                "component": component,
                "test_objective": f"Test {performance_aspect}",
                "test_approach": "Load and stress testing",
                "test_tools": TESTING_TOOLS["performance"],
                "metrics": ["Response time", "Throughput", "Resource utilization"]
            }
            
            basic_plan["performance_tests"].append(performance_test)
        
        logger.info(f"Generated basic test plan with {len(basic_plan['unit_tests'])} unit tests")
        return basic_plan
        
    except Exception as e:
        logger.error(f"Error generating basic test plan: {str(e)}", exc_info=True)
        # Return a minimal test plan
        return {
            "unit_tests": [
                {
                    "component": "Generic",
                    "test_objective": "Test core functionality",
                    "test_approach": "Black-box testing",
                    "test_tools": ["pytest"],
                    "test_data_requirements": ["Standard test data"],
                    "dependencies": []
                }
            ],
            "integration_tests": [],
            "security_tests": [],
            "performance_tests": [],
            "test_environment": {
                "requirements": ["Development environment"],
                "configurations": ["Standard configuration"]
            },
            "test_sequence": ["Unit Tests"]
        }

@trace_method
def prioritize_tests(test_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prioritize tests in the test plan based on criticality.
    
    Args:
        test_plan: Test plan to prioritize
        
    Returns:
        Dict[str, Any]: Test plan with prioritized tests
    """
    logger.info("Prioritizing tests")
    
    try:
        prioritized_plan = test_plan.copy()
        
        # Define priority criteria
        priority_criteria = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        
        # Prioritize unit tests
        if "unit_tests" in prioritized_plan:
            # Sort unit tests by implicit priority (assuming earlier tests are more important)
            prioritized_plan["unit_tests"] = sorted(
                prioritized_plan["unit_tests"],
                key=lambda t: priority_criteria.get(t.get("priority", "MEDIUM"), 2),
                reverse=True
            )
        
        # Prioritize integration tests
        if "integration_tests" in prioritized_plan:
            # Sort integration tests by implicit priority
            prioritized_plan["integration_tests"] = sorted(
                prioritized_plan["integration_tests"],
                key=lambda t: priority_criteria.get(t.get("priority", "MEDIUM"), 2),
                reverse=True
            )
        
        # Add priority field if not present
        for test_category in ["unit_tests", "integration_tests", "security_tests", "performance_tests"]:
            if test_category in prioritized_plan:
                for test in prioritized_plan[test_category]:
                    if "priority" not in test:
                        # Determine priority based on component criticality
                        component = test.get("component", "").lower()
                        if "auth" in component or "security" in component:
                            test["priority"] = "HIGH"
                        elif "api" in component or "database" in component:
                            test["priority"] = "MEDIUM"
                        else:
                            test["priority"] = "LOW"
        
        logger.info("Test prioritization completed")
        return prioritized_plan
        
    except Exception as e:
        logger.error(f"Error prioritizing tests: {str(e)}", exc_info=True)
        return test_plan