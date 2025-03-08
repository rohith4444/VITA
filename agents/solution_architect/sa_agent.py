from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation, monitor_llm
from agents.core.base_agent import BaseAgent
from agents.solution_architect.llm.sa_service import LLMService
from agents.core.graph.graph_builder import WorkflowGraphBuilder  
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from tools.team_lead.agent_communicator import (
    AgentCommunicator, MessageType, MessagePriority, DeliverableType
)
from .sa_state_graph import (
    SolutionArchitectGraphState, validate_state, get_next_stage, 
    update_coordination_metadata, create_initial_state
)
from tools.solution_architect.technology_selector import select_tech_stack
from tools.solution_architect.architecture_validator import validate_architecture
from tools.solution_architect.specification_generator import generate_specifications

class SolutionArchitectAgent(BaseAgent):
    """Solution Architect Agent responsible for system architecture design."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"solution_architect.{agent_id}")
        self.logger.info(f"Initializing SolutionArchitectAgent with ID: {agent_id}")
        
        try:
            self.llm_service = LLMService()
            
            # Initialize agent communicator for Team Lead coordination
            self.agent_communicator = AgentCommunicator()
            self.agent_communicator.register_agent(agent_id)
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("SolutionArchitectAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SolutionArchitectAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph-based execution flow with Team Lead coordination."""
        self.logger.info("Building SolutionArchitect processing graph")
        try:
            # Initialize graph builder
            builder = WorkflowGraphBuilder(SolutionArchitectGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes for original workflow
            self.logger.debug("Adding graph nodes for core functionality")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_requirements", self.analyze_requirements)
            builder.add_node("select_tech_stack", self.select_tech_stack)
            builder.add_node("design_architecture", self.design_architecture)
            builder.add_node("validate_architecture", self.validate_architecture)
            builder.add_node("generate_specifications", self.generate_specifications)
            
            # Add new nodes for Team Lead coordination
            self.logger.debug("Adding graph nodes for Team Lead coordination")
            builder.add_node("package_deliverables", self.package_deliverables)
            builder.add_node("awaiting_feedback", self.await_feedback)
            builder.add_node("apply_feedback", self.apply_feedback)
            
            # Add edges for original workflow
            self.logger.debug("Adding graph edges for core workflow")
            builder.add_edge("start", "analyze_requirements")
            builder.add_edge("analyze_requirements", "select_tech_stack")
            builder.add_edge("select_tech_stack", "design_architecture")
            builder.add_edge("design_architecture", "validate_architecture")
            builder.add_edge("validate_architecture", "generate_specifications")
            
            # Add new edges for Team Lead coordination
            self.logger.debug("Adding graph edges for Team Lead coordination")
            builder.add_edge("generate_specifications", "package_deliverables")
            builder.add_edge("package_deliverables", "awaiting_feedback")
            builder.add_edge("awaiting_feedback", "apply_feedback")
            
            # Add conditional edges for feedback loops
            builder.add_edge("apply_feedback", "select_tech_stack", 
                          condition=self._should_revise_tech_stack)
            builder.add_edge("apply_feedback", "design_architecture", 
                          condition=self._should_revise_architecture)
            builder.add_edge("apply_feedback", "generate_specifications", 
                          condition=self._should_revise_specifications)
            builder.add_edge("apply_feedback", "package_deliverables", 
                          condition=self._should_repackage_deliverables)
            
            # Set entry point
            builder.set_entry_point("start")
            
            # Compile graph
            compiled_graph = builder.compile()
            self.logger.info("Successfully built and compiled graph with Team Lead coordination")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise

    def _get_graph_builder(self) -> WorkflowGraphBuilder:
        """Return the graph builder for visualization."""
        if not hasattr(self, '_graph_builder'):
            self._build_graph()  # This will create and store the builder
        return self._graph_builder
    
    # Conditional methods for feedback-based transitions
    
    def _should_revise_tech_stack(self, state: SolutionArchitectGraphState) -> bool:
        """Determine if tech stack needs revision based on feedback."""
        feedback = state.get("feedback", {})
        revision_areas = feedback.get("revision_areas", [])
        
        for area in revision_areas:
            if "tech stack" in area.get("area", "").lower() or "technology" in area.get("area", "").lower():
                return True
                
        return False
    
    def _should_revise_architecture(self, state: SolutionArchitectGraphState) -> bool:
        """Determine if architecture design needs revision based on feedback."""
        feedback = state.get("feedback", {})
        revision_areas = feedback.get("revision_areas", [])
        
        for area in revision_areas:
            if "architecture" in area.get("area", "").lower() or "design" in area.get("area", "").lower():
                return True
                
        return False
    
    def _should_revise_specifications(self, state: SolutionArchitectGraphState) -> bool:
        """Determine if specifications need revision based on feedback."""
        feedback = state.get("feedback", {})
        revision_areas = feedback.get("revision_areas", [])
        
        for area in revision_areas:
            if "specification" in area.get("area", "").lower() or "detail" in area.get("area", "").lower():
                return True
                
        return False
    
    def _should_repackage_deliverables(self, state: SolutionArchitectGraphState) -> bool:
        """Determine if deliverables need repackaging based on feedback."""
        feedback = state.get("feedback", {})
        revision_areas = feedback.get("revision_areas", [])
        
        for area in revision_areas:
            if "format" in area.get("area", "").lower() or "package" in area.get("area", "").lower():
                return True
                
        # Default case - if no specific revision area matches, repackage the deliverables
        if revision_areas and not (self._should_revise_tech_stack(state) or 
                                  self._should_revise_architecture(state) or 
                                  self._should_revise_specifications(state)):
            return True
                
        return False

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's workflow with support for Team Lead coordination.
        
        Args:
            input_data: Dictionary containing input data which may include:
                - input: Project description
                - project_plan: Project plan details
                - task_info: Optional task information from Team Lead
                
        Returns:
            Dict[str, Any]: Final results of the workflow
        """
        self.logger.info("Starting SolutionArchitect workflow execution")
        try:
            # Extract core input fields
            if "input" not in input_data:
                raise ValueError("Input must contain 'input' field with project description")
                
            if "project_plan" not in input_data:
                raise ValueError("Input must contain 'project_plan' field with project plan")
            
            # Extract task information if provided by Team Lead
            task_info = input_data.get("task_info", {})
            
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            if task_info:
                self.logger.debug(f"Received task info from Team Lead: {task_info}")
            
            # Create initial state with task information
            initial_state = create_initial_state(
                project_description=input_data["input"],
                project_plan=input_data["project_plan"],
                task_info=task_info
            )
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke(initial_state)
            
            self.logger.info("Workflow completed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Handle initial input processing with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting receive_input phase")
        
        try:
            input_data = state["input"]
            project_plan = state["project_plan"]
            
            self.logger.debug(f"Extracted input data: {input_data[:200]}...")
            self.logger.debug(f"Project plan: {str(project_plan)[:200]}...")
            
            # Process task info if available
            task_id = state.get("task_id")
            task_context = {}
            
            if task_id:
                self.logger.info(f"Processing task {task_id} from Team Lead")
                
                # Build task context
                task_context = {
                    "task_id": task_id,
                    "priority": state.get("task_priority"),
                    "assigned_by": state.get("assigned_by"),
                    "due_time": state.get("due_time")
                }
                
                # Process task instruction for better understanding
                task_instruction = {
                    "task_id": task_id,
                    "description": input_data,
                    "priority": state.get("task_priority", "MEDIUM")
                }
                
                processed_instruction = await self.llm_service.process_task_instruction(task_instruction)
                
                # Store processed instruction in coordination metadata
                state = update_coordination_metadata(state, {
                    "processed_instruction": processed_instruction,
                    "instruction_processed_at": datetime.utcnow().isoformat()
                })
                
                # If task requires specific focus area, store it
                if "focus_areas" in processed_instruction:
                    task_context["focus_areas"] = processed_instruction["focus_areas"]
            
            # Store initial request in short-term memory
            memory_entry = {
                "initial_request": input_data,
                "project_plan": project_plan,
                "task_context": task_context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            # Initialize empty deliverables if not present
            if "deliverables" not in state:
                state["deliverables"] = {}
                
            # Initialize empty feedback if not present
            if "feedback" not in state:
                state["feedback"] = {}
                
            await self.update_status("analyzing_requirements")
            
            state["status"] = "analyzing_requirements"
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_requirements(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Analyze project requirements with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting analyze_requirements phase")
        
        try:
            project_description = state["input"]
            project_plan = state["project_plan"]
            
            # Extract key information from project plan
            milestones = project_plan.get("milestones", [])
            features = []
            
            # Extract features from milestones and tasks
            for milestone in milestones:
                milestone_name = milestone.get("name", "")
                features.append(milestone_name)
                for task in milestone.get("tasks", []):
                    features.append(task.get("name", ""))
            
            self.logger.debug(f"Extracted {len(features)} features")
            
            # Get task context for requirements analysis
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # Add any specific instructions from Team Lead
                coordination_metadata = state.get("coordination_metadata", {})
                processed_instruction = coordination_metadata.get("processed_instruction", {})
                
                if processed_instruction:
                    task_context["instructions"] = processed_instruction.get("interpretation")
            
            # Process requirements with LLM
            requirements_analysis = await self.llm_service.analyze_architecture_requirements(
                project_description=project_description,
                features=features,
                task_context=task_context
            )
            
            self.logger.debug(f"Requirements analysis: {str(requirements_analysis)[:200]}...")
            
            # Store in working memory
            working_memory_entry = {
                "project_description": project_description,
                "requirement_analysis": requirements_analysis,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store in long-term memory for later reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=working_memory_entry,
                metadata={
                    "type": "requirement_analysis",
                    "importance": 0.8
                }
            )
            
            # Update state with requirements analysis
            state["requirements_analysis"] = requirements_analysis
            state["status"] = "selecting_tech_stack"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_requirements: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="select_tech_stack",
                      metadata={"phase": "technology_selection"})
    async def select_tech_stack(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Select appropriate technology stack with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting select_tech_stack phase")
        
        try:
            project_description = state["input"]
            project_plan = state["project_plan"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Get task context for tech stack selection
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # If we're revising based on feedback, add that context
                if state.get("feedback"):
                    feedback = state.get("feedback", {})
                    tech_constraints = []
                    
                    # Extract tech-related feedback
                    for area in feedback.get("revision_areas", []):
                        if "tech" in area.get("area", "").lower() or "technology" in area.get("area", "").lower():
                            tech_constraints.append(area.get("requested_change", ""))
                    
                    if tech_constraints:
                        task_context["tech_constraints"] = "; ".join(tech_constraints)
            
            # Use technology selector tool with task context
            tech_stack = await select_tech_stack(
                project_description=project_description,
                requirements=requirements_analysis,
                llm_service=self.llm_service,
                task_context=task_context
            )
            
            self.logger.debug(f"Selected tech stack: {tech_stack}")
            
            # Store in working memory
            working_memory_entry = {
                "tech_stack": tech_stack,
                "selection_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Update state
            state["tech_stack"] = tech_stack
            state["status"] = "designing_architecture"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in select_tech_stack: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="design_architecture",
                      metadata={"phase": "architecture_design"})
    async def design_architecture(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Design system architecture with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting design_architecture phase")
        
        try:
            project_description = state["input"]
            tech_stack = state["tech_stack"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Get task context for architecture design
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # If we're revising based on feedback, add that context
                if state.get("feedback"):
                    feedback = state.get("feedback", {})
                    architecture_focus = []
                    
                    # Extract architecture-related feedback
                    for area in feedback.get("revision_areas", []):
                        if "architecture" in area.get("area", "").lower() or "design" in area.get("area", "").lower():
                            architecture_focus.append(area.get("requested_change", ""))
                    
                    if architecture_focus:
                        task_context["architecture_focus"] = "; ".join(architecture_focus)
            
            # Generate architecture design using LLM
            architecture_design = await self.llm_service.generate_architecture_design(
                project_description=project_description,
                tech_stack=tech_stack,
                requirements=requirements_analysis,
                task_context=task_context
            )
            
            self.logger.debug(f"Generated architecture design: {str(architecture_design)[:200]}...")
            
            # Store in working memory
            working_memory_entry = {
                "architecture_design": architecture_design,
                "design_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store in long-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=working_memory_entry,
                metadata={
                    "type": "architecture_design",
                    "importance": 0.9
                }
            )
            
            # Update state
            state["architecture_design"] = architecture_design
            state["status"] = "validating_architecture"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in design_architecture: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="validate_architecture",
                      metadata={"phase": "validation"})
    async def validate_architecture(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Validate the architecture with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting validate_architecture phase")
        
        try:
            architecture_design = state["architecture_design"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Get task context for architecture validation
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # If we're revising based on feedback, add validation focus
                if state.get("feedback"):
                    feedback = state.get("feedback", {})
                    validation_focus = []
                    
                    # Extract validation-related feedback
                    for area in feedback.get("revision_areas", []):
                        if "validation" in area.get("area", "").lower() or "quality" in area.get("area", "").lower():
                            validation_focus.append(area.get("requested_change", ""))
                    
                    if validation_focus:
                        task_context["validation_focus"] = "; ".join(validation_focus)
            
            # Use architecture validator tool
            validation_results = await validate_architecture(
                architecture_design=architecture_design,
                requirements=requirements_analysis,
                llm_service=self.llm_service,
                task_context=task_context
            )
            
            self.logger.debug(f"Validation results: {validation_results}")
            
            # Store in working memory
            working_memory_entry = {
                "validation_results": validation_results,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Update state
            state["validation_results"] = validation_results
            state["status"] = "generating_specifications"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in validate_architecture: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="generate_specifications",
                      metadata={"phase": "documentation"})
    async def generate_specifications(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Generate detailed technical specifications with task context awareness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state
        """
        self.logger.info("Starting generate_specifications phase")
        
        try:
            architecture_design = state["architecture_design"]
            tech_stack = state["tech_stack"]
            validation_results = state["validation_results"]
            
            # Get task context for specification generation
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # If we're revising based on feedback, add specification focus
                if state.get("feedback"):
                    feedback = state.get("feedback", {})
                    specification_focus = []
                    
                    # Extract specification-related feedback
                    for area in feedback.get("revision_areas", []):
                        if "specification" in area.get("area", "").lower() or "detail" in area.get("area", "").lower():
                            specification_focus.append(area.get("requested_change", ""))
                    
                    if specification_focus:
                        task_context["specification_focus"] = "; ".join(specification_focus)
            
            # Use specification generator tool
            specifications = await generate_specifications(
                architecture_design=architecture_design,
                tech_stack=tech_stack,
                validation_results=validation_results,
                llm_service=self.llm_service,
                task_context=task_context
            )
            
            self.logger.debug(f"Generated specifications: {str(specifications)[:200]}...")
            
            # Store in working memory
            working_memory_entry = {
                "specifications": specifications,
                "specification_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store in long-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=working_memory_entry,
                metadata={
                    "type": "technical_specifications",
                    "importance": 0.9
                }
            )
            
            # Update state
            state["specifications"] = specifications
            state["status"] = "packaging_deliverables"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_specifications: {str(e)}", exc_info=True)
            raise

    async def package_deliverables(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Package deliverables for Team Lead.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with packaged deliverables
        """
        self.logger.info("Starting package_deliverables phase")
        
        try:
            architecture_design = state["architecture_design"]
            tech_stack = state["tech_stack"]
            specifications = state["specifications"]
            
            # Get task context for deliverable packaging
            task_context = None
            if state.get("task_id"):
                task_context = {
                    "task_id": state.get("task_id"),
                    "priority": state.get("task_priority"),
                    "due_time": state.get("due_time")
                }
                
                # If we're repackaging based on feedback, add packaging focus
                if state.get("feedback") and self._should_repackage_deliverables(state):
                    feedback = state.get("feedback", {})
                    
                    expected_deliverables = []
                    for area in feedback.get("revision_areas", []):
                        if "format" in area.get("area", "").lower() or "package" in area.get("area", "").lower():
                            if area.get("requested_change"):
                                expected_deliverables.append(area.get("requested_change"))
                    
                    if expected_deliverables:
                        task_context["expected_deliverables"] = "; ".join(expected_deliverables)
            
            # Use LLM to package deliverables
            packaged_deliverables = await self.llm_service.package_deliverables(
                architecture_design=architecture_design,
                tech_stack=tech_stack,
                specifications=specifications,
                task_context=task_context
            )
            
            self.logger.debug(f"Packaged deliverables: {str(packaged_deliverables)[:200]}...")
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"packaged_deliverables": packaged_deliverables}
            )
            
            # Update state
            state["deliverables"] = packaged_deliverables
            
            # If we have a Team Lead task, send the deliverables
            if state.get("task_id") and state.get("assigned_by"):
                team_lead_id = state.get("assigned_by")
                
                for idx, deliverable in enumerate(packaged_deliverables.get("deliverables", [])):
                    deliverable_id = f"{self.agent_id}_deliverable_{idx}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    
                    # Determine deliverable type
                    deliverable_type = DeliverableType.DOCUMENTATION
                    if "architecture" in deliverable.get("type", "").lower():
                        deliverable_type = DeliverableType.DESIGN
                    
                    # Transfer deliverable to Team Lead
                    self.agent_communicator.transfer_deliverable(
                        source_agent_id=self.agent_id,
                        target_agent_id=team_lead_id,
                        content=deliverable.get("content", {}),
                        deliverable_type=deliverable_type,
                        task_id=state.get("task_id"),
                        message=f"Architecture deliverable: {deliverable.get('name', 'Unknown')}"
                    )
                    
                    self.logger.info(f"Sent deliverable to Team Lead: {deliverable_id}")
                
                # Send project structure recommendation separately
                if "project_structure_recommendation" in packaged_deliverables:
                    structure_id = f"{self.agent_id}_structure_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    
                    self.agent_communicator.transfer_deliverable(
                        source_agent_id=self.agent_id,
                        target_agent_id=team_lead_id,
                        content=packaged_deliverables["project_structure_recommendation"],
                        deliverable_type=DeliverableType.DESIGN,
                        task_id=state.get("task_id"),
                        message="Project structure recommendation for integration"
                    )
                
                # Send status report to Team Lead
                status_report = await self.llm_service.generate_status_report(
                    current_state=state,
                    progress={
                        "completion_percentage": 100,
                        "milestones_completed": ["Requirements Analysis", "Tech Stack Selection", 
                                            "Architecture Design", "Specifications"]
                    },
                    task_context=task_context
                )
                
                self.agent_communicator.send_message(
                    source_agent_id=self.agent_id,
                    target_agent_id=team_lead_id,
                    content=status_report,
                    message_type=MessageType.NOTIFICATION,
                    task_id=state.get("task_id"),
                    priority=MessagePriority.MEDIUM,
                    metadata={"report_type": "completion"}
                )
            
            # Set status to awaiting feedback
            state["status"] = "awaiting_feedback"
            state["awaiting_feedback"] = True
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in package_deliverables: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="await_feedback",
                      metadata={"phase": "feedback_awaiting"})
    async def await_feedback(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Wait for feedback from Team Lead.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with received feedback
        """
        self.logger.info("Starting await_feedback phase")
        
        try:
            # Check if we have a Team Lead task
            if not state.get("task_id") or not state.get("assigned_by"):
                # If not working with Team Lead, skip feedback phase
                self.logger.info("No Team Lead task, skipping feedback phase")
                state["status"] = "completed"
                return state
            
            team_lead_id = state.get("assigned_by")
            task_id = state.get("task_id")
            
            # Check for feedback messages
            feedback_messages = []
            all_messages = self.agent_communicator.get_messages(self.agent_id)
            
            for message in all_messages:
                # Check if message is feedback from Team Lead for this task
                if (message.get("source_agent_id") == team_lead_id and 
                    message.get("task_id") == task_id and
                    message.get("message_type") == MessageType.FEEDBACK.value):
                    feedback_messages.append(message)
                    
                    # Acknowledge message
                    self.agent_communicator.acknowledge_message(self.agent_id, message.get("id"))
            
            # Process feedback if available
            if feedback_messages:
                latest_feedback = max(feedback_messages, key=lambda m: m.get("timestamp", ""))
                
                # Get original deliverable that feedback is for
                deliverable_id = latest_feedback.get("metadata", {}).get("deliverable_id")
                original_deliverable = None
                
                if deliverable_id:
                    # Find the deliverable in our packaged deliverables
                    for deliverable in state.get("deliverables", {}).get("deliverables", []):
                        if str(deliverable.get("id", "")) == str(deliverable_id):
                            original_deliverable = deliverable
                            break
                
                # Default to all deliverables if specific one not found
                if not original_deliverable:
                    original_deliverable = state.get("deliverables", {})
                
                # Process feedback
                processed_feedback = await self.llm_service.process_feedback(
                    feedback={"message": latest_feedback.get("content"), "timestamp": latest_feedback.get("timestamp")},
                    original_deliverable=original_deliverable
                )
                
                # Store in working memory
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={"feedback": processed_feedback}
                )
                
                # Update state
                state["feedback"] = processed_feedback
                state["status"] = "applying_feedback"
                state["awaiting_feedback"] = False
                
                return state
            
            # If no feedback yet, remain in awaiting state
            self.logger.info("No feedback received yet, remaining in awaiting state")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in await_feedback: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="apply_feedback",
                      metadata={"phase": "feedback_application"})
    async def apply_feedback(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """
        Apply feedback from Team Lead.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state after applying feedback
        """
        self.logger.info("Starting apply_feedback phase")
        
        try:
            feedback = state.get("feedback", {})
            
            if not feedback:
                self.logger.warning("No feedback to apply, skipping to completion")
                state["status"] = "completed"
                return state
            
            # Log feedback areas
            revision_areas = feedback.get("revision_areas", [])
            self.logger.info(f"Applying feedback with {len(revision_areas)} revision areas")
            
            for area in revision_areas:
                self.logger.info(f"Revision area: {area.get('area')} - {area.get('priority', 'MEDIUM')}")
            
            # Determine which stage to return to based on feedback
            revision_plan = feedback.get("revision_plan", {})
            stage_to_revisit = revision_plan.get("stage_to_revisit", "")
            
            # Default next stage determination
            # The conditional state transitions are handled by the graph conditions
            # defined in _should_revise_* methods
            
            # Add acknowledgment of feedback to memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "feedback_applied": True,
                    "revision_areas": revision_areas,
                    "feedback_application_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Determine next status based on feedback logic
            # The actual transition will be determined by the condition methods
            # But we set a default next state in case none of the conditions match
            state["status"] = "packaging_deliverables"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in apply_feedback: {str(e)}", exc_info=True)
            raise

    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's activities and findings.
        
        Returns:
            Dict[str, Any]: Report containing architecture design and specifications
        """
        self.logger.info("Starting report generation")
        
        try:
            # Retrieve working memory for current state
            working_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING
            )
            
            # Retrieve long-term memory for architecture design
            architecture_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "architecture_design"},
                sort_by="timestamp",
                limit=1
            )
            
            # Retrieve long-term memory for specifications
            specs_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "technical_specifications"},
                sort_by="timestamp",
                limit=1
            )
            
            # Compile report
            current_state = working_memory[0].content if working_memory else {}
            architecture_design = architecture_memory[0].content if architecture_memory else {}
            specifications = specs_memory[0].content if specs_memory else {}
            
            # Add Team Lead coordination information
            coordination_info = {}
            if current_state.get("awaiting_feedback"):
                coordination_info["status"] = "awaiting_feedback"
            elif current_state.get("feedback"):
                coordination_info["feedback_received"] = True
                coordination_info["revision_areas"] = current_state.get("feedback", {}).get("revision_areas", [])
            
            if current_state.get("deliverables"):
                coordination_info["deliverables_prepared"] = len(current_state.get("deliverables", {}).get("deliverables", []))
            
            # Create full report
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "tech_stack": current_state.get("tech_stack", {}),
                "architecture_design": architecture_design.get("architecture_design", {}),
                "validation_results": current_state.get("validation_results", {}),
                "specifications": specifications.get("specifications", {}),
                "coordination": coordination_info,
                "task_id": current_state.get("task_id"),
                "awaiting_feedback": current_state.get("awaiting_feedback", False)
            }
            
            self.logger.info("Report generation completed successfully")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise
                