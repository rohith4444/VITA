from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime
import json
from core.logging.logger import setup_logger
from core.tracing.service import trace_method, trace_class
from agents.core.base_agent import BaseAgent
from agents.team_lead.llm.tl_service import TeamLeadLLMService
from agents.team_lead.tl_state_graph import TeamLeadGraphState, validate_state, get_next_stage
from tools.team_lead.task_cordinator import coordinate_project_execution
from tools.team_lead.progress_tracker import (
    update_task_status, calculate_project_progress, identify_bottlenecks,
    analyze_timeline_adherence, detect_at_risk_tasks, generate_progress_report,
    handle_task_completion_events, manage_checkpoints
)
from tools.team_lead.agent_communicator import (
    AgentCommunicator, MessageType, MessagePriority, DeliverableType
)
from tools.team_lead.result_compiler import (
    ResultCompiler, ProjectType, ComponentType
)
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from agents.core.monitoring.decorators import monitor_operation

# Initialize logger
logger = setup_logger("team_lead.agent")

@trace_class
class TeamLeadAgent(BaseAgent):
    """
    Team Lead Agent responsible for coordinating other agents, monitoring progress, and 
    compiling results into a cohesive project.
    
    Attributes:
        agent_id (str): Unique identifier for this agent instance
        name (str): Display name for the agent
        memory_manager (MemoryManager): Memory management system
        llm_service (TeamLeadLLMService): LLM service for decision-making
        agent_communicator (AgentCommunicator): Tool for agent communication
        result_compiler (ResultCompiler): Tool for compiling project results
        registered_agents (Dict[str, Dict[str, Any]]): Information about available agents
        active_tasks (Dict[str, Dict[str, Any]]): Currently active tasks
        project_name (str): Name of the current project
    """
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        """
        Initialize the Team Lead Agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            name: Display name for the agent
            memory_manager: Memory management system
        """
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"team_lead.{agent_id}")
        self.logger.info(f"Initializing TeamLeadAgent with ID: {agent_id}")
        
        try:
            # Initialize LLM service
            self.llm_service = TeamLeadLLMService()
            
            # Initialize communication and compilation tools
            self.agent_communicator = AgentCommunicator()
            self.result_compiler = ResultCompiler()
            
            # Register self with agent communicator
            self.agent_communicator.register_agent(agent_id)
            
            # Initialize agent registry and active tasks
            self.registered_agents = {}
            self.active_tasks = {}
            self.project_name = f"project_{agent_id}"
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("TeamLeadAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TeamLeadAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self):
        """Build the LangGraph-based execution flow for Team Lead Agent."""
        self.logger.info("Building TeamLead processing graph")
        try:
            # Initialize graph builder
            from agents.core.graph.graph_builder import WorkflowGraphBuilder
            builder = WorkflowGraphBuilder(TeamLeadGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes (primary state handlers)
            self.logger.debug("Adding graph nodes")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_tasks", self.analyze_tasks)
            builder.add_node("plan_execution", self.plan_execution)
            builder.add_node("assign_agents", self.assign_agents)
            builder.add_node("monitor_progress", self.monitor_progress)
            builder.add_node("collect_deliverables", self.collect_deliverables)
            builder.add_node("compile_results", self.compile_results)
            builder.add_node("complete", self.complete_project)
            
            # Add edges (state transitions)
            self.logger.debug("Adding graph edges")
            builder.add_edge("start", "analyze_tasks")
            builder.add_edge("analyze_tasks", "plan_execution")
            builder.add_edge("plan_execution", "assign_agents")
            builder.add_edge("assign_agents", "monitor_progress")
            
            # Add cyclic monitoring edges
            builder.add_edge("monitor_progress", "monitor_progress", 
                          condition=self._should_continue_monitoring)
            builder.add_edge("monitor_progress", "collect_deliverables", 
                          condition=self._should_collect_deliverables)
            
            # Add ability to return to monitoring from deliverable collection
            builder.add_edge("collect_deliverables", "monitor_progress", 
                          condition=self._should_return_to_monitoring)
            builder.add_edge("collect_deliverables", "compile_results", 
                          condition=self._should_compile_results)
            
            builder.add_edge("compile_results", "complete")
            
            # Set entry point
            builder.set_entry_point("start")
            
            # Add conditional transitions for exception handling
            # (For simplicity, not fully implemented in this version)
            
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
    
    @trace_method
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Team Lead Agent's workflow.
        
        Args:
            input_data: Input containing project description and plan
            
        Returns:
            Dict[str, Any]: Final results of the team lead process
        """
        self.logger.info("Starting TeamLead workflow execution")
        try:
            # Ensure input contains required fields
            if "input" not in input_data:
                raise ValueError("Input must contain 'input' field with project description")
                
            if "project_plan" not in input_data:
                raise ValueError("Input must contain 'project_plan' field with project plan")
            
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            
            # Create initial state
            initial_state = {
                "input": input_data["input"],
                "project_plan": input_data["project_plan"],
                "tasks": [],
                "execution_plan": {},
                "agent_assignments": {},
                "progress": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "completion_percentage": 0,
                    "milestone_progress": [],
                    "task_summary": {
                        "total": 0,
                        "completed": 0,
                        "in_progress": 0,
                        "blocked": 0,
                        "pending": 0
                    }
                },
                "deliverables": {},
                "compilation_result": {},
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
    
    # State transition condition methods
    
    def _should_continue_monitoring(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent should continue in the monitoring state.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if the agent should continue monitoring
        """
        # Get current progress
        progress = state.get("progress", {})
        completion_percentage = progress.get("completion_percentage", 0)
        
        # Check if we've reached a checkpoint or milestone
        if completion_percentage < 50:
            # Continue monitoring if less than 50% complete
            return True
        
        # Check if there are critical bottlenecks that need resolution
        task_summary = progress.get("task_summary", {})
        blocked_tasks = task_summary.get("blocked", 0)
        
        if blocked_tasks > 0:
            # Continue monitoring if there are blocked tasks
            return True
            
        return False
    
    def _should_collect_deliverables(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent should transition to collecting deliverables.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if the agent should collect deliverables
        """
        # Get current progress
        progress = state.get("progress", {})
        completion_percentage = progress.get("completion_percentage", 0)
        
        # Transition to deliverable collection when substantial progress is made
        if completion_percentage >= 50:
            task_summary = progress.get("task_summary", {})
            blocked_tasks = task_summary.get("blocked", 0)
            
            # Don't transition if there are critical blockers
            if blocked_tasks > 0:
                return False
                
            return True
            
        return False
    
    def _should_return_to_monitoring(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent should return to monitoring from collection.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if the agent should return to monitoring
        """
        # Check if all required deliverables have been collected
        deliverables = state.get("deliverables", {})
        
        # Get expected deliverable count from execution plan
        execution_plan = state.get("execution_plan", {})
        expected_deliverable_count = 0
        
        for phase in execution_plan.get("phases", []):
            expected_deliverable_count += len(phase.get("tasks", []))
        
        # Return to monitoring if we don't have enough deliverables
        if len(deliverables) < (expected_deliverable_count * 0.8):
            return True
            
        return False
    
    def _should_compile_results(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent should proceed to compiling results.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if the agent should compile results
        """
        # Check if we have enough deliverables to compile
        deliverables = state.get("deliverables", {})
        
        # Get expected deliverable count from execution plan
        execution_plan = state.get("execution_plan", {})
        expected_deliverable_count = 0
        
        for phase in execution_plan.get("phases", []):
            expected_deliverable_count += len(phase.get("tasks", []))
        
        progress = state.get("progress", {})
        completion_percentage = progress.get("completion_percentage", 0)
        
        # Proceed to compilation if we have enough deliverables and progress
        if len(deliverables) >= (expected_deliverable_count * 0.8) and completion_percentage >= 80:
            return True
            
        return False
    
    # State handler methods
    
    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: TeamLeadGraphState) -> Dict[str, Any]:
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
            project_plan = state["project_plan"]
            
            self.logger.debug(f"Extracted input data: {input_data[:200]}...")
            self.logger.debug(f"Project plan: {str(project_plan)[:200]}...")
            
            # Store initial request in memory
            memory_entry = {
                "initial_request": input_data,
                "project_plan": project_plan,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            # Create project in result compiler
            self.project_name = f"project_{self.agent_id}"
            self.result_compiler.create_project(
                project_name=self.project_name,
                project_type=ProjectType.GENERIC
            )
            
            # Record the status transition
            await self.update_status("analyzing_tasks")
            
            state["status"] = "analyzing_tasks"
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_tasks",
                      metadata={"phase": "task_analysis"})
    async def analyze_tasks(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Analyze project tasks using the task coordinator tool.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with tasks
        """
        self.logger.info("Starting analyze_tasks phase")
        
        try:
            project_description = state["input"]
            project_plan = state["project_plan"]
            
            # Use task coordinator to break down the project
            execution_result = await coordinate_project_execution(
                project_plan=project_plan,
                llm_service=self.llm_service
            )
            
            # Store tasks and execution plan
            state["tasks"] = execution_result.get("tasks", [])
            state["execution_plan"] = execution_result.get("execution_plan", {})
            
            # Store in working memory
            working_memory_entry = {
                "tasks": state["tasks"],
                "execution_plan": state["execution_plan"],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Update progress information
            state["progress"]["task_summary"]["total"] = len(state["tasks"])
            state["progress"]["task_summary"]["pending"] = len(state["tasks"])
            
            # Update status
            await self.update_status("planning_execution")
            state["status"] = "planning_execution"
            
            self.logger.info(f"Task analysis completed with {len(state['tasks'])} tasks")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_tasks: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="plan_execution",
                      metadata={"phase": "execution_planning"})
    async def plan_execution(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Plan the execution sequence based on analyzed tasks.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with execution plan
        """
        self.logger.info("Starting plan_execution phase")
        
        try:
            tasks = state["tasks"]
            execution_plan = state["execution_plan"]
            
            # Validate execution plan and refine if needed
            if not execution_plan or "phases" not in execution_plan:
                # If execution plan is missing or incomplete, regenerate it
                self.logger.warning("Execution plan is incomplete, regenerating")
                
                # Call LLM to create execution plan
                coordination_result = await self.llm_service.coordinate_tasks(
                    project_description=state["input"],
                    project_plan=state["project_plan"],
                    existing_tasks=tasks
                )
                
                execution_plan = coordination_result.get("execution_plan", {})
                state["execution_plan"] = execution_plan
            
            # Store execution plan in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"execution_plan": execution_plan}
            )
            
            # Update status
            await self.update_status("assigning_agents")
            state["status"] = "assigning_agents"
            
            self.logger.info("Execution planning completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in plan_execution: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="assign_agents",
                      metadata={"phase": "agent_assignment"})
    async def assign_agents(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Assign tasks to appropriate agents.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with agent assignments
        """
        self.logger.info("Starting assign_agents phase")
        
        try:
            tasks = state["tasks"]
            execution_plan = state["execution_plan"]
            
            # Initialize agent assignments
            agent_assignments = {}
            
            # Define available agents and their capabilities
            # In a real system, this would be dynamically determined
            available_agents = ["solution_architect", "full_stack_developer", "qa_test"]
            agent_capabilities = {
                "solution_architect": {
                    "agent_type": "solution_architect",
                    "strengths": ["architecture design", "system planning", "technical decisions"]
                },
                "full_stack_developer": {
                    "agent_type": "full_stack_developer",
                    "strengths": ["coding", "implementation", "integration"]
                },
                "qa_test": {
                    "agent_type": "qa_test",
                    "strengths": ["testing", "quality assurance", "validation"]
                }
            }
            
            # Register agents with communicator
            for agent_id in available_agents:
                self.agent_communicator.register_agent(agent_id)
                self.registered_agents[agent_id] = agent_capabilities[agent_id]
            
            # Get agent assignments from execution plan if available
            if "agent_assignments" in execution_plan and execution_plan["agent_assignments"]:
                agent_assignments = execution_plan["agent_assignments"]
            else:
                # Otherwise, assign tasks based on task properties
                for task in tasks:
                    # Get the most suitable agent for this task
                    selection_result = await self.llm_service.select_agent(
                        task=task,
                        available_agents=available_agents,
                        agent_capabilities=agent_capabilities
                    )
                    
                    selected_agent = selection_result.get("selected_agent_id", "full_stack_developer")
                    
                    # Add task to agent's assignments
                    if selected_agent not in agent_assignments:
                        agent_assignments[selected_agent] = []
                    
                    agent_assignments[selected_agent].append({
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "priority": "MEDIUM",  # Default priority
                        "task_data": task
                    })
            
            # Store agent assignments in state
            state["agent_assignments"] = agent_assignments
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"agent_assignments": agent_assignments}
            )
            
            # Initialize active tasks tracking
            for agent_id, tasks in agent_assignments.items():
                for task in tasks:
                    task_id = task["task_id"]
                    self.active_tasks[task_id] = {
                        "agent_id": agent_id,
                        "status": "pending",
                        "progress": 0,
                        "start_time": None,
                        "completion_time": None
                    }
            
            # Update status
            await self.update_status("monitoring_progress")
            state["status"] = "monitoring_progress"
            
            self.logger.info(f"Agent assignment completed with {len(agent_assignments)} agents")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in assign_agents: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="monitor_progress",
                      metadata={"phase": "progress_monitoring"})
    async def monitor_progress(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Monitor progress of tasks and handle issues.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with progress information
        """
        self.logger.info("Starting monitor_progress phase")
        
        try:
            tasks = state["tasks"]
            execution_plan = state["execution_plan"]
            agent_assignments = state["agent_assignments"]
            
            # Get current task statuses
            task_statuses = {}
            for task in tasks:
                task_id = task["id"]
                if task_id in self.active_tasks:
                    task_statuses[task_id] = self.active_tasks[task_id]["status"]
                else:
                    task_statuses[task_id] = "pending"
            
            # Analyze current progress
            project_progress = calculate_project_progress(tasks, execution_plan)
            state["progress"] = project_progress
            
            # Check for bottlenecks
            bottlenecks = identify_bottlenecks(tasks, execution_plan)
            
            # Analyze timeline adherence
            timeline_analysis = analyze_timeline_adherence(tasks, execution_plan)
            
            # Detect at-risk tasks
            at_risk_tasks = detect_at_risk_tasks(tasks, execution_plan, timeline_analysis)
            
            # Generate progress report
            progress_report = generate_progress_report(
                tasks=tasks,
                execution_plan=execution_plan,
                project_progress=project_progress,
                bottlenecks=bottlenecks,
                timeline_analysis=timeline_analysis,
                at_risk_tasks=at_risk_tasks
            )
            
            # Store progress report in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"progress_report": progress_report}
            )
            
            # Analyze if any task needs attention
            progress_analysis = await self.llm_service.analyze_progress(
                execution_plan=execution_plan,
                current_progress=project_progress,
                task_statuses=task_statuses
            )
            
            # Handle critical issues
            critical_issues = progress_analysis.get("critical_issues", [])
            for issue in critical_issues:
                self.logger.warning(f"Critical issue detected: {issue.get('issue')}")
                # Apply automated mitigation if available
                # (Implementation would depend on issue type)
            
            # Process incomplete tasks (simulate some tasks completing for demo purposes)
            # In a real system, this would wait for actual agent completion
            pending_tasks = [task["id"] for task in tasks 
                          if task_statuses.get(task["id"]) == "pending"]
            
            if pending_tasks:
                # Simulate a task being completed (for demonstration)
                # In a real system, this would be triggered by agent responses
                completed_task_id = pending_tasks[0]
                agent_id = next((agent for agent, agent_tasks in agent_assignments.items() 
                               if any(t["task_id"] == completed_task_id for t in agent_tasks)), 
                              "full_stack_developer")
                
                completed_task = next((task for task in tasks if task["id"] == completed_task_id), None)
                
                if completed_task:
                    # Update task status
                    updated_task = update_task_status(
                        task_id=completed_task_id,
                        tasks=tasks,
                        new_status="completed",
                        completion_percentage=100,
                        notes=f"Completed by agent {agent_id}",
                        update_timestamp=datetime.utcnow().isoformat()
                    )
                    
                    # Update tasks list
                    tasks_index = next((i for i, task in enumerate(tasks) 
                                     if task["id"] == completed_task_id), None)
                    if tasks_index is not None:
                        tasks[tasks_index] = updated_task
                    
                    # Update active tasks tracking
                    self.active_tasks[completed_task_id] = {
                        "agent_id": agent_id,
                        "status": "completed",
                        "progress": 100,
                        "start_time": datetime.utcnow().isoformat(),
                        "completion_time": datetime.utcnow().isoformat()
                    }
                    
                    # Handle task completion event
                    updated_tasks, event_data = handle_task_completion_events(
                        task_id=completed_task_id,
                        tasks=tasks,
                        execution_plan=execution_plan,
                        completion_data={
                            "timestamp": datetime.utcnow().isoformat(),
                            "success": True
                        },
                        agent_id=agent_id
                    )
                    
                    # Process deliverable (simulate)
                    deliverable = {
                        "id": f"deliverable_{completed_task_id}",
                        "deliverable_type": "code",
                        "source_agent_id": agent_id,
                        "task_id": completed_task_id,
                        "content": {
                            "component": completed_task["name"],
                            "code": f"// Example code for {completed_task['name']}"
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    state["deliverables"][deliverable["id"]] = deliverable
                    
                    self.logger.info(f"Task {completed_task_id} completed by {agent_id}")
            
            # Check for checkpoints
            checkpoint_triggered = None
            for checkpoint in execution_plan.get("checkpoints", []):
                # Check if this checkpoint should be triggered
                checkpoint_verification = manage_checkpoints(
                    checkpoint_id=checkpoint.get("checkpoint_id", ""),
                    execution_plan=execution_plan,
                    tasks=tasks,
                    project_progress=project_progress
                )
                
                if checkpoint_verification.get("status") == "verified":
                    checkpoint_triggered = checkpoint_verification
                    break
            
            if checkpoint_triggered:
                self.logger.info(f"Checkpoint triggered: {checkpoint_triggered.get('checkpoint_id')}")
                # Store checkpoint in memory
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.LONG_TERM,
                    content={"checkpoint": checkpoint_triggered},
                    metadata={"type": "checkpoint"}
                )
            
            # Update state with latest tasks and progress
            state["tasks"] = tasks
            state["progress"] = project_progress
            
            self.logger.info(f"Progress monitoring completed. Project at {project_progress.get('completion_percentage', 0)}% completion")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in monitor_progress: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="collect_deliverables",
                      metadata={"phase": "deliverable_collection"})
    async def collect_deliverables(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Collect and process deliverables from agents.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with deliverables
        """
        self.logger.info("Starting collect_deliverables phase")
        
        try:
            tasks = state["tasks"]
            execution_plan = state["execution_plan"]
            agent_assignments = state["agent_assignments"]
            deliverables = state.get("deliverables", {})
            
            # For each agent, collect pending deliverables
            for agent_id, agent_tasks in agent_assignments.items():
                # Get pending deliverables from the agent
                pending_deliverables = self.agent_communicator.get_pending_deliverables(agent_id)
                
                for pending in pending_deliverables:
                    # Get the deliverable
                    deliverable = pending.get("deliverable", {})
                    deliverable_id = deliverable.get("id", "")
                    task_id = deliverable.get("task_id", "")
                    
                    # Find the corresponding task
                    task = next((t for t in tasks if t["id"] == task_id), None)
                    
                    if task and deliverable_id:
                        # Analyze the deliverable
                        related_deliverables = []
                        # Find related deliverables (those that have dependencies on this task)
                        for other_id, other_deliverable in deliverables.items():
                            if task_id in task.get("dependencies", []):
                                related_deliverables.append(other_deliverable)
                        
                        # Integrate the deliverable
                        integration_result = await self.llm_service.integrate_deliverables(
                            task=task,
                            deliverable=deliverable,
                            related_deliverables=related_deliverables
                        )
                        
                        # Process based on acceptance
                        acceptance = integration_result.get("acceptance", "accept")
                        
                        if acceptance == "accept":
                            # Store the deliverable
                            deliverables[deliverable_id] = deliverable
                            
                            # Add to result compiler
                            component_type = ComponentType.CODE
                            if deliverable.get("deliverable_type") == "documentation":
                                component_type = ComponentType.DOCUMENTATION
                                
                            self.result_compiler.add_component(
                                project_name=self.project_name,
                                name=task.get("name", "Unknown"),
                                component_type=component_type,
                                agent_id=agent_id,
                                content=deliverable.get("content", {}),
                                metadata={"task_id": task_id}
                            )
                            
                            self.logger.info(f"Accepted deliverable {deliverable_id} for task {task_id}")
                        elif acceptance == "revise":
                            # Send feedback to agent for revision
                            feedback_points = [issue.get("issue") for issue in integration_result.get("integration_issues", [])]
                            feedback = await self.llm_service.provide_feedback(
                                task=task,
                                deliverable=deliverable,
                                feedback_points=feedback_points
                            )
                            
                            # Send feedback message to agent
                            self.agent_communicator.send_message(
                                source_agent_id=self.agent_id,
                                target_agent_id=agent_id,
                                content=feedback.get("feedback_message", "Please revise your deliverable."),
                                message_type=MessageType.FEEDBACK,
                                task_id=task_id,
                                priority=MessagePriority.HIGH,
                                metadata={"deliverable_id": deliverable_id}
                            )
                            
                            self.logger.info(f"Requested revision for deliverable {deliverable_id}")
                        else:  # reject
                            # Log rejection
                            self.logger.warning(f"Rejected deliverable {deliverable_id} for task {task_id}")
                            
                            # Send rejection message to agent
                            self.agent_communicator.send_message(
                                source_agent_id=self.agent_id,
                                target_agent_id=agent_id,
                                content="The deliverable was rejected. Please start over.",
                                message_type=MessageType.FEEDBACK,
                                task_id=task_id,
                                priority=MessagePriority.HIGH,
                                metadata={"deliverable_id": deliverable_id}
                            )
            
            # Update state with collected deliverables
            state["deliverables"] = deliverables
            
            # Check if we have all expected deliverables
            total_tasks = len(tasks)
            collected_deliverables = len(deliverables)
            collection_percentage = (collected_deliverables / total_tasks) * 100 if total_tasks > 0 else 0
            
            self.logger.info(f"Deliverable collection completed: {collected_deliverables}/{total_tasks} ({collection_percentage:.1f}%)")
            
            # Store deliverable information in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"deliverables": deliverables}
            )
            
            # Update status based on collection progress
            if collection_percentage >= 80:
                await self.update_status("compiling_results")
                state["status"] = "compiling_results"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in collect_deliverables: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="compile_results",
                      metadata={"phase": "result_compilation"})
    async def compile_results(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Compile all deliverables into a final project result.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with compilation result
        """
        self.logger.info("Starting compile_results phase")
        
        try:
            deliverables = state["deliverables"]
            project_description = state["input"]
            
            # Define target component structure
            component_structure = {
                "directories": {
                    "code": ["src", "api", "components"],
                    "docs": ["specifications", "guides"],
                    "config": []
                }
            }
            
            # Compile results using LLM
            compilation_plan = await self.llm_service.compile_results(
                project_description=project_description,
                deliverables=deliverables,
                component_structure=component_structure
            )
            
            # Store compilation plan
            state["compilation_result"] = compilation_plan
            
            # Execute compilation using result compiler
            compilation_result = self.result_compiler.compile_project(self.project_name)
            
            # Store in long-term memory for future reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "compilation_result": compilation_result,
                    "project_name": self.project_name
                },
                metadata={"type": "final_result"}
            )
            
            # Update status
            await self.update_status("completed")
            state["status"] = "completed"
            
            self.logger.info("Result compilation completed successfully")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in compile_results: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="complete_project",
                      metadata={"phase": "completion"})
    async def complete_project(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Complete the project and finalize all outputs.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Final state with results
        """
        self.logger.info("Starting complete_project phase")
        
        try:
            # Add completion timestamp
            state["completion_timestamp"] = datetime.utcnow().isoformat()
            
            # Generate final project report
            final_report = {
                "project_name": self.project_name,
                "completion_timestamp": state["completion_timestamp"],
                "task_summary": {
                    "total_tasks": len(state["tasks"]),
                    "completed_tasks": sum(1 for task in state["tasks"] 
                                        if task.get("progress", {}).get("status") == "completed")
                },
                "final_progress": state["progress"],
                "compilation_result": state["compilation_result"],
                "output_location": self.result_compiler.get_project_status(self.project_name).get("output_dir", "unknown")
            }
            
            # Store final report in long-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=final_report,
                metadata={"type": "final_report"}
            )
            
            # Clean up resources
            for agent_id in self.registered_agents:
                self.agent_communicator.clear_agent_messages(agent_id)
                
            self.logger.info("Project completed successfully")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in complete_project: {str(e)}", exc_info=True)
            raise
    
    @trace_method
    async def update_status(self, new_status: str) -> None:
        """
        Update the agent's status and store in memory.
        
        Args:
            new_status: New status string
        """
        self.logger.info(f"Updating status to: {new_status}")
        
        try:
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"status": new_status, "timestamp": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            self.logger.error(f"Error updating status: {str(e)}", exc_info=True)
    
    @trace_method
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's work.
        
        Returns:
            Dict[str, Any]: Report data
        """
        self.logger.info("Generating TeamLead report")
        
        try:
            # Retrieve latest working state
            working_state = await self.memory_manager.get_working_state(self.agent_id)
            
            # Retrieve long-term memory entries for final report
            long_term_entries = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "final_report"}
            )
            
            final_report = {}
            if long_term_entries:
                final_report = long_term_entries[0].content
            
            # Compile report
            report = {
                "agent_id": self.agent_id,
                "agent_type": "team_lead",
                "current_status": working_state.get("status", "unknown"),
                "tasks_managed": len(working_state.get("tasks", [])),
                "agents_coordinated": list(working_state.get("agent_assignments", {}).keys()),
                "progress_summary": working_state.get("progress", {}),
                "final_report": final_report,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            self.logger.info("Report generation completed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return {
                "agent_id": self.agent_id,
                "agent_type": "team_lead",
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }