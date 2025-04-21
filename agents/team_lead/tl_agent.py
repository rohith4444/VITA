from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime
import json
import os
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

# Import Code Assembler if available
try:
    from agents.code_assembler.ca_agent import CodeAssemblerAgent
    HAS_CODE_ASSEMBLER = True
except ImportError:
    HAS_CODE_ASSEMBLER = False
    setup_logger("team_lead.agent").warning("CodeAssemblerAgent not available, advanced compilation disabled")

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
        has_code_assembler (bool): Whether the Code Assembler Agent is available
        code_assembler_agent (Optional[CodeAssemblerAgent]): Code Assembler Agent instance
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
            
            # Initialize communication tools
            self.agent_communicator = AgentCommunicator()
            
            # Register self with agent communicator
            self.agent_communicator.register_agent(agent_id)
            
            # Initialize agent registry and active tasks
            self.registered_agents = {}
            self.active_tasks = {}
            self.project_name = f"project_{agent_id}"
            
            # Check Code Assembler availability
            self.has_code_assembler = HAS_CODE_ASSEMBLER
            self.code_assembler_agent = None
            
            # Initialize result compiler with memory manager for Code Assembler integration
            self.result_compiler = ResultCompiler(memory_manager=memory_manager if self.has_code_assembler else None)
            
            if self.has_code_assembler:
                self.logger.info("Code Assembler Agent is available for advanced project compilation")
            else:
                self.logger.info("Code Assembler Agent not available, will use basic compilation")
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("TeamLeadAgent initialization completed")
            
            # Initialize specialized agents (async initialization handled in run method)
            self._specialized_agents_initialized = False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TeamLeadAgent: {str(e)}", exc_info=True)
            raise

    async def initialize_agents(self):
        """Initialize and register specialized agents."""
        if self._specialized_agents_initialized:
            return
            
        try:
            self.logger.info("Initializing specialized agents")
            
            # Initialize Code Assembler Agent if available
            if self.has_code_assembler:
                self.logger.info("Initializing Code Assembler Agent")
                code_assembler_id = f"code_assembler_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.code_assembler_agent = CodeAssemblerAgent(
                    agent_id=code_assembler_id,
                    name="Code Assembler",
                    memory_manager=self.memory_manager
                )
                self.logger.info(f"Code Assembler Agent initialized with ID: {code_assembler_id}")
                
                # Register Code Assembler with agent communicator
                self.agent_communicator.register_agent(code_assembler_id)
                
                # Add to registered agents
                self.registered_agents[code_assembler_id] = {
                    "agent_type": "code_assembler",
                    "strengths": ["code integration", "dependency resolution", "project assembly"],
                    "id": code_assembler_id
                }
            
            self._specialized_agents_initialized = True
            self.logger.info("Specialized agents initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error initializing specialized agents: {str(e)}", exc_info=True)
            self._specialized_agents_initialized = False

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
            
            # Add new nodes for Scrum Master interaction
            builder.add_node("receive_user_feedback", self.receive_user_feedback)
            builder.add_node("prepare_milestone_delivery", self.prepare_milestone_delivery)
            builder.add_node("respond_to_user_query", self.respond_to_user_query)
            
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
            
            # Add edges for Scrum Master interaction
            builder.add_edge("receive_user_feedback", "monitor_progress")
            builder.add_edge("prepare_milestone_delivery", "monitor_progress")
            builder.add_edge("respond_to_user_query", "monitor_progress")
            
            # Add edges from monitoring to Scrum Master interaction states
            builder.add_edge("monitor_progress", "receive_user_feedback",
                          condition=self._has_user_feedback)
            builder.add_edge("monitor_progress", "prepare_milestone_delivery",
                          condition=self._should_prepare_milestone)
            builder.add_edge("monitor_progress", "respond_to_user_query",
                          condition=self._has_user_query)
            
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

    # New condition methods for Scrum Master interaction
    
    def _has_user_feedback(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent has user feedback to process.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if there is user feedback to process
        """
        return state.get("user_feedback") is not None and state.get("user_feedback") != {}
    
    def _should_prepare_milestone(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent should prepare a milestone for user presentation.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if a milestone should be prepared
        """
        # Check if a milestone is available for delivery
        progress = state.get("progress", {})
        milestone_progress = progress.get("milestone_progress", [])
        
        # Find completed milestones that haven't been presented to the user yet
        for milestone in milestone_progress:
            if milestone.get("status") == "completed" and milestone.get("presented_to_user", False) == False:
                return True
                
        return False
    
    def _has_user_query(self, state: TeamLeadGraphState) -> bool:
        """
        Determine if the agent has a user query to respond to.
        
        Args:
            state: Current workflow state
            
        Returns:
            bool: True if there is a user query to respond to
        """
        return state.get("user_query") is not None and state.get("user_query") != {}
    
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
            
            # Initialize specialized agents if not already done
            await self.initialize_agents()
            
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
            
            # Check for user interactions from Scrum Master
            if state.get("user_feedback"):
                self.logger.info("User feedback detected, transitioning to feedback handling")
                state["status"] = "receive_user_feedback"
                await self.update_status(state["status"])
                return state
                
            if state.get("user_query"):
                self.logger.info("User query detected, transitioning to query handling")
                state["status"] = "respond_to_user_query"
                await self.update_status(state["status"])
                return state
            
            # Check if we need to prepare a milestone for user review
            milestone_needed = self._should_prepare_milestone(state)
            if milestone_needed:
                self.logger.info("Milestone delivery needed, transitioning to milestone preparation")
                state["status"] = "prepare_milestone_delivery"
                await self.update_status(state["status"])
                return state
            
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
                    
                    # Add deliverable to state
                    if "deliverables" not in state:
                        state["deliverables"] = {}
                    state["deliverables"][completed_task_id] = deliverable
                    
                    # Update tasks with new list
                    state["tasks"] = updated_tasks
                    
                    # Update progress based on new task status
                    project_progress = calculate_project_progress(updated_tasks, execution_plan)
                    state["progress"] = project_progress
                    
                    # Handle checkpoint if triggered
                    checkpoint_id = event_data.get("checkpoint_triggered")
                    if checkpoint_id:
                        checkpoint_status = manage_checkpoints(
                            checkpoint_id=checkpoint_id,
                            execution_plan=execution_plan,
                            tasks=updated_tasks,
                            project_progress=project_progress
                        )
                        self.logger.info(f"Checkpoint {checkpoint_id} status: {checkpoint_status.get('status')}")
            
            # Update memory with latest task status
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "tasks": tasks,
                    "active_tasks": self.active_tasks,
                    "progress": project_progress
                }
            )
            
            # Update status
            state["tasks"] = tasks
            
            # Check transition conditions
            if self._should_collect_deliverables(state):
                state["status"] = "collecting_deliverables"
            else:
                state["status"] = "monitoring_progress"
                
            await self.update_status(state["status"])
            
            self.logger.info(f"Progress monitoring completed. Overall progress: {project_progress.get('completion_percentage', 0)}%")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in monitor_progress: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="collect_deliverables",
                      metadata={"phase": "deliverable_collection"})
    async def collect_deliverables(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Collect and validate deliverables from agents.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with collected deliverables
        """
        self.logger.info("Starting collect_deliverables phase")
        
        try:
            tasks = state["tasks"]
            execution_plan = state["execution_plan"]
            agent_assignments = state["agent_assignments"]
            deliverables = state.get("deliverables", {})
            
            # Check for user interactions from Scrum Master
            if state.get("user_feedback"):
                self.logger.info("User feedback detected, transitioning to feedback handling")
                state["status"] = "receive_user_feedback"
                await self.update_status(state["status"])
                return state
                
            if state.get("user_query"):
                self.logger.info("User query detected, transitioning to query handling")
                state["status"] = "respond_to_user_query"
                await self.update_status(state["status"])
                return state
            
            # Check if we need to prepare a milestone for user review
            milestone_needed = self._should_prepare_milestone(state)
            if milestone_needed:
                self.logger.info("Milestone delivery needed, transitioning to milestone preparation")
                state["status"] = "prepare_milestone_delivery"
                await self.update_status(state["status"])
                return state
            
            # Process completed tasks that don't have deliverables yet
            completed_tasks = [task for task in tasks 
                             if task.get("progress", {}).get("status") == "completed" 
                             and task["id"] not in deliverables]
            
            for task in completed_tasks:
                task_id = task["id"]
                # Find which agent completed this task
                agent_id = None
                for agent, agent_tasks in agent_assignments.items():
                    for agent_task in agent_tasks:
                        if agent_task.get("task_id") == task_id:
                            agent_id = agent
                            break
                    if agent_id:
                        break
                
                if not agent_id:
                    agent_id = "unknown_agent"
                
                # In a real system, we would request the deliverable from the agent
                # For now, simulate the deliverable
                deliverable_type = DeliverableType.CODE
                if "design" in task.get("name", "").lower() or "architecture" in task.get("name", "").lower():
                    deliverable_type = DeliverableType.DOCUMENTATION
                elif "test" in task.get("name", "").lower() or "qa" in task.get("name", "").lower():
                    deliverable_type = DeliverableType.TEST
                
                # Create deliverable content
                if deliverable_type == DeliverableType.CODE:
                    content = f"// Code implementation for {task.get('name', 'Unknown Task')}\n\nfunction example() {{\n  console.log('Task implementation');\n}}"
                elif deliverable_type == DeliverableType.TEST:
                    content = f"// Test implementation for {task.get('name', 'Unknown Task')}\n\nfunction testExample() {{\n  assert(true, 'Test passes');\n}}"
                else:
                    content = f"# Documentation for {task.get('name', 'Unknown Task')}\n\nThis document outlines the approach and implementation details."
                
                # Add deliverable
                deliverables[task_id] = {
                    "id": f"deliverable_{task_id}",
                    "deliverable_type": deliverable_type.value,
                    "source_agent_id": agent_id,
                    "task_id": task_id,
                    "content": content,
                    "metadata": {
                        "task_name": task.get("name", "Unknown Task"),
                        "milestone": task.get("milestone", "Unknown Milestone")
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Add component to result compiler
                try:
                    self.result_compiler.add_component(
                        project_name=self.project_name,
                        name=task.get("name", "Unknown Component"),
                        component_type=ComponentType.CODE if deliverable_type == DeliverableType.CODE else 
                                      ComponentType.TEST if deliverable_type == DeliverableType.TEST else
                                      ComponentType.DOCUMENTATION,
                        agent_id=agent_id,
                        content=content,
                        metadata={
                            "task_id": task_id,
                            "milestone": task.get("milestone", "Unknown Milestone")
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error adding component to result compiler: {str(e)}")
            
            # Validate and integrate collected deliverables
            for task_id, deliverable in list(deliverables.items()):
                # Skip already processed deliverables
                if deliverable.get("processed", False):
                    continue
                    
                task = next((t for t in tasks if t["id"] == task_id), None)
                if not task:
                    continue
                
                # Find related deliverables
                related_deliverables = []
                dependencies = task.get("dependency_info", {}).get("predecessors", [])
                for dep_id in dependencies:
                    if dep_id in deliverables:
                        related_deliverables.append(deliverables[dep_id])
                
                # Use LLM to analyze and integrate the deliverable
                integration_result = await self.llm_service.integrate_deliverables(
                    task=task,
                    deliverable=deliverable,
                    related_deliverables=related_deliverables
                )
                
                # Update deliverable with integration results
                deliverable["integration_result"] = integration_result
                deliverable["processed"] = True
                
                # Handle integration issues if any
                issues = integration_result.get("integration_issues", [])
                if issues:
                    for issue in issues:
                        self.logger.warning(f"Integration issue for task {task_id}: {issue.get('issue')}")
                        # In a real system, would handle the issue (e.g., request fixes)
            
            # Update state with collected deliverables
            state["deliverables"] = deliverables
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"deliverables": deliverables}
            )
            
            # Check transition conditions
            if self._should_return_to_monitoring(state):
                state["status"] = "monitoring_progress"
            elif self._should_compile_results(state):
                state["status"] = "compiling_results"
            else:
                state["status"] = "collecting_deliverables"
                
            await self.update_status(state["status"])
            
            self.logger.info(f"Deliverable collection completed with {len(deliverables)} deliverables")
            return state 
        except Exception as e:
            self.logger.error(f"Error in collect_deliverables: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="compile_results",
                      metadata={"phase": "result_compilation"})
    async def compile_results(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Compile project deliverables into final result.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with compilation result
        """
        self.logger.info("Starting compile_results phase")
        
        try:
            deliverables = state.get("deliverables", {})
            
            # Create project structure template
            project_structure = {
                "directories": {
                    "code": ["src", "components", "utils", "styles"],
                    "documentation": ["docs", "api", "architecture"],
                    "tests": ["unit", "integration", "e2e"]
                }
            }
            
            # Use Code Assembler if available, otherwise use basic compilation
            if self.has_code_assembler and self.code_assembler_agent:
                self.logger.info("Using Code Assembler for advanced compilation")
                
                # Compile project using Code Assembler
                compilation_result = await self.result_compiler.compile_project(
                    project_name=self.project_name,
                    project_description=state.get("input", "")
                )
                
            else:
                self.logger.info("Using basic compilation")
                
                # Use LLM service to organize compilation
                compilation_plan = await self.llm_service.compile_results(
                    project_description=state.get("input", ""),
                    deliverables=deliverables,
                    component_structure=project_structure
                )
                
                # Compile project
                compilation_result = await self.result_compiler.compile_project(
                    project_name=self.project_name
                )
            
            # Update state with compilation result
            state["compilation_result"] = compilation_result or {}
            
            # Store in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"compilation_result": state["compilation_result"]}
            )
            
            # Update status
            state["status"] = "completed"
            await self.update_status(state["status"])
            
            self.logger.info("Results compilation completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in compile_results: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="complete_project",
                      metadata={"phase": "completion"})
    async def complete_project(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Finalize project and perform cleanup.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Final state
        """
        self.logger.info("Starting complete_project phase")
        
        try:
            # Store final state in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "final_state": {
                        "completion_timestamp": datetime.utcnow().isoformat(),
                        "tasks_completed": state.get("progress", {}).get("task_summary", {}).get("completed", 0),
                        "tasks_total": state.get("progress", {}).get("task_summary", {}).get("total", 0),
                        "success": True
                    }
                }
            )
            
            self.logger.info("Project completed successfully")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in complete_project: {str(e)}", exc_info=True)
            raise
    
    # New methods for Scrum Master interaction
    
    @monitor_operation(operation_type="receive_user_feedback",
                      metadata={"phase": "user_feedback"})
    async def receive_user_feedback(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Process user feedback received via Scrum Master.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with processed feedback
        """
        self.logger.info("Starting receive_user_feedback phase")
        
        try:
            user_feedback = state.get("user_feedback", {})
            
            if not user_feedback:
                self.logger.warning("No user feedback found, returning to monitoring")
                state["status"] = "monitoring_progress"
                await self.update_status(state["status"])
                return state
            
            feedback_type = user_feedback.get("type", "general")
            feedback_content = user_feedback.get("content", "")
            feedback_priority = user_feedback.get("priority", "medium")
            
            self.logger.info(f"Processing user feedback of type {feedback_type} with priority {feedback_priority}")
            
            # Process feedback based on type
            if feedback_type in ["bug_report", "issue"]:
                # For bugs/issues, find affected tasks
                affected_tasks = []
                components = user_feedback.get("components", [])
                
                for task in state.get("tasks", []):
                    task_name = task.get("name", "").lower()
                    # Check if this task relates to the affected components
                    if any(component.lower() in task_name for component in components):
                        affected_tasks.append(task)
                
                if affected_tasks:
                    # Mark affected tasks for attention
                    for task in affected_tasks:
                        task_id = task.get("id", "")
                        
                        # Update task with feedback info
                        if "feedback" not in task:
                            task["feedback"] = []
                            
                        task["feedback"].append({
                            "id": user_feedback.get("id", f"feedback_{len(task['feedback'])+1}"),
                            "type": feedback_type,
                            "content": feedback_content,
                            "priority": feedback_priority,
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "pending"
                        })
                        
                        # If task is already completed, mark for review
                        if task.get("progress", {}).get("status") == "completed":
                            # Update task status to reflect feedback
                            updated_task = update_task_status(
                                task_id=task_id,
                                tasks=state["tasks"],
                                new_status="in_progress",  # Reopen task
                                completion_percentage=90,  # Partial completion
                                notes=f"Reopened due to user feedback: {feedback_content[:50]}...",
                                update_timestamp=datetime.utcnow().isoformat()
                            )
                            
                            # Update task in state
                            tasks_index = next((i for i, t in enumerate(state["tasks"]) 
                                             if t["id"] == task_id), None)
                            if tasks_index is not None:
                                state["tasks"][tasks_index] = updated_task
                                
                            # Update active tasks tracking
                            self.active_tasks[task_id] = {
                                "agent_id": self.active_tasks.get(task_id, {}).get("agent_id", "unknown"),
                                "status": "in_progress",
                                "progress": 90,
                                "start_time": self.active_tasks.get(task_id, {}).get("start_time", datetime.utcnow().isoformat()),
                                "completion_time": None  # Reset completion time
                            }
                
                # Update project progress
                project_progress = calculate_project_progress(state["tasks"], state["execution_plan"])
                state["progress"] = project_progress
                
            elif feedback_type in ["feature_request", "enhancement"]:
                # For feature requests, create new tasks
                new_task_id = f"task_{len(state['tasks'])+1}"
                milestone = state.get("progress", {}).get("milestone_progress", [])
                milestone_name = milestone[-1].get("milestone") if milestone else "Enhancement"
                
                new_task = {
                    "id": new_task_id,
                    "name": f"Implementation of {user_feedback.get('feature', 'requested feature')}",
                    "milestone": milestone_name,
                    "milestone_index": len(milestone) - 1 if milestone else 0,
                    "dependencies": [],
                    "effort": "MEDIUM",
                    "description": f"Implement requested feature: {feedback_content}",
                    "status": "pending",
                    "agent_skill_requirements": {
                        "solution_architect": 0.3,
                        "full_stack_developer": 0.8,
                        "qa_test": 0.4
                    }
                }
                
                # Add task
                state["tasks"].append(new_task)
                
                # Update task count
                state["progress"]["task_summary"]["total"] += 1
                state["progress"]["task_summary"]["pending"] += 1
                
                # Assign to appropriate agent
                for agent, tasks in state["agent_assignments"].items():
                    if "full_stack_developer" in agent:
                        tasks.append({
                            "task_id": new_task_id,
                            "task_name": new_task["name"],
                            "priority": "HIGH" if feedback_priority == "high" else "MEDIUM",
                            "task_data": new_task
                        })
                        
                        # Update active tasks tracking
                        self.active_tasks[new_task_id] = {
                            "agent_id": agent,
                            "status": "pending",
                            "progress": 0,
                            "start_time": None,
                            "completion_time": None
                        }
                        break
            
            elif feedback_type in ["approval", "rejection"]:
                # For milestone approval/rejection
                milestone_id = user_feedback.get("milestone_id")
                
                if milestone_id:
                    # Find checkpoint for this milestone
                    checkpoint_id = None
                    for checkpoint in state.get("execution_plan", {}).get("checkpoints", []):
                        if checkpoint.get("milestone_reached") == milestone_id:
                            checkpoint_id = checkpoint.get("checkpoint_id")
                            break
                    
                    if checkpoint_id:
                        # Update checkpoint status
                        if feedback_type == "approval":
                            # Process approval
                            checkpoint_status = manage_checkpoints(
                                checkpoint_id=checkpoint_id,
                                execution_plan=state["execution_plan"],
                                tasks=state["tasks"],
                                project_progress=state["progress"]
                            )
                            
                            self.logger.info(f"User approved milestone {milestone_id}, checkpoint {checkpoint_id}")
                            
                        else:  # rejection
                            # Find tasks in this milestone
                            for task in state["tasks"]:
                                if task.get("milestone") == milestone_id and task.get("progress", {}).get("status") == "completed":
                                    # Reopen task due to rejection
                                    updated_task = update_task_status(
                                        task_id=task["id"],
                                        tasks=state["tasks"],
                                        new_status="in_progress",
                                        completion_percentage=80,
                                        notes=f"Reopened due to milestone rejection: {feedback_content[:50]}...",
                                        update_timestamp=datetime.utcnow().isoformat()
                                    )
                                    
                                    # Update task in state
                                    tasks_index = next((i for i, t in enumerate(state["tasks"]) 
                                                    if t["id"] == task["id"]), None)
                                    if tasks_index is not None:
                                        state["tasks"][tasks_index] = updated_task
                            
                            self.logger.info(f"User rejected milestone {milestone_id}, reopening tasks")
                            
                            # Update project progress
                            project_progress = calculate_project_progress(state["tasks"], state["execution_plan"])
                            state["progress"] = project_progress
            
            # Mark feedback as processed
            user_feedback["processed"] = True
            user_feedback["processed_timestamp"] = datetime.utcnow().isoformat()
            state["user_feedback"] = user_feedback
            
            # Store processed feedback in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"processed_feedback": user_feedback}
            )
            
            # Send acknowledgment to Scrum Master
            response_content = {
                "feedback_id": user_feedback.get("id", "unknown"),
                "status": "processed",
                "action_taken": f"Processed {feedback_type} feedback",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.agent_communicator.send_message(
                source_agent_id=self.agent_id,
                target_agent_id="scrum_master",
                content=response_content,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
                user_id=user_feedback.get("user_id")
            )
            
            # Return to progress monitoring
            state["status"] = "monitoring_progress"
            await self.update_status(state["status"])
            
            # Clear user feedback after processing
            state["user_feedback"] = None
            
            self.logger.info("User feedback processing completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_user_feedback: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="prepare_milestone_delivery",
                      metadata={"phase": "milestone_delivery"})
    async def prepare_milestone_delivery(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Prepare milestone data for user presentation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with milestone delivery data
        """
        self.logger.info("Starting prepare_milestone_delivery phase")
        
        try:
            progress = state.get("progress", {})
            milestone_progress = progress.get("milestone_progress", [])
            
            # Find completed milestone that needs presentation
            milestone_to_present = None
            for milestone in milestone_progress:
                if milestone.get("status") == "completed" and milestone.get("presented_to_user", False) == False:
                    milestone_to_present = milestone
                    break
            
            if not milestone_to_present:
                self.logger.warning("No completed milestone found for presentation")
                state["status"] = "monitoring_progress"
                await self.update_status(state["status"])
                return state
            
            milestone_name = milestone_to_present.get("milestone", "Unknown Milestone")
            
            # Collect tasks for this milestone
            milestone_tasks = [task for task in state["tasks"] if task.get("milestone") == milestone_name]
            
            # Collect deliverables for this milestone
            milestone_deliverables = {}
            for task in milestone_tasks:
                task_id = task.get("id", "")
                if task_id in state.get("deliverables", {}):
                    milestone_deliverables[task_id] = state["deliverables"][task_id]
            
            # Create milestone data for presentation
            milestone_data = {
                "id": milestone_name,
                "name": milestone_name,
                "description": f"Milestone implementation including {len(milestone_tasks)} tasks",
                "completion_percentage": milestone_to_present.get("completion_percentage", 100),
                "components": [task.get("name", "Unknown Component") for task in milestone_tasks],
                "technical_details": {
                    "completed_tasks": milestone_to_present.get("tasks_completed", 0),
                    "total_tasks": milestone_to_present.get("tasks_total", 0),
                    "test_coverage": "95%"  # Example value
                },
                "requires_approval": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store milestone data in state
            state["milestone_delivery"] = milestone_data
            
            # Mark milestone as presented
            milestone_to_present["presented_to_user"] = True
            
            # Store milestone data in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"milestone_delivery": milestone_data}
            )
            
            # Transfer deliverable to Scrum Master for user presentation
            deliverable_id = await self.agent_communicator.transfer_deliverable(
                source_agent_id=self.agent_id,
                target_agent_id="scrum_master",
                content=milestone_data,
                deliverable_type=DeliverableType.USER_PRESENTATION,
                message=f"Milestone {milestone_name} ready for user presentation",
                for_user_presentation=True,
                user_id=state.get("user_feedback", {}).get("user_id")
            )
            
            if deliverable_id:
                self.logger.info(f"Transferred milestone {milestone_name} to Scrum Master with ID {deliverable_id}")
            else:
                self.logger.warning(f"Failed to transfer milestone {milestone_name} to Scrum Master")
            
            # Return to progress monitoring
            state["status"] = "monitoring_progress"
            await self.update_status(state["status"])
            
            # Clear milestone delivery after sending
            state["milestone_delivery"] = None
            
            self.logger.info(f"Milestone {milestone_name} prepared for delivery")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in prepare_milestone_delivery: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="respond_to_user_query",
                      metadata={"phase": "user_query"})
    async def respond_to_user_query(self, state: TeamLeadGraphState) -> Dict[str, Any]:
        """
        Respond to user technical questions via Scrum Master.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict[str, Any]: Updated state with query response
        """
        self.logger.info("Starting respond_to_user_query phase")
        
        try:
            user_query = state.get("user_query", {})
            
            if not user_query:
                self.logger.warning("No user query found, returning to monitoring")
                state["status"] = "monitoring_progress"
                await self.update_status(state["status"])
                return state
            
            query_content = user_query.get("question", "")
            query_type = user_query.get("type", "general")
            user_id = user_query.get("user_id", "unknown")
            
            self.logger.info(f"Processing user query of type {query_type}: {query_content[:50]}...")
            
            # Process query based on type
            response = ""
            
            if query_type in ["architecture", "design"]:
                # Find architecture/design information
                architecture_tasks = [
                    task for task in state["tasks"] 
                    if any(keyword in task.get("name", "").lower() for keyword in ["architect", "design", "structure"])
                ]
                
                if architecture_tasks:
                    # Get deliverables for these tasks
                    architecture_deliverables = {}
                    for task in architecture_tasks:
                        task_id = task.get("id", "")
                        if task_id in state.get("deliverables", {}):
                            architecture_deliverables[task_id] = state["deliverables"][task_id]
                    
                    # Create response based on deliverables
                    response = f"Based on our architecture design, the system includes the following components:\n\n"
                    for task in architecture_tasks:
                        response += f"- {task.get('name', 'Unknown Component')}\n"
                    
                    if "database" in query_content.lower():
                        response += "\n\nThe database structure uses a relational model with the following entities:\n"
                        response += "- Users: Stores user authentication and profile data\n"
                        response += "- Users: Stores user authentication and profile data\n"
                        response += "- Projects: Stores project metadata and relationships\n"
                        response += "- Tasks: Contains task details and assignment information\n"
                        response += "- Resources: Tracks project resources and availability\n"
                else:
                    response = "The architecture follows a modern component-based design with proper separation of concerns. It includes frontend components, backend services, and appropriate data storage solutions."
            elif query_type in ["implementation", "code"]:
                # Find implementation-related tasks
                code_tasks = [
                    task for task in state["tasks"] 
                    if any(keyword in task.get("name", "").lower() for keyword in ["implement", "code", "develop", "build"])
                ]
                
                if code_tasks:
                    # Get code deliverables
                    code_deliverables = {}
                    for task in code_tasks:
                        task_id = task.get("id", "")
                        if task_id in state.get("deliverables", {}):
                            code_deliverables[task_id] = state["deliverables"][task_id]
                    
                    # Create response based on code details
                    response = f"The implementation includes the following components:\n\n"
                    for task in code_tasks[:5]:  # Limit to avoid too long responses
                        response += f"- {task.get('name', 'Unknown Component')}\n"
                    
                    if "language" in query_content.lower() or "framework" in query_content.lower():
                        response += "\n\nThe implementation uses the following technologies:\n"
                        response += "- Frontend: React with TypeScript\n"
                        response += "- Backend: Python with FastAPI\n"
                        response += "- Database: PostgreSQL\n"
                        response += "- Deployment: Docker and Kubernetes\n"
                else:
                    response = "The implementation follows best practices for modern software development, with clean code organization, appropriate error handling, and efficient algorithms."
            elif query_type in ["testing", "qa"]:
                # Find testing-related tasks
                test_tasks = [
                    task for task in state["tasks"] 
                    if any(keyword in task.get("name", "").lower() for keyword in ["test", "qa", "verify", "validation"])
                ]
                
                if test_tasks:
                    # Create response about testing approach
                    response = f"Our testing approach includes the following aspects:\n\n"
                    for task in test_tasks[:5]:  # Limit to avoid too long responses
                        response += f"- {task.get('name', 'Unknown Component')}\n"
                    
                    if "coverage" in query_content.lower():
                        response += "\n\nThe current test coverage is approximately 85%, with comprehensive unit tests and integration tests for critical components."
                    
                    if "methodology" in query_content.lower():
                        response += "\n\nWe follow a test-driven development approach with continuous integration to ensure code quality."
                else:
                    response = "The testing strategy includes unit tests, integration tests, and end-to-end tests to ensure robust functionality and reliability."
            elif query_type in ["timeline", "schedule", "progress"]:
                # Create response about project timeline
                progress = state.get("progress", {})
                completion_percentage = progress.get("completion_percentage", 0)
                task_summary = progress.get("task_summary", {})
                
                response = f"The project is currently {completion_percentage}% complete.\n\n"
                response += f"Task Summary:\n"
                response += f"- Total Tasks: {task_summary.get('total', 0)}\n"
                response += f"- Completed: {task_summary.get('completed', 0)}\n"
                response += f"- In Progress: {task_summary.get('in_progress', 0)}\n"
                response += f"- Pending: {task_summary.get('pending', 0)}\n"
                
                # Add milestone information
                milestone_progress = progress.get("milestone_progress", [])
                if milestone_progress:
                    response += "\nMilestone Progress:\n"
                    for milestone in milestone_progress:
                        milestone_name = milestone.get("milestone", "Unknown")
                        milestone_percentage = milestone.get("completion_percentage", 0)
                        milestone_status = milestone.get("status", "pending")
                        response += f"- {milestone_name}: {milestone_percentage}% complete ({milestone_status})\n"
            else:
                # General project information
                response = f"The project is progressing according to plan. We're implementing the requested functionality with a focus on maintainability, performance, and user experience. The team is addressing all requirements methodically and ensuring high-quality deliverables."
            
            # Send response to Scrum Master
            response_content = {
                "query_id": user_query.get("id", "unknown"),
                "response": response,
                "technical_level": user_query.get("technical_level", "medium"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message_id = self.agent_communicator.send_message(
                source_agent_id=self.agent_id,
                target_agent_id="scrum_master",
                content=response_content,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
                user_id=user_id
            )
            
            if message_id:
                self.logger.info(f"Sent query response to Scrum Master with message ID {message_id}")
            else:
                self.logger.warning("Failed to send query response to Scrum Master")
            
            # Mark query as processed
            user_query["processed"] = True
            user_query["processed_timestamp"] = datetime.utcnow().isoformat()
            user_query["response"] = response
            state["user_query"] = user_query
            
            # Store processed query in memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={"processed_query": user_query}
            )
            
            # Return to progress monitoring
            state["status"] = "monitoring_progress"
            await self.update_status(state["status"])
            
            # Clear user query after processing
            state["user_query"] = None
            
            self.logger.info("User query processing completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in respond_to_user_query: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="run", 
                      metadata={"phase": "execution"})
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Team Lead Agent workflow.
        
        Args:
            input_data: Input data containing project description and plan
            
        Returns:
            Dict[str, Any]: Result of the workflow execution
        """
        self.logger.info("Starting Team Lead Agent execution")
        
        try:
            # Ensure specialized agents are initialized
            await self.initialize_agents()
            
            # Extract input data
            project_description = input_data.get("project_description", "")
            project_plan = input_data.get("project_plan", {})
            
            # Check for Scrum Master interaction inputs
            user_feedback = input_data.get("user_feedback")
            user_query = input_data.get("user_query")
            prepare_milestone = input_data.get("prepare_milestone", False)
            
            # Create initial state
            state = {
                "input": project_description,
                "project_plan": project_plan,
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
                "status": "initialized",
                
                # Initialize Scrum Master interaction fields
                "user_feedback": user_feedback,
                "milestone_delivery": None,
                "user_query": user_query
            }
            
            # Run the workflow
            final_state = await self.graph.start(state)
            
            # Extract result data
            result = {
                "status": final_state.get("status", "unknown"),
                "completion_percentage": final_state.get("progress", {}).get("completion_percentage", 0),
                "tasks_completed": final_state.get("progress", {}).get("task_summary", {}).get("completed", 0),
                "tasks_total": final_state.get("progress", {}).get("task_summary", {}).get("total", 0),
                "deliverables_count": len(final_state.get("deliverables", {})),
                "compilation_success": final_state.get("compilation_result", {}).get("success", False),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add milestone information if available
            milestone_progress = final_state.get("progress", {}).get("milestone_progress", [])
            if milestone_progress:
                result["milestones"] = [
                    {
                        "name": milestone.get("milestone", "Unknown"),
                        "status": milestone.get("status", "pending"),
                        "completion_percentage": milestone.get("completion_percentage", 0)
                    }
                    for milestone in milestone_progress
                ]
            
            self.logger.info(f"Team Lead Agent execution completed with status: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in Team Lead Agent execution: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        

    # Add this method to your tl_agent.py file inside the TeamLeadAgent class
    # It should be at the same level as other methods like run(), assign_agents(), etc.

    @monitor_operation(operation_type="generate_report", 
                    metadata={"phase": "reporting"})
    async def generate_report(self, report_type: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a report about the team's progress and activities.
        
        Args:
            report_type: Type of report to generate
            parameters: Optional parameters for the report
            
        Returns:
            Dict[str, Any]: Generated report data
        """
        self.logger.info(f"Generating {report_type} report")
        
        try:
            # Default parameters
            params = parameters or {}
            
            if report_type == "progress":
                # Generate progress report
                progress = params.get("progress", self.state.get("progress", {}))
                tasks = params.get("tasks", self.state.get("tasks", []))
                execution_plan = params.get("execution_plan", self.state.get("execution_plan", {}))
                
                # Use progress tracker to generate report
                progress_report = generate_progress_report(
                    tasks=tasks,
                    execution_plan=execution_plan,
                    project_progress=progress
                )
                
                return {
                    "report_type": "progress",
                    "report_data": progress_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            elif report_type == "milestone":
                # Generate milestone report
                milestone_id = params.get("milestone_id")
                if not milestone_id:
                    raise ValueError("milestone_id is required for milestone reports")
                    
                milestone_tasks = [
                    task for task in self.state.get("tasks", [])
                    if task.get("milestone") == milestone_id
                ]
                
                milestone_deliverables = {}
                for task in milestone_tasks:
                    task_id = task.get("id", "")
                    if task_id in self.state.get("deliverables", {}):
                        milestone_deliverables[task_id] = self.state["deliverables"][task_id]
                
                return {
                    "report_type": "milestone",
                    "milestone_id": milestone_id,
                    "task_count": len(milestone_tasks),
                    "deliverable_count": len(milestone_deliverables),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            elif report_type == "agent_activity":
                # Generate agent activity report
                agent_id = params.get("agent_id")
                if not agent_id:
                    # Report on all agents
                    agent_assignments = self.state.get("agent_assignments", {})
                    
                    activity_summary = {}
                    for agent_id, tasks in agent_assignments.items():
                        completed_tasks = sum(1 for task in tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "completed")
                        in_progress_tasks = sum(1 for task in tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "in_progress")
                        pending_tasks = sum(1 for task in tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "pending")
                        
                        activity_summary[agent_id] = {
                            "total_tasks": len(tasks),
                            "completed_tasks": completed_tasks,
                            "in_progress_tasks": in_progress_tasks,
                            "pending_tasks": pending_tasks,
                            "completion_percentage": (completed_tasks / len(tasks)) * 100 if len(tasks) > 0 else 0
                        }
                    
                    return {
                        "report_type": "agent_activity",
                        "activity_summary": activity_summary,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    # Report on specific agent
                    agent_tasks = self.state.get("agent_assignments", {}).get(agent_id, [])
                    
                    completed_tasks = sum(1 for task in agent_tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "completed")
                    in_progress_tasks = sum(1 for task in agent_tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "in_progress")
                    pending_tasks = sum(1 for task in agent_tasks if self.active_tasks.get(task.get("task_id", ""), {}).get("status") == "pending")
                    
                    return {
                        "report_type": "agent_activity",
                        "agent_id": agent_id,
                        "total_tasks": len(agent_tasks),
                        "completed_tasks": completed_tasks,
                        "in_progress_tasks": in_progress_tasks,
                        "pending_tasks": pending_tasks,
                        "completion_percentage": (completed_tasks / len(agent_tasks)) * 100 if len(agent_tasks) > 0 else 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
            else:
                # Unknown report type
                return {
                    "report_type": "unknown",
                    "error": f"Unknown report type: {report_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return {
                "report_type": report_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }