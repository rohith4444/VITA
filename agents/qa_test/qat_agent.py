from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from agents.core.base_agent import BaseAgent
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from .qat_state_graph import QATestGraphState, validate_state, get_next_stage
from .llm.qat_service import QATestLLMService
from tools.qa_test.test_analyzer import analyze_test_requirements
from tools.qa_test.test_planner import create_test_plan, prioritize_tests
from tools.qa_test.test_generator import generate_test_cases
from tools.qa_test.test_code_generator import generate_test_code
from core.tracing.service import trace_class

@trace_class
class QATestAgent(BaseAgent):
    """QA/Test Agent responsible for test planning and generation."""
    
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
        """Build the LangGraph-based execution flow."""
        self.logger.info("Building QATest processing graph")
        try:
            # Initialize graph
            graph = StateGraph(QATestGraphState)
            
            # Add nodes
            self.logger.debug("Adding graph nodes")
            graph.add_node("start", self.receive_input)
            graph.add_node("analyze_requirements", self.analyze_test_requirements)
            graph.add_node("plan_tests", self.plan_tests)
            graph.add_node("generate_test_cases", self.generate_test_cases)
            graph.add_node("generate_test_code", self.generate_test_code)  # New node

            # Add edges
            self.logger.debug("Adding graph edges")
            graph.add_edge("start", "analyze_requirements")
            graph.add_edge("analyze_requirements", "plan_tests")
            graph.add_edge("plan_tests", "generate_test_cases")
            graph.add_edge("generate_test_cases", "generate_test_code")  # New edge
            
            # Set entry point
            graph.set_entry_point("start")
            
            # Compile graph
            compiled_graph = graph.compile()
            self.logger.info("Successfully built and compiled graph")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's workflow."""
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
            
            # Get language and framework preferences if provided
            programming_language = input_data.get("programming_language", None)
            test_framework = input_data.get("test_framework", None)
            
            # Execute graph
            self.logger.debug("Starting graph execution")
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
                "status": "initialized"
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
                "status": "analyzing_requirements"
            }
            self.logger.debug(f"receive_input returning: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_test_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_test_requirements(self, state: QATestGraphState) -> Dict[str, Any]:
        """Analyzes code and specifications to determine test requirements."""
        self.logger.info("Starting analyze_test_requirements phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            input_description = state["input"]
            code = state["code"]
            specifications = state["specifications"]
            
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
                
                # Use the test analyzer tool
                test_requirements = await analyze_test_requirements(
                    code=code,
                    specifications=specifications,
                    input_description=input_description,
                    llm_service=self.llm_service
                )
                
                self.logger.debug(f"Test requirements analysis: {test_requirements}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_requirements",
                    "test_requirements": test_requirements,
                    "analysis_timestamp": datetime.utcnow().isoformat()
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
        """Creates a test plan based on the analyzed requirements."""
        self.logger.info("Starting plan_tests phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_requirements = state["test_requirements"]
            
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
                
                # Use the test planner tool
                test_plan = await create_test_plan(
                    test_requirements=test_requirements,
                    llm_service=self.llm_service
                )
                
                # Prioritize tests
                test_plan = prioritize_tests(test_plan)
                
                self.logger.debug(f"Test plan: {test_plan}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_plan",
                    "test_plan": test_plan,
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
        """Generates detailed test cases based on the test plan."""
        self.logger.info("Starting generate_test_cases phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_plan = state["test_plan"]
            code = state["code"]
            test_requirements = state["test_requirements"]
            
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
                
                # Use the test generator tool
                test_cases = await generate_test_cases(
                    test_plan=test_plan,
                    code=code,
                    test_requirements=test_requirements,
                    llm_service=self.llm_service
                )
                
                self.logger.debug(f"Test cases: {test_cases}")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_cases",
                    "test_cases": test_cases,
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
            state["status"] = "completed"
            
            self.logger.info(f"Test case generation completed with {len(test_cases.get('unit_test_cases', []))} unit test cases and {len(test_cases.get('integration_test_cases', []))} integration test cases")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_test_cases: {str(e)}", exc_info=True)
            raise
    
    
    @monitor_operation(operation_type="generate_test_code",
                    metadata={"phase": "code_generation"})
    async def generate_test_code(self, state: QATestGraphState) -> Dict[str, Any]:
        """Generates executable test code based on test cases."""
        self.logger.info("Starting generate_test_code phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            test_cases = state["test_cases"]
            code = state["code"]
            test_requirements = state["test_requirements"]
            programming_language = state.get("programming_language")
            test_framework = state.get("test_framework")
            
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
                
                # Generate test code
                test_code = await generate_test_code(
                    test_cases=test_cases,
                    code=code,
                    programming_language=programming_language,
                    test_framework=test_framework,
                    llm_service=self.llm_service
                )
                
                self.logger.debug(f"Generated test code with {len(test_code)} files")
                
                # Store in working memory
                working_memory_entry = {
                    "type": "test_code",
                    "test_code": test_code,
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
            state["status"] = "completed"
            
            self.logger.info(f"Test code generation completed with {len(test_code)} test files")
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_test_code: {str(e)}", exc_info=True)
            raise

    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's activities and findings.
        
        Returns:
            Dict[str, Any]: Report containing test analysis, planning, test cases, and test code
        """
        self.logger.info("Starting report generation")
        self.logger.debug(f"Agent ID: {self.agent_id}, Current Status: {self.status}")
        
        try:
            # Retrieve working memory for current state
            working_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING
            )
            self.logger.debug(f"Retrieved working memory entries: {len(working_memory)}")
            
            # Retrieve long-term memory for test code
            long_term_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "test_code"},
                sort_by="timestamp",
                limit=1
            )
            self.logger.debug(f"Retrieved long-term memory entries: {len(long_term_memory)}")
            
            # Compile report
            test_requirements = {}
            test_plan = {}
            test_cases = {}
            test_code = {}
            programming_language = None
            test_framework = None
            
            # Extract data from working memory
            for entry in working_memory:
                content = entry.content
                if "test_requirements" in content:
                    test_requirements = content["test_requirements"]
                if "test_plan" in content:
                    test_plan = content["test_plan"]
                if "test_cases" in content:
                    test_cases = content["test_cases"]
                if "test_code" in content:
                    test_code = content["test_code"]
            
            # If test code not found in working memory, check long-term memory
            if not test_code and long_term_memory:
                test_code = long_term_memory[0].content.get("test_code", {})
                programming_language = long_term_memory[0].content.get("programming_language")
                test_framework = long_term_memory[0].content.get("test_framework")
            
            # Generate summary statistics
            unit_test_count = len(test_cases.get("unit_test_cases", []))
            integration_test_count = len(test_cases.get("integration_test_cases", []))
            total_test_count = unit_test_count + integration_test_count
            
            test_code_files_count = len(test_code)
            
            functional_req_count = len(test_requirements.get("functional_test_requirements", []))
            integration_req_count = len(test_requirements.get("integration_test_requirements", []))
            security_req_count = len(test_requirements.get("security_test_requirements", []))
            performance_req_count = len(test_requirements.get("performance_test_requirements", []))
            
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "summary": {
                    "test_requirements": {
                        "functional": functional_req_count,
                        "integration": integration_req_count,
                        "security": security_req_count,
                        "performance": performance_req_count,
                        "total": functional_req_count + integration_req_count + security_req_count + performance_req_count
                    },
                    "test_cases": {
                        "unit": unit_test_count,
                        "integration": integration_test_count,
                        "total": total_test_count
                    },
                    "test_code": {
                        "files": test_code_files_count,
                        "programming_language": programming_language,
                        "test_framework": test_framework
                    }
                },
                "test_requirements": test_requirements,
                "test_plan": test_plan,
                "test_cases": test_cases,
                "test_code": test_code
            }
            
            self.logger.info(f"Report generation completed with {total_test_count} test cases and {test_code_files_count} test code files")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            # Return basic report on error
            return {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "error": str(e)
            }