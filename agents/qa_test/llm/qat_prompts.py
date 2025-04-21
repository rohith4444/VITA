from typing import Dict, List, Any, Optional
import json

from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("qa_test.llm.prompts")

#Helper functions - defined before they're used
def get_framework_specific_instructions(language: str, framework: str) -> str:
    """Get framework-specific instructions for the prompt."""
    if language == "javascript" and framework == "jest":
        return """
        - Use Jest's describe() and test() or it() functions
        - Use expect() with appropriate matchers
        - Mock dependencies using jest.fn() or jest.mock()
        - Use beforeEach() for test setup
        - Use async/await for asynchronous tests
        - Export nothing (tests are auto-discovered)
        """
    elif language == "python" and framework == "pytest":
        return """
        - Use pytest's function-based tests (def test_something())
        - Use pytest fixtures for setup
        - Use assert statements for verification
        - Use the monkeypatch fixture for mocking
        - Use pytest.mark decorators for categorization
        - Use async/await with pytest.mark.asyncio for async tests
        """
    elif language == "python" and framework == "unittest":
        return """
        - Create test classes that inherit from unittest.TestCase
        - Use setUp and tearDown methods for setup/cleanup
        - Use self.assert* methods for verification
        - Use unittest.mock for mocking
        - Use async test methods with self.loop.run_until_complete
        - Use if __name__ == '__main__': unittest.main() at the end
        """
    elif language == "java" and framework == "junit":
        return """
        - Use @Test annotation for test methods
        - Use JUnit 5 assertions (assertEquals, assertTrue, etc.)
        - Use @BeforeEach and @AfterEach for setup/cleanup
        - Use @Mock annotation for mocking
        - Use assertThrows for exception testing
        - Create a test class for each component
        """
    else:
        return f"Generate idiomatic test code for {framework} in {language}."

def get_example_test(language: str, framework: str) -> str:
    """Get an example test for few-shot learning."""
    if language == "javascript" and framework == "jest":
        return """
        // UserService.test.js
        jest.mock('../repositories/UserRepository');
        
        describe('UserService', () => {
          let userService;
          let mockUserRepository;
          
          beforeEach(() => {
            mockUserRepository = {
              findById: jest.fn(),
              create: jest.fn(),
              update: jest.fn(),
              delete: jest.fn()
            };
            userService = new UserService(mockUserRepository);
          });
          
          test('should create a user when valid data is provided', async () => {
            // Arrange
            const userData = { email: 'test@example.com', password: 'password123' };
            mockUserRepository.create.mockResolvedValue({ id: '123', ...userData });
            
            // Act
            const result = await userService.create(userData);
            
            // Assert
            expect(mockUserRepository.create).toHaveBeenCalledWith(userData);
            expect(result).toEqual({ id: '123', ...userData });
          });
          
          test('should throw error when creating user without required fields', async () => {
            // Arrange
            const userData = { email: 'test@example.com' }; // Missing password
            
            // Act & Assert
            await expect(userService.create(userData)).rejects.toThrow('Email and password are required');
            expect(mockUserRepository.create).not.toHaveBeenCalled();
          });
        });
        """
    elif language == "python" and framework == "pytest":
        return """
        # test_user_service.py
        import pytest
        from unittest.mock import MagicMock
        from app.services.user_service import UserService
        
        @pytest.fixture
        def user_repository():
            mock = MagicMock()
            mock.find_by_id = MagicMock()
            mock.create = MagicMock()
            mock.update = MagicMock()
            mock.delete = MagicMock()
            return mock
            
        @pytest.fixture
        def user_service(user_repository):
            return UserService(user_repository)
            
        def test_create_user_with_valid_data(user_service, user_repository):
            # Arrange
            user_data = {"email": "test@example.com", "password": "password123"}
            user_repository.create.return_value = {"id": "123", **user_data}
            
            # Act
            result = user_service.create(user_data)
            
            # Assert
            user_repository.create.assert_called_once_with(user_data)
            assert result == {"id": "123", **user_data}
            
        def test_create_user_with_missing_data(user_service, user_repository):
            # Arrange
            user_data = {"email": "test@example.com"}  # Missing password
            
            # Act & Assert
            with pytest.raises(ValueError, match="Email and password are required"):
                user_service.create(user_data)
            user_repository.create.assert_not_called()
        """
    else:
        return "Example test not available for this language/framework combination."

def get_file_extension(language: str) -> str:
    """Get file extension for the programming language."""
    if language == "python":
        return "py"
    elif language == "java":
        return "java"
    else:  # Default to JavaScript
        return "js"

@trace_method
def format_test_requirements_analysis_prompt(
    code: Dict[str, Any], 
    specifications: Dict[str, Any],
    input_description: str,
    components_to_test: Optional[Dict[str, Any]] = None,
    dependencies: Optional[Dict[str, List[str]]] = None,
    task_priority: Optional[str] = None
) -> str:
    """
    Format the prompt for analyzing test requirements with Team Lead directives.
    
    Args:
        code: Code to be tested, organized by components
        specifications: Technical specifications
        input_description: Project description and requirements
        components_to_test: Specific components to test, as directed by Team Lead
        dependencies: Component dependencies for integration testing
        task_priority: Priority level from Team Lead (HIGH/MEDIUM/LOW)
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting test requirements analysis prompt")
    
    try:
        # Extract code samples for the prompt (prioritize specified components if any)
        code_samples = ""
        if components_to_test:
            logger.debug(f"Using Team Lead specified components: {list(components_to_test.keys())}")
            for component, details in components_to_test.items():
                if component in code:
                    content = code[component]
                    if isinstance(content, str):
                        code_samples += f"\n--- {component} (PRIORITY COMPONENT) ---\n{content[:1000]}..."
                    elif isinstance(content, dict) and "content" in content:
                        code_samples += f"\n--- {component} (PRIORITY COMPONENT) ---\n{content['content'][:1000]}..."
        
        # Add remaining components if needed
        for component, content in code.items():
            # Skip if already included in priority components
            if components_to_test and component in components_to_test:
                continue
                
            if isinstance(content, str):
                code_samples += f"\n--- {component} ---\n{content[:1000]}..."
            elif isinstance(content, dict) and "content" in content:
                code_samples += f"\n--- {component} ---\n{content['content'][:1000]}..."
        
        # Extract specifications for the prompt
        spec_summary = ""
        if "component_specifications" in specifications:
            for comp in specifications.get("component_specifications", [])[:3]:
                comp_name = comp.get("component", "Unknown")
                purpose = comp.get("purpose", "")
                functionality = "\n".join([f"- {f}" for f in comp.get("functionality", [])[:3]])
                spec_summary += f"\n### {comp_name} ###\nPurpose: {purpose}\nFunctionality:\n{functionality}\n"
        
        # Format API specifications if available
        api_specs = ""
        if "api_specifications" in specifications:
            for api in specifications.get("api_specifications", [])[:2]:
                api_name = api.get("api_name", "Unknown API")
                endpoints = api.get("endpoints", [])[:3]
                api_specs += f"\n### {api_name} ###\n"
                for endpoint in endpoints:
                    path = endpoint.get("path", "")
                    method = endpoint.get("method", "")
                    desc = endpoint.get("description", "")
                    api_specs += f"- {method} {path}: {desc}\n"
        
        # Format dependencies information if available
        dependencies_info = ""
        if dependencies:
            dependencies_info = "\nCOMPONENT DEPENDENCIES:\n"
            for component, deps in dependencies.items():
                if deps:
                    dependencies_info += f"{component} depends on: {', '.join(deps)}\n"
        
        # Add priority instructions if provided
        priority_instructions = ""
        if task_priority:
            if task_priority == "HIGH":
                priority_instructions = "\nTEST PRIORITY: HIGH\nThis is a critical component requiring thorough testing. Focus on exhaustive test coverage including edge cases, error conditions, and performance aspects."
            elif task_priority == "LOW":
                priority_instructions = "\nTEST PRIORITY: LOW\nFocus on basic functionality testing. Prioritize core features and common use cases."
            else:  # MEDIUM
                priority_instructions = "\nTEST PRIORITY: MEDIUM\nBalance thorough testing with efficient use of resources. Cover main functionality and important edge cases."

        formatted_prompt = f"""
        As a Quality Assurance specialist working as part of a coordinated team, analyze the following code and specifications to determine testing requirements:

        PROJECT DESCRIPTION:
        {input_description[:500]}...

        CODE SAMPLES:
        {code_samples}

        SPECIFICATIONS:
        {spec_summary}

        API SPECIFICATIONS:
        {api_specs}
        {dependencies_info}
        {priority_instructions}

        Please analyze the code and specifications to identify test requirements. Focus on:
        1. Functional requirements that need to be tested
        2. Critical components and their dependencies
        3. Expected behaviors and edge cases
        4. Potential failure points
        5. Security considerations
        6. Performance aspects
        {"7. Emphasize thorough testing of priority components" if components_to_test else ""}
        {"8. Pay special attention to integration points between dependent components" if dependencies else ""}

        Format your response as a JSON object with:
        {{
            "functional_test_requirements": [
                {{
                    "component": "Component name",
                    "functionality": "Functionality to test",
                    "expected_behavior": "Expected behavior",
                    "priority": "HIGH/MEDIUM/LOW",
                    "potential_edge_cases": ["Edge case 1", "Edge case 2"]
                }}
            ],
            "integration_test_requirements": [
                {{
                    "components": ["Component 1", "Component 2"],
                    "interaction": "How components interact",
                    "expected_behavior": "Expected behavior",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "security_test_requirements": [
                {{
                    "component": "Component name",
                    "vulnerability_type": "Type of vulnerability",
                    "test_approach": "How to test for this vulnerability",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "performance_test_requirements": [
                {{
                    "component": "Component name",
                    "performance_aspect": "Aspect to test (speed, memory, etc.)",
                    "benchmark": "Expected performance",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Test requirements analysis prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting test requirements prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_test_planning_prompt(
    test_requirements: Dict[str, Any],
    task_priority: Optional[str] = None,
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for test planning based on analyzed requirements with Team Lead directives.
    
    Args:
        test_requirements: Analyzed test requirements
        task_priority: Priority level from Team Lead (HIGH/MEDIUM/LOW)
        project_structure: Project structure information from Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting test planning prompt")
    
    try:
        # Format functional test requirements for the prompt
        functional_reqs = ""
        for idx, req in enumerate(test_requirements.get("functional_test_requirements", []), 1):
            component = req.get("component", "Unknown")
            functionality = req.get("functionality", "")
            expected = req.get("expected_behavior", "")
            priority = req.get("priority", "MEDIUM")
            
            functional_reqs += f"""
            {idx}. Component: {component}
               Functionality: {functionality}
               Expected Behavior: {expected}
               Priority: {priority}
            """
        
        # Format integration test requirements
        integration_reqs = ""
        for idx, req in enumerate(test_requirements.get("integration_test_requirements", []), 1):
            components = ", ".join(req.get("components", ["Unknown"]))
            interaction = req.get("interaction", "")
            expected = req.get("expected_behavior", "")
            priority = req.get("priority", "MEDIUM")
            
            integration_reqs += f"""
            {idx}. Components: {components}
               Interaction: {interaction}
               Expected Behavior: {expected}
               Priority: {priority}
            """
        
        # Include other test requirements
        security_reqs = "\n".join([
            f"- {req.get('component', '')}: {req.get('vulnerability_type', '')}" 
            for req in test_requirements.get("security_test_requirements", [])[:3]
        ])
        
        performance_reqs = "\n".join([
            f"- {req.get('component', '')}: {req.get('performance_aspect', '')}" 
            for req in test_requirements.get("performance_test_requirements", [])[:3]
        ])
        
        # Add priority instructions if provided
        priority_instructions = ""
        if task_priority:
            if task_priority == "HIGH":
                priority_instructions = "\nTEST PRIORITY: HIGH\nCreate a comprehensive test plan with thorough coverage. Include extensive edge case testing and performance validation. Allocate resources for thorough review cycles."
            elif task_priority == "LOW":
                priority_instructions = "\nTEST PRIORITY: LOW\nCreate a focused test plan covering core functionality. Prioritize essential test cases. Optimize for testing efficiency."
            else:  # MEDIUM
                priority_instructions = "\nTEST PRIORITY: MEDIUM\nCreate a balanced test plan with good coverage of functionality and important edge cases. Include key performance tests."
        
        # Add project structure guidance if available
        structure_guidance = ""
        if project_structure:
            structure_guidance = "\nPROJECT STRUCTURE GUIDANCE:\nEnsure test organization mirrors the project structure for traceability. Organize tests to reflect the following component organization:\n"
            for component_type, paths in project_structure.items():
                structure_guidance += f"- {component_type}: {', '.join(paths)}\n"

        formatted_prompt = f"""
        As a Test Planner working in a coordinated team environment, create a comprehensive test plan based on the following requirements:

        FUNCTIONAL TEST REQUIREMENTS:
        {functional_reqs}

        INTEGRATION TEST REQUIREMENTS:
        {integration_reqs}

        SECURITY TEST REQUIREMENTS:
        {security_reqs}

        PERFORMANCE TEST REQUIREMENTS:
        {performance_reqs}
        {priority_instructions}
        {structure_guidance}

        Create a structured test plan that outlines how to test each requirement. For each category of tests, specify:
        1. The testing approach
        2. Testing tools/frameworks to use
        3. Testing environment requirements
        4. Test data requirements
        5. Test sequence and dependencies
        {"6. Organization that mirrors the project structure" if project_structure else ""}
        {"7. Test prioritization approach based on the task priority" if task_priority else ""}

        Format your response as a JSON object with:
        {{
            "unit_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "test_data_requirements": ["Data requirement 1", "Data requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "integration_tests": [
                {{
                    "components": ["Component 1", "Component 2"],
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "test_data_requirements": ["Data requirement 1", "Data requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "security_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "performance_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "metrics": ["Metric 1", "Metric 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "test_environment": {{
                "requirements": ["Requirement 1", "Requirement 2"],
                "configurations": ["Configuration 1", "Configuration 2"]
            }},
            "test_sequence": [
                "Step 1",
                "Step 2"
            ],
            "organization": {{
                "structure": "Description of how tests are organized",
                "mapping": "How tests map to project components"
            }}
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Test planning prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting test planning prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_test_case_generation_prompt(
    test_plan: Dict[str, Any], 
    code: Dict[str, Any],
    test_requirements: Dict[str, Any],
    components_to_test: Optional[Dict[str, Any]] = None,
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating test cases based on the test plan with Team Lead directives.
    
    Args:
        test_plan: Test planning details
        code: Code to be tested
        test_requirements: Analyzed test requirements
        components_to_test: Specific components to test, as directed by Team Lead
        project_structure: Project structure information from Team Lead
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting test case generation prompt")
    
    try:
        # Extract unit tests from the test plan
        unit_tests_plan = ""
        for idx, test in enumerate(test_plan.get("unit_tests", []), 1):
            component = test.get("component", "Unknown")
            objective = test.get("test_objective", "")
            approach = test.get("test_approach", "")
            priority = test.get("priority", "MEDIUM")
            
            # Mark priority components
            priority_marker = ""
            if components_to_test and component in components_to_test:
                priority_marker = " [PRIORITY]"
            
            unit_tests_plan += f"""
            {idx}. Component: {component}{priority_marker}
               Objective: {objective}
               Approach: {approach}
               Priority: {priority}
            """
        
        # Extract integration tests from the test plan
        integration_tests_plan = ""
        for idx, test in enumerate(test_plan.get("integration_tests", []), 1):
            components = ", ".join(test.get("components", ["Unknown"]))
            objective = test.get("test_objective", "")
            approach = test.get("test_approach", "")
            priority = test.get("priority", "MEDIUM")
            
            # Mark priority components
            priority_marker = ""
            if components_to_test and any(comp in components_to_test for comp in test.get("components", [])):
                priority_marker = " [PRIORITY]"
            
            integration_tests_plan += f"""
            {idx}. Components: {components}{priority_marker}
               Objective: {objective}
               Approach: {approach}
               Priority: {priority}
            """
        
        # Extract relevant code for the tested components
        code_samples = ""
        # Get component names from test plan
        component_names = set()
        for test in test_plan.get("unit_tests", []):
            component_names.add(test.get("component", ""))
        for test in test_plan.get("integration_tests", []):
            component_names.update(test.get("components", []))
        
        # Prioritize components directed by Team Lead
        priority_components = []
        if components_to_test:
            priority_components = list(components_to_test.keys())
            
            # Add prioritized components first
            for component in priority_components:
                if component in code:
                    content = code[component]
                    if isinstance(content, str):
                        code_samples += f"\n--- {component} (PRIORITY) ---\n{content[:1000]}..."
                    elif isinstance(content, dict) and "content" in content:
                        code_samples += f"\n--- {component} (PRIORITY) ---\n{content['content'][:1000]}..."
        
        # Add other relevant components
        for component in component_names:
            # Skip if already added as priority
            if component in priority_components:
                continue
                
            if component in code:
                content = code[component]
                if isinstance(content, str):
                    code_samples += f"\n--- {component} ---\n{content[:1000]}..."
                elif isinstance(content, dict) and "content" in content:
                    code_samples += f"\n--- {component} ---\n{content['content'][:1000]}..."
        
        # Add structure guidance if available
        structure_guidance = ""
        if project_structure:
            structure_guidance = "\nTEST ORGANIZATION STRUCTURE:\nEnsure test cases are organized according to the project structure for traceability:\n"
            for component_type, paths in project_structure.items():
                structure_guidance += f"- {component_type}: {', '.join(paths)}\n"

        formatted_prompt = f"""
        As a Test Case Developer working in a coordinated team environment, generate detailed test cases based on the following test plan and code:

        UNIT TESTS PLAN:
        {unit_tests_plan}

        INTEGRATION TESTS PLAN:
        {integration_tests_plan}

        CODE:
        {code_samples}
        {structure_guidance}

        Create detailed test cases for each test in the plan. For each test case, include:
        1. Test case ID and name
        2. Preconditions
        3. Test steps with expected results
        4. Test data
        5. Pass/fail criteria
        {"6. Component path within project structure" if project_structure else ""}
        {"7. Priority information for targeted testing" if components_to_test else ""}

        Make sure test cases are traceable back to the components they test, especially for those marked as priority.
        For integration tests, clearly identify the interaction points between components.

        Format your response as a JSON object with:
        {{
            "unit_test_cases": [
                {{
                    "id": "UT-001",
                    "name": "Test case name",
                    "component": "Component name",
                    "component_path": "Path in project structure",
                    "objective": "Test objective",
                    "preconditions": ["Precondition 1", "Precondition 2"],
                    "test_steps": [
                        {{
                            "step": "Step description",
                            "expected_result": "Expected result"
                        }}
                    ],
                    "test_data": {{
                        "input": "Test input",
                        "expected_output": "Expected output"
                    }},
                    "pass_criteria": ["Criterion 1", "Criterion 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "integration_test_cases": [
                {{
                    "id": "IT-001",
                    "name": "Test case name",
                    "components": ["Component 1", "Component 2"],
                    "component_paths": ["Path 1", "Path 2"],
                    "objective": "Test objective",
                    "preconditions": ["Precondition 1", "Precondition 2"],
                    "test_steps": [
                        {{
                            "step": "Step description",
                            "expected_result": "Expected result"
                        }}
                    ],
                    "test_data": {{
                        "input": "Test input",
                        "expected_output": "Expected output"
                    }},
                    "pass_criteria": ["Criterion 1", "Criterion 2"],
                    "integration_points": ["Description of integration point 1", "Description of integration point 2"],
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Test case generation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting test case generation prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_test_code_generation_prompt(
    test_cases: Dict[str, Any], 
    code: Dict[str, Any],
    programming_language: str,
    test_framework: str,
    project_structure: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating executable test code with Team Lead directives.
    
    Args:
        test_cases: Test case specifications
        code: Code to be tested
        programming_language: Target programming language
        test_framework: Testing framework to use
        project_structure: Project structure information for organizing tests
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting test code generation prompt")
    
    try:
        # Extract unit test cases
        unit_test_cases = test_cases.get("unit_test_cases", [])
        unit_test_cases_str = json.dumps(unit_test_cases, indent=2)
        
        # Extract integration test cases
        integration_test_cases = test_cases.get("integration_test_cases", [])
        integration_test_cases_str = json.dumps(integration_test_cases, indent=2)
        
        # Format code components
        code_samples = ""
        for component_name, component_content in code.items():
            # Handle different formats of code content
            if isinstance(component_content, str):
                code_text = component_content
            elif isinstance(component_content, dict) and "content" in component_content:
                code_text = component_content["content"]
            else:
                code_text = str(component_content)
            
            # Limit code length to avoid overwhelming the LLM
            if len(code_text) > 2000:
                code_text = code_text[:2000] + "...[truncated]"
            
            code_samples += f"\n\n// {component_name}\n{code_text}"
        
        # Framework-specific instructions
        framework_instructions = get_framework_specific_instructions(programming_language, test_framework)
        
        # Example test for few-shot learning
        example_test = get_example_test(programming_language, test_framework)
        
        # Add project structure information
        structure_instructions = ""
        if project_structure:
            structure_instructions = """
            ORGANIZATION REQUIREMENTS:
            The test code should be organized according to the project structure for proper integration and traceability.
            
            - Each component should have its own test file or test suite
            - Test files should follow naming conventions that relate to the component being tested
            - Tests should be grouped by component and functionality
            - Test file paths should reflect the component paths in the project structure
            """

        formatted_prompt = f"""
        As a skilled test engineer working in a coordinated team environment, generate executable test code for the following test cases.
        
        PROGRAMMING LANGUAGE: {programming_language}
        TESTING FRAMEWORK: {test_framework}
        
        CODE TO BE TESTED:
        {code_samples}
        
        UNIT TEST CASES:
        {unit_test_cases_str}
        
        INTEGRATION TEST CASES:
        {integration_test_cases_str}
        
        FRAMEWORK-SPECIFIC INSTRUCTIONS:
        {framework_instructions}
        
        {structure_instructions}
        
        EXAMPLE TEST:
        {example_test}
        
        REQUIREMENTS:
        1. Generate complete, executable test files
        2. Follow best practices for {test_framework}
        3. Properly mock dependencies
        4. Include appropriate assertions for each test case
        5. Group tests logically by component or functionality
        6. Add helpful comments explaining the tests
        7. Include component and test case IDs in comments for traceability
        {"8. Organize test files according to project structure" if project_structure else ""}
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "filename1.test.{get_file_extension(programming_language)}": "// Complete test file code here",
            "filename2.test.{get_file_extension(programming_language)}": "// Complete test file code here"
        }}
        
        Make sure each file contains the complete, valid code needed to run the tests. Do not truncate or use placeholders.
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Test code generation prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting test code generation prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_feedback_processing_prompt(
    feedback: Dict[str, Any],
    test_plan: Dict[str, Any],
    test_cases: Dict[str, Any],
    test_code: Dict[str, str]
) -> str:
    """
    Format the prompt for processing feedback from Team Lead.
    
    Args:
        feedback: Feedback received from Team Lead
        test_plan: Current test plan
        test_cases: Current test cases
        test_code: Current test code
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting feedback processing prompt")
    
    try:
        # Extract feedback details
        feedback_points = feedback.get("feedback_points", [])
        feedback_items = "\n".join([f"{i+1}. {point}" for i, point in enumerate(feedback_points)])
        
        # Format current test summary
        unit_tests_count = len(test_plan.get("unit_tests", []))
        integration_tests_count = len(test_plan.get("integration_tests", []))
        unit_test_cases_count = len(test_cases.get("unit_test_cases", []))
        integration_test_cases_count = len(test_cases.get("integration_test_cases", []))
        test_files_count = len(test_code)
        
        test_summary = f"""
        Current Test Summary:
        - Unit Tests in Plan: {unit_tests_count}
        - Integration Tests in Plan: {integration_tests_count}
        - Unit Test Cases: {unit_test_cases_count}
        - Integration Test Cases: {integration_test_cases_count}
        - Test Code Files: {test_files_count}
        """
        
        # Determine feedback category
        feedback_category = feedback.get("category", "general")
        category_specific_instructions = ""
        
        if feedback_category == "test_coverage":
            category_specific_instructions = """
            Focus on expanding test coverage by:
            1. Adding tests for missing functionality
            2. Enhancing edge case testing
            3. Adding more thorough integration tests
            """
        elif feedback_category == "test_quality":
            category_specific_instructions = """
            Focus on improving test quality by:
            1. Enhancing test assertions
            2. Improving test data to cover more scenarios
            3. Making tests more robust against changes
            """
        elif feedback_category == "test_organization":
            category_specific_instructions = """
            Focus on improving test organization by:
            1. Better alignment with project structure
            2. More logical grouping of tests
            3. Better naming and documentation
            """

        formatted_prompt = f"""
        As a QA Test Engineer, you've received feedback from the Team Lead on your test plan, cases, and code. 
        Please analyze this feedback and determine how to incorporate it into your testing artifacts.
        
        FEEDBACK FROM TEAM LEAD:
        {feedback_items}
        
        {test_summary}
        
        FEEDBACK CATEGORY: {feedback_category}
        {category_specific_instructions}
        
        Please provide a detailed plan for addressing this feedback, including:
        1. Specific changes needed to the test plan
        2. Specific changes needed to test cases
        3. Specific changes needed to test code
        4. Any additional requirements or information needed to address the feedback fully
        
        Format your response as a JSON object with:
        {{
            "feedback_analysis": "Your analysis of the feedback",
            "test_plan_changes": [
                {{
                    "change_type": "add/modify/remove",
                    "target": "Which part of the test plan to change",
                    "change_description": "Description of the change",
                    "rationale": "Why this change addresses the feedback"
                }}
            ],
            "test_case_changes": [
                {{
                    "change_type": "add/modify/remove",
                    "target": "Which test case to change",
                    "change_description": "Description of the change",
                    "rationale": "Why this change addresses the feedback"
                }}
            ],
            "test_code_changes": [
                {{
                    "change_type": "add/modify/remove",
                    "target": "Which test file to change",
                    "change_description": "Description of the change",
                    "rationale": "Why this change addresses the feedback"
                }}
            ],
            "additional_requirements": [
                "Any additional information or requirements needed"
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Feedback processing prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting feedback processing prompt: {str(e)}", exc_info=True)
        raise

@trace_method
def format_status_report_prompt(
    test_requirements: Dict[str, Any],
    test_plan: Dict[str, Any],
    test_cases: Dict[str, Any],
    test_code: Dict[str, str],
    task_id: str,
    components_to_test: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the prompt for generating a status report for Team Lead.
    
    Args:
        test_requirements: Analyzed test requirements
        test_plan: Test planning details
        test_cases: Generated test cases
        test_code: Generated test code
        task_id: ID of the task assigned by Team Lead
        components_to_test: Specific components being tested
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting status report prompt")
    
    try:
        # Format current test summary
        unit_tests_count = len(test_plan.get("unit_tests", []))
        integration_tests_count = len(test_plan.get("integration_tests", []))
        security_tests_count = len(test_plan.get("security_tests", []))
        performance_tests_count = len(test_plan.get("performance_tests", []))
        
        unit_test_cases_count = len(test_cases.get("unit_test_cases", []))
        integration_test_cases_count = len(test_cases.get("integration_test_cases", []))
        test_files_count = len(test_code)
        
        # Identify priority components
        priority_components = []
        if components_to_test:
            priority_components = list(components_to_test.keys())
        
        test_summary = f"""
        Test Coverage Summary:
        - Unit Tests in Plan: {unit_tests_count}
        - Integration Tests in Plan: {integration_tests_count}
        - Security Tests in Plan: {security_tests_count}
        - Performance Tests in Plan: {performance_tests_count}
        - Unit Test Cases: {unit_test_cases_count}
        - Integration Test Cases: {integration_test_cases_count}
        - Test Code Files: {test_files_count}
        """
        
        priority_components_str = ""
        if priority_components:
            priority_components_str = f"""
            Priority Components:
            {', '.join(priority_components)}
            """

        formatted_prompt = f"""
        As a QA Test Engineer reporting to your Team Lead, create a comprehensive status report on the testing work completed for task {task_id}.
        
        {test_summary}
        {priority_components_str}
        
        Please provide a detailed status report that includes:
        
        1. Test coverage analysis - what has been tested and what remains
        2. Key findings from testing process
        3. Potential issues, risks, or blockers
        4. Test quality assessment
        5. Recommendations for improvements
        
        Format your response as a JSON object with:
        {{
            "task_id": "{task_id}",
            "completion_status": "percentage of testing completed",
            "coverage_analysis": {{
                "components_tested": ["Component 1", "Component 2"],
                "components_pending": ["Component 3"],
                "coverage_metrics": {{
                    "unit_test_coverage": "percentage or description",
                    "integration_test_coverage": "percentage or description"
                }}
            }},
            "key_findings": [
                {{
                    "component": "Component name",
                    "finding": "Description of finding",
                    "severity": "HIGH/MEDIUM/LOW",
                    "impact": "Impact description"
                }}
            ],
            "issues_and_risks": [
                {{
                    "issue_type": "blocker/risk/concern",
                    "description": "Description of the issue",
                    "affected_components": ["Component 1"],
                    "mitigation": "Proposed mitigation strategy"
                }}
            ],
            "quality_assessment": {{
                "test_quality_score": "1-10 score",
                "strengths": ["Strength 1", "Strength 2"],
                "areas_for_improvement": ["Area 1", "Area 2"]
            }},
            "recommendations": [
                {{
                    "recommendation": "Description of recommendation",
                    "priority": "HIGH/MEDIUM/LOW",
                    "rationale": "Why this is recommended"
                }}
            ]
        }}
        """
        
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        logger.info("Status report prompt formatted successfully")
        return formatted_prompt
        
    except Exception as e:
        logger.error(f"Error formatting status report prompt: {str(e)}", exc_info=True)
        raise