from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from agents.core.base_agent import BaseAgent
from agents.core.graph.graph_builder import WorkflowGraphBuilder
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from .fsd_state_graph import FullStackDeveloperGraphState, validate_state, get_next_stage, get_coordination_state, can_process_teamlead_message
from .llm.fsd_service import LLMService
from tools.full_stack_developer.requirement_analyzer import analyze_requirements
from tools.full_stack_developer.solution_designer import design_solution
from tools.full_stack_developer.code_generator import generate_code
from tools.full_stack_developer.documentation_generator import generate_documentation

class FullStackDeveloperAgent(BaseAgent):
    """Full Stack Developer Agent responsible for implementing features and components."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"full_stack_developer.{agent_id}")
        self.logger.info(f"Initializing FullStackDeveloperAgent with ID: {agent_id}")
        
        try:
            self.llm_service = LLMService()
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("FullStackDeveloperAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FullStackDeveloperAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph-based execution flow."""
        self.logger.info("Building FullStackDeveloper processing graph")
        try:
            # Initialize graph builder
            builder = WorkflowGraphBuilder(FullStackDeveloperGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes for original workflow
            self.logger.debug("Adding graph nodes for core workflow")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_requirements", self.analyze_requirements)
            builder.add_node("design_solution", self.design_solution)
            builder.add_node("generate_code", self.generate_code)
            builder.add_node("prepare_documentation", self.prepare_documentation)
            
            # Add nodes for Team Lead coordination
            self.logger.debug("Adding graph nodes for Team Lead coordination")
            builder.add_node("process_team_lead_instruction", self.process_team_lead_instruction)
            builder.add_node("package_deliverables", self.package_deliverables)
            builder.add_node("process_feedback", self.process_feedback)
            builder.add_node("implement_revisions", self.implement_revisions)
            builder.add_node("generate_status_report", self.generate_status_report)

            # Add edges for original workflow
            self.logger.debug("Adding graph edges for core workflow")
            builder.add_edge("start", "analyze_requirements")
            builder.add_edge("analyze_requirements", "design_solution")
            builder.add_edge("design_solution", "generate_code")
            builder.add_edge("generate_code", "prepare_documentation")
            builder.add_edge("prepare_documentation", "package_deliverables")
            
            # Add edges for Team Lead coordination
            self.logger.debug("Adding graph edges for Team Lead coordination")
            builder.add_edge("start", "process_team_lead_instruction", 
                          condition=lambda state: state.get("task_id") is not None)
            builder.add_edge("process_team_lead_instruction", "analyze_requirements")
            builder.add_edge("package_deliverables", "analyze_requirements", 
                          condition=lambda state: state.get("coordination_state") == "independent")
            builder.add_edge("package_deliverables", "process_feedback", 
                          condition=lambda state: state.get("feedback") and len(state.get("feedback", [])) > 0)
            builder.add_edge("process_feedback", "implement_revisions")
            builder.add_edge("implement_revisions", "analyze_requirements")
            
            # Status reporting can happen from any state
            for state_name in ["analyze_requirements", "design_solution", "generate_code", 
                              "prepare_documentation", "package_deliverables"]:
                builder.add_conditional_edge(state_name, "generate_status_report", "analyze_requirements", 
                                          condition=lambda state: state.get("team_lead_id") is not None)
            
            # Set entry point
            builder.set_entry_point("start")
            
            # Compile graph
            compiled_graph = builder.compile()
            self.logger.info("Successfully built and compiled graph")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="generate_status_report",
                     metadata={"phase": "coordination"})
    async def generate_status_report(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Generate and send a status report to the Team Lead."""
        self.logger.info("Generating status report")
        
        try:
            if not state.get("task_id") or not state.get("team_lead_id"):
                self.logger.warning("Missing task_id or team_lead_id, skipping status report")
                # Return to previous state
                return state
            
            task_id = state["task_id"]
            team_lead_id = state["team_lead_id"]
            current_stage = state["status"]
            
            # Determine progress percentage based on stage
            progress_percentage = 0
            if current_stage == "analyzing_requirements":
                progress_percentage = 25
            elif current_stage == "designing_solution":
                progress_percentage = 50
            elif current_stage == "generating_code":
                progress_percentage = 75
            elif current_stage == "preparing_documentation":
                progress_percentage = 90
            elif current_stage == "awaiting_feedback":
                progress_percentage = 100
            
            # Prepare progress details
            progress_details = {
                "completion_percentage": progress_percentage,
                "completed_steps": self._get_completed_steps(state),
                "current_activity": self._get_current_activity(state),
                "started_at": self._get_start_time(state),
                "estimated_completion": self._get_estimated_completion(state)
            }
            
            # Generate the status report
            status_report = await self.llm_service.generate_status_report(
                task_id=task_id,
                team_lead_id=team_lead_id,
                current_stage=current_stage,
                progress_details=progress_details
            )
            
            # Store the status report
            if "status_reports" not in state:
                state["status_reports"] = []
                
            state["status_reports"].append(status_report)
            
            # Send the status report to Team Lead
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "message_type": "status_report",
                    "from_agent": self.agent_id,
                    "to_agent": team_lead_id,
                    "task_id": task_id,
                    "status_report": status_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Return to the previous state
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {str(e)}", exc_info=True)
            # Return to previous state on error
            return state
    
    async def _send_progress_update(
        self, 
        state: Dict[str, Any], 
        phase: str, 
        completion_percentage: int, 
        message: str
    ) -> None:
        """Helper method to send progress updates to the Team Lead."""
        if not state.get("task_id") or not state.get("team_lead_id"):
            return
            
        task_id = state["task_id"]
        team_lead_id = state["team_lead_id"]
        
        progress_details = {
            "completion_percentage": completion_percentage,
            "completed_steps": self._get_completed_steps(state),
            "current_activity": message,
            "started_at": self._get_start_time(state),
            "estimated_completion": self._get_estimated_completion(state)
        }
        
        # Generate a status report
        status_report = await self.llm_service.generate_status_report(
            task_id=task_id,
            team_lead_id=team_lead_id,
            current_stage=phase,
            progress_details=progress_details
        )
        
        # Store and send the status report
        if "status_reports" not in state:
            state["status_reports"] = []
            
        state["status_reports"].append(status_report)
        
        await self.memory_manager.store(
            agent_id=self.agent_id,
            memory_type=MemoryType.WORKING,
            content={
                "message_type": "status_report",
                "from_agent": self.agent_id,
                "to_agent": team_lead_id,
                "task_id": task_id,
                "status_report": status_report,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _get_completed_steps(self, state: Dict[str, Any]) -> List[str]:
        """Get list of completed steps based on current state."""
        completed = []
        current_state = state["status"]
        
        # Add steps in order of completion
        if "requirements" in state and state["requirements"]:
            completed.append("Requirements analysis")
            
        if "solution_design" in state and state["solution_design"]:
            completed.append("Solution design")
            
        if "generated_code" in state and state["generated_code"]:
            completed.append("Code generation")
            
        if "documentation" in state and state["documentation"]:
            completed.append("Documentation")
            
        if "deliverables" in state and state["deliverables"]:
            completed.append("Deliverable packaging")
            
        return completed
    
    def _get_current_activity(self, state: Dict[str, Any]) -> str:
        """Get the current activity description based on state."""
        current_state = state["status"]
        
        activities = {
            "initialized": "Starting task",
            "analyzing_requirements": "Analyzing requirements",
            "designing_solution": "Designing solution architecture",
            "generating_code": "Generating code",
            "preparing_documentation": "Preparing documentation",
            "packaging_deliverables": "Packaging deliverables",
            "awaiting_feedback": "Awaiting feedback",
            "processing_feedback": "Processing feedback",
            "implementing_revisions": "Implementing revisions",
            "completed": "Task completed"
        }
        
        return activities.get(current_state, "Working on task")
    
    def _get_start_time(self, state: Dict[str, Any]) -> str:
        """Get the task start time."""
        # In a real implementation, this would retrieve the actual start time
        # For now, just return current time
        return datetime.utcnow().isoformat()
    
    def _get_estimated_completion(self, state: Dict[str, Any]) -> str:
        """Get estimated completion time."""
        # In a real implementation, this would calculate based on task complexity
        # For now, just return a placeholder
        return "Soon"
    
    async def receive_team_lead_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive and process a message from the Team Lead.
        
        Args:
            message: Message from Team Lead
            
        Returns:
            Dict[str, Any]: Response to Team Lead
        """
        self.logger.info(f"Received message from Team Lead: {message.get('type', 'unknown')}")
        
        try:
            message_type = message.get("type", "unknown")
            task_id = message.get("task_id")
            
            if message_type == "task_assignment":
                # Process task assignment
                return await self._process_task_assignment(message)
            elif message_type == "feedback":
                # Process feedback on deliverables
                return await self._process_feedback_message(message)
            elif message_type == "status_request":
                # Generate and send status report
                return await self._process_status_request(message)
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                return {
                    "success": False,
                    "error": f"Unknown message type: {message_type}",
                    "message_id": message.get("message_id")
                }
                
        except Exception as e:
            self.logger.error(f"Error processing Team Lead message: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message_id": message.get("message_id")
            }
    
    async def _process_task_assignment(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task assignment message from Team Lead."""
        task_id = message.get("task_id")
        task_specification = message.get("specification", "")
        team_lead_id = message.get("team_lead_id")
        
        # Create input data for the run method
        input_data = {
            "input": task_specification,
            "task_id": task_id,
            "team_lead_id": team_lead_id,
            "instructions": message.get("instructions", {})
        }
        
        # Store the assignment in memory
        await self.memory_manager.store(
            agent_id=self.agent_id,
            memory_type=MemoryType.SHORT_TERM,
            content={
                "type": "task_assignment",
                "task_id": task_id,
                "team_lead_id": team_lead_id,
                "specification": task_specification,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Run the agent workflow asynchronously
        # In a real implementation, this would be handled by a task queue
        # For now, just acknowledge receipt
        
        return {
            "success": True,
            "message": f"Task {task_id} received and processing started",
            "message_id": message.get("message_id"),
            "task_id": task_id
        }
    
    async def _process_feedback_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a feedback message from Team Lead."""
        task_id = message.get("task_id")
        feedback = message.get("feedback", {})
        team_lead_id = message.get("team_lead_id")
        
        # Store the feedback in memory
        await self.memory_manager.store(
            agent_id=self.agent_id,
            memory_type=MemoryType.WORKING,
            content={
                "type": "feedback",
                "task_id": task_id,
                "team_lead_id": team_lead_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Acknowledge receipt
        return {
            "success": True,
            "message": f"Feedback for task {task_id} received and processing started",
            "message_id": message.get("message_id"),
            "task_id": task_id
        }
    
    async def _process_status_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a status request from Team Lead."""
        task_id = message.get("task_id")
        team_lead_id = message.get("team_lead_id")
        
        # Retrieve current task state
        task_state = await self._get_task_state(task_id)
        
        if not task_state:
            return {
                "success": False,
                "error": f"No active task found with ID {task_id}",
                "message_id": message.get("message_id")
            }
        
        # Generate a status report
        progress_details = {
            "completion_percentage": task_state.get("completion_percentage", 0),
            "completed_steps": task_state.get("completed_steps", []),
            "current_activity": task_state.get("current_activity", "Working on task"),
            "started_at": task_state.get("started_at", datetime.utcnow().isoformat()),
            "estimated_completion": task_state.get("estimated_completion", "Soon")
        }
        
        status_report = await self.llm_service.generate_status_report(
            task_id=task_id,
            team_lead_id=team_lead_id,
            current_stage=task_state.get("status", "unknown"),
            progress_details=progress_details
        )
        
        # Send the status report via memory
        await self.memory_manager.store(
            agent_id=self.agent_id,
            memory_type=MemoryType.WORKING,
            content={
                "message_type": "status_report",
                "from_agent": self.agent_id,
                "to_agent": team_lead_id,
                "task_id": task_id,
                "status_report": status_report,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": f"Status report for task {task_id} generated and sent",
            "message_id": message.get("message_id"),
            "task_id": task_id,
            "status_report": status_report
        }
    
    async def _get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the current state of a task from memory."""
        # In a real implementation, this would query the workflow state database
        # For now, just return a placeholder
        task_entries = await self.memory_manager.retrieve(
            agent_id=self.agent_id,
            memory_type=MemoryType.WORKING,
            filter_criteria={"task_id": task_id}
        )
        
        if not task_entries:
            return None
            
        # Construct state from memory entries
        task_state = {
            "task_id": task_id,
            "status": "unknown",
            "completion_percentage": 0,
            "completed_steps": [],
            "current_activity": "Unknown",
            "started_at": datetime.utcnow().isoformat(),
            "estimated_completion": "Unknown"
        }
        
        # Find the most recent status update
        for entry in sorted(task_entries, key=lambda e: e.timestamp, reverse=True):
            content = entry.content
            if "phase" in content:
                if content["phase"] == "requirements":
                    task_state["status"] = "analyzing_requirements"
                    task_state["completion_percentage"] = 25
                elif content["phase"] == "solution_design":
                    task_state["status"] = "designing_solution"
                    task_state["completion_percentage"] = 50
                elif content["phase"] == "code_generation":
                    task_state["status"] = "generating_code"
                    task_state["completion_percentage"] = 75
                elif content["phase"] == "documentation":
                    task_state["status"] = "preparing_documentation"
                    task_state["completion_percentage"] = 90
                elif content["phase"] == "deliverables_packaging":
                    task_state["status"] = "awaiting_feedback"
                    task_state["completion_percentage"] = 100
                    
                # Only need the most recent status
                break
        
        return task_state
    
    def _get_graph_builder(self) -> WorkflowGraphBuilder:
        """Return the graph builder for visualization."""
        if not hasattr(self, '_graph_builder'):
            self._build_graph()  # This will create and store the builder
        return self._graph_builder

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's workflow."""
        self.logger.info("Starting FullStackDeveloper workflow execution")
        try:
            # Ensure input contains required fields
            if not isinstance(input_data, dict):
                raise ValueError("Input must be a dictionary")
                
            if "input" not in input_data:
                raise ValueError("Input must contain 'input' field with task specification")
            
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            
            # Check if this is a Team Lead instruction
            is_team_lead_instruction = "task_id" in input_data and "team_lead_id" in input_data
            
            # Create initial state based on input type
            initial_state = {
                "input": input_data["input"],
                "requirements": {},
                "solution_design": {},
                "generated_code": {},
                "documentation": {},
                "status": "initialized",
                "deliverables": {},
                "feedback": [],
                "revision_requests": [],
                "status_reports": []
            }
            
            # Add Team Lead coordination fields if present
            if is_team_lead_instruction:
                initial_state["task_id"] = input_data["task_id"]
                initial_state["team_lead_id"] = input_data["team_lead_id"]
                initial_state["instructions"] = input_data.get("instructions", {})
                initial_state["coordination_state"] = "awaiting_instructions"
                
                self.logger.info(f"Received Team Lead instruction for task {input_data['task_id']}")
            else:
                initial_state["task_id"] = None
                initial_state["team_lead_id"] = None
                initial_state["instructions"] = None
                initial_state["coordination_state"] = "independent"
            
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
    async def receive_input(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Process initial input and prepare for analysis."""
        self.logger.info("Starting receive_input phase")
        
        try:
            task_specification = state["input"]
            self.logger.debug(f"Task specification: {task_specification[:200]}...")
            
            # Store initial request in short-term memory
            memory_entry = {
                "task_specification": task_specification,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add Team Lead info if present
            if state.get("task_id"):
                memory_entry["task_id"] = state["task_id"]
                memory_entry["team_lead_id"] = state["team_lead_id"]
                memory_entry["coordination_mode"] = "team_lead_directed"
            else:
                memory_entry["coordination_mode"] = "independent"
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            # Update agent status
            await self.update_status("analyzing_requirements")
            
            # Update state status
            state["status"] = "analyzing_requirements"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="process_team_lead_instruction",
                     metadata={"phase": "coordination"})
    async def process_team_lead_instruction(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Process instructions received from the Team Lead."""
        self.logger.info(f"Processing Team Lead instruction for task {state.get('task_id')}")
        
        try:
            if not state.get("task_id") or not state.get("team_lead_id"):
                self.logger.warning("Missing task_id or team_lead_id, skipping instruction processing")
                state["status"] = "analyzing_requirements"
                return state
            
            task_id = state["task_id"]
            team_lead_id = state["team_lead_id"]
            instructions = state.get("instructions", {})
            
            # Process the instruction using LLM service
            instruction_analysis = await self.llm_service.process_teamlead_instructions(
                instruction=instructions,
                task_id=task_id,
                team_lead_id=team_lead_id
            )
            
            # Store the analysis result in state
            state["instructions"] = {
                **instructions,
                "analysis": instruction_analysis
            }
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "phase": "instruction_processing",
                    "task_id": task_id,
                    "team_lead_id": team_lead_id,
                    "instruction_analysis": instruction_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Generate a status report to acknowledge receipt
            status_report = await self.llm_service.generate_status_report(
                task_id=task_id,
                team_lead_id=team_lead_id,
                current_stage="processing_instructions",
                progress_details={
                    "completion_percentage": 10,
                    "completed_steps": ["Received task", "Analyzed instructions"],
                    "current_activity": "Beginning requirements analysis",
                    "started_at": datetime.utcnow().isoformat(),
                    "estimated_completion": "Estimating based on task complexity..."
                }
            )
            
            # Store the status report
            if "status_reports" not in state:
                state["status_reports"] = []
                
            state["status_reports"].append(status_report)
            
            # Send the status report to Team Lead (via memory for now)
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "message_type": "status_report",
                    "from_agent": self.agent_id,
                    "to_agent": team_lead_id,
                    "task_id": task_id,
                    "status_report": status_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Update coordination state
            state["coordination_state"] = "working"
            
            # Move to requirements analysis
            state["status"] = "analyzing_requirements"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing Team Lead instruction: {str(e)}", exc_info=True)
            # Fall back to requirements analysis on error
            state["status"] = "analyzing_requirements"
            return state

    @monitor_operation(operation_type="analyze_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_requirements(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Analyze the task specification to extract requirements."""
        self.logger.info("Starting analyze_requirements phase")
        
        try:
            task_specification = state["input"]
            
            # If we have Team Lead instructions, add them to the specification
            if state.get("instructions") and state.get("instructions").get("analysis"):
                instruction_analysis = state["instructions"]["analysis"]
                core_objectives = instruction_analysis.get("core_objectives", [])
                deliverables = instruction_analysis.get("deliverables", [])
                
                # Enhance the task specification with instruction insights
                enhanced_spec = f"{task_specification}\n\nCORE OBJECTIVES:\n"
                for obj in core_objectives:
                    enhanced_spec += f"- {obj}\n"
                
                enhanced_spec += "\nDELIVERABLES:\n"
                for deliv in deliverables:
                    enhanced_spec += f"- {deliv}\n"
                
                task_specification = enhanced_spec
            
            # Analyze requirements using the tool
            requirements = await analyze_requirements(
                task_specification=task_specification,
                llm_service=self.llm_service
            )
            
            self.logger.debug(f"Requirements analysis result with {len(requirements.get('features', []))} features")
            
            # Store in working memory
            working_memory_entry = {
                "phase": "requirements",
                "requirements": requirements,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add task info if this is a Team Lead directed task
            if state.get("task_id"):
                working_memory_entry["task_id"] = state["task_id"]
                working_memory_entry["team_lead_id"] = state["team_lead_id"]
            
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
                    "type": "requirements_analysis",
                    "importance": 0.8
                }
            )
            
            # Update state with requirements and status
            state["requirements"] = requirements
            state["status"] = "designing_solution"
            
            # Update progress and send status report if Team Lead directed
            if state.get("team_lead_id") and state.get("task_id"):
                await self._send_progress_update(
                    state=state,
                    phase="requirements_analysis",
                    completion_percentage=25,
                    message="Requirements analysis completed"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_requirements: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="design_solution",
                      metadata={"phase": "design"})
    async def design_solution(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Design technical solution based on requirements."""
        self.logger.info("Starting design_solution phase")
        
        try:
            task_specification = state["input"]
            requirements = state["requirements"]
            
            # Design solution using the tool
            solution_design = await design_solution(
                task_specification=task_specification,
                requirements=requirements,
                llm_service=self.llm_service
            )
            
            self.logger.debug(f"Solution design complete with components: {list(solution_design.keys())}")
            
            # Store in working memory
            working_memory_entry = {
                "phase": "solution_design",
                "solution_design": solution_design,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add task info if this is a Team Lead directed task
            if state.get("task_id"):
                working_memory_entry["task_id"] = state["task_id"]
                working_memory_entry["team_lead_id"] = state["team_lead_id"]
            
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
                    "type": "solution_design",
                    "importance": 0.9
                }
            )
            
            # Update state with solution design and status
            state["solution_design"] = solution_design
            state["status"] = "generating_code"
            
            # Update progress and send status report if Team Lead directed
            if state.get("team_lead_id") and state.get("task_id"):
                await self._send_progress_update(
                    state=state,
                    phase="solution_design",
                    completion_percentage=45,
                    message="Solution design completed"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in design_solution: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="generate_code",
                      metadata={"phase": "implementation"})
    async def generate_code(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Generate code based on solution design."""
        self.logger.info("Starting generate_code phase")
        
        try:
            task_specification = state["input"]
            requirements = state["requirements"]
            solution_design = state["solution_design"]
            
            # Generate code using the tool
            generated_code = await generate_code(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                llm_service=self.llm_service
            )
            
            file_count = sum(len(files) for files in generated_code.values())
            self.logger.debug(f"Code generation complete with {file_count} files")
            
            # Store in working memory
            working_memory_entry = {
                "phase": "code_generation",
                "generated_code": generated_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add task info if this is a Team Lead directed task
            if state.get("task_id"):
                working_memory_entry["task_id"] = state["task_id"]
                working_memory_entry["team_lead_id"] = state["team_lead_id"]
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store in long-term memory (just metadata to avoid storing large code)
            code_summary = {component: list(files.keys()) for component, files in generated_code.items()}
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "phase": "code_generation",
                    "code_summary": code_summary,
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "type": "code_generation",
                    "importance": 0.9
                }
            )
            
            # Update state with generated code and status
            state["generated_code"] = generated_code
            state["status"] = "preparing_documentation"
            
            # Update progress and send status report if Team Lead directed
            if state.get("team_lead_id") and state.get("task_id"):
                await self._send_progress_update(
                    state=state,
                    phase="code_generation",
                    completion_percentage=75,
                    message="Code generation completed"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_code: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="prepare_documentation",
                      metadata={"phase": "documentation"})
    async def prepare_documentation(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Generate documentation for the implemented solution."""
        self.logger.info("Starting prepare_documentation phase")
        
        try:
            task_specification = state["input"]
            requirements = state["requirements"]
            solution_design = state["solution_design"]
            generated_code = state["generated_code"]
            
            # Generate documentation using the tool
            documentation = await generate_documentation(
                task_specification=task_specification,
                requirements=requirements,
                solution_design=solution_design,
                generated_code=generated_code,
                llm_service=self.llm_service
            )
            
            self.logger.debug(f"Documentation generation complete with {len(documentation)} files")
            
            # Store in working memory
            working_memory_entry = {
                "phase": "documentation",
                "documentation": documentation,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add task info if this is a Team Lead directed task
            if state.get("task_id"):
                working_memory_entry["task_id"] = state["task_id"]
                working_memory_entry["team_lead_id"] = state["team_lead_id"]
            
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
                    "type": "documentation",
                    "importance": 0.8
                }
            )
            
            # Update state with documentation and status
            state["documentation"] = documentation
            
            # Move to packaging deliverables
            state["status"] = "packaging_deliverables"
            
            # Update progress and send status report if Team Lead directed
            if state.get("team_lead_id") and state.get("task_id"):
                await self._send_progress_update(
                    state=state,
                    phase="documentation",
                    completion_percentage=90,
                    message="Documentation completed"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in prepare_documentation: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="package_deliverables",
                     metadata={"phase": "delivery"})
    async def package_deliverables(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Package deliverables for submission to Team Lead or completion."""
        self.logger.info("Starting package_deliverables phase")
        
        try:
            # Check if we need to package for Team Lead or just complete
            if state.get("task_id") and state.get("team_lead_id"):
                # Package deliverables for Team Lead
                task_id = state["task_id"]
                requirements = state["requirements"]
                solution_design = state["solution_design"]
                generated_code = state["generated_code"]
                documentation = state["documentation"]
                
                # Use LLM to package deliverables with metadata
                deliverables_package = await self.llm_service.package_deliverables(
                    task_id=task_id,
                    requirements=requirements,
                    solution_design=solution_design,
                    generated_code=generated_code,
                    documentation=documentation
                )
                
                # Store the packaged deliverables
                state["deliverables"] = deliverables_package
                
                # Store in working memory
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "phase": "deliverables_packaging",
                        "task_id": task_id,
                        "team_lead_id": state["team_lead_id"],
                        "deliverables": deliverables_package,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Send the deliverables to Team Lead (via memory for now)
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "message_type": "deliverable",
                        "from_agent": self.agent_id,
                        "to_agent": state["team_lead_id"],
                        "task_id": task_id,
                        "deliverable": deliverables_package,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Update progress to 100%
                await self._send_progress_update(
                    state=state,
                    phase="deliverable_submission",
                    completion_percentage=100,
                    message="Task completed, deliverables submitted"
                )
                
                # Move to awaiting feedback
                state["coordination_state"] = "awaiting_feedback"
                state["status"] = "awaiting_feedback"
                
                # Record completion time for reference
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "phase": "task_completion",
                        "task_id": task_id,
                        "completion_time": datetime.utcnow().isoformat(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
            else:
                # Just mark as completed for independent mode
                state["status"] = "completed"
                state["coordination_state"] = "completed"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in package_deliverables: {str(e)}", exc_info=True)
            # Fall back to completed state on error
            state["status"] = "completed"
            return state

    @monitor_operation(operation_type="process_feedback",
                     metadata={"phase": "revision"})
    async def process_feedback(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Process feedback from Team Lead on submitted deliverables."""
        self.logger.info("Starting process_feedback phase")
        
        try:
            if not state.get("feedback") or len(state.get("feedback", [])) == 0:
                self.logger.warning("No feedback to process, skipping feedback processing")
                state["status"] = "completed"
                return state
            
            task_id = state["task_id"]
            team_lead_id = state["team_lead_id"]
            feedback = state["feedback"][-1]  # Get most recent feedback
            deliverables = state["deliverables"]
            
            # Process the feedback using LLM service
            feedback_analysis = await self.llm_service.process_feedback(
                task_id=task_id,
                feedback=feedback,
                deliverables=deliverables,
                team_lead_id=team_lead_id
            )
            
            # Store the revision plan
            revision_plan = feedback_analysis.get("revision_plan", [])
            state["revision_requests"] = revision_plan
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "phase": "feedback_processing",
                    "task_id": task_id,
                    "team_lead_id": team_lead_id,
                    "feedback": feedback,
                    "feedback_analysis": feedback_analysis,
                    "revision_plan": revision_plan,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Generate a status report to acknowledge feedback
            status_report = await self.llm_service.generate_status_report(
                task_id=task_id,
                team_lead_id=team_lead_id,
                current_stage="processing_feedback",
                progress_details={
                    "completion_percentage": 90,
                    "completed_steps": ["Delivered work", "Received feedback", "Analyzed feedback"],
                    "current_activity": "Planning revisions based on feedback",
                    "started_at": datetime.utcnow().isoformat(),
                    "estimated_completion": "Estimating based on revision scope..."
                }
            )
            
            # Store and send the status report
            state["status_reports"].append(status_report)
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "message_type": "status_report",
                    "from_agent": self.agent_id,
                    "to_agent": team_lead_id,
                    "task_id": task_id,
                    "status_report": status_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Move to implementing revisions
            state["coordination_state"] = "revising"
            state["status"] = "implementing_revisions"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            # Fall back to completed state on error
            state["status"] = "completed"
            return state

    @monitor_operation(operation_type="implement_revisions",
                     metadata={"phase": "revision"})
    async def implement_revisions(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Implement revisions based on Team Lead feedback."""
        self.logger.info("Starting implement_revisions phase")
        
        try:
            if not state.get("revision_requests") or len(state.get("revision_requests", [])) == 0:
                self.logger.warning("No revision requests to implement, skipping revision implementation")
                state["status"] = "completed"
                return state
            
            task_id = state["task_id"]
            team_lead_id = state["team_lead_id"]
            revision_requests = state["revision_requests"]
            
            # Apply the revisions to the appropriate components
            for revision in revision_requests:
                area = revision.get("area", "")
                changes_needed = revision.get("changes_needed", "")
                affected_files = revision.get("affected_files", [])
                
                self.logger.info(f"Implementing revision for area: {area}")
                
                # Apply changes based on the area
                if "frontend" in area.lower():
                    if "frontend" in state["generated_code"]:
                        # For each affected file, make the necessary changes
                        for file_path in affected_files:
                            if file_path in state["generated_code"]["frontend"]:
                                # In a real implementation, this would use more sophisticated 
                                # code modification techniques based on the changes_needed
                                self.logger.info(f"Modifying frontend file: {file_path}")
                                # For now, just append a revision comment
                                state["generated_code"]["frontend"][file_path] += f"\n\n// Revision: {changes_needed}\n"
                
                elif "backend" in area.lower():
                    if "backend" in state["generated_code"]:
                        # Similar approach for backend files
                        for file_path in affected_files:
                            if file_path in state["generated_code"]["backend"]:
                                self.logger.info(f"Modifying backend file: {file_path}")
                                state["generated_code"]["backend"][file_path] += f"\n\n// Revision: {changes_needed}\n"
                
                elif "database" in area.lower():
                    if "database" in state["generated_code"]:
                        # Similar approach for database files
                        for file_path in affected_files:
                            if file_path in state["generated_code"]["database"]:
                                self.logger.info(f"Modifying database file: {file_path}")
                                state["generated_code"]["database"][file_path] += f"\n\n-- Revision: {changes_needed}\n"
                
                elif "documentation" in area.lower():
                    # Handle documentation revisions
                    for file_path in affected_files:
                        if file_path in state["documentation"]:
                            self.logger.info(f"Modifying documentation: {file_path}")
                            state["documentation"][file_path] += f"\n\n<!-- Revision: {changes_needed} -->\n"
            
            # Store the revised deliverables
            revised_deliverables = await self.llm_service.package_deliverables(
                task_id=task_id,
                requirements=state["requirements"],
                solution_design=state["solution_design"],
                generated_code=state["generated_code"],
                documentation=state["documentation"]
            )
            
            # Update the deliverables in state
            state["deliverables"] = revised_deliverables
            revised_deliverables["revision_number"] = len(state.get("feedback", []))
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "phase": "revision_implementation",
                    "task_id": task_id,
                    "team_lead_id": team_lead_id,
                    "revised_deliverables": revised_deliverables,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Send the revised deliverables to Team Lead
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "message_type": "revised_deliverable",
                    "from_agent": self.agent_id,
                    "to_agent": team_lead_id,
                    "task_id": task_id,
                    "deliverable": revised_deliverables,
                    "revision_number": len(state.get("feedback", [])),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Update progress to 100%
            await self._send_progress_update(
                state=state,
                phase="revision_submission",
                completion_percentage=100,
                message="Revisions completed and submitted"
            )
            
            # Clear revision requests and move back to requirements analysis 
            # for potential further revisions or completion
            state["revision_requests"] = []
            state["coordination_state"] = "awaiting_feedback"
            state["status"] = "analyzing_requirements"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error implementing revisions: {str(e)}", exc_info=True)
            # Fall back to completed state on error
            state["status"] = "completed"
            return state