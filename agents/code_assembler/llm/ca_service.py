from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
from openai import AsyncOpenAI
from backend.config import Config
from agents.core.monitoring.decorators import monitor_llm, monitor_operation
from agents.code_assembler.llm.ca_prompts import (
    format_component_analysis_prompt,
    format_structure_planning_prompt,
    format_integration_planning_prompt,
    format_config_generation_prompt,
    format_project_compilation_prompt,
    format_conflict_resolution_prompt,
    format_documentation_generation_prompt
)
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

@trace_class
class CodeAssemblerLLMService:
    """
    LLM service for Code Assembler Agent.
    Handles interactions with LLM for code integration, component analysis, structure planning, etc.
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
        self.logger = setup_logger("llm.code_assembler.service")
        self.logger.info("Initializing Code Assembler LLM Service")
        self.model = model
        
        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Code Assembler LLM Service: {str(e)}", exc_info=True)
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
        self.logger.info(f"Code Assembler LLM Service initialized with model: {self.model}")
    
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
                            if "component" in key or "dependencies" in key:
                                parsed_response[key] = []
                            elif "structure" in key or "plan" in key:
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
        run_name="analyze_components",
        metadata={
            "operation_details": {
                "prompt_template": "component_analysis",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def analyze_components(
        self,
        components: Dict[str, Any],
        project_type: str,
        project_description: str
    ) -> Dict[str, Any]:
        """
        Analyze component relationships and dependencies.
        
        Args:
            components: Dictionary of collected components
            project_type: Type of project being assembled
            project_description: Description of the project
            
        Returns:
            Dict[str, Any]: Analysis results including dependencies and organization
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting component analysis")
        
        try:
            # Format prompt for component analysis
            formatted_prompt = format_component_analysis_prompt(
                components=components,
                project_type=project_type,
                project_description=project_description
            )

            # Call LLM for component analysis
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in analyzing code components and their relationships."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["component_dependencies", "file_organization", "missing_components", "build_order"]
            analysis_result = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Component analysis completed with {len(analysis_result.get('component_dependencies', []))} dependencies identified")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in component analysis: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="plan_project_structure",
        metadata={
            "operation_details": {
                "prompt_template": "structure_planning",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def plan_project_structure(
        self,
        dependency_analysis: Dict[str, Any],
        components: Dict[str, Any],
        project_type: str
    ) -> Dict[str, Any]:
        """
        Plan the project file structure based on component analysis.
        
        Args:
            dependency_analysis: Result of component dependency analysis
            components: Dictionary of collected components
            project_type: Type of project being assembled
            
        Returns:
            Dict[str, Any]: Project structure plan
            
        Raises:
            Exception: If structure planning fails
        """
        self.logger.info("Starting project structure planning")
        
        try:
            # Format prompt for structure planning
            formatted_prompt = format_structure_planning_prompt(
                dependency_analysis=dependency_analysis,
                components=components,
                project_type=project_type
            )

            # Call LLM for structure planning
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in organizing code into optimal project structures."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["directory_structure", "file_mappings", "organization_principles"]
            structure_plan = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Structure planning completed with {len(structure_plan.get('file_mappings', []))} file mappings")
            return structure_plan
            
        except Exception as e:
            self.logger.error(f"Error in structure planning: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="plan_component_integration",
        metadata={
            "operation_details": {
                "prompt_template": "integration_planning",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def plan_component_integration(
        self,
        file_structure: Dict[str, Any],
        validation_results: Dict[str, Any],
        components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Plan the integration of components into a cohesive project.
        
        Args:
            file_structure: Planned file and directory structure
            validation_results: Results of structure validation
            components: Dictionary of collected components
            
        Returns:
            Dict[str, Any]: Component integration plan
            
        Raises:
            Exception: If integration planning fails
        """
        self.logger.info("Starting component integration planning")
        
        try:
            # Format prompt for integration planning
            formatted_prompt = format_integration_planning_prompt(
                file_structure=file_structure,
                validation_results=validation_results,
                components=components
            )

            # Call LLM for integration planning
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in integrating code components into cohesive projects."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["integration_strategies", "conflict_resolutions", "integration_sequence"]
            integration_plan = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Integration planning completed with {len(integration_plan.get('integration_strategies', []))} integration strategies")
            return integration_plan
            
        except Exception as e:
            self.logger.error(f"Error in integration planning: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_config_files",
        metadata={
            "operation_details": {
                "prompt_template": "config_generation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_config_files(
        self,
        project_name: str,
        config_name: str,
        config_type: str,
        technologies: Dict[str, List[str]],
        prompt: str
    ) -> str:
        """
        Generate configuration file content.
        
        Args:
            project_name: Name of the project
            config_name: Name of the configuration file
            config_type: Type of configuration
            technologies: Technologies used in the project
            prompt: Prompt for configuration generation
            
        Returns:
            str: Generated configuration content
            
        Raises:
            Exception: If configuration generation fails
        """
        self.logger.info(f"Generating configuration file: {config_name}")
        
        try:
            # Call LLM for config generation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in generating configuration files for software projects."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )
            
            self.logger.info(f"Configuration generation completed for {config_name}")
            return response_content
            
        except Exception as e:
            self.logger.error(f"Error generating configuration {config_name}: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="compile_project",
        metadata={
            "operation_details": {
                "prompt_template": "project_compilation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def compile_project(
        self,
        file_structure: Dict[str, Any],
        integration_plan: Dict[str, Any],
        config_files: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate plan for final project compilation.
        
        Args:
            file_structure: Planned file and directory structure
            integration_plan: Plan for integrating components
            config_files: Generated configuration files
            validation_results: Results of structure validation
            
        Returns:
            Dict[str, Any]: Project compilation plan
            
        Raises:
            Exception: If compilation planning fails
        """
        self.logger.info("Starting project compilation planning")
        
        try:
            # Format prompt for project compilation
            formatted_prompt = format_project_compilation_prompt(
                file_structure=file_structure,
                integration_plan=integration_plan,
                config_files=config_files,
                validation_results=validation_results
            )

            # Call LLM for compilation planning
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in compiling code components into complete projects."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["compilation_plan", "output_structure", "validation_checklist"]
            compilation_plan = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Project compilation planning completed")
            return compilation_plan
            
        except Exception as e:
            self.logger.error(f"Error in project compilation planning: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="resolve_conflict",
        metadata={
            "operation_details": {
                "prompt_template": "conflict_resolution",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def resolve_conflict(
        self,
        conflict: Dict[str, Any],
        components: Dict[str, Any],
        project_type: str
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between components.
        
        Args:
            conflict: Information about the conflict
            components: Dictionary of collected components
            project_type: Type of project being assembled
            
        Returns:
            Dict[str, Any]: Conflict resolution with implementation details
            
        Raises:
            Exception: If conflict resolution fails
        """
        self.logger.info(f"Resolving conflict between components")
        
        try:
            # Format prompt for conflict resolution
            formatted_prompt = format_conflict_resolution_prompt(
                conflict=conflict,
                components=components,
                project_type=project_type
            )

            # Call LLM for conflict resolution
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in resolving conflicts between code components."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["conflict_analysis", "resolution_strategies", "recommended_strategy", "implementation"]
            resolution = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Conflict resolution completed")
            return resolution
            
        except Exception as e:
            self.logger.error(f"Error in conflict resolution: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="generate_documentation",
        metadata={
            "operation_details": {
                "prompt_template": "documentation_generation",
                "max_tokens": 2000,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_documentation(
        self,
        components: Dict[str, Any],
        project_type: str,
        file_structure: Dict[str, Any],
        project_description: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation for the project.
        
        Args:
            components: Dictionary of collected components
            project_type: Type of project being assembled
            file_structure: Planned file and directory structure
            project_description: Description of the project
            
        Returns:
            Dict[str, Any]: Generated documentation contents
            
        Raises:
            Exception: If documentation generation fails
        """
        self.logger.info("Starting documentation generation")
        
        try:
            # Format prompt for documentation generation
            formatted_prompt = format_documentation_generation_prompt(
                components=components,
                project_type=project_type,
                file_structure=file_structure,
                project_description=project_description
            )

            # Call LLM for documentation generation
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in generating comprehensive documentation for software projects."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=2000
            )

            # Parse and validate response
            expected_keys = ["readme", "setup_guide", "usage_documentation"]
            documentation = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info("Documentation generation completed")
            return documentation
            
        except Exception as e:
            self.logger.error(f"Error in documentation generation: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="identify_missing_components",
        metadata={
            "operation_details": {
                "prompt_template": "missing_components",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def generate_missing_components(
        self,
        missing_components: List[Dict[str, Any]],
        existing_components: Dict[str, Any],
        project_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate content for missing components identified in validation.
        
        Args:
            missing_components: List of missing components to generate
            existing_components: Dictionary of existing components
            project_type: Type of project being assembled
            
        Returns:
            Dict[str, Dict[str, Any]]: Generated components with content
            
        Raises:
            Exception: If component generation fails
        """
        self.logger.info(f"Generating {len(missing_components)} missing components")
        
        try:
            generated_components = {}
            
            for missing in missing_components:
                component_name = missing.get("name", "unknown")
                purpose = missing.get("purpose", "")
                related_components = missing.get("related_to", [])
                
                # Extract related components content for context
                related_content = {}
                for related_id in related_components:
                    if related_id in existing_components:
                        related_content[related_id] = existing_components[related_id]
                
                # Create a prompt for this specific component
                prompt = f"""
                As a Code Assembler AI, generate content for a missing component in a software project:
                
                COMPONENT NAME:
                {component_name}
                
                PURPOSE:
                {purpose}
                
                PROJECT TYPE:
                {project_type}
                
                RELATED COMPONENTS:
                {str(related_content)[:500]}...
                
                Generate appropriate content for this component that fulfills its purpose and integrates with the related components.
                The content should be complete, well-structured, and follow best practices for this type of component.
                
                Format your response as the raw content of the component, with no additional explanations.
                """
                
                # Call LLM to generate the component
                component_content = await self._create_chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a Code Assembler AI with expertise in generating code components."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500
                )
                
                # Store the generated component
                generated_components[component_name] = {
                    "name": component_name,
                    "content": component_content,
                    "purpose": purpose,
                    "generated": True,
                    "related_to": related_components
                }
                
                self.logger.info(f"Generated missing component: {component_name}")
            
            self.logger.info(f"Generated {len(generated_components)} missing components")
            return generated_components
            
        except Exception as e:
            self.logger.error(f"Error generating missing components: {str(e)}", exc_info=True)
            raise

    @monitor_llm(
        run_name="assess_project_quality",
        metadata={
            "operation_details": {
                "prompt_template": "quality_assessment",
                "max_tokens": 1500,
                "temperature": 0.3,
                "response_format": "structured_json"
            }
        }
    )
    async def assess_project_quality(
        self,
        components: Dict[str, Any],
        file_structure: Dict[str, Any],
        project_type: str
    ) -> Dict[str, Any]:
        """
        Assess the quality of the assembled project.
        
        Args:
            components: Dictionary of collected components
            file_structure: Planned file and directory structure
            project_type: Type of project being assembled
            
        Returns:
            Dict[str, Any]: Quality assessment with recommendations
            
        Raises:
            Exception: If quality assessment fails
        """
        self.logger.info("Starting project quality assessment")
        
        try:
            # Create a prompt for quality assessment
            prompt = f"""
            As a Code Assembler AI, assess the quality of this assembled software project:
            
            PROJECT TYPE:
            {project_type}
            
            FILE STRUCTURE:
            {str(file_structure)[:500]}...
            
            COMPONENTS OVERVIEW:
            Total Components: {len(components)}
            Component Types: {set(comp.get("type", "unknown") for comp in components.values())}
            
            Assess the overall quality of the project, focusing on:
            1. Code quality and consistency
            2. Architecture and organization
            3. Completeness and coverage
            4. Best practices adherence
            5. Potential improvements
            
            Format your response as a JSON object with:
            {{
                "overall_quality_score": 0-100,
                "quality_assessment": "Overall assessment of project quality",
                "strengths": [
                    "Strength 1",
                    "Strength 2"
                ],
                "weaknesses": [
                    "Weakness 1",
                    "Weakness 2"
                ],
                "improvement_recommendations": [
                    {{
                        "area": "Area for improvement",
                        "recommendation": "Specific recommendation",
                        "priority": "HIGH/MEDIUM/LOW"
                    }}
                ],
                "best_practices_adherence": {{
                    "score": 0-100,
                    "notes": "Notes on best practices adherence"
                }}
            }}
            """
            
            # Call LLM for quality assessment
            response_content = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Code Assembler AI with expertise in assessing software project quality."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )

            # Parse and validate response
            expected_keys = ["overall_quality_score", "quality_assessment", "improvement_recommendations"]
            assessment = await self._parse_llm_response(response_content, expected_keys)
            
            self.logger.info(f"Project quality assessment completed with score: {assessment.get('overall_quality_score', 0)}")
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in project quality assessment: {str(e)}", exc_info=True)
            # Return basic assessment if it fails
            return {
                "overall_quality_score": 50,
                "quality_assessment": "Unable to complete full assessment due to error",
                "improvement_recommendations": [
                    {
                        "area": "Error handling",
                        "recommendation": "Review project quality manually",
                        "priority": "HIGH"
                    }
                ]
            }