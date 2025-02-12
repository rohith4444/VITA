import os
from typing import Dict, Any, List
import json
import openai
from dotenv import load_dotenv
from core.logging.logger import setup_logger
from .prompts import format_analysis_prompt, format_task_prompt

load_dotenv()

class LLMService:
    """Service for handling LLM interactions."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        openai.api_key = self.api_key
        self.model = "gpt-4"
        self.logger = setup_logger("llm.service")
        self.logger.info("Initializing LLM Service with model: gpt-4")
        
    async def analyze_requirements(self, 
                                 requirements: Dict[str, Any],
                                 prompt_template: str) -> Dict[str, Any]:
        """Analyze project requirements using LLM."""
        self.logger.info("Starting requirements analysis")
        self.logger.debug(f"Input requirements: {requirements}")
        
        try:
            # Format the prompt
            formatted_prompt = format_analysis_prompt(
                requirements.get('features', []),
                requirements.get('timeline', ''),
                requirements.get('constraints', [])
            )
            self.logger.debug("Prompt formatted successfully")
            
            # Call OpenAI API
            self.logger.debug("Calling OpenAI API for requirements analysis")
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skilled project manager and technical analyst."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse and structure the response
            analysis = self._parse_llm_response(response.choices[0].message.content)
            
            self.logger.info("Requirements analysis completed successfully")
            self.logger.debug(f"Analysis results: {analysis}")
            
            return analysis
            
        except openai.error.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error in requirements analysis: {str(e)}")
            raise
    
    async def generate_task_breakdown(self, 
                                    analysis: Dict[str, Any],
                                    prompt_template: str) -> List[Dict[str, Any]]:
        """Generate detailed task breakdown using LLM."""
        self.logger.info("Starting task breakdown generation")
        self.logger.debug(f"Input analysis: {analysis}")
        
        try:
            # Format the prompt
            formatted_prompt = format_task_prompt(
                analysis.get('scope', ''),
                analysis.get('features', []),
                analysis.get('constraints', [])
            )
            self.logger.debug("Task breakdown prompt formatted successfully")
            
            # Call OpenAI API
            self.logger.debug("Calling OpenAI API for task breakdown")
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical project manager specializing in task breakdown and estimation."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse and structure the response
            tasks = self._parse_task_breakdown(response.choices[0].message.content)
            
            self.logger.info(f"Task breakdown generated successfully: {len(tasks)} tasks")
            self.logger.debug(f"Generated tasks: {tasks}")
            
            return tasks
            
        except openai.error.OpenAIError as e:
            self.logger.error(f"OpenAI API error in task breakdown: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error in task breakdown generation: {str(e)}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and structure the LLM response."""
        self.logger.debug("Parsing LLM response")
        try:
            parsed_response = json.loads(response)
            self.logger.debug("Response parsed successfully as JSON")
            return parsed_response
        except json.JSONDecodeError:
            self.logger.warning("JSON parsing failed, falling back to basic parsing")
            try:
                # Fallback basic parsing
                lines = response.split('\n')
                analysis = {
                    'understood_requirements': [],
                    'suggested_features': [],
                    'potential_risks': [],
                    'technical_considerations': []
                }
                current_section = None
                
                for line in lines:
                    if line.strip().endswith(':'):
                        current_section = line.strip()[:-1].lower().replace(' ', '_')
                        continue
                    if current_section and line.strip():
                        analysis[current_section] = analysis.get(current_section, []) + [line.strip()]
                
                self.logger.debug("Basic parsing completed successfully")
                return analysis
            except Exception as e:
                self.logger.error(f"Error in basic response parsing: {str(e)}")
                raise
    
    def _parse_task_breakdown(self, response: str) -> List[Dict[str, Any]]:
        """Parse and structure the task breakdown response."""
        self.logger.debug("Parsing task breakdown response")
        try:
            # Try JSON parsing first
            tasks = json.loads(response)
            self.logger.debug("Task breakdown parsed successfully as JSON")
            return tasks
        except json.JSONDecodeError:
            self.logger.warning("JSON parsing failed for task breakdown, falling back to basic parsing")
            try:
                # Fallback basic parsing
                tasks = []
                current_task = None
                
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('Task:'):
                        if current_task:
                            tasks.append(current_task)
                        current_task = {'name': line[5:].strip()}
                    elif current_task and line.strip():
                        key, value = line.split(':', 1)
                        current_task[key.strip().lower()] = value.strip()
                
                if current_task:
                    tasks.append(current_task)
                
                self.logger.debug(f"Basic parsing completed: {len(tasks)} tasks extracted")
                return tasks
            except Exception as e:
                self.logger.error(f"Error in basic task breakdown parsing: {str(e)}")
                raise