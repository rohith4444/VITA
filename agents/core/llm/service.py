import os
from typing import Dict, Any, List
import json
import openai
from backend.config import Config
from core.logging.logger import setup_logger
from .prompts import format_requirement_analysis_prompt, format_project_plan_prompt

class LLMService:
    """Service for handling LLM interactions."""
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        openai.api_key = self.api_key
        self.model = "gpt-4"
        self.logger = setup_logger("llm.service")
        self.logger.info("Initializing LLM Service with model: gpt-4")
        
    async def analyze_requirements(self, project_description: str) -> Dict[str, Any]:
        """Analyze and restructure user requirements using LLM."""
        self.logger.info("Starting requirement analysis")
        self.logger.debug(f"Received project description: {project_description}")
        
        try:
            # Format the prompt
            formatted_prompt = format_requirement_analysis_prompt(project_description)
            self.logger.debug("Prompt formatted successfully")

            # Call OpenAI API
            self.logger.debug("Calling OpenAI API for requirement analysis")
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
            self.logger.debug(f"Structured output: {analysis}")

            return analysis
            
        except openai.error.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return {"error": "LLM request failed"}
    
    async def generate_project_plan(self, problem_statement: str, features: List[str]) -> Dict[str, Any]:
        """Generate a structured project plan using LLM."""
        self.logger.info("Generating project plan using LLM")
        self.logger.debug(f"Problem statement: {problem_statement}, Features: {features}")

        try:
            prompt = format_project_plan_prompt(problem_statement, features)

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert software project planner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            structured_plan = json.loads(response.choices[0].message.content)
            self.logger.debug(f"LLM Response: {structured_plan}")

            return structured_plan

        except openai.error.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return {"error": "LLM request failed"}

        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response")
            return {"error": "Invalid response format"}