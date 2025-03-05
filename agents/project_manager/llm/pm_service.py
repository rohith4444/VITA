from typing import Dict, Any, Optional
import json
from openai import AsyncOpenAI
from backend.config import Config
from core.logging.logger import setup_logger
from core.tracing.service import trace_class
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from .pm_prompts import format_requirement_analysis_prompt, format_project_plan_prompt

@trace_class
class LLMService:
    """Service for handling LLM interactions with OpenAI's GPT models."""
    
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
            parsed_response = json.loads(response)
            
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
        run_name="analyze_requirements",
        metadata={
            "operation_details": {
                "prompt_template": "requirement_analysis",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_requirements(self, project_description: str) -> Dict[str, Any]:
        """
        Analyze and restructure user requirements using LLM.
        
        Args:
            project_description (str): The project description to analyze
            
        Returns:
            Dict[str, Any]: Structured analysis of requirements
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting requirement analysis")
        self.logger.debug(f"Project description length: {len(project_description)} chars")
        
        try:
            formatted_prompt = format_requirement_analysis_prompt(project_description)
            self.logger.debug("Prompt formatted successfully")

            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a skilled project manager and business analyst."},
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            # Parse response with expected keys validation
            analysis = await self._parse_llm_response(
                response_content,
                expected_keys=['features', 'restructured_requirements']
            )
            
            self.logger.info("Requirement analysis completed successfully")
            self.logger.debug(f"Analysis contains {len(analysis.get('features', []))} features")

            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in requirement analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_project_plan",
        metadata={
            "operation_details": {
                "prompt_template": "project_plan",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_project_plan(
        self,
        problem_statement: str,
        features: list[str]
    ) -> Dict[str, Any]:
        """
        Generate a structured project plan using LLM.
        
        Args:
            problem_statement (str): The problem statement to plan for
            features (list): List of features to include in the plan
            
        Returns:
            Dict[str, Any]: Structured project plan
            
        Raises:
            Exception: If plan generation fails
        """
        self.logger.info("Generating project plan")
        self.logger.debug(f"Problem statement length: {len(problem_statement)} chars")
        self.logger.debug(f"Number of features: {len(features)}")

        try:
            prompt = format_project_plan_prompt(problem_statement, features)
            
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert software project planner."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )

            # Parse response with expected keys validation
            plan =await self._parse_llm_response(
                response_content,
                expected_keys=['milestones']
            )
            
            self.logger.info("Project plan generated successfully")
            self.logger.debug(f"Plan contains {len(plan.get('milestones', []))} milestones")

            return plan

        except Exception as e:
            self.logger.error(f"Error in project plan generation: {str(e)}", exc_info=True)
            raise