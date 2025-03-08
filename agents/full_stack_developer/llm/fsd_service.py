from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
from openai import AsyncOpenAI
from backend.config import Config
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from agents.full_stack_developer.llm.fsd_prompts import (
    format_requirements_analysis_prompt,
    format_solution_design_prompt,
    format_code_generation_prompt,
    format_documentation_generation_prompt,
    format_instruction_processing_prompt,
    format_deliverable_packaging_prompt,
    format_feedback_processing_prompt,
    format_quality_check_prompt,
    format_status_report_prompt
)
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class LLMService:
    """
    LLM service for Full Stack Developer Agent.
    Handles interactions with LLM for requirements analysis, solution design, 
    code generation, documentation, and Team Lead coordination.
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
        self.logger = setup_logger("llm.fsd.service")
        self.logger.info("Initializing FSD LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize FSD LLM Service: {str(e)}", exc_info=True)
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
        self.logger.info(f"FSD LLM Service initialized with model: {self.model}")
    
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
                        if key == "features":
                            parsed_response[key] = []
                        elif key == "technical_constraints":
                            parsed_response[key] = []
                        elif key == "dependencies":
                            parsed_response[key] = []
                        elif key == "technology_recommendations":
                            parsed_response[key] = {}
                        elif key == "challenges":
                            parsed_response[key] = []
                        else:
                            parsed_response[key] = ""
            
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}", exc_info=True)
            # Return a fallback response for resilience
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response[:500] + ("..." if len(response) > 500 else "")
            }
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="analyze_requirements",
        metadata={
            "operation_details": {
                "prompt_template": "requirements_analysis",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_requirements(
        self, 
        task_specification: str,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a task specification to extract requirements.
        
        Args:
            task_specification: Raw task specification
            project_structure: Optional project structure context from Team Lead
            
        Returns:
            Dict[str, Any]: Structured requirements analysis
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting requirements analysis")
        
        try:
            # Format the prompt
            formatted_prompt = format_requirements_analysis_prompt(
                task_specification=task_specification,
                project_structure=project_structure
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer with expertise in requirements analysis."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = ["features", "technical_constraints", "dependencies", "technology_recommendations", "challenges"]
            analysis = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Requirements analysis completed with {len(analysis.get('features', []))} features")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in requirements analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="design_solution",
        metadata={
            "operation_details": {
                "prompt_template": "solution_design",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def design_solution(
        self, 
        task_specification: str, 
        requirements: Dict[str, Any], 
        component: str,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Design a solution for a specific component.
        
        Args:
            task_specification: Raw task specification
            requirements: Requirements analysis
            component: Which component to design ("frontend", "backend", or "database")
            project_structure: Optional project structure context from Team Lead
            
        Returns:
            Dict[str, Any]: Structured solution design
            
        Raises:
            Exception: If design fails
        """
        self.logger.info(f"Starting {component} solution design")
        
        try:
            # Format the prompt
            formatted_prompt = format_solution_design_prompt(
                task_specification=task_specification,
                requirements=requirements,
                component=component,
                project_structure=project_structure
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a senior full-stack developer with expertise in {component} design."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = []
            if component == "frontend":
                expected_keys = ["architecture", "components", "state_management", "routing", "ui_frameworks", "file_structure"]
            elif component == "backend":
                expected_keys = ["architecture", "api_endpoints", "business_logic", "middleware", "auth_approach", "file_structure"]
            elif component == "database":
                expected_keys = ["database_type", "models", "relationships", "indexing_strategy", "migrations"]
            
            design = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"{component.capitalize()} solution design completed")
            return design
            
        except Exception as e:
            self.logger.error(f"Error in {component} solution design: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_code",
        metadata={
            "operation_details": {
                "prompt_template": "code_generation",
                "max_tokens": 4000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_code(
        self, 
        task_specification: str, 
        requirements: Dict[str, Any], 
        solution_design: Dict[str, Any], 
        component: str,
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate code for a specific component.
        
        Args:
            task_specification: Raw task specification
            requirements: Requirements analysis
            solution_design: Solution design for the component
            component: Which component to generate code for
            project_structure: Optional project structure context from Team Lead
            
        Returns:
            Dict[str, str]: Dictionary mapping file paths to file contents
            
        Raises:
            Exception: If code generation fails
        """
        self.logger.info(f"Starting {component} code generation")
        
        try:
            # Format the prompt
            formatted_prompt = format_code_generation_prompt(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                component=component,
                project_structure=project_structure
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a senior full-stack developer with expertise in {component} implementation."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            # Parse and validate the response
            code_files = await self._parse_llm_response(response)
            
            self.logger.info(f"{component.capitalize()} code generation completed with {len(code_files)} files")
            return code_files
            
        except Exception as e:
            self.logger.error(f"Error in {component} code generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_documentation",
        metadata={
            "operation_details": {
                "prompt_template": "documentation_generation",
                "max_tokens": 3000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_documentation(
        self, 
        task_specification: str, 
        requirements: Dict[str, Any], 
        solution_design: Dict[str, Any], 
        generated_code: Dict[str, Dict[str, str]],
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate documentation for the implementation.
        
        Args:
            task_specification: Raw task specification
            requirements: Requirements analysis
            solution_design: Solution design for all components
            generated_code: Generated code for all components
            project_structure: Optional project structure context from Team Lead
            
        Returns:
            Dict[str, str]: Dictionary mapping documentation file names to contents
            
        Raises:
            Exception: If documentation generation fails
        """
        self.logger.info("Starting documentation generation")
        
        try:
            # Format the prompt
            formatted_prompt = format_documentation_generation_prompt(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                generated_code=generated_code,
                project_structure=project_structure
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer with expertise in technical documentation."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            
            # Parse and validate the response
            documentation = await self._parse_llm_response(response)
            
            self.logger.info(f"Documentation generation completed with {len(documentation)} documents")
            return documentation
            
        except Exception as e:
            self.logger.error(f"Error in documentation generation: {str(e)}", exc_info=True)
            raise

    # New methods for Team Lead coordination

    @monitor_llm(
        run_name="process_teamlead_instructions",
        metadata={
            "operation_details": {
                "prompt_template": "instruction_processing",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def process_teamlead_instructions(
        self,
        instruction: Dict[str, Any],
        task_id: str,
        team_lead_id: str
    ) -> Dict[str, Any]:
        """
        Process instructions from the Team Lead.
        
        Args:
            instruction: Instruction from Team Lead
            task_id: ID of the task
            team_lead_id: ID of the Team Lead
            
        Returns:
            Dict[str, Any]: Processed instruction analysis
            
        Raises:
            Exception: If instruction processing fails
        """
        self.logger.info(f"Processing instruction for task {task_id}")
        
        try:
            # Format the prompt
            formatted_prompt = format_instruction_processing_prompt(
                instruction=instruction,
                task_id=task_id,
                team_lead_id=team_lead_id
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer processing instructions from your Team Lead."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = ["task_analysis", "core_objectives", "deliverables", "implementation_approach"]
            analysis = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Instruction processing completed for task {task_id}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error processing instructions: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="package_deliverables",
        metadata={
            "operation_details": {
                "prompt_template": "deliverable_packaging",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def package_deliverables(
        self,
        task_id: str,
        requirements: Dict[str, Any],
        solution_design: Dict[str, Any],
        generated_code: Dict[str, Dict[str, str]],
        documentation: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Package deliverables for submission to Team Lead.
        
        Args:
            task_id: ID of the task
            requirements: Analyzed requirements
            solution_design: Design details for all components
            generated_code: Generated code files
            documentation: Generated documentation
            
        Returns:
            Dict[str, Any]: Packaged deliverables with metadata
            
        Raises:
            Exception: If deliverable packaging fails
        """
        self.logger.info(f"Packaging deliverables for task {task_id}")
        
        try:
            # Format the prompt
            formatted_prompt = format_deliverable_packaging_prompt(
                task_id=task_id,
                requirements=requirements,
                solution_design=solution_design,
                generated_code=generated_code,
                documentation=documentation
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer packaging your work for submission."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = ["summary", "components", "integration_guide", "metadata"]
            package = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Deliverable packaging completed for task {task_id}")
            return package
            
        except Exception as e:
            self.logger.error(f"Error packaging deliverables: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="process_feedback",
        metadata={
            "operation_details": {
                "prompt_template": "feedback_processing",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def process_feedback(
        self,
        task_id: str,
        feedback: Dict[str, Any],
        deliverables: Dict[str, Any],
        team_lead_id: str
    ) -> Dict[str, Any]:
        """
        Process feedback from the Team Lead.
        
        Args:
            task_id: ID of the task
            feedback: Feedback from Team Lead
            deliverables: The deliverables that received feedback
            team_lead_id: ID of the Team Lead
            
        Returns:
            Dict[str, Any]: Analysis of feedback with revision plan
            
        Raises:
            Exception: If feedback processing fails
        """
        self.logger.info(f"Processing feedback for task {task_id}")
        
        try:
            # Format the prompt
            formatted_prompt = format_feedback_processing_prompt(
                task_id=task_id,
                feedback=feedback,
                deliverables=deliverables,
                team_lead_id=team_lead_id
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer processing feedback on your work."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = ["feedback_analysis", "revision_plan", "revision_approach"]
            analysis = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Feedback processing completed for task {task_id}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="check_quality",
        metadata={
            "operation_details": {
                "prompt_template": "quality_check",
                "max_tokens": 2000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def check_quality(
        self,
        task_id: str,
        component: str,
        content: Dict[str, str],
        project_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform a quality check on generated content.
        
        Args:
            task_id: ID of the task
            component: Which component to check
            content: Content to check (e.g., generated code or documentation)
            project_structure: Optional project structure context from Team Lead
            
        Returns:
            Dict[str, Any]: Quality assessment with issues and recommendations
            
        Raises:
            Exception: If quality check fails
        """
        self.logger.info(f"Checking quality of {component} for task {task_id}")
        
        try:
            # Format the prompt
            formatted_prompt = format_quality_check_prompt(
                task_id=task_id,
                component=component,
                content=content,
                project_structure=project_structure
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer performing a quality assessment."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and validate the response
            expected_keys = ["overall_quality", "summary", "issues", "strengths", "pass_quality_check"]
            assessment = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Quality check completed for {component} with score {assessment.get('overall_quality', 'unknown')}")
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error checking quality: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_status_report",
        metadata={
            "operation_details": {
                "prompt_template": "status_report",
                "max_tokens": 1500,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_status_report(
        self,
        task_id: str,
        team_lead_id: str,
        current_stage: str,
        progress_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a status report for the Team Lead.
        
        Args:
            task_id: ID of the task
            team_lead_id: ID of the Team Lead
            current_stage: Current stage of the workflow
            progress_details: Details about current progress
            
        Returns:
            Dict[str, Any]: Formatted status report
            
        Raises:
            Exception: If status report generation fails
        """
        self.logger.info(f"Generating status report for task {task_id}")
        
        try:
            # Format the prompt
            formatted_prompt = format_status_report_prompt(
                task_id=task_id,
                team_lead_id=team_lead_id,
                current_stage=current_stage,
                progress_details=progress_details
            )
            
            # Create the chat completion
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full-stack developer reporting status to your Team Lead."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parse and validate the response
            expected_keys = ["status_summary", "progress_percentage", "accomplishments", "next_steps"]
            report = await self._parse_llm_response(response, expected_keys)
            
            self.logger.info(f"Status report generated for task {task_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {str(e)}", exc_info=True)
            raise