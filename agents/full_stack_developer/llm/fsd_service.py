from typing import Dict, List, Any, Optional
import json
from openai import AsyncOpenAI
from backend.config import Config
from core.logging.logger import setup_logger
from core.tracing.service import trace_class
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from .fsd_prompts import (
    format_requirements_analysis_prompt,
    format_solution_design_prompt,
    format_code_generation_prompt,
    format_documentation_generation_prompt
)

@trace_class
class LLMService:
    """Service for handling LLM interactions specific to the Full Stack Developer Agent."""
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the LLM service with configuration and API setup.
        
        Args:
            model (str): The OpenAI model to use. Defaults to "gpt-4".
        
        Raises:
            ValueError: If API key is missing or invalid
            Exception: For other initialization failures
        """
        self.logger = setup_logger("full_stack_developer.llm.service")
        self.logger.info("Initializing Full Stack Developer LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Full Stack Developer LLM Service: {str(e)}", exc_info=True)
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
        self.logger.info(f"Full Stack Developer LLM Service initialized with model: {self.model}")

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
            # Find JSON in response (in case LLM adds commentary)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
                
            json_str = response[json_start:json_end]
            parsed_response = json.loads(json_str)
            
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in parsed_response]
                if missing_keys:
                    raise ValueError(f"Response missing expected keys: {missing_keys}")
            
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
            raise
        
    async def _create_chat_completion(
        self,
        messages: list,
        temperature: float = 0.2,
        max_tokens: int = 4000
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
    async def analyze_requirements(self, task_specification: str) -> Dict[str, Any]:
        """
        Analyze task specification to extract requirements and constraints.
        
        Args:
            task_specification (str): The task specification to analyze
            
        Returns:
            Dict[str, Any]: Structured analysis of requirements
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting requirements analysis")
        
        try:
            formatted_prompt = format_requirements_analysis_prompt(task_specification)

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior full stack developer with expertise in requirements analysis."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            analysis = await self._parse_llm_response(
                response_content,
                expected_keys=['features', 'technical_constraints', 'dependencies', 'technology_recommendations']
            )
            
            self.logger.info("Requirements analysis completed successfully")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in requirements analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="design_solution_component",
        metadata={
            "operation_details": {
                "prompt_template": "solution_design",
                "max_tokens": 3000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def design_solution_component(
        self,
        task_specification: str,
        requirements: Dict[str, Any],
        component: str
    ) -> Dict[str, Any]:
        """
        Design a specific component of the solution.
        
        Args:
            task_specification (str): Original task specification
            requirements (Dict[str, Any]): Analyzed requirements
            component (str): Component to design ("frontend", "backend", or "database")
            
        Returns:
            Dict[str, Any]: Component design
            
        Raises:
            Exception: If design generation fails
        """
        self.logger.info(f"Starting {component} solution design")
        
        if component not in ["frontend", "backend", "database"]:
            raise ValueError(f"Invalid component: {component}. Must be 'frontend', 'backend', or 'database'")
        
        try:
            formatted_prompt = format_solution_design_prompt(
                task_specification=task_specification,
                requirements=requirements,
                component=component
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a senior {component} developer with expertise in architecture and system design."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=3000
            )

            # Parse response
            design = await self._parse_llm_response(response_content)
            
            self.logger.info(f"{component.capitalize()} solution design completed successfully")
            return design
            
        except Exception as e:
            self.logger.error(f"Error in {component} solution design: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_component_code",
        metadata={
            "operation_details": {
                "prompt_template": "code_generation",
                "max_tokens": 4000,
                "temperature": 0.2,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_component_code(
        self,
        task_specification: str,
        requirements: Dict[str, Any],
        solution_design: Dict[str, Any],
        component: str
    ) -> Dict[str, str]:
        """
        Generate code for a specific component.
        
        Args:
            task_specification (str): Original task specification
            requirements (Dict[str, Any]): Analyzed requirements
            solution_design (Dict[str, Any]): Solution design for all components
            component (str): Component to generate code for ("frontend", "backend", or "database")
            
        Returns:
            Dict[str, str]: Dictionary of file paths and their content
            
        Raises:
            Exception: If code generation fails
        """
        self.logger.info(f"Starting {component} code generation")
        
        if component not in ["frontend", "backend", "database"]:
            raise ValueError(f"Invalid component: {component}. Must be 'frontend', 'backend', or 'database'")
        
        try:
            formatted_prompt = format_code_generation_prompt(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                component=component
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a senior {component} developer with expertise in writing high-quality, production-ready code."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=4000
            )

            # Parse response
            code_files = await self._parse_llm_response(response_content)
            
            self.logger.info(f"{component.capitalize()} code generation completed successfully")
            self.logger.debug(f"Generated {len(code_files)} {component} code files")
            
            return code_files
            
        except Exception as e:
            self.logger.error(f"Error in {component} code generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_documentation",
        metadata={
            "operation_details": {
                "prompt_template": "documentation_generation",
                "max_tokens": 4000,
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
        generated_code: Dict[str, Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Generate project documentation.
        
        Args:
            task_specification (str): Original task specification
            requirements (Dict[str, Any]): Analyzed requirements
            solution_design (Dict[str, Any]): Solution design for all components
            generated_code (Dict[str, Dict[str, str]]): Generated code files
            
        Returns:
            Dict[str, str]: Dictionary of documentation files and their content
            
        Raises:
            Exception: If documentation generation fails
        """
        self.logger.info("Starting documentation generation")
        
        try:
            formatted_prompt = format_documentation_generation_prompt(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                generated_code=generated_code
            )

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior technical writer with expertise in software documentation."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=4000
            )

            # Parse response
            documentation = await self._parse_llm_response(response_content)
            
            self.logger.info("Documentation generation completed successfully")
            self.logger.debug(f"Generated {len(documentation)} documentation files")
            
            return documentation
            
        except Exception as e:
            self.logger.error(f"Error in documentation generation: {str(e)}", exc_info=True)
            raise