from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.qa_test.llm.qat_service import QATestLLMService

# Initialize logger
logger = setup_logger("tools.qa_test.test_generator")

@trace_method
async def generate_test_cases(
    test_plan: Dict[str, Any],
    code: Dict[str, Any],
    test_requirements: Dict[str, Any],
    llm_service: QATestLLMService
) -> Dict[str, Any]:
    """
    Generate detailed test cases based on the test plan.
    
    Args:
        test_plan: Test planning details
        code: Code to be tested
        test_requirements: Analyzed test requirements
        llm_service: QA-specific LLM service
        
    Returns:
        Dict[str, Any]: Generated test cases
    """
    logger.info("Starting test case generation")
    
    try:
        # Call LLM service to generate test cases
        test_cases = await llm_service.generate_test_cases(
            test_plan=test_plan,
            code=code,
            test_requirements=test_requirements
        )
        
        # Enhance the LLM response with additional test cases
        #test_cases = enhance_test_cases(test_cases, test_plan, code)
        
        logger.info(f"Test case generation completed with {len(test_cases.get('unit_test_cases', []))} unit test cases and {len(test_cases.get('integration_test_cases', []))} integration test cases")
        return test_cases
        
    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}", exc_info=True)
        return generate_basic_test_cases(test_plan, code)

@trace_method
def enhance_test_cases(
    test_cases: Dict[str, Any],
    test_plan: Dict[str, Any],
    code: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance the LLM-generated test cases with additional test cases or details.
    
    Args:
        test_cases: Initial test cases from LLM
        test_plan: Test planning details
        code: Code to be tested
        
    Returns:
        Dict[str, Any]: Enhanced test cases
    """
    logger.info("Enhancing test cases")
    
    try:
        enhanced = test_cases.copy()
        
        # Check if key test case categories are present
        required_categories = [
            "unit_test_cases",
            "integration_test_cases"
        ]
        
        for category in required_categories:
            if category not in enhanced or not enhanced[category]:
                logger.warning(f"Missing or empty category: {category}")
                enhanced[category] = []
        
        # Validate and enhance unit test cases
        unit_tests_plan = test_plan.get("unit_tests", [])
        unit_test_cases = enhanced.get("unit_test_cases", [])
        
        # Check for missing test cases from the plan
        plan_components = {test.get("component") for test in unit_tests_plan if "component" in test}
        case_components = {case.get("component") for case in unit_test_cases if "component" in case}
        
        missing_components = plan_components - case_components
        if missing_components:
            logger.debug(f"Found {len(missing_components)} missing components in unit test cases")
            
            # Generate basic test cases for missing components
            for component in missing_components:
                # Find the test plan for this component
                component_plan = next((test for test in unit_tests_plan if test.get("component") == component), None)
                
                if component_plan:
                    # Generate a basic test case
                    basic_case = generate_basic_unit_test_case(component_plan, len(unit_test_cases) + 1)
                    unit_test_cases.append(basic_case)
                    logger.debug(f"Added basic test case for component: {component}")
        
        # Validate and enhance integration test cases
        integration_tests_plan = test_plan.get("integration_tests", [])
        integration_test_cases = enhanced.get("integration_test_cases", [])
        
        # Check for missing test cases from the plan
        plan_integrations = [tuple(sorted(test.get("components", []))) for test in integration_tests_plan]
        case_integrations = [tuple(sorted(case.get("components", []))) for case in integration_test_cases]
        
        missing_integrations = set(plan_integrations) - set(case_integrations)
        if missing_integrations:
            logger.debug(f"Found {len(missing_integrations)} missing integrations in integration test cases")
            
            # Generate basic test cases for missing integrations
            for integration in missing_integrations:
                # Find the test plan for this integration
                integration_plan = next((
                    test for test in integration_tests_plan 
                    if tuple(sorted(test.get("components", []))) == integration
                ), None)
                
                if integration_plan:
                    # Generate a basic test case
                    basic_case = generate_basic_integration_test_case(integration_plan, len(integration_test_cases) + 1)
                    integration_test_cases.append(basic_case)
                    logger.debug(f"Added basic test case for integration: {integration}")
        
        # Ensure all test cases have the required fields
        for unit_case in unit_test_cases:
            ensure_test_case_fields(unit_case, "unit")
            
        for integration_case in integration_test_cases:
            ensure_test_case_fields(integration_case, "integration")
        
        # Check and enhance test case IDs for uniqueness
        update_test_case_ids(unit_test_cases, "UT")
        update_test_case_ids(integration_test_cases, "IT")
        
        enhanced["unit_test_cases"] = unit_test_cases
        enhanced["integration_test_cases"] = integration_test_cases
        
        logger.info("Test case enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing test cases: {str(e)}", exc_info=True)
        return test_cases

@trace_method
def generate_basic_test_cases(
    test_plan: Dict[str, Any],
    code: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate basic test cases when LLM-based generation fails.
    
    Args:
        test_plan: Test planning details
        code: Code to be tested
        
    Returns:
        Dict[str, Any]: Basic test cases
    """
    logger.info("Generating basic test cases")
    
    basic_cases = {
        "unit_test_cases": [],
        "integration_test_cases": []
    }
    
    try:
        # Generate unit test cases from unit tests plan
        for idx, test in enumerate(test_plan.get("unit_tests", []), 1):
            unit_case = generate_basic_unit_test_case(test, idx)
            basic_cases["unit_test_cases"].append(unit_case)
        
        # Generate integration test cases from integration tests plan
        for idx, test in enumerate(test_plan.get("integration_tests", []), 1):
            integration_case = generate_basic_integration_test_case(test, idx)
            basic_cases["integration_test_cases"].append(integration_case)
        
        logger.info(f"Generated {len(basic_cases['unit_test_cases'])} basic unit test cases and {len(basic_cases['integration_test_cases'])} basic integration test cases")
        return basic_cases
        
    except Exception as e:
        logger.error(f"Error generating basic test cases: {str(e)}", exc_info=True)
        # Return minimal test cases
        return {
            "unit_test_cases": [
                {
                    "id": "UT-001",
                    "name": "Basic Functionality Test",
                    "component": "Generic",
                    "objective": "Test core functionality",
                    "preconditions": ["Application is running"],
                    "test_steps": [
                        {
                            "step": "Execute core functionality",
                            "expected_result": "Operation completes successfully"
                        }
                    ],
                    "test_data": {
                        "input": "Standard input",
                        "expected_output": "Expected output"
                    },
                    "pass_criteria": ["Operation completes without errors"]
                }
            ],
            "integration_test_cases": []
        }

@trace_method
def generate_basic_unit_test_case(test_plan_entry: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Generate a basic unit test case from a test plan entry.
    
    Args:
        test_plan_entry: Entry from the unit tests plan
        index: Index for generating ID
        
    Returns:
        Dict[str, Any]: Basic unit test case
    """
    component = test_plan_entry.get("component", "Unknown")
    objective = test_plan_entry.get("test_objective", "Test functionality")
    approach = test_plan_entry.get("test_approach", "Black-box testing")
    
    # Generate test case
    test_case = {
        "id": f"UT-{index:03d}",
        "name": f"{component} - {objective}",
        "component": component,
        "objective": objective,
        "preconditions": [
            "System is in a clean state",
            f"{component} is accessible"
        ],
        "test_steps": [
            {
                "step": f"Initialize {component}",
                "expected_result": f"{component} initializes without errors"
            },
            {
                "step": "Execute test operation",
                "expected_result": "Operation completes successfully"
            },
            {
                "step": "Verify results",
                "expected_result": "Results match expected output"
            }
        ],
        "test_data": {
            "input": "Valid test input",
            "expected_output": "Expected test output"
        },
        "pass_criteria": [
            "All steps complete successfully",
            "Output matches expected results"
        ]
    }
    
    return test_case

@trace_method
def generate_basic_integration_test_case(test_plan_entry: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Generate a basic integration test case from a test plan entry.
    
    Args:
        test_plan_entry: Entry from the integration tests plan
        index: Index for generating ID
        
    Returns:
        Dict[str, Any]: Basic integration test case
    """
    components = test_plan_entry.get("components", ["Unknown"])
    objective = test_plan_entry.get("test_objective", "Test integration")
    approach = test_plan_entry.get("test_approach", "Integration testing")
    
    # Format components for display
    components_str = " and ".join(components)
    
    # Generate test case
    test_case = {
        "id": f"IT-{index:03d}",
        "name": f"Integration between {components_str}",
        "components": components,
        "objective": objective,
        "preconditions": [
            "System is in a clean state",
            f"All components ({components_str}) are accessible"
        ],
        "test_steps": [
            {
                "step": f"Initialize all components ({components_str})",
                "expected_result": "All components initialize without errors"
            },
            {
                "step": "Trigger integration flow",
                "expected_result": "Flow executes successfully"
            },
            {
                "step": "Verify integration results",
                "expected_result": "Results match expected output"
            }
        ],
        "test_data": {
            "input": "Valid integration test input",
            "expected_output": "Expected integration output"
        },
        "pass_criteria": [
            "All integration steps complete successfully",
            "Components interact as expected",
            "Output matches expected results"
        ]
    }
    
    return test_case

@trace_method
def ensure_test_case_fields(test_case: Dict[str, Any], test_type: str) -> None:
    """
    Ensure a test case has all required fields.
    
    Args:
        test_case: Test case to check and update
        test_type: Type of test case ('unit' or 'integration')
    """
    # Required fields for all test cases
    required_fields = {
        "id": f"{test_type.upper()[0]}T-001",
        "name": "Test Case",
        "objective": "Test functionality",
        "preconditions": [],
        "test_steps": [],
        "test_data": {},
        "pass_criteria": []
    }
    
    # Type-specific required fields
    if test_type == "unit":
        required_fields["component"] = "Unknown"
    elif test_type == "integration":
        required_fields["components"] = ["Unknown"]
    
    # Ensure all required fields are present
    for field, default_value in required_fields.items():
        if field not in test_case or test_case[field] is None:
            test_case[field] = default_value
    
    # Ensure test steps has required structure
    if not test_case["test_steps"]:
        test_case["test_steps"] = [
            {
                "step": "Execute test",
                "expected_result": "Test completes successfully"
            }
        ]
    else:
        for step in test_case["test_steps"]:
            if "step" not in step:
                step["step"] = "Execute test"
            if "expected_result" not in step:
                step["expected_result"] = "Test completes successfully"
    
    # Ensure test data has required structure
    if not test_case["test_data"]:
        test_case["test_data"] = {
            "input": "Test input",
            "expected_output": "Expected output"
        }
    
    # Ensure pass criteria has at least one entry
    if not test_case["pass_criteria"]:
        test_case["pass_criteria"] = ["Test completes successfully"]

@trace_method
def update_test_case_ids(test_cases: List[Dict[str, Any]], prefix: str) -> None:
    """
    Update test case IDs to ensure uniqueness.
    
    Args:
        test_cases: List of test cases to update
        prefix: ID prefix ('UT' for unit tests, 'IT' for integration tests)
    """
    # Sort test cases by existing ID if possible
    test_cases.sort(key=lambda tc: tc.get("id", ""))
    
    # Update IDs to ensure correct sequence
    for idx, test_case in enumerate(test_cases, 1):
        test_case["id"] = f"{prefix}-{idx:03d}"