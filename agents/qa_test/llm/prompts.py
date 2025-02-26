from typing import Dict, List, Any
import json

from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize module logger
logger = setup_logger("qa_test.llm.prompts")

@trace_method
def format_test_requirements_analysis_prompt(
    code: Dict[str, Any], 
    specifications: Dict[str, Any],
    input_description: str
) -> str:
    """
    Format the prompt for analyzing test requirements.
    
    Args:
        code: Code to be tested, organized by components
        specifications: Technical specifications
        input_description: Project description and requirements
        
    Returns:
        str: Formatted prompt for the LLM
    """
    logger.debug("Formatting test requirements analysis prompt")
    
    try:
        # Extract code samples for the prompt
        code_samples = ""
        for component, content in code.items():
            if isinstance(content, str):
                # If content is directly a string (e.g., code content)
                code_samples += f"\n--- {component} ---\n{content[:1000]}..."
            elif isinstance(content, dict) and "content" in content:
                # If content is a dict with a 'content' field
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

        formatted_prompt = f"""
        As a Quality Assurance specialist, analyze the following code and specifications to determine testing requirements:

        PROJECT DESCRIPTION:
        {input_description[:500]}...

        CODE SAMPLES:
        {code_samples}

        SPECIFICATIONS:
        {spec_summary}

        API SPECIFICATIONS:
        {api_specs}

        Please analyze the code and specifications to identify test requirements. Focus on:
        1. Functional requirements that need to be tested
        2. Critical components and their dependencies
        3. Expected behaviors and edge cases
        4. Potential failure points
        5. Security considerations
        6. Performance aspects

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
def format_test_planning_prompt(test_requirements: Dict[str, Any]) -> str:
    """
    Format the prompt for test planning based on analyzed requirements.
    
    Args:
        test_requirements: Analyzed test requirements
        
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

        formatted_prompt = f"""
        As a Test Planner, create a comprehensive test plan based on the following requirements:

        FUNCTIONAL TEST REQUIREMENTS:
        {functional_reqs}

        INTEGRATION TEST REQUIREMENTS:
        {integration_reqs}

        SECURITY TEST REQUIREMENTS:
        {security_reqs}

        PERFORMANCE TEST REQUIREMENTS:
        {performance_reqs}

        Create a structured test plan that outlines how to test each requirement. For each category of tests, specify:
        1. The testing approach
        2. Testing tools/frameworks to use
        3. Testing environment requirements
        4. Test data requirements
        5. Test sequence and dependencies

        Format your response as a JSON object with:
        {{
            "unit_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "test_data_requirements": ["Data requirement 1", "Data requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"]
                }}
            ],
            "integration_tests": [
                {{
                    "components": ["Component 1", "Component 2"],
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "test_data_requirements": ["Data requirement 1", "Data requirement 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"]
                }}
            ],
            "security_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"]
                }}
            ],
            "performance_tests": [
                {{
                    "component": "Component name",
                    "test_objective": "What to test",
                    "test_approach": "How to test it",
                    "test_tools": ["Tool 1", "Tool 2"],
                    "metrics": ["Metric 1", "Metric 2"]
                }}
            ],
            "test_environment": {{
                "requirements": ["Requirement 1", "Requirement 2"],
                "configurations": ["Configuration 1", "Configuration 2"]
            }},
            "test_sequence": [
                "Step 1",
                "Step 2"
            ]
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
    test_requirements: Dict[str, Any]
) -> str:
    """
    Format the prompt for generating test cases based on the test plan.
    
    Args:
        test_plan: Test planning details
        code: Code to be tested
        test_requirements: Analyzed test requirements
        
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
            
            unit_tests_plan += f"""
            {idx}. Component: {component}
               Objective: {objective}
               Approach: {approach}
            """
        
        # Extract integration tests from the test plan
        integration_tests_plan = ""
        for idx, test in enumerate(test_plan.get("integration_tests", []), 1):
            components = ", ".join(test.get("components", ["Unknown"]))
            objective = test.get("test_objective", "")
            approach = test.get("test_approach", "")
            
            integration_tests_plan += f"""
            {idx}. Components: {components}
               Objective: {objective}
               Approach: {approach}
            """
        
        # Extract relevant code for the tested components
        code_samples = ""
        # Get component names from test plan
        component_names = set()
        for test in test_plan.get("unit_tests", []):
            component_names.add(test.get("component", ""))
        for test in test_plan.get("integration_tests", []):
            component_names.update(test.get("components", []))
        
        # Add code for relevant components
        for component, content in code.items():
            if component in component_names or not component_names:  # Include if relevant or if no specific components
                if isinstance(content, str):
                    code_samples += f"\n--- {component} ---\n{content[:1000]}..."
                elif isinstance(content, dict) and "content" in content:
                    code_samples += f"\n--- {component} ---\n{content['content'][:1000]}..."

        formatted_prompt = f"""
        As a Test Case Developer, generate detailed test cases based on the following test plan and code:

        UNIT TESTS PLAN:
        {unit_tests_plan}

        INTEGRATION TESTS PLAN:
        {integration_tests_plan}

        CODE:
        {code_samples}

        Create detailed test cases for each test in the plan. For each test case, include:
        1. Test case ID and name
        2. Preconditions
        3. Test steps with expected results
        4. Test data
        5. Pass/fail criteria

        Format your response as a JSON object with:
        {{
            "unit_test_cases": [
                {{
                    "id": "UT-001",
                    "name": "Test case name",
                    "component": "Component name",
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
                    "pass_criteria": ["Criterion 1", "Criterion 2"]
                }}
            ],
            "integration_test_cases": [
                {{
                    "id": "IT-001",
                    "name": "Test case name",
                    "components": ["Component 1", "Component 2"],
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
                    "pass_criteria": ["Criterion 1", "Criterion 2"]
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
    test_framework: str
) -> str:
    """
    Format the prompt for generating executable test code.
    
    Args:
        test_cases: Test case specifications
        code: Code to be tested
        programming_language: Target programming language
        test_framework: Testing framework to use
        
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

        formatted_prompt = f"""
        As a skilled test engineer, generate executable test code for the following test cases.
        
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
        
        EXAMPLE TEST:
        {example_test}
        
        REQUIREMENTS:
        1. Generate complete, executable test files
        2. Follow best practices for {test_framework}
        3. Properly mock dependencies
        4. Include appropriate assertions for each test case
        5. Group tests logically by component or functionality
        6. Add helpful comments explaining the tests
        
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