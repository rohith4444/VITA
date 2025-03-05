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
from .fsd_state_graph import FullStackDeveloperGraphState, validate_state, get_next_stage
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
            
            # Add nodes
            self.logger.debug("Adding graph nodes")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_requirements", self.analyze_requirements)
            builder.add_node("design_solution", self.design_solution)
            builder.add_node("generate_code", self.generate_code)
            builder.add_node("prepare_documentation", self.prepare_documentation)

            # Add edges
            self.logger.debug("Adding graph edges")
            builder.add_edge("start", "analyze_requirements")
            builder.add_edge("analyze_requirements", "design_solution")
            builder.add_edge("design_solution", "generate_code")
            builder.add_edge("generate_code", "prepare_documentation")
            
            # Set entry point
            builder.set_entry_point("start")
            
            # Compile graph
            compiled_graph = builder.compile()
            self.logger.info("Successfully built and compiled graph")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise

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
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke({
                "input": input_data["input"],
                "requirements": {},
                "solution_design": {},
                "generated_code": {},
                "documentation": {},
                "status": "initialized"
            })
            
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
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            await self.update_status("analyzing_requirements")
            
            # Update state status
            state["status"] = "analyzing_requirements"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_requirements(self, state: FullStackDeveloperGraphState) -> Dict[str, Any]:
        """Analyze the task specification to extract requirements."""
        self.logger.info("Starting analyze_requirements phase")
        
        try:
            task_specification = state["input"]
            
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
            state["status"] = "completed"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in prepare_documentation: {str(e)}", exc_info=True)
            raise

    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's activities and findings.
        
        Returns:
            Dict[str, Any]: Report containing code and documentation
        """
        self.logger.info("Starting report generation")
        
        try:
            # Retrieve working memory for current state
            working_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING
            )
            
            # Retrieve long-term memory for key artifacts
            long_term_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                sort_by="timestamp"
            )
            
            # Extract relevant information
            requirements = {}
            solution_design = {}
            code_summary = {}
            documentation = {}
            
            for entry in working_memory:
                content = entry.content
                phase = content.get("phase", "")
                
                if phase == "requirements":
                    requirements = content.get("requirements", {})
                elif phase == "solution_design":
                    solution_design = content.get("solution_design", {})
                elif phase == "code_generation":
                    code_summary = {
                        component: list(files.keys())
                        for component, files in content.get("generated_code", {}).items()
                    }
                elif phase == "documentation":
                    documentation = content.get("documentation", {})
            
            # Calculate statistics
            tech_stack = {}
            if "technology_recommendations" in requirements:
                tech_stack = requirements["technology_recommendations"]
            
            features_count = len(requirements.get("features", []))
            component_count = len(solution_design.keys())
            file_count = sum(len(files) for files in code_summary.values())
            doc_count = len(documentation)
            
            # Compile report
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "summary": {
                    "features_implemented": features_count,
                    "components_designed": component_count,
                    "files_generated": file_count,
                    "documentation_files": doc_count
                },
                "technology_stack": tech_stack,
                "code_structure": code_summary,
                "documentation": list(documentation.keys()),
                "execution_time": {
                    "started_at": long_term_memory[0].timestamp.isoformat() if long_term_memory else "unknown",
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            
            self.logger.info("Report generation completed successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise