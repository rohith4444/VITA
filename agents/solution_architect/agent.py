from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation, monitor_llm
from agents.core.base_agent import BaseAgent
from agents.solution_architect.llm.service import LLMService
from agents.core.graph.graph_builder import WorkflowGraphBuilder  
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from .state_graph import SolutionArchitectGraphState, validate_state, get_next_stage
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
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("SolutionArchitectAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SolutionArchitectAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph-based execution flow."""
        self.logger.info("Building SolutionArchitect processing graph")
        try:
            # Initialize graph builder
            builder = WorkflowGraphBuilder(SolutionArchitectGraphState)
            
            # Store builder for visualization
            self._graph_builder = builder
            
            # Add nodes
            self.logger.debug("Adding graph nodes")
            builder.add_node("start", self.receive_input)
            builder.add_node("analyze_requirements", self.analyze_requirements)
            builder.add_node("select_tech_stack", self.select_tech_stack)
            builder.add_node("design_architecture", self.design_architecture)
            builder.add_node("validate_architecture", self.validate_architecture)
            builder.add_node("generate_specifications", self.generate_specifications)

            # Add edges
            self.logger.debug("Adding graph edges")
            builder.add_edge("start", "analyze_requirements")
            builder.add_edge("analyze_requirements", "select_tech_stack")
            builder.add_edge("select_tech_stack", "design_architecture")
            builder.add_edge("design_architecture", "validate_architecture")
            builder.add_edge("validate_architecture", "generate_specifications")
            
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
        self.logger.info("Starting SolutionArchitect workflow execution")
        try:
            # Ensure input contains required fields
            if "input" not in input_data:
                raise ValueError("Input must contain 'input' field with project description")
                
            if "project_plan" not in input_data:
                raise ValueError("Input must contain 'project_plan' field with project plan")
            
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke({
                "input": input_data["input"],
                "project_plan": input_data["project_plan"],
                "tech_stack": {},
                "architecture_design": {},
                "validation_results": {},
                "specifications": {},
                "status": "initialized"
            })
            
            self.logger.info("Workflow completed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """Handles project input processing."""
        self.logger.info("Starting receive_input phase")
        
        try:
            input_data = state["input"]
            project_plan = state["project_plan"]
            
            self.logger.debug(f"Extracted input data: {input_data[:200]}...")
            self.logger.debug(f"Project plan: {str(project_plan)[:200]}...")
            
            # Store initial request in short-term memory
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
            
            await self.update_status("analyzing_requirements")
            
            result = {
                "input": input_data, 
                "project_plan": project_plan, 
                "status": "analyzing_requirements",
                "tech_stack": {},
                "architecture_design": {},
                "validation_results": {},
                "specifications": {}
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="analyze_requirements",
                      metadata={"phase": "analysis"})
    async def analyze_requirements(self, state: SolutionArchitectGraphState) -> Dict[str, Any]:
        """Analyzes and structures project requirements."""
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
            
            # Process requirements with LLM
            requirements_analysis = await self.llm_service.analyze_architecture_requirements(
                project_description=project_description,
                features=features
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
        """Selects appropriate technology stack for the project."""
        self.logger.info("Starting select_tech_stack phase")
        
        try:
            project_description = state["input"]
            project_plan = state["project_plan"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Use technology selector tool
            tech_stack = await select_tech_stack(
                project_description=project_description,
                requirements=requirements_analysis,
                llm_service=self.llm_service
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
        """Designs system architecture based on requirements and tech stack."""
        self.logger.info("Starting design_architecture phase")
        
        try:
            project_description = state["input"]
            tech_stack = state["tech_stack"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Generate architecture design using LLM
            architecture_design = await self.llm_service.generate_architecture_design(
                project_description=project_description,
                tech_stack=tech_stack,
                requirements=requirements_analysis
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
        """Validates the architecture against requirements and best practices."""
        self.logger.info("Starting validate_architecture phase")
        
        try:
            architecture_design = state["architecture_design"]
            requirements_analysis = state.get("requirements_analysis", {})
            
            # Use architecture validator tool
            validation_results = await validate_architecture(
                architecture_design=architecture_design,
                requirements=requirements_analysis,
                llm_service=self.llm_service
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
        """Generates detailed technical specifications."""
        self.logger.info("Starting generate_specifications phase")
        
        try:
            architecture_design = state["architecture_design"]
            tech_stack = state["tech_stack"]
            validation_results = state["validation_results"]
            
            # Use specification generator tool
            specifications = await generate_specifications(
                architecture_design=architecture_design,
                tech_stack=tech_stack,
                validation_results=validation_results,
                llm_service=self.llm_service
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
            state["status"] = "completed"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in generate_specifications: {str(e)}", exc_info=True)
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
            
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "tech_stack": current_state.get("tech_stack", {}),
                "architecture_design": architecture_design.get("architecture_design", {}),
                "validation_results": current_state.get("validation_results", {}),
                "specifications": specifications.get("specifications", {})
            }
            
            self.logger.info("Report generation completed successfully")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise