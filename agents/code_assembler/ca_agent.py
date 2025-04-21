from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime
import json
import os
from core.logging.logger import setup_logger
from core.tracing.service import trace_method, trace_class
from agents.core.base_agent import BaseAgent
from agents.code_assembler.llm.ca_service import CodeAssemblerLLMService
from agents.code_assembler.ca_state_graph import CodeAssemblerGraphState, validate_state, get_next_stage
from tools.code_assembler.dependency_analyzer import DependencyAnalyzer
from tools.code_assembler.file_organizer import FileOrganizer, ProjectType, Component, ComponentType
from tools.code_assembler.structure_validator import StructureValidator, ValidationLevel
from tools.code_assembler.config_generator import ConfigGenerator, ConfigType
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from agents.core.monitoring.decorators import monitor_operation

# Initialize logger
logger = setup_logger("code_assembler.agent")

@trace_class
class CodeAssemblerAgent(BaseAgent):
    """
    Code Assembler Agent responsible for collecting, organizing, and integrating 
    code components into a cohesive final project.
    
    Attributes:
        agent_id (str): Unique identifier for this agent instance
        name (str): Display name for the agent
        memory_manager (MemoryManager): Memory management system
        llm_service (CodeAssemblerLLMService): LLM service for decision-making
        project_name (str): Name of the current project
        output_dir (str): Directory for the assembled project
    """
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        """
        Initialize the Code Assembler Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            name: Display name for the agent
            memory_manager: Memory management system
        """
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"code_assembler.{agent_id}")
        self.logger.info(f"Initializing CodeAssemblerAgent with ID: {agent_id}")
        
        try:
            # Initialize LLM service
            self.llm_service = CodeAssemblerLLMService()
            
            # Initialize project variables
            self.project_name = f"project_{agent_id}"
            self.output_dir = os.path.join("outputs", self.project_name)
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("CodeAssemblerAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeAssemblerAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self):
        """Build the LangGraph-based execution flow for Code Assembler Agent."""
        self.logger.info("Building CodeAssembler processing graph")
        try:
            # Initialize graph builder
            from agents.core.graph.graph_builder import WorkflowGraphBuilder
            builder = WorkflowGraphBuilder(CodeAssemblerGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes (primary state handlers)
            self.logger.debug("Adding graph nodes")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_dependencies", self.analyze_dependencies)
            builder.add_node("plan_structure", self.plan_structure)
            builder.add_node("validate_structure", self.validate_structure)
            builder.add_node("integrate_components", self.integrate_components)
            builder.add_node("generate_configs", self.generate_configs)
            builder.add_node("compile_project", self.compile_project)
            builder.add_node("complete", self.complete_assembly)
            
            # Add edges (state transitions)
            self.logger.debug("Adding graph edges")
            builder.add_edge("start", "analyze_dependencies")
            builder.add_edge("analyze_dependencies", "plan_structure")
            builder.add_edge("plan_structure", "validate_structure")
            builder.add_edge("validate_structure", "integrate_components", 
                          condition=self._structure_is_valid)
            builder.add_edge("validate_structure", "plan_structure", 
                          condition=self._structure_needs_revision)
            builder.add_edge("integrate_components", "generate_configs")
            builder.add_edge("generate_configs", "compile_project")
            builder.add_edge("compile_project", "complete")
            
            # Add conditional transitions for error handling
            builder.add_edge("analyze_dependencies", "analyze_dependencies",
                         condition=self._should_retry_analysis)
            
            # Set entry point
            builder.set_entry_point("start")
            
            # Compile graph
            compiled_graph = builder.compile()
            self.logger.info("Successfully built and compiled graph")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise

    def _get_graph_builder(self):
        """Return the graph builder for visualization."""
        if not hasattr(self, '_graph_builder'):
            self._build_graph()  # This will create and store the builder
        return self._graph_builder
    
    # State transition condition methods
    
    def _structure_is_valid(self, state: CodeAssemblerGraphState) -> bool:
        """
        Determine if the structure is valid and we can proceed to integration.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if structure is valid and we can proceed
        """
        validation_results = state.get("validation_results", {})
        return not validation_results.get("has_errors", False)
    
    def _structure_needs_revision(self, state: CodeAssemblerGraphState) -> bool:
        """
        Determine if the structure needs revision before proceeding.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if structure needs revision
        """
        validation_results = state.get("validation_results", {})
        return validation_results.get("has_errors", False)
    
    def _should_retry_analysis(self, state: CodeAssemblerGraphState) -> bool:
        """
        Determine if dependency analysis should be retried.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if analysis should be retried
        """
        # This is a placeholder for potential retry logic
        # In a real implementation, you might check for specific error conditions
        return False
    
    @trace_method
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Code Assembler Agent's workflow.
        
        Args:
            input_data: Input containing project details and collected components
            
        Returns:
            Dict[str, Any]: Final results of the code assembly process
        """
        self.logger.info("Starting CodeAssembler workflow execution")
        try:
            # Ensure input contains required fields
            if "components" not in input_data:
                raise ValueError("Input must contain 'components' field with collected components")
                
            if "project_type" not in input_data:
                input_data["project_type"] = "generic"  # Default to generic project type
                
            if "project_description" not in input_data:
                input_data["project_description"] = "Software project"  # Default description
            
            self.logger.debug(f"Input data contains {len(input_data.get('components', {}))} components")
            
            # Create initial state
            initial_state = {
                "input": input_data,
                "components": input_data.get("components", {}),
                "dependency_graph": {},
                "file_structure": {},
                "validation_results": {},
                "integration_plan": {},
                "compiled_project": {},
                "config_files": {},
                "output_location": "",
                "status": "initialized"
            }
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke(initial_state)
            
            self.logger.info("Workflow completed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            raise
    
    # State handler methods
    
    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Handle initial input and setup.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting receive_input phase")
        
        try:
            input_data = state["input"]
            components = state["components"]
            
            # Create project name based on input
            if "project_name" in input_data:
                self.project_name = input_data["project_name"]
            else:
                self.project_name = f"project_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Update output directory
            self.output_dir = os.path.join("outputs", self.project_name)
            
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Store initial data in memory
            memory_entry = {
                "project_name": self.project_name,
                "component_count": len(components),
                "project_type": input_data.get("project_type", "generic"),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            # Update status for next phase
            state["status"] = "analyzing_dependencies"
            
            self.logger.info(f"Input processing completed for project: {self.project_name}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_dependencies",
                      metadata={"phase": "dependency_analysis"})
    async def analyze_dependencies(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Analyze component dependencies using the dependency analyzer tool.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with dependency analysis
        """
        self.logger.info("Starting analyze_dependencies phase")
        
        try:
            input_data = state["input"]
            components = state["components"]
            project_type = input_data.get("project_type", "generic")
            project_description = input_data.get("project_description", "Software project")
            
            # Use DependencyAnalyzer to analyze component dependencies
            dependency_analyzer = DependencyAnalyzer()
            
            # Register components with the analyzer
            for component_id, component in components.items():
                file_path = component.get("file_path", f"{component_id}.txt")
                content = component.get("content", "")
                
                dependency_analyzer.register_component(
                    component_id=component_id,
                    file_path=file_path,
                    content=content,
                    metadata=component
                )
            
            # Analyze dependencies
            dependency_graph = dependency_analyzer.analyze_all_dependencies()
            
            # Generate dependency report
            dependency_report = dependency_analyzer.generate_dependency_report()
            
            # Store in state
            state["dependency_graph"] = dependency_report
            
            # Use LLM for additional analysis
            component_analysis = await self.llm_service.analyze_components(
                components=components,
                project_type=project_type,
                project_description=project_description
            )
            
            # Merge LLM analysis with tool analysis
            merged_analysis = self._merge_dependency_analyses(dependency_report, component_analysis)
            state["dependency_graph"] = merged_analysis
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "dependency_analysis": merged_analysis,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )
            
            # Update status for next phase
            state["status"] = "planning_structure"
            
            self.logger.info(f"Dependency analysis completed with {len(merged_analysis.get('component_dependencies', []))} dependencies")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_dependencies: {str(e)}", exc_info=True)
            raise
    
    def _merge_dependency_analyses(
        self, 
        tool_analysis: Dict[str, Any], 
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge dependency analyses from tool and LLM.
        
        Args:
            tool_analysis: Analysis from DependencyAnalyzer tool
            llm_analysis: Analysis from LLM service
            
        Returns:
            Dict[str, Any]: Merged analysis
        """
        merged = tool_analysis.copy()
        
        # Merge component dependencies
        if "component_dependencies" in llm_analysis:
            if "component_dependencies" not in merged:
                merged["component_dependencies"] = []
            
            # Add unique dependencies from LLM analysis
            existing_deps = {f"{dep.get('source_component')}_{dep.get('target_component')}" 
                            for dep in merged.get("component_dependencies", [])}
            
            for dep in llm_analysis.get("component_dependencies", []):
                dep_key = f"{dep.get('source_component')}_{dep.get('target_component')}"
                if dep_key not in existing_deps:
                    merged["component_dependencies"].append(dep)
        
        # Add file organization from LLM analysis
        if "file_organization" in llm_analysis:
            merged["file_organization"] = llm_analysis["file_organization"]
        
        # Add missing components from LLM analysis
        if "missing_components" in llm_analysis:
            merged["missing_components"] = llm_analysis["missing_components"]
        
        # Use LLM-generated build order if tool didn't provide one
        if not merged.get("build_order") and "build_order" in llm_analysis:
            merged["build_order"] = llm_analysis["build_order"]
        
        return merged

    @monitor_operation(operation_type="plan_structure",
                      metadata={"phase": "structure_planning"})
    async def plan_structure(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Plan the project structure based on dependency analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with file structure plan
        """
        self.logger.info("Starting plan_structure phase")
        
        try:
            input_data = state["input"]
            components = state["components"]
            dependency_graph = state["dependency_graph"]
            project_type = input_data.get("project_type", "generic")
            
            # Convert project_type string to ProjectType enum
            project_type_enum = ProjectType.UNKNOWN
            try:
                project_type_enum = ProjectType(project_type)
            except (ValueError, KeyError):
                self.logger.warning(f"Unknown project type: {project_type}, using UNKNOWN")
            
            # Use LLM to plan the structure
            structure_plan = await self.llm_service.plan_project_structure(
                dependency_analysis=dependency_graph,
                components=components,
                project_type=project_type
            )
            
            # Store the structure plan in state
            state["file_structure"] = structure_plan
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "file_structure": structure_plan,
                    "structure_timestamp": datetime.now().isoformat()
                }
            )
            
            # Update status for next phase
            state["status"] = "validating_structure"
            
            self.logger.info(f"Structure planning completed with {len(structure_plan.get('file_mappings', []))} file mappings")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in plan_structure: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="validate_structure",
                      metadata={"phase": "structure_validation"})
    async def validate_structure(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Validate the planned project structure.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with validation results
        """
        self.logger.info("Starting validate_structure phase")
        
        try:
            input_data = state["input"]
            file_structure = state["file_structure"]
            project_type = input_data.get("project_type", "generic")
            
            # Convert project_type string to ProjectType enum
            project_type_enum = ProjectType.UNKNOWN
            try:
                project_type_enum = ProjectType(project_type)
            except (ValueError, KeyError):
                self.logger.warning(f"Unknown project type: {project_type}, using UNKNOWN")
            
            # Create a temporary project structure to validate
            # This is just to check the structure, not to create the final output
            temp_output_dir = os.path.join(self.output_dir, "_validation_temp")
            os.makedirs(temp_output_dir, exist_ok=True)
            
            # Create a simplified project structure based on the plan
            directory_structure = file_structure.get("directory_structure", {})
            root_directory = directory_structure.get("root_directory", "project")
            temp_project_dir = os.path.join(temp_output_dir, root_directory)
            
            # Create the basic directory structure
            for directory in directory_structure.get("directories", []):
                dir_path = os.path.join(temp_project_dir, directory.get("path", ""))
                os.makedirs(dir_path, exist_ok=True)
            
            # Create empty files for essential files
            for file_mapping in file_structure.get("file_mappings", []):
                file_path = file_mapping.get("file_path", "")
                if file_path:
                    full_path = os.path.join(temp_project_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    open(full_path, 'w').close()  # Create empty file
            
            # Use StructureValidator to validate the structure
            validator = StructureValidator(temp_project_dir, project_type_enum)
            validation_messages = validator.validate()
            
            # Generate validation report
            validation_report = validator.generate_validation_report()
            
            # Store validation results in state
            state["validation_results"] = validation_report
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "validation_results": validation_report,
                    "validation_timestamp": datetime.now().isoformat()
                }
            )
            
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_output_dir, ignore_errors=True)
            
            # Update status - the next state will be determined by the condition functions
            state["status"] = "integrating_components" if not validation_report.get("has_errors", False) else "planning_structure"
            
            status_message = "passed" if not validation_report.get("has_errors", False) else "failed"
            self.logger.info(f"Structure validation {status_message} with {validation_report.get('error_count', 0)} errors")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in validate_structure: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="integrate_components",
                      metadata={"phase": "component_integration"})
    async def integrate_components(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Plan and perform component integration.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with integration plan
        """
        self.logger.info("Starting integrate_components phase")
        
        try:
            components = state["components"]
            file_structure = state["file_structure"]
            validation_results = state["validation_results"]
            
            # Use LLM to plan component integration
            integration_plan = await self.llm_service.plan_component_integration(
                file_structure=file_structure,
                validation_results=validation_results,
                components=components
            )
            
            # Store integration plan in state
            state["integration_plan"] = integration_plan
            
            # Resolve conflicts if any
            conflicts = integration_plan.get("conflict_resolutions", [])
            if conflicts:
                self.logger.info(f"Resolving {len(conflicts)} conflicts")
                
                for conflict in conflicts:
                    conflict_resolution = await self.llm_service.resolve_conflict(
                        conflict=conflict,
                        components=components,
                        project_type=state["input"].get("project_type", "generic")
                    )
                    
                    # Apply conflict resolution to components
                    self._apply_conflict_resolution(conflict_resolution, components)
            
            # Handle missing components
            missing_components = state["dependency_graph"].get("missing_components", [])
            if missing_components:
                self.logger.info(f"Generating {len(missing_components)} missing components")
                
                generated_components = await self.llm_service.generate_missing_components(
                    missing_components=missing_components,
                    existing_components=components,
                    project_type=state["input"].get("project_type", "generic")
                )
                
                # Add generated components to the components dictionary
                components.update(generated_components)
                state["components"] = components
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "integration_plan": integration_plan,
                    "integration_timestamp": datetime.now().isoformat()
                }
            )
            
            # Update status for next phase
            state["status"] = "generating_configs"
            
            self.logger.info(f"Component integration planning completed with {len(integration_plan.get('integration_strategies', []))} strategies")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in integrate_components: {str(e)}", exc_info=True)
            raise
    
    def _apply_conflict_resolution(
        self, 
        conflict_resolution: Dict[str, Any], 
        components: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Apply conflict resolution to components.
        
        Args:
            conflict_resolution: Conflict resolution from LLM
            components: Dictionary of components to update
        """
        implementation = conflict_resolution.get("implementation", {})
        
        # Apply modifications to existing components
        for modified in implementation.get("modified_components", []):
            component_id = modified.get("component_id")
            modified_content = modified.get("modified_content")
            
            if component_id in components and modified_content:
                original_content = components[component_id].get("content", "")
                original_excerpt = modified.get("original_content", "")
                
                if original_excerpt and original_excerpt in original_content:
                    # Replace just the specific part
                    new_content = original_content.replace(original_excerpt, modified_content)
                    components[component_id]["content"] = new_content
                    self.logger.debug(f"Applied targeted modification to component {component_id}")
                else:
                    # Replace entire content if specific part not found
                    components[component_id]["content"] = modified_content
                    self.logger.debug(f"Applied full content replacement to component {component_id}")
        
        # Add new components if any
        for new_comp in implementation.get("new_components", []):
            component_name = new_comp.get("name", f"new_component_{len(components)}")
            content = new_comp.get("content", "")
            purpose = new_comp.get("purpose", "")
            
            # Generate a unique ID for the new component
            component_id = f"{component_name}_{datetime.now().strftime('%H%M%S')}"
            
            # Add to components dictionary
            components[component_id] = {
                "name": component_name,
                "content": content,
                "purpose": purpose,
                "generated": True
            }
            
            self.logger.debug(f"Added new component {component_id} from conflict resolution")

    @monitor_operation(operation_type="generate_configs",
                      metadata={"phase": "config_generation"})
    async def generate_configs(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Generate configuration files for the project.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with configuration files
        """
        self.logger.info("Starting generate_configs phase")
        
        try:
            input_data = state["input"]
            components = state["components"]
            dependency_graph = state["dependency_graph"]
            file_structure = state["file_structure"]
            project_type = input_data.get("project_type", "generic")
            
            # Use ConfigGenerator to generate configuration files
            config_generator = ConfigGenerator(
                project_name=self.project_name,
                dependency_info=dependency_graph,
                project_structure=file_structure,
                output_dir=self.output_dir,
                llm_service=self.llm_service
            )
            
            # Generate configuration files
            generated_configs = await config_generator.generate_configs()
            
            # Store config files in state
            state["config_files"] = generated_configs
            
            # Write configuration files to disk
            written_files = await config_generator.write_configs(generated_configs)
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "config_files": generated_configs,
                    "written_config_files": written_files,
                    "config_timestamp": datetime.now().isoformat()
                }
            )
            
            # Update status for next phase
            state["status"] = "compiling_project"
            
            self.logger.info(f"Configuration generation completed with {len(written_files)} files written")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_configs: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="compile_project",
                      metadata={"phase": "project_compilation"})
    async def compile_project(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Compile the final project from all components and configurations.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with compiled project
        """
        self.logger.info("Starting compile_project phase")
        
        try:
            input_data = state["input"]
            components = state["components"]
            file_structure = state["file_structure"]
            integration_plan = state["integration_plan"]
            config_files = state["config_files"]
            validation_results = state["validation_results"]
            project_type = input_data.get("project_type", "generic")
            
            # Convert project_type string to ProjectType enum
            project_type_enum = ProjectType.UNKNOWN
            try:
                project_type_enum = ProjectType(project_type)
            except (ValueError, KeyError):
                self.logger.warning(f"Unknown project type: {project_type}, using UNKNOWN")
            
            # Get compilation plan from LLM
            compilation_plan = await self.llm_service.compile_project(
                file_structure=file_structure,
                integration_plan=integration_plan,
                config_files=config_files,
                validation_results=validation_results
            )
            
            # Use FileOrganizer to organize and write files
            file_organizer = FileOrganizer(
                project_type=project_type_enum,
                output_dir=self.output_dir
            )
            
            # Register components with the organizer
            for component_id, component_data in components.items():
                component_name = component_data.get("name", component_id)
                content = component_data.get("content", "")
                
                # Determine component type
                component_type = ComponentType.UNKNOWN
                if "type" in component_data:
                    try:
                        component_type = ComponentType(component_data["type"])
                    except (ValueError, KeyError):
                        # Guess component type based on name and content
                        if "component" in component_name.lower() or "jsx" in component_name.lower():
                            component_type = ComponentType.FRONTEND
                        elif "api" in component_name.lower() or "controller" in component_name.lower():
                            component_type = ComponentType.BACKEND
                        elif "model" in component_name.lower() or "schema" in component_name.lower():
                            component_type = ComponentType.DATABASE
                        elif "config" in component_name.lower():
                            component_type = ComponentType.CONFIG
                        elif "test" in component_name.lower():
                            component_type = ComponentType.TEST
                
                # Find file path from structure plan
                file_path = None
                for mapping in file_structure.get("file_mappings", []):
                    if mapping.get("component_id") == component_id:
                        file_path = mapping.get("file_path")
                        break
                
                # Create component
                component = Component(
                    name=component_name,
                    content=content,
                    component_type=component_type,
                    file_path=file_path,
                    metadata=component_data
                )
                
                # Add to organizer
                file_organizer.add_component(component)
            
            # Add config files 
            for config_type, configs in config_files.items():
                for file_name, content in configs.items():
                    file_organizer.add_component(
                        Component(
                            name=file_name,
                            content=content,
                            component_type=ComponentType.CONFIG,
                            file_path=file_name
                        )
                    )
            
            # Generate documentation if not already included
            documentation_exists = any(comp.component_type == ComponentType.DOCUMENTATION for comp in file_organizer._components)
            
            if not documentation_exists:
                self.logger.info("Generating project documentation")
                documentation = await self.llm_service.generate_documentation(
                    components=components,
                    project_type=project_type,
                    file_structure=file_structure,
                    project_description=input_data.get("project_description", "Software project")
                )
                
                # Add README.md
                if "readme" in documentation:
                    file_organizer.add_component(
                        Component(
                            name="README.md",
                            content=documentation["readme"],
                            component_type=ComponentType.DOCUMENTATION,
                            file_path="README.md"
                        )
                    )
                
                # Add setup guide
                if "setup_guide" in documentation:
                    file_organizer.add_component(
                        Component(
                            name="SETUP.md",
                            content=documentation["setup_guide"],
                            component_type=ComponentType.DOCUMENTATION,
                            file_path="docs/SETUP.md"
                        )
                    )
                
                # Add usage documentation
                if "usage_documentation" in documentation:
                    file_organizer.add_component(
                        Component(
                            name="USAGE.md",
                            content=documentation["usage_documentation"],
                            component_type=ComponentType.DOCUMENTATION,
                            file_path="docs/USAGE.md"
                        )
                    )
                
                # Add additional documentation
                for doc in documentation.get("additional_documentation", []):
                    file_name = doc.get("file_name", "")
                    content = doc.get("content", "")
                    if file_name and content:
                        file_organizer.add_component(
                            Component(
                                name=file_name,
                                content=content,
                                component_type=ComponentType.DOCUMENTATION,
                                file_path=f"docs/{file_name}"
                            )
                        )
            
            # Organize and write all files
            project_dir = file_organizer.organize_files()
            
            # Create compilation result
            compilation_result = {
                "project_dir": project_dir,
                "compilation_plan": compilation_plan,
                "file_count": len(file_organizer.file_paths),
                "component_count": len(components),
                "compilation_timestamp": datetime.now().isoformat()
            }
            
            # Store in state
            state["compiled_project"] = compilation_result
            state["output_location"] = project_dir
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "compiled_project": compilation_result,
                    "compilation_timestamp": datetime.now().isoformat()
                }
            )
            
            # Also store in long-term memory for future reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "project_name": self.project_name,
                    "output_location": project_dir,
                    "component_count": len(components),
                    "compilation_timestamp": datetime.now().isoformat()
                },
                metadata={"type": "compilation_result"}
            )
            
            # Update status for next phase
            state["status"] = "completed"
            
            self.logger.info(f"Project compilation completed. Output at: {project_dir}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in compile_project: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="complete_assembly",
                      metadata={"phase": "completion"})
    async def complete_assembly(self, state: CodeAssemblerGraphState) -> Dict[str, Any]:
        """
        Complete the assembly process and finalize outputs.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Final state with results
        """
        self.logger.info("Starting complete_assembly phase")
        
        try:
            # Get project information
            compilation_result = state["compiled_project"]
            output_location = state["output_location"]
            
            # Generate quality assessment
            quality_assessment = await self.llm_service.assess_project_quality(
                components=state["components"],
                file_structure=state["file_structure"],
                project_type=state["input"].get("project_type", "generic")
            )
            
            # Add quality assessment to compilation result
            compilation_result["quality_assessment"] = quality_assessment
            state["compiled_project"] = compilation_result
            
            # Generate final summary report
            summary_report = {
                "project_name": self.project_name,
                "output_location": output_location,
                "component_count": len(state["components"]),
                "file_count": compilation_result.get("file_count", 0),
                "quality_score": quality_assessment.get("overall_quality_score", 0),
                "completion_timestamp": datetime.now().isoformat(),
                "recommendations": quality_assessment.get("improvement_recommendations", []),
                "strengths": quality_assessment.get("strengths", []),
                "weaknesses": quality_assessment.get("weaknesses", [])
            }
            
            # Write summary report to output location
            summary_path = os.path.join(output_location, "assembly_summary.json")
            try:
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(summary_report, f, indent=2)
            except Exception as e:
                self.logger.error(f"Error writing summary report: {str(e)}")
            
            # Store in long-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=summary_report,
                metadata={"type": "final_summary"}
            )
            
            self.logger.info(f"Assembly completion finalized. Summary at: {summary_path}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in complete_assembly: {str(e)}", exc_info=True)
            # Even if there's an error, try to return a usable state
            if "compiled_project" in state:
                self.logger.info("Returning partial results despite error")
                return state
            raise
    
    @trace_method
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's work.
        
        Returns:
            Dict[str, Any]: Report data
        """
        self.logger.info("Generating CodeAssembler report")
        
        try:
            # Retrieve latest working state
            working_state = await self.memory_manager.get_working_state(self.agent_id)
            
            # Retrieve long-term memory entries for final summary
            long_term_entries = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "final_summary"}
            )
            
            final_summary = {}
            if long_term_entries:
                final_summary = long_term_entries[0].content
            
            # Compile report
            report = {
                "agent_id": self.agent_id,
                "agent_type": "code_assembler",
                "project_name": self.project_name,
                "output_location": working_state.get("output_location", ""),
                "components_processed": len(working_state.get("components", {})),
                "file_count": working_state.get("compiled_project", {}).get("file_count", 0),
                "quality_assessment": working_state.get("compiled_project", {}).get("quality_assessment", {}),
                "final_summary": final_summary,
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info("Report generation completed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return {
                "agent_id": self.agent_id,
                "agent_type": "code_assembler",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }