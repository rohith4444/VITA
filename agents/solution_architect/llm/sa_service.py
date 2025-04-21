from typing import Dict, List, Any, Optional, Tuple
import json
from openai import AsyncOpenAI
from backend.config import Config
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from agents.solution_architect.llm.sa_prompts import (
    format_architecture_requirements_prompt,
    format_tech_stack_prompt,
    format_architecture_design_prompt,
    format_architecture_validation_prompt,
    format_specifications_prompt,
    format_task_instruction_prompt,
    format_feedback_processing_prompt,
    format_deliverable_packaging_prompt,
    format_status_report_prompt
)
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class LLMService:
    """
    This class only contains the methods required for the Solution Architect Agent.
    The existing LLMService class methods should be extended with these methods.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the LLM service with configuration and API setup.
        
        Args:
            model (str): The OpenAI model to use. Defaults to "gpt-4".
        
        Raises:
            ValueError: If API key is missing or invalid
            Exception: For other initialization failures
        """
        self.logger = setup_logger("llm.service")
        self.logger.info("Initializing LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM Service: {str(e)}", exc_info=True)
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
        self.logger.info(f"LLM Service initialized with model: {self.model}")
    
    async def _validate_api_key(self) -> None:
        """
        Validate the API key by making a test request.
        
        Raises:
            ValueError: If the API key is invalid
        """
        try:
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for validation
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            self.logger.info("API key validation successful")
        except Exception as e:
            self.logger.error(f"API key validation failed: {str(e)}")
            raise ValueError(f"Invalid OpenAI API key: {str(e)}")

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
                    raise ValueError(f"Response missing expected keys: {missing_keys}")
            
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
            raise
        
    async def _create_chat_completion(
        self,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 1500
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
        run_name="analyze_architecture_requirements",
        metadata={
            "operation_details": {
                "prompt_template": "architecture_requirements",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_architecture_requirements(self, 
                                              project_description: str,
                                              features: List[str],
                                              task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze and structure architecture requirements using LLM.
        
        Args:
            project_description (str): The project description
            features (List[str]): List of project features
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Structured analysis of requirements
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting architecture requirements analysis")
        
        try:
            formatted_prompt = format_architecture_requirements_prompt(
                project_description=project_description,
                features=features,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in software design."},
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            # Parse response
            analysis = await self._parse_llm_response(
                response_content,
                expected_keys=['functional_requirements', 'non_functional_requirements', 'constraints']
            )
            
            self.logger.info("Architecture requirements analysis completed successfully")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in architecture requirements analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="select_technology_stack",
        metadata={
            "operation_details": {
                "prompt_template": "tech_stack_selection",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def select_technology_stack(self,
                                    project_description: str,
                                    requirements: Dict[str, Any],
                                    task_context: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Select appropriate technology stack using LLM.
        
        Args:
            project_description (str): The project description
            requirements (Dict[str, Any]): Structured requirements
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Selected technology stack
            
        Raises:
            Exception: If selection fails
        """
        self.logger.info("Starting technology stack selection")
        
        try:
            formatted_prompt = format_tech_stack_prompt(
                project_description=project_description,
                requirements=requirements,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in technology selection."},
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            # Parse response
            tech_stack = await self._parse_llm_response(
                response_content,
                expected_keys=['frontend', 'backend', 'database', 'infrastructure']
            )
            
            self.logger.info("Technology stack selection completed successfully")
            
            return tech_stack
            
        except Exception as e:
            self.logger.error(f"Error in technology stack selection: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_architecture_design",
        metadata={
            "operation_details": {
                "prompt_template": "architecture_design",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_architecture_design(self,
                                         project_description: str,
                                         tech_stack: Dict[str, List[Dict[str, Any]]],
                                         requirements: Dict[str, Any],
                                         task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate system architecture design using LLM.
        
        Args:
            project_description (str): The project description
            tech_stack (Dict[str, List[Dict[str, Any]]]): Selected technology stack
            requirements (Dict[str, Any]): Structured requirements
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Architecture design
            
        Raises:
            Exception: If design generation fails
        """
        self.logger.info("Starting architecture design generation")
        
        try:
            formatted_prompt = format_architecture_design_prompt(
                project_description=project_description,
                tech_stack=tech_stack,
                requirements=requirements,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in system design."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response
            architecture_design = await self._parse_llm_response(
                response_content,
                expected_keys=['system_components', 'component_relationships', 'data_flows']
            )
            
            self.logger.info("Architecture design generation completed successfully")
            
            return architecture_design
            
        except Exception as e:
            self.logger.error(f"Error in architecture design generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="validate_architecture",
        metadata={
            "operation_details": {
                "prompt_template": "architecture_validation",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def validate_architecture_design(self,
                                         architecture_design: Dict[str, Any],
                                         requirements: Dict[str, Any],
                                         task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate architecture design using LLM.
        
        Args:
            architecture_design (Dict[str, Any]): Architecture design
            requirements (Dict[str, Any]): Structured requirements
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Validation results
            
        Raises:
            Exception: If validation fails
        """
        self.logger.info("Starting architecture validation")
        
        try:
            formatted_prompt = format_architecture_validation_prompt(
                architecture_design=architecture_design,
                requirements=requirements,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in architecture validation."},
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            # Parse response
            validation_results = await self._parse_llm_response(
                response_content,
                expected_keys=['validation_summary', 'requirement_coverage']
            )
            
            self.logger.info("Architecture validation completed successfully")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in architecture validation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_specifications",
        metadata={
            "operation_details": {
                "prompt_template": "technical_specifications",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_technical_specifications(self,
                                              architecture_design: Dict[str, Any],
                                              tech_stack: Dict[str, List[Dict[str, Any]]],
                                              validation_results: Dict[str, Any],
                                              task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate technical specifications using LLM.
        
        Args:
            architecture_design (Dict[str, Any]): Architecture design
            tech_stack (Dict[str, List[Dict[str, Any]]]): Selected technology stack
            validation_results (Dict[str, Any]): Validation results
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Technical specifications
            
        Raises:
            Exception: If specification generation fails
        """
        self.logger.info("Starting technical specifications generation")
        
        try:
            formatted_prompt = format_specifications_prompt(
                architecture_design=architecture_design,
                tech_stack=tech_stack,
                validation_results=validation_results,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in technical specifications."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response
            specifications = await self._parse_llm_response(
                response_content,
                expected_keys=['component_specifications', 'api_specifications', 'database_specifications']
            )
            
            self.logger.info("Technical specifications generation completed successfully")
            
            return specifications
            
        except Exception as e:
            self.logger.error(f"Error in technical specifications generation: {str(e)}", exc_info=True)
            raise

    # New methods for Team Lead coordination

    @monitor_llm(
        run_name="process_task_instruction",
        metadata={
            "operation_details": {
                "prompt_template": "task_instruction",
                "max_tokens": 1000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def process_task_instruction(self, task_instruction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task instructions from Team Lead using LLM.
        
        Args:
            task_instruction (Dict[str, Any]): Task instruction from Team Lead
            
        Returns:
            Dict[str, Any]: Processed task information
            
        Raises:
            Exception: If processing fails
        """
        self.logger.info("Processing task instruction from Team Lead")
        
        try:
            formatted_prompt = format_task_instruction_prompt(task_instruction)

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in interpreting task requirements."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1000
            )

            # Parse response
            processed_instruction = await self._parse_llm_response(
                response_content,
                expected_keys=['task_type', 'interpretation', 'expected_deliverables']
            )
            
            self.logger.info(f"Task instruction processing completed successfully: {processed_instruction.get('task_type', 'unknown')}")
            
            return processed_instruction
            
        except Exception as e:
            self.logger.error(f"Error processing task instruction: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="process_feedback",
        metadata={
            "operation_details": {
                "prompt_template": "feedback_processing",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def process_feedback(self, feedback: Dict[str, Any], original_deliverable: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process feedback from Team Lead using LLM.
        
        Args:
            feedback (Dict[str, Any]): Feedback from Team Lead
            original_deliverable (Dict[str, Any]): Original deliverable that received feedback
            
        Returns:
            Dict[str, Any]: Processed feedback with revision plan
            
        Raises:
            Exception: If processing fails
        """
        self.logger.info("Processing feedback from Team Lead")
        
        try:
            formatted_prompt = format_feedback_processing_prompt(
                feedback=feedback,
                original_deliverable=original_deliverable
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in interpreting feedback."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse response
            processed_feedback = await self._parse_llm_response(
                response_content,
                expected_keys=['revision_areas', 'revision_plan']
            )
            
            self.logger.info("Feedback processing completed successfully")
            
            return processed_feedback
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="package_deliverables",
        metadata={
            "operation_details": {
                "prompt_template": "deliverable_packaging",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def package_deliverables(self,
                                 architecture_design: Dict[str, Any],
                                 tech_stack: Dict[str, List[Dict[str, Any]]],
                                 specifications: Dict[str, Any],
                                 task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Package deliverables for Team Lead using LLM.
        
        Args:
            architecture_design (Dict[str, Any]): Architecture design
            tech_stack (Dict[str, List[Dict[str, Any]]]): Selected technology stack
            specifications (Dict[str, Any]): Technical specifications
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Packaged deliverables
            
        Raises:
            Exception: If packaging fails
        """
        self.logger.info("Packaging deliverables for Team Lead")
        
        try:
            formatted_prompt = format_deliverable_packaging_prompt(
                architecture_design=architecture_design,
                tech_stack=tech_stack,
                specifications=specifications,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in creating clear deliverables."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response
            packaged_deliverables = await self._parse_llm_response(
                response_content,
                expected_keys=['deliverables', 'project_structure_recommendation']
            )
            
            self.logger.info(f"Deliverable packaging completed successfully with {len(packaged_deliverables.get('deliverables', []))} deliverables")           
            return packaged_deliverables
            
        except Exception as e:
            self.logger.error(f"Error packaging deliverables: {str(e)}", exc_info=True)
            return packaged_deliverables
            
        except Exception as e:
            self.logger.error(f"Error packaging deliverables: {str(e)}", exc_info=True)
            # Return a basic structure in case of failure
            return {
                "deliverables": [],
                "project_structure_recommendation": {
                    "root_directories": [],
                    "directory_organization": "Failed to generate structure recommendation"
                },
                "error": str(e)
            }

    @monitor_llm(
        run_name="generate_status_report",
        metadata={
            "operation_details": {
                "prompt_template": "status_report",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_status_report(self,
                                   current_state: Dict[str, Any],
                                   progress: Dict[str, Any],
                                   task_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a status report for Team Lead using LLM.
        
        Args:
            current_state (Dict[str, Any]): Current state of the Solution Architect
            progress (Dict[str, Any]): Progress information
            task_context (Optional[Dict[str, Any]]): Optional context from Team Lead task
            
        Returns:
            Dict[str, Any]: Status report
            
        Raises:
            Exception: If report generation fails
        """
        self.logger.info("Generating status report for Team Lead")
        
        try:
            formatted_prompt = format_status_report_prompt(
                current_state=current_state,
                progress=progress,
                task_context=task_context
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled Solution Architect with expertise in reporting progress clearly."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse response
            status_report = await self._parse_llm_response(
                response_content,
                expected_keys=['status_summary', 'achievements', 'pending_work']
            )
            
            self.logger.info("Status report generation completed successfully")
            
            return status_report
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {str(e)}", exc_info=True)
            # Return a basic report in case of failure
            return {
                "status_summary": "Error occurred during status report generation",
                "current_stage": current_state.get("status", "unknown"),
                "completion_percentage": progress.get("completion_percentage", 0),
                "achievements": [],
                "pending_work": [],
                "issues": [{"description": f"Error generating status report: {str(e)}"}],
                "error": str(e)
            }