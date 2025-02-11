import os
from typing import Dict, Any, List
import openai
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """Service for handling LLM interactions."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.model = "gpt-4"  # Can be configured based on needs
        
    async def analyze_requirements(self, 
                                 requirements: Dict[str, Any],
                                 prompt_template: str) -> Dict[str, Any]:
        """
        Analyze project requirements using LLM.
        
        Args:
            requirements: Dictionary containing project requirements
            prompt_template: Template for the prompt
        
        Returns:
            Dictionary containing analyzed requirements
        """
        try:
            # Format the prompt with requirements
            formatted_prompt = prompt_template.format(
                features=requirements.get('features', []),
                timeline=requirements.get('timeline', ''),
                constraints=requirements.get('constraints', [])
            )
            
            # Call OpenAI API
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
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error in LLM analysis: {str(e)}")
    
    async def generate_task_breakdown(self, 
                                    analysis: Dict[str, Any],
                                    prompt_template: str) -> List[Dict[str, Any]]:
        """
        Generate detailed task breakdown using LLM.
        
        Args:
            analysis: Dictionary containing requirement analysis
            prompt_template: Template for the prompt
        
        Returns:
            List of tasks with details
        """
        try:
            # Format the prompt with analysis
            formatted_prompt = prompt_template.format(
                scope=analysis.get('scope', ''),
                features=analysis.get('features', []),
                constraints=analysis.get('constraints', [])
            )
            
            # Call OpenAI API
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
            
            return tasks
            
        except Exception as e:
            raise Exception(f"Error in task breakdown: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and structure the LLM response."""
        # TODO: Implement more robust parsing
        # For now, assuming response is in a structured format
        try:
            import json
            return json.loads(response)
        except:
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
            
            return analysis
    
    def _parse_task_breakdown(self, response: str) -> List[Dict[str, Any]]:
        """Parse and structure the task breakdown response."""
        try:
            import json
            return json.loads(response)
        except:
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
            
            return tasks