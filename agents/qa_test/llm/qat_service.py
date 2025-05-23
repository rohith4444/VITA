from typing import Dict, List, Any, Optional
import json
from openai import AsyncOpenAI
from backend.config import Config
from core.logging.logger import setup_logger
from core.tracing.service import trace_class
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from .qat_prompts import (
    format_test_requirements_analysis_prompt,
    format_test_planning_prompt,
    format_test_case_generation_prompt,
    format_test_code_generation_prompt,
    format_feedback_processing_prompt,
    format_status_report_prompt,
    format_deliverable_packaging_prompt
)

@trace_class
class QATestLLMService:
    """Service for handling LLM interactions specific to QA/Test operations with Team Lead coordination."""
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the LLM service with configuration and API setup.
        
        Args:
            model (str): The OpenAI model to use. Defaults to "gpt-4".
        
        Raises:
            ValueError: If API key is missing or invalid
            Exception: For other initialization failures
        """
        self.logger = setup_logger("qa_test.llm.service")
        self.logger.info("Initializing QA/Test LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize QA/Test LLM Service: {str(e)}", exc_info=True)
            raise

    def _initialize_client(self) -> None:
        """Initialize the OpenAI client with proper configuration."""
        config_instance = Config()
        self.api_key = config_instance.OPENAI_API_KEY
        
        if not self.api_key:
            self.logger.error("OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Log the first few characters of the API key to verify it's loaded (safely)
        key_preview = self.api_key[:4] + '*' * (len(self.api_key) - 8) + self.api_key[-4:]
        self.logger.debug(f"Loaded API key: {key_preview}")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.logger.info(f"QA/Test LLM Service initialized with model: {self.model}")
    
    @monitor_operation(
        operation_type="llm_response_parsing",
        include_in_parent=True
    )
    async def _parse_llm_response(self, response: str, expected_keys: Optional[list] = None) -> Dict[str, Any]:
        """
        Parse and validate the LLM response into a structured format.
        
        Args:
            response (str): The raw response string from the LLM
            expected_keys (Optional[list]): List of keys expected in the response
        
        Returns:
            Dict[str, Any]: Parsed and validated response
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            ValueError: If response is missing expected keys
        """
        self.logger.debug("Parsing LLM response")
        try:
            # Extract JSON content from the response if needed
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                # Extract JSON part
                json_content = response[json_start:json_end]
                parsed_response = json.loads(json_content)
            else:
                # Try parsing the whole response
                parsed_response = json.loads(response)
            
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in parsed_response]
                if missing_keys:
                    self.logger.warning(f"Response missing expected keys: {missing_keys}")
                    
                    # Try to salvage what we can and fill in missing keys with defaults
                    for key in missing_keys:
                        if isinstance(key, str):
                            if "test" in key or "requirements" in key:
                                parsed_response[key] = []
                            elif "plan" in key:
                                parsed_response[key] = {}
                            else:
                                parsed_response[key] = ""
            
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
            # Try to create a structured response from unstructured text
            if response:
                return {"text": response, "parsing_error": str(e)}
            raise
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
            raise
        
    async def _create_chat_completion(
        self,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Create a chat completion with error handling and logging.
        
        Args:
            messages (list): List of message dictionaries
            temperature (float): Model temperature
            max_tokens (int): Maximum tokens in response
            
        Returns:
            str: Model response content
            
        Raises:
            Exception: If API call fails
        """
        try:
            self.logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
            raise
        
    @monitor_llm(
        run_name="analyze_test_requirements",
        metadata={
            "operation_details": {
                "prompt_template": "test_requirements_analysis",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_test_requirements(
        self, 
        code: Dict[str, Any], 
        specifications: Dict[str, Any],
        input_description: str,
        components_to_test: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
        task_priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code and specifications to determine test requirements.
        
        Args:
            code: Code to be tested
            specifications: Technical specifications
            input_description: Project description and requirements
            components_to_test: Specific components to test, as directed by Team Lead
            dependencies: Component dependencies for integration testing
            task_priority: Priority level from Team Lead (HIGH/MEDIUM/LOW)
            
        Returns:
            Dict[str, Any]: Structured test requirements
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting test requirements analysis")
        
        try:
            formatted_prompt = format_test_requirements_analysis_prompt(
                code=code,
                specifications=specifications,
                input_description=input_description,
                components_to_test=components_to_test,
                dependencies=dependencies,
                task_priority=task_priority
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in software testing."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            requirements = await self._parse_llm_response(
                response_content,
                expected_keys=['functional_test_requirements', 'integration_test_requirements']
            )
            
            self.logger.info("Test requirements analysis completed successfully")
            self.logger.debug(f"Analysis contains {len(requirements.get('functional_test_requirements', []))} functional requirements")

            return requirements
            
        except Exception as e:
            self.logger.error(f"Error in test requirements analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="create_test_plan",
        metadata={
            "operation_details": {
                "prompt_template": "test_planning",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def create_test_plan(
        self, 
        test_requirements: Dict[str, Any],
        task_priority: Optional[str] = None,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a test plan based on the analyzed requirements.
        
        Args:
            test_requirements: Analyzed test requirements
            task_priority: Priority level from Team Lead (HIGH/MEDIUM/LOW)
            project_structure: Project structure information from Team Lead
            
        Returns:
            Dict[str, Any]: Structured test plan
            
        Raises:
            Exception: If plan creation fails
        """
        self.logger.info("Starting test plan creation")
        
        try:
            formatted_prompt = format_test_planning_prompt(
                test_requirements=test_requirements,
                task_priority=task_priority,
                project_structure=project_structure
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in test planning."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            test_plan = await self._parse_llm_response(
                response_content,
                expected_keys=['unit_tests', 'integration_tests', 'test_environment']
            )
            
            self.logger.info("Test plan creation completed successfully")
            self.logger.debug(f"Test plan contains {len(test_plan.get('unit_tests', []))} unit tests and {len(test_plan.get('integration_tests', []))} integration tests")

            return test_plan
            
        except Exception as e:
            self.logger.error(f"Error in test plan creation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_test_cases",
        metadata={
            "operation_details": {
                "prompt_template": "test_case_generation",
                "max_tokens": 2500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_test_cases(
        self, 
        test_plan: Dict[str, Any], 
        code: Dict[str, Any],
        test_requirements: Dict[str, Any],
        components_to_test: Optional[Dict[str, Any]] = None,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed test cases based on the test plan.
        
        Args:
            test_plan: Test planning details
            code: Code to be tested
            test_requirements: Analyzed test requirements
            components_to_test: Specific components to test, as directed by Team Lead
            project_structure: Project structure information from Team Lead
            
        Returns:
            Dict[str, Any]: Structured test cases
            
        Raises:
            Exception: If test case generation fails
        """
        self.logger.info("Starting test case generation")
        
        try:
            formatted_prompt = format_test_case_generation_prompt(
                test_plan=test_plan,
                code=code,
                test_requirements=test_requirements,
                components_to_test=components_to_test,
                project_structure=project_structure
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in developing test cases."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2500
            )

            # Parse response with expected keys validation
            test_cases = await self._parse_llm_response(
                response_content,
                expected_keys=['unit_test_cases', 'integration_test_cases']
            )
            
            self.logger.info("Test case generation completed successfully")
            self.logger.debug(f"Generated {len(test_cases.get('unit_test_cases', []))} unit test cases and {len(test_cases.get('integration_test_cases', []))} integration test cases")

            return test_cases
            
        except Exception as e:
            self.logger.error(f"Error in test case generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_test_code",
        metadata={
            "operation_details": {
                "prompt_template": "test_code_generation",
                "max_tokens": 3000,
                "temperature": 0.3,
                "response_format": "structured_code"
            }
        }
    )
    async def generate_test_code(
        self, 
        test_cases: Dict[str, Any], 
        code: Dict[str, Any],
        programming_language: str,
        test_framework: str,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate executable test code based on test cases.
        
        Args:
            test_cases: Test case specifications
            code: Code to be tested
            programming_language: Target programming language (e.g., "javascript", "python")
            test_framework: Testing framework to use (e.g., "jest", "pytest")
            project_structure: Project structure information from Team Lead
            
        Returns:
            Dict[str, str]: Dictionary of test file names and their contents
            
        Raises:
            Exception: If code generation fails
        """
        self.logger.info(f"Starting test code generation for {programming_language} using {test_framework}")
        
        try:
            formatted_prompt = format_test_code_generation_prompt(
                test_cases=test_cases,
                code=code,
                programming_language=programming_language,
                test_framework=test_framework,
                project_structure=project_structure
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a skilled QA engineer with expertise in writing test code using {test_framework} for {programming_language}."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=3000
            )

            # Parse response into test code files
            test_code_files = await self._parse_test_code_response(response_content)
            
            self.logger.info(f"Test code generation completed successfully with {len(test_code_files)} test files")

            return test_code_files
            
        except Exception as e:
            self.logger.error(f"Error in test code generation: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="llm_test_code_parsing",
        include_in_parent=True
    )
    async def _parse_test_code_response(self, response: str) -> Dict[str, str]:
        """
        Parse the test code response from LLM.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Dict[str, str]: Dictionary of test file names and their contents
            
        Raises:
            ValueError: If response cannot be parsed as valid JSON
            ValueError: If response format is not as expected
        """
        self.logger.debug("Parsing test code response")
        
        try:
            # Strip any non-JSON content at the beginning or end
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
                
            json_str = response[json_start:json_end]
            
            # Parse the JSON
            test_code_files = json.loads(json_str)
            
            # Validate the format
            if not isinstance(test_code_files, dict):
                raise ValueError("Response is not a dictionary of test files")
                
            for filename, content in test_code_files.items():
                if not isinstance(content, str):
                    raise ValueError(f"Test file content for {filename} is not a string")
                    
            self.logger.debug(f"Successfully parsed {len(test_code_files)} test files from response")
            return test_code_files
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse test code response as JSON: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to parse test code response as JSON: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error parsing test code response: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="process_feedback",
        metadata={
            "operation_details": {
                "prompt_template": "feedback_processing",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def process_feedback(
        self,
        feedback: Dict[str, Any],
        test_plan: Dict[str, Any],
        test_cases: Dict[str, Any],
        test_code: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process feedback from Team Lead and determine necessary changes.
        
        Args:
            feedback: Feedback received from Team Lead
            test_plan: Current test plan
            test_cases: Current test cases
            test_code: Current test code
            
        Returns:
            Dict[str, Any]: Analysis and change recommendations
            
        Raises:
            Exception: If feedback processing fails
        """
        self.logger.info("Starting feedback processing")
        
        try:
            formatted_prompt = format_feedback_processing_prompt(
                feedback=feedback,
                test_plan=test_plan,
                test_cases=test_cases,
                test_code=test_code
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in refining test artifacts based on feedback."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            feedback_analysis = await self._parse_llm_response(
                response_content,
                expected_keys=['feedback_analysis', 'test_plan_changes', 'test_case_changes', 'test_code_changes']
            )
            
            self.logger.info("Feedback processing completed successfully")
            self.logger.debug(f"Feedback analysis contains {len(feedback_analysis.get('test_plan_changes', []))} plan changes, {len(feedback_analysis.get('test_case_changes', []))} case changes, and {len(feedback_analysis.get('test_code_changes', []))} code changes")

            return feedback_analysis
            
        except Exception as e:
            self.logger.error(f"Error in feedback processing: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_status_report",
        metadata={
            "operation_details": {
                "prompt_template": "status_report",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_status_report(
        self,
        test_requirements: Dict[str, Any],
        test_plan: Dict[str, Any],
        test_cases: Dict[str, Any],
        test_code: Dict[str, str],
        task_id: str,
        components_to_test: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a status report for Team Lead.
        
        Args:
            test_requirements: Analyzed test requirements
            test_plan: Test planning details
            test_cases: Generated test cases
            test_code: Generated test code
            task_id: ID of the task assigned by Team Lead
            components_to_test: Specific components being tested
            
        Returns:
            Dict[str, Any]: Structured status report
            
        Raises:
            Exception: If status report generation fails
        """
        self.logger.info("Starting status report generation")
        
        try:
            formatted_prompt = format_status_report_prompt(
                test_requirements=test_requirements,
                test_plan=test_plan,
                test_cases=test_cases,
                test_code=test_code,
                task_id=task_id,
                components_to_test=components_to_test
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in reporting test status and results."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            status_report = await self._parse_llm_response(
                response_content,
                expected_keys=['task_id', 'completion_status', 'coverage_analysis', 'key_findings']
            )
            
            self.logger.info("Status report generation completed successfully")
            self.logger.debug(f"Status report indicates {status_report.get('completion_status', '0%')} completion with {len(status_report.get('key_findings', []))} key findings")

            return status_report
            
        except Exception as e:
            self.logger.error(f"Error in status report generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="package_deliverable",
        metadata={
            "operation_details": {
                "prompt_template": "deliverable_packaging",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def package_deliverable(
        self,
        test_requirements: Dict[str, Any],
        test_plan: Dict[str, Any],
        test_cases: Dict[str, Any],
        test_code: Dict[str, str],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Package test artifacts as a deliverable for Team Lead.
        
        Args:
            test_requirements: Analyzed test requirements
            test_plan: Test planning details
            test_cases: Generated test cases
            test_code: Generated test code
            task_id: ID of the task assigned by Team Lead
            
        Returns:
            Dict[str, Any]: Structured deliverable package
            
        Raises:
            Exception: If deliverable packaging fails
        """
        self.logger.info("Starting deliverable packaging")
        
        try:
            formatted_prompt = format_deliverable_packaging_prompt(
                test_requirements=test_requirements,
                test_plan=test_plan,
                test_cases=test_cases,
                test_code=test_code,
                task_id=task_id
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled QA engineer with expertise in packaging test deliverables."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            deliverable_package = await self._parse_llm_response(
                response_content,
                expected_keys=['deliverable_id', 'task_id', 'summary', 'traceability_matrix']
            )
            
            self.logger.info("Deliverable packaging completed successfully")
            self.logger.debug(f"Deliverable package created with ID: {deliverable_package.get('deliverable_id', 'unknown')}")

            return deliverable_package
            
        except Exception as e:
            self.logger.error(f"Error in deliverable packaging: {str(e)}", exc_info=True)
            raise