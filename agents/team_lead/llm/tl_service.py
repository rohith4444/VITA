from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
from openai import AsyncOpenAI
from backend.config import Config
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from agents.team_lead.llm.tl_prompts import (
    format_task_coordination_prompt,
    format_agent_selection_prompt,
    format_progress_analysis_prompt,
    format_deliverable_integration_prompt,
    format_result_compilation_prompt,
    format_task_instruction_prompt,
    format_agent_feedback_prompt
)
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class TeamLeadLLMService:
    """
    LLM service for Team Lead Agent decision-making.
    Handles interactions with LLM for coordination, task analysis, progress monitoring, etc.
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
        self.logger = setup_logger("llm.team_lead.service")
        self.logger.info("Initializing Team Lead LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Team Lead LLM Service: {str(e)}", exc_info=True)
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
        self.logger.info(f"Team Lead LLM Service initialized with model: {self.model}")
    
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
                        if isinstance(key, str):
                            if "tasks" in key:
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

    @monitor_llm(
        run_name="coordinate_tasks",
        metadata={
            "operation_details": {
                "prompt_template": "task_coordination",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def coordinate_tasks(
        self,
        project_description: str,
        project_plan: Dict[str, Any],
        existing_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate project tasks by analyzing project plan and generating structured task breakdown.
        
        Args:
            project_description: Project description
            project_plan: Project plan from Project Manager agent
            existing_tasks: Optional list of already analyzed tasks
            
        Returns:
            Dict[str, Any]: Coordination results including tasks and execution plan
            
        Raises:
            Exception: If coordination fails
        """
        self.logger.info("Starting task coordination analysis")
        
        try:
            # Format prompt for task coordination
            formatted_prompt = format_task_coordination_prompt(
                project_description=project_description,
                project_plan=project_plan,
                tasks=existing_tasks
            )

            # Call LLM for task coordination
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI with expertise in project coordination and task management."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["tasks", "execution_plan"]
            coordination_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Task coordination completed with {len(coordination_result.get('tasks', []))} tasks")
            return coordination_result
            
        except Exception as e:
            self.logger.error(f"Error in task coordination: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="select_agent",
        metadata={
            "operation_details": {
                "prompt_template": "agent_selection",
                "max_tokens": 1000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def select_agent(
        self,
        task: Dict[str, Any],
        available_agents: List[str],
        agent_capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select the most appropriate agent for a given task.
        
        Args:
            task: Task information
            available_agents: List of available agent IDs
            agent_capabilities: Dictionary of agent capabilities
            
        Returns:
            Dict[str, Any]: Agent selection result with reasoning
            
        Raises:
            Exception: If agent selection fails
        """
        self.logger.info(f"Selecting agent for task {task.get('id', '')}")
        
        try:
            # Format prompt for agent selection
            formatted_prompt = format_agent_selection_prompt(
                task=task,
                available_agents=available_agents,
                agent_capabilities=agent_capabilities
            )

            # Call LLM for agent selection
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI with expertise in agent selection and task assignment."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1000
            )

            # Parse and validate response
            expected_keys = ["selected_agent_id", "reasoning", "confidence"]
            selection_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Selected agent {selection_result.get('selected_agent_id')} for task {task.get('id', '')}")
            return selection_result
            
        except Exception as e:
            self.logger.error(f"Error in agent selection: {str(e)}", exc_info=True)
            # Default to most appropriate agent based on task name if selection fails
            default_agent = self._default_agent_selection(task, available_agents)
            return {
                "selected_agent_id": default_agent,
                "reasoning": "Default selection based on task type.",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _default_agent_selection(self, task: Dict[str, Any], available_agents: List[str]) -> str:
        """
        Provide a default agent selection when LLM-based selection fails.
        
        Args:
            task: Task information
            available_agents: List of available agent IDs
            
        Returns:
            str: Selected agent ID
        """
        task_name = task.get("name", "").lower()
        
        # Default mappings based on keywords
        if any(kw in task_name for kw in ["architecture", "design", "system", "solution"]):
            agent_type = "solution_architect"
        elif any(kw in task_name for kw in ["test", "qa", "quality", "verify"]):
            agent_type = "qa_test"
        else:
            agent_type = "full_stack_developer"
        
        # Find an available agent of this type
        for agent_id in available_agents:
            if agent_type in agent_id:
                return agent_id
        
        # If no matching agent, return the first available
        return available_agents[0] if available_agents else "full_stack_developer"

    @monitor_llm(
        run_name="analyze_progress",
        metadata={
            "operation_details": {
                "prompt_template": "progress_analysis",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_progress(
        self,
        execution_plan: Dict[str, Any],
        current_progress: Dict[str, Any],
        task_statuses: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze project progress and provide recommendations.
        
        Args:
            execution_plan: Execution plan for the project
            current_progress: Current progress tracking data
            task_statuses: Dictionary mapping task IDs to status
            
        Returns:
            Dict[str, Any]: Progress analysis with recommendations
            
        Raises:
            Exception: If progress analysis fails
        """
        self.logger.info("Starting progress analysis")
        
        try:
            # Format prompt for progress analysis
            formatted_prompt = format_progress_analysis_prompt(
                execution_plan=execution_plan,
                current_progress=current_progress,
                task_statuses=task_statuses
            )

            # Call LLM for progress analysis
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI with expertise in project monitoring and analysis."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["project_health", "critical_issues", "action_items"]
            analysis_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Progress analysis completed with project health: {analysis_result.get('project_health', 'unknown')}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in progress analysis: {str(e)}", exc_info=True)
            # Return basic analysis if it fails
            return {
                "project_health": "unknown",
                "completion_assessment": "Unable to assess completion due to error",
                "critical_issues": [{"issue": "Analysis error", "impact": "Unknown", "recommendation": "Retry analysis"}],
                "action_items": [{"action": "Retry progress analysis", "priority": "HIGH"}],
                "error": str(e)
            }

    @monitor_llm(
        run_name="integrate_deliverables",
        metadata={
            "operation_details": {
                "prompt_template": "deliverable_integration",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def integrate_deliverables(
        self,
        task: Dict[str, Any],
        deliverable: Dict[str, Any],
        related_deliverables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze and integrate deliverables from different agents.
        
        Args:
            task: Task information
            deliverable: The main deliverable to analyze
            related_deliverables: List of related deliverables
            
        Returns:
            Dict[str, Any]: Deliverable integration result
            
        Raises:
            Exception: If deliverable integration fails
        """
        self.logger.info(f"Integrating deliverable for task {task.get('id', '')}")
        
        try:
            # Format prompt for deliverable integration
            formatted_prompt = format_deliverable_integration_prompt(
                task=task,
                deliverable=deliverable,
                related_deliverables=related_deliverables
            )

            # Call LLM for deliverable integration
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI with expertise in integrating and validating deliverables."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["acceptance", "quality_assessment", "integration_issues"]
            integration_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Deliverable integration completed with acceptance: {integration_result.get('acceptance', 'unknown')}")
            return integration_result
            
        except Exception as e:
            self.logger.error(f"Error in deliverable integration: {str(e)}", exc_info=True)
            # Return basic integration result if it fails
            return {
                "acceptance": "revise",
                "quality_assessment": "Unable to assess quality due to error",
                "integration_issues": [{"issue": "Integration error", "severity": "HIGH", "resolution": "Retry integration"}],
                "next_steps": ["Retry deliverable integration"],
                "error": str(e)
            }

    @monitor_llm(
        run_name="compile_results",
        metadata={
            "operation_details": {
                "prompt_template": "result_compilation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def compile_results(
        self,
        project_description: str,
        deliverables: Dict[str, Dict[str, Any]],
        component_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compile project results from deliverables into a final structure.
        
        Args:
            project_description: Project description
            deliverables: Dictionary of deliverables
            component_structure: Target component structure for the project
            
        Returns:
            Dict[str, Any]: Compilation result with plan and structure
            
        Raises:
            Exception: If result compilation fails
        """
        self.logger.info("Starting result compilation")
        
        try:
            # Format prompt for result compilation
            formatted_prompt = format_result_compilation_prompt(
                project_description=project_description,
                deliverables=deliverables,
                component_structure=component_structure
            )

            # Call LLM for result compilation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI with expertise in compiling and organizing project results."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["compilation_plan", "final_project_structure"]
            compilation_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Result compilation completed successfully")
            return compilation_result
            
        except Exception as e:
            self.logger.error(f"Error in result compilation: {str(e)}", exc_info=True)
            # Return basic compilation result if it fails
            return {
                "compilation_plan": {
                    "directory_structure": {"root_directory": "project", "subdirectories": []},
                    "file_mappings": []
                },
                "final_project_structure": {"components": []},
                "error": str(e)
            }

    @monitor_llm(
        run_name="create_task_instruction",
        metadata={
            "operation_details": {
                "prompt_template": "task_instruction",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_text"
            }
        }
    )
    async def create_task_instruction(
        self,
        task: Dict[str, Any],
        agent_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Create detailed task instructions for an agent.
        
        Args:
            task: Task information
            agent_type: Type of the agent receiving instructions
            context: Additional context for the task
            
        Returns:
            str: Formatted task instruction
            
        Raises:
            Exception: If instruction creation fails
        """
        self.logger.info(f"Creating task instruction for {agent_type} on task {task.get('id', '')}")
        
        try:
            # Format prompt for task instruction
            formatted_prompt = format_task_instruction_prompt(
                task=task,
                agent_type=agent_type,
                context=context
            )

            # Call LLM for task instruction
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a Team Lead AI creating instructions for a {agent_type.replace('_', ' ').title()} agent."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )
            
            self.logger.info(f"Task instruction created for {agent_type} on task {task.get('id', '')}")
            return response_content
            
        except Exception as e:
            self.logger.error(f"Error creating task instruction: {str(e)}", exc_info=True)
            # Return basic instruction if it fails
            return f"""
            Task: {task.get('name', 'Unknown Task')}
            
            Please complete this task based on your capabilities as a {agent_type.replace('_', ' ').title()}.
            
            Task ID: {task.get('id', '')}
            """

    @monitor_llm(
        run_name="provide_feedback",
        metadata={
            "operation_details": {
                "prompt_template": "agent_feedback",
                "max_tokens": 1000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def provide_feedback(
        self,
        task: Dict[str, Any],
        deliverable: Dict[str, Any],
        feedback_points: List[str]
    ) -> Dict[str, Any]:
        """
        Provide constructive feedback to an agent on their deliverable.
        
        Args:
            task: Task information
            deliverable: The deliverable to provide feedback on
            feedback_points: List of feedback points to address
            
        Returns:
            Dict[str, Any]: Structured feedback with improvement suggestions
            
        Raises:
            Exception: If feedback generation fails
        """
        self.logger.info(f"Generating feedback for task {task.get('id', '')}")
        
        try:
            # Format prompt for agent feedback
            formatted_prompt = format_agent_feedback_prompt(
                task=task,
                deliverable=deliverable,
                feedback_points=feedback_points
            )

            # Call LLM for agent feedback
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Team Lead AI providing constructive feedback to team members."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1000
            )

            # Parse and validate response
            expected_keys = ["feedback_message", "improvement_areas"]
            feedback_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Feedback generated for task {task.get('id', '')}")
            return feedback_result
            
        except Exception as e:
            self.logger.error(f"Error generating feedback: {str(e)}", exc_info=True)
            # Return basic feedback if it fails
            return {
                "feedback_message": f"Thank you for your work on task {task.get('id', '')}. Some improvements are needed.",
                "positive_aspects": ["Effort made to complete the task"],
                "improvement_areas": [{"area": "General quality", "suggestion": "Please review and improve", "priority": "MEDIUM"}],
                "revision_instructions": "Please address the feedback and resubmit.",
                "error": str(e)
            }