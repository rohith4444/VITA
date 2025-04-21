from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from agents.core.base_agent import BaseAgent
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from .qat_state_graph import QATestGraphState, validate_state, get_next_stage, get_priority_factor, format_status_report
from .llm.qat_service import QATestLLMService
from tools.qa_test.test_analyzer import analyze_test_requirements
from tools.qa_test.test_planner import create_test_plan, prioritize_tests
from tools.qa_test.test_generator import generate_test_cases
from tools.qa_test.test_code_generator import generate_test_code
from core.tracing.service import trace_class

@trace_class
class QATestAgent(BaseAgent):
    """QA/Test Agent responsible for test planning and generation with Team Lead coordination."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"qa_test.{agent_id}")
        self.logger.info(f"Initializing QATestAgent with ID: {agent_id}")
        
        try:
            self.llm_service = QATestLLMService()
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("QATestAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize QATestAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph-based execution flow with Team Lead coordination."""
        self.logger.info("Building QATest processing graph")
        try:
            # Initialize graph
            graph = StateGraph(QATestGraphState)
            
            # Add nodes for core testing workflow
            self.logger.debug("Adding core testing nodes")
            graph.add_node("start", self.receive_input)
            graph.add_node("analyze_requirements", self.analyze_test_requirements)
            graph.add_node("plan_tests", self.plan_tests)
            graph.add_node("generate_test_cases", self.generate_test_cases)
            graph.add_node("generate_test_code", self.generate_test_code)
            
            # Add nodes for Team Lead coordination
            self.logger.debug("Adding Team Lead coordination nodes")
            graph.add_node("receive_task", self.receive_team_lead_task)
            graph.add_node("process_feedback", self.process_team_lead_feedback)
            graph.add_node("update_tests", self.update_tests_from_feedback)
            graph.add_node("report_results", self.report_results_to_team_lead)
            graph.add_node("await_approval", self.await_team_lead_approval)
            
            # Add standard testing flow edges
            self.logger.debug("Adding core testing edges")
            graph.add_edge("start", "analyze_requirements")
            graph.add_edge("analyze_requirements", "plan_tests")
            graph.add_edge("plan_tests", "generate_test_cases")
            graph.add_edge("generate_test_cases", "generate_test_code")
            
            # Add Team Lead coordination edges
            self.logger.debug("Adding Team Lead coordination edges")
            graph.add_edge("start", "receive_task", 
                          condition=self._has_team_lead_task)
            graph.add_edge("receive_task", "analyze_requirements")
            graph.add_edge("generate_test_code", "report_results")
            graph.add_edge("report_results", "await_approval")
            
            # Add feedback handling edges
            graph.add_edge("await_approval", "process_feedback", 
                          condition=self._has_feedback)
            graph.add_edge("process_feedback", "update_tests")
            graph.add_edge("update_tests", "generate_test_cases")
            
            # Add completion edge
            graph.add_edge("await_approval", "end",
                          condition=self._is_approved)
            
            # Set entry point
            graph.set_entry_point("start")
            
            # Compile graph
            compiled_graph = graph.compile()
            self.logger.info("Successfully built and compiled graph with Team Lead coordination")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise
    
    # Condition functions for graph transitions
    
    def _has_team_lead_task(self, state: QATestGraphState) -> bool:
        """Check if the input contains a Team Lead task."""
        return bool(state.get("task_id"))
    
    def _has_feedback(self, state: QATestGraphState) -> bool:
        """Check if feedback has been received from Team Lead."""
        return bool(state.get("feedback"))
    
    def _is_approved(self, state: QATestGraphState) -> bool:
        """Check if the Team Lead has approved the test results."""
        return state.get("status") == "completed"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's workflow with Team Lead coordination support."""
        self.logger.info("Starting QATest workflow execution")
        try:
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            
            # Validate input data
            if "input" not in input_data:
                raise ValueError("Input must contain 'input' field with project description")
                
            if "code" not in input_data:
                raise ValueError("Input must contain 'code' field with code to be tested")
                
            if "specifications" not in input_data:
                self.logger.warning("No specifications provided, will proceed with minimal specifications")
                input_data["specifications"] = {}
            
            # Extract Team Lead coordination fields if present
            task_id = input_data.get("task_id", "")
            task_priority = input_data.get("task_priority", "MEDIUM")
            components_to_test = input_data.get("components_to_test", {})
            dependencies = input_data.get("dependencies", {})
            coordination_metadata = input_data.get("coordination_metadata", {})
            
            # Get language and framework preferences
            programming_language = input_data.get("programming_language", None)
            test_framework = input_data.get("test_framework", None)
            
            # Execute graph with enhanced state
            self.logger.debug("Starting graph execution with Team Lead coordination")
            result = await self.graph.ainvoke({
                "input": input_data.get("input", ""),
                "code": input_data.get("code", {}),
                "specifications": input_data.get("specifications", {}),
                "test_requirements": {},
                "test_plan": {},
                "test_cases": {},
                "test_code": {},
                "programming_language": programming_language,
                "test_framework": test_framework,
                
                # Team Lead coordination fields
                "task_id": task_id,
                "task_priority": task_priority,
                "components_to_test": components_to_test,
                "dependencies": dependencies,
                "coordination_metadata": coordination_metadata,
                "status_report": {},
                "feedback": input_data.get("feedback", {}),
                
                "status": "receiving_task" if task_id else "initialized"
            })
            
            self.logger.info("Workflow completed successfully")
            self.logger.debug(f"Workflow result: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: QATestGraphState) -> Dict[str, Any]:
        """Handles initial input processing."""
        self.logger.info("Starting receive_input phase")
        self.logger.debug(f"Received initial state: {state}")
        
        try:
            input_data = state["input"]
            code = state["code"]
            specifications = state["specifications"]
            
            self.logger.debug(f"Extracted input data: {input_data[:200] if isinstance(input_data, str) else 'Not a string'}...")
            self.logger.debug(f"Code contains {len(code)} components")
            self.logger.debug(f"Specifications contains {len(specifications)} sections")
            
            # Store initial input in short-term memory
            memory_entry = {
                "initial_request": input_data,
                "code_components": list(code.keys()),
                "specification_sections": list(specifications.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in short-term memory: {memory_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            await self.update_status("analyzing_requirements")
            
            result = {
                "input": input_data,
                "code": code,
                "specifications": specifications,
                "test_requirements": {},
                "test_plan": {},
                "test_cases": {},
                "test_code": {},
                "status": "analyzing_requirements"
            }
            self.logger.debug(f"receive_input returning: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="receive_team_lead_task", 
                  metadata={"phase": "coordination"})
    async def receive_team_lead_task(self, state: QATestGraphState) -> Dict[str, Any]:
        """Process task instructions from Team Lead."""
        self.logger.info("Processing Team Lead task instructions")
        
        try:
            # Extract task information
            task_id = state.get("task_id", "")
            task_priority = state.get("task_priority", "MEDIUM")
            components_to_test = state.get("components_to_test", {})
            dependencies = state.get("dependencies", {})
            
            self.logger.info(f"Received task {task_id} with priority {task_priority}")
            self.logger.debug(f"Components to test: {list(components_to_test.keys())}")
            self.logger.debug(f"Dependencies: {dependencies}")
            
            # Store task information in memory
            memory_entry = {
                "type": "team_lead_task",
                "task_id": task_id,
                "task_priority": task_priority,
                "components_to_test": components_to_test,
                "dependencies": dependencies,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=memory_entry
            )
            
            # Update state to move to requirements analysis
            state["status"] = "analyzing_requirements"
            
            self.logger.info(f"Task {task_id} processing completed, proceeding to test requirements analysis")
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing Team Lead task: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_test_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_test_requirements(self, state: QATestGraphState) -> Dict[str, Any]:
        """Analyzes code and specifications to determine test requirements, considering Team Lead directives."""
        self.logger.info("Starting analyze_test_requirements phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            input_description = state["input"]
            code = state["code"]
            specifications = state["specifications"]
            
            # Get Team Lead coordination information
            components_to_test = state.get("components_to_test", {})
            dependencies = state.get("dependencies", {})
            task_priority = state.get("task_priority", "MEDIUM")
            
            # Check working memory for similar previous analysis
            previous_analyses = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"type": "test_requirements"}
            )
            self.logger.debug(f"Found previous analyses: {len(previous_analyses)}")
            
            if previous_analyses:
                self.logger.info("Using previous analysis from working memory")
                test_requirements = previous_analyses[0].content.get("test_requirements", {})
            else:
                self.logger.info("Performing new test requirements analysis")
                
                # Use the test analyzer tool with Team Lead coordination info
                test_requirements = await analyze_test_requirements(
                    code=code,
                    specifications=specifications,
                    input_description=input_description,
                    llm_service=self.llm_service,
                    components_to_test=components_to_test,
                    dependencies=dependencies,
                    task_priority=task_priority
                )
                
                self.logger.debug(f"Test requirements analysis: {test_requirements}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_requirements",
                    "test_requirements": test_requirements,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "components_to_test": components_to_test,
                    "dependencies": dependencies,
                    "task_priority": task_priority
                }
                self.logger.debug(f"Storing in working memory: {working_memory_entry}")
                
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content=working_memory_entry
                )
            
            # Store in long-term memory
            long_term_entry = {
                "type": "test_requirements",
                "input_description": input_description,
                "code_components": list(code.keys()),
                "specification_sections": list(specifications.keys()),
                "test_requirements": test_requirements,
                "components_to_test": components_to_test,
                "dependencies": dependencies,
                "task_priority": task_priority,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "test_requirements",
                    "importance": 0.8
                }
            )
            
            # Update state
            state["test_requirements"] = test_requirements
            state["status"] = "planning_tests"
            
            self.logger.info(f"Test requirements analysis completed with {len(test_requirements.get('functional_test_requirements', []))} functional requirements")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in analyze_test_requirements: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="plan_tests",
                      metadata={"phase": "planning"})
    async def plan_tests(self, state: QATestGraphState) -> Dict[str, Any]:
        """Creates a test plan based on the analyzed requirements, considering Team Lead directives."""
        self.logger.info("Starting plan_tests phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_requirements = state["test_requirements"]
            
            # Get Team Lead directives
            task_priority = state.get("task_priority", "MEDIUM")
            coordination_metadata = state.get("coordination_metadata", {})
            
            # Extract project structure if available
            project_structure = coordination_metadata.get("project_structure", None)
            
            # Check working memory for similar previous test plan
            previous_plans = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"type": "test_plan"}
            )
            self.logger.debug(f"Found previous plans: {len(previous_plans)}")
            
            if previous_plans:
                self.logger.info("Using previous test plan from working memory")
                test_plan = previous_plans[0].content.get("test_plan", {})
            else:
                self.logger.info("Creating new test plan")
                
                # Use the test planner tool with Team Lead directives
                test_plan = await create_test_plan(
                    test_requirements=test_requirements,
                    llm_service=self.llm_service,
                    task_priority=task_priority,
                    project_structure=project_structure
                )
                
                # Prioritize tests
                test_plan = prioritize_tests(
                    test_plan, 
                    priority_factor=get_priority_factor(state)
                )
                
                self.logger.debug(f"Test plan: {test_plan}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_plan",
                    "test_plan": test_plan,
                    "task_priority": task_priority,
                    "project_structure": project_structure,
                    "planning_timestamp": datetime.utcnow().isoformat()
                }
                self.logger.debug(f"Storing in working memory: {working_memory_entry}")
                
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content=working_memory_entry
                )
            
            # Store in long-term memory
            long_term_entry = {
                "type": "test_plan",
                "test_requirements": test_requirements,
                "test_plan": test_plan,
                "task_priority": task_priority,
                "project_structure": project_structure,
                "planning_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "test_plan",
                    "importance": 0.8
                }
            )
            
            # Update state
            state["test_plan"] = test_plan
            state["status"] = "generating_test_cases"
            
            self.logger.info(f"Test planning completed with {len(test_plan.get('unit_tests', []))} unit tests and {len(test_plan.get('integration_tests', []))} integration tests")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in plan_tests: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="generate_test_cases",
                      metadata={"phase": "generation"})
    async def generate_test_cases(self, state: QATestGraphState) -> Dict[str, Any]:
        """Generates detailed test cases based on the test plan, considering Team Lead directives."""
        self.logger.info("Starting generate_test_cases phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_plan = state["test_plan"]
            code = state["code"]
            test_requirements = state["test_requirements"]
            
            # Get Team Lead directives
            components_to_test = state.get("components_to_test", {})
            coordination_metadata = state.get("coordination_metadata", {})
            
            # Extract project structure if available
            project_structure = coordination_metadata.get("project_structure", None)
            
            # Check working memory for similar previous test cases
            previous_cases = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"type": "test_cases"}
            )
            self.logger.debug(f"Found previous test cases: {len(previous_cases)}")
            
            if previous_cases:
                self.logger.info("Using previous test cases from working memory")
                test_cases = previous_cases[0].content.get("test_cases", {})
            else:
                self.logger.info("Generating new test cases")
                
                # Use the test generator tool with Team Lead directives
                test_cases = await generate_test_cases(
                    test_plan=test_plan,
                    code=code,
                    test_requirements=test_requirements,
                    llm_service=self.llm_service,
                    components_to_test=components_to_test,
                    project_structure=project_structure
                )
                
                self.logger.debug(f"Test cases: {test_cases}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_cases",
                    "test_cases": test_cases,
                    "components_to_test": components_to_test,
                    "project_structure": project_structure,
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
                self.logger.debug(f"Storing in working memory: {working_memory_entry}")
                
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content=working_memory_entry
                )
            
            # Store in long-term memory
            long_term_entry = {
                "type": "test_cases",
                "test_plan": test_plan,
                "test_cases": test_cases,
                "components_to_test": components_to_test,
                "project_structure": project_structure,
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "test_cases",
                    "importance": 0.9
                }
            )
            
            # Update state
            state["test_cases"] = test_cases
            state["status"] = "generating_test_code"
            
            self.logger.info(f"Test case generation completed with {len(test_cases.get('unit_test_cases', []))} unit test cases and {len(test_cases.get('integration_test_cases', []))} integration test cases")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_test_cases: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="report_results_to_team_lead",
                    metadata={"phase": "coordination"})
    async def report_results_to_team_lead(self, state: QATestGraphState) -> Dict[str, Any]:
        """Generates and sends a status report to the Team Lead."""
        self.logger.info("Reporting test results to Team Lead")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_requirements = state.get("test_requirements", {})
            test_plan = state.get("test_plan", {})
            test_cases = state.get("test_cases", {})
            test_code = state.get("test_code", {})
            task_id = state.get("task_id", "")
            components_to_test = state.get("components_to_test", {})
            
            # Generate status report
            status_report = await self.llm_service.generate_status_report(
                test_requirements=test_requirements,
                test_plan=test_plan,
                test_cases=test_cases,
                test_code=test_code,
                task_id=task_id,
                components_to_test=components_to_test
            )
            
            # Store status report in memory
            report_memory_entry = {
                "type": "status_report",
                "task_id": task_id,
                "status_report": status_report,
                "report_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=report_memory_entry
            )
            
            # Update state with status report
            state["status_report"] = status_report
            state["status"] = "awaiting_approval"
            
            self.logger.info(f"Status report generated for task {task_id} with completion status: {status_report.get('completion_status', 'unknown')}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error reporting results to Team Lead: {str(e)}", exc_info=True)
            raise
            
    @monitor_operation(operation_type="await_team_lead_approval",
                    metadata={"phase": "coordination"})
    async def await_team_lead_approval(self, state: QATestGraphState) -> Dict[str, Any]:
        """Waits for and processes approval or feedback from Team Lead."""
        self.logger.info("Awaiting Team Lead approval")
        self.logger.debug(f"Received state: {state}")
        
        try:
            # Check if we have explicit approval
            coordination_metadata = state.get("coordination_metadata", {})
            approval_status = coordination_metadata.get("approval_status", None)
            
            if approval_status == "approved":
                self.logger.info("Team Lead has approved the test results")
                state["status"] = "completed"
                
                # Package final deliverable
                deliverable_package = await self.llm_service.package_deliverable(
                    test_requirements=state.get("test_requirements", {}),
                    test_plan=state.get("test_plan", {}),
                    test_cases=state.get("test_cases", {}),
                    test_code=state.get("test_code", {}),
                    task_id=state.get("task_id", "")
                )
                
                # Store deliverable in memory
                deliverable_memory_entry = {
                    "type": "deliverable_package",
                    "deliverable": deliverable_package,
                    "task_id": state.get("task_id", ""),
                    "package_timestamp": datetime.utcnow().isoformat()
                }
                
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content=deliverable_memory_entry
                )
                
                # Add deliverable to state
                state["deliverable_package"] = deliverable_package
                
            elif approval_status == "rejected" or state.get("feedback"):
                self.logger.info("Team Lead has provided feedback, moving to process feedback")
                state["status"] = "processing_feedback"
            else:
                self.logger.info("No explicit approval or feedback yet, maintaining awaiting_approval state")
                # State remains as awaiting_approval
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error awaiting Team Lead approval: {str(e)}", exc_info=True)
            raise
    
    @monitor_operation(operation_type="generate_test_code",
                    metadata={"phase": "code_generation"})
    async def generate_test_code(self, state: QATestGraphState) -> Dict[str, Any]:
        """Generates executable test code based on test cases, considering project structure."""
        self.logger.info("Starting generate_test_code phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_cases = state["test_cases"]
            code = state["code"]
            programming_language = state.get("programming_language")
            test_framework = state.get("test_framework")
            
            # Get project structure from coordination metadata
            coordination_metadata = state.get("coordination_metadata", {})
            project_structure = coordination_metadata.get("project_structure", None)
            
            # Check working memory for similar previous test code
            previous_code = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"type": "test_code"}
            )
            self.logger.debug(f"Found previous test code: {len(previous_code)}")
            
            if previous_code:
                self.logger.info("Using previous test code from working memory")
                test_code = previous_code[0].content.get("test_code", {})
            else:
                self.logger.info("Generating new test code")
                
                # Generate test code with project structure awareness
                test_code = await generate_test_code(
                    test_cases=test_cases,
                    code=code,
                    programming_language=programming_language,
                    test_framework=test_framework,
                    llm_service=self.llm_service,
                    project_structure=project_structure
                )
                
                self.logger.debug(f"Generated test code with {len(test_code)} files")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_code",
                    "test_code": test_code,
                    "programming_language": programming_language,
                    "test_framework": test_framework,
                    "project_structure": project_structure,
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
                self.logger.debug(f"Storing in working memory: {working_memory_entry}")
                
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content=working_memory_entry
                )
            
            # Store in long-term memory
            long_term_entry = {
                "type": "test_code",
                "test_cases": test_cases,
                "test_code": test_code,
                "programming_language": programming_language,
                "test_framework": test_framework,
                "project_structure": project_structure,
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "test_code",
                    "importance": 0.9
                }
            )
            
            # Update state
            state["test_code"] = test_code
            
            # If we're working with Team Lead, move to reporting
            if state.get("task_id"):
                state["status"] = "reporting_results"
            else:
                state["status"] = "completed"
            
            self.logger.info(f"Test code generation completed with {len(test_code)} test files")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_test_code: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="process_team_lead_feedback",
                    metadata={"phase": "coordination"})
    async def process_team_lead_feedback(self, state: QATestGraphState) -> Dict[str, Any]:
        """Processes feedback from Team Lead about test results."""
        self.logger.info("Processing feedback from Team Lead")
        self.logger.debug(f"Received state: {state}")
        
        try:
            feedback = state.get("feedback", {})
            test_plan = state.get("test_plan", {})
            test_cases = state.get("test_cases", {})
            test_code = state.get("test_code", {})
            
            self.logger.info(f"Processing feedback: {feedback.get('feedback_points', [])}")
            
            # Use LLM service to process feedback
            feedback_analysis = await self.llm_service.process_feedback(
                feedback=feedback,
                test_plan=test_plan,
                test_cases=test_cases,
                test_code=test_code
            )
            
            # Store feedback and analysis in memory
            working_memory_entry = {
                "type": "team_lead_feedback",
                "feedback": feedback,
                "feedback_analysis": feedback_analysis,
                "feedback_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store feedback in state for use by update_tests_from_feedback
            state["feedback_analysis"] = feedback_analysis
            state["status"] = "updating_tests"
            
            self.logger.info("Feedback processing completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing Team Lead feedback: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="update_tests_from_feedback",
                    metadata={"phase": "coordination"})
    async def update_tests_from_feedback(self, state: QATestGraphState) -> Dict[str, Any]:
        """Updates test artifacts based on Team Lead feedback."""
        self.logger.info("Updating tests based on feedback")
        self.logger.debug(f"Received state: {state}")
        
        try:
            feedback_analysis = state.get("feedback_analysis", {})
            test_plan = state.get("test_plan", {})
            test_cases = state.get("test_cases", {})
            test_code = state.get("test_code", {})
            
            # Apply test plan changes
            test_plan_changes = feedback_analysis.get("test_plan_changes", [])
            if test_plan_changes:
                self.logger.info(f"Applying {len(test_plan_changes)} changes to test plan")
                
                # Simplified implementation - in a real system, we would have more detailed logic
                # to apply specific changes to the test plan
                # For now, we'll reset to re-generate test cases
                state["status"] = "generating_test_cases"
            
            # Apply test case changes
            test_case_changes = feedback_analysis.get("test_case_changes", [])
            if test_case_changes:
                self.logger.info(f"Applying {len(test_case_changes)} changes to test cases")
                
                # Simplified implementation
                state["status"] = "generating_test_cases"
            
            # Apply test code changes
            test_code_changes = feedback_analysis.get("test_code_changes", [])
            if test_code_changes:
                self.logger.info(f"Applying {len(test_code_changes)} changes to test code")
                
                # Simplified implementation
                state["status"] = "generating_test_code"
            
            # If no specific changes were identified, default to regenerating test cases
            if not any([test_plan_changes, test_case_changes, test_code_changes]):
                self.logger.info("No specific changes identified, defaulting to test case regeneration")
                state["status"] = "generating_test_cases"
            
            # Store update record in memory
            update_memory_entry = {
                "type": "test_updates",
                "feedback_analysis": feedback_analysis,
                "changes_applied": {
                    "test_plan": len(test_plan_changes),
                    "test_cases": len(test_case_changes),
                    "test_code": len(test_code_changes)
                },
                "update_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=update_memory_entry
            )
            
            self.logger.info("Test updates from feedback completed")
            return state
            
        except Exception as e:
            self.logger.error(f"Error updating tests from feedback: {str(e)}", exc_info=True)
            raise