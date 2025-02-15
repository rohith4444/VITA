from typing import Dict, Any, List
import json
import openai
from backend.config import Config
from core.logging.logger import setup_logger
from .prompts import format_requirement_analysis_prompt, format_project_plan_prompt

class LLMService:
    """Service for handling LLM interactions."""
    
    def __init__(self):
        self.logger = setup_logger("llm.service")
        self.logger.info("Initializing LLM Service")
        
        try:
            self.api_key = Config.OPENAI_API_KEY
            if not self.api_key:
                self.logger.error("OpenAI API key not found in configuration")
                raise ValueError("OpenAI API key not found in environment variables")
                
            openai.api_key = self.api_key
            self.model = "gpt-4"
            self.logger.info(f"LLM Service initialized with model: {self.model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM Service: {str(e)}", exc_info=True)
            raise
        
    async def analyze_requirements(self, project_description: str) -> Dict[str, Any]:
        """
        Analyze and restructure user requirements using LLM.
        
        Args:
            project_description: Raw project description from user
            
        Returns:
            Dict[str, Any]: Structured analysis of requirements
        """
        self.logger.info("Starting requirement analysis")
        self.logger.debug(f"Project description length: {len(project_description)} chars")
        
        try:
            # Format the prompt
            formatted_prompt = format_requirement_analysis_prompt(project_description)
            self.logger.debug("Prompt formatted successfully")

            # Call OpenAI API
            self.logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skilled project manager and business analyst."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            # Parse response
            analysis = self._parse_llm_response(response.choices[0].message.content)
            self.logger.info("Requirement analysis completed successfully")
            self.logger.debug(f"Analysis contains {len(analysis.get('features', []))} features")

            return analysis
            
        except openai.error.InvalidAPIKeyError:
            self.logger.error("Invalid OpenAI API key", exc_info=True)
            raise
        except openai.error.RateLimitError:
            self.logger.error("OpenAI API rate limit exceeded", exc_info=True)
            raise
        except openai.error.APIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response as JSON", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in requirement analysis: {str(e)}", exc_info=True)
            raise
    
    async def generate_project_plan(self, problem_statement: str, features: List[str]) -> Dict[str, Any]:
        """
        Generate a structured project plan using LLM.
        
        Args:
            problem_statement: Structured problem description
            features: List of key project features
            
        Returns:
            Dict[str, Any]: Structured project plan
        """
        self.logger.info("Generating project plan")
        self.logger.debug(f"Problem statement length: {len(problem_statement)} chars")
        self.logger.debug(f"Number of features: {len(features)}")

        try:
            prompt = format_project_plan_prompt(problem_statement, features)

            self.logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software project planner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            structured_plan = json.loads(response.choices[0].message.content)
            self.logger.info("Project plan generated successfully")
            self.logger.debug(f"Plan contains {len(structured_plan.get('milestones', []))} milestones")

            return structured_plan

        except openai.error.InvalidAPIKeyError:
            self.logger.error("Invalid OpenAI API key", exc_info=True)
            raise
        except openai.error.RateLimitError:
            self.logger.error("OpenAI API rate limit exceeded", exc_info=True)
            raise
        except openai.error.APIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response as JSON", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in project plan generation: {str(e)}", exc_info=True)
            raise

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response: Raw response from OpenAI API
            
        Returns:
            Dict[str, Any]: Parsed response
        """
        self.logger.debug("Parsing LLM response")
        try:
            parsed_response = json.loads(response)
            self.logger.debug("Successfully parsed LLM response")
            return parsed_response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response: {str(e)}", exc_info=True)
            raise