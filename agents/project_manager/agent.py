from typing import Dict, Any
import json
from datetime import datetime
from langgraph.graph import StateGraph
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from .state_graph import ProjectManagerGraphState
from tools.project_manager.generate_task_breakdown import generate_task_breakdown
from tools.project_manager.resource_allocator import allocate_resources
from tools.project_manager.timeline_generator import estimate_time

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent responsible for project planning."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"project_manager.{agent_id}")
        self.logger.info(f"Initializing ProjectManagerAgent with ID: {agent_id}")
        
        try:
            self.llm_service = LLMService()
            
            # Build the processing graph
            self.graph = self._build_graph()
            self.logger.info("ProjectManagerAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ProjectManagerAgent: {str(e)}", exc_info=True)
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph-based execution flow."""
        self.logger.info("Building ProjectManager processing graph")
        try:
            # Initialize graph
            graph = StateGraph(ProjectManagerGraphState)
            
            # Add nodes
            self.logger.debug("Adding graph nodes")
            graph.add_node("start", self.receive_input)
            graph.add_node("analyze_requirements", self.analyze_requirements)
            graph.add_node("generate_project_plan", self.generate_project_plan)

            # Add edges
            self.logger.debug("Adding graph edges")
            graph.add_edge("start", "analyze_requirements")
            graph.add_edge("analyze_requirements", "generate_project_plan")
            
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
        self.logger.info("Starting ProjectManager workflow execution")
        try:
            self.logger.debug(f"Input data: {str(input_data)[:200]}...")
            
            # Execute graph
            self.logger.debug("Starting graph execution")
            result = await self.graph.ainvoke({
                "input": input_data.get("input"),
                "status": input_data.get("status", "initialized")
            })
            
            self.logger.info("Workflow completed successfully")
            self.logger.debug(f"Workflow result: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during workflow execution: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="receive_input", 
                  metadata={"phase": "initialization"})
    async def receive_input(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Handles project input processing."""
        self.logger.info("Starting receive_input phase")
        self.logger.debug(f"Received initial state: {state}")
        
        try:
            input_data = state["input"]
            self.logger.debug(f"Extracted input data: {input_data[:200]}...")  # Log first 200 chars
            
            # Store initial request in short-term memory
            memory_entry = {
                "initial_request": input_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in short-term memory: {memory_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content=memory_entry
            )
            
            self.update_status("receiving_project_input")
            
            result = {"input": input_data, "status": "analyzing_requirements"}
            self.logger.debug(f"receive_input returning: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in receive_input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="analyze_requirements",
        metadata={
            "phase": "analysis",
            "memory_operations": {
                "working_memory": "read_write",
                "long_term_memory": "write",
            }
        }
    )
    async def analyze_requirements(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Analyzes and structures project requirements."""
        self.logger.info("Starting analyze_requirements phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            project_description = state["input"]
            self.logger.debug(f"Project description to analyze: {project_description[:200]}...")
            
            # Check working memory for similar previous analysis
            previous_analyses = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"project_description": project_description}
            )
            self.logger.debug(f"Found previous analyses: {previous_analyses}")
            
            if previous_analyses:
                self.logger.info("Using previous analysis from working memory")
                response = previous_analyses[0].content
            else:
                self.logger.info("Performing new requirements analysis")
                response = await self.llm_service.analyze_requirements(project_description)
                self.logger.debug(f"LLM analysis response: {response}")
                
                # Store in working memory
                working_memory_entry = {
                    "project_description": project_description,
                    "requirement_analysis": response,
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
                "project_description": project_description,
                "requirement_analysis": response,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "requirement_analysis",
                    "importance": 0.8
                }
            )
            
            result = {"requirements": response, "status": "generating_project_plan"}
            self.logger.debug(f"analyze_requirements returning: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in analyze_requirements: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="generate_project_plan",
        metadata={
            "phase": "planning",
            "memory_operations": {
                "long_term_memory": "read_write",
                "working_memory": "write"
            }
        }
    )
    async def generate_project_plan(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Generates a structured project plan."""
        self.logger.info("Starting generate_project_plan phase")
        self.logger.debug(f"Received state: {state}")
        
        try:
            requirements = state["requirements"]
            self.logger.debug(f"Requirements to process: {requirements}")

            # Extract restructured requirements and features
            if isinstance(requirements, dict) and 'restructured_requirements' in requirements and 'features' in requirements:
                problem_statement = requirements['restructured_requirements']
                features = requirements['features']
            else:
                self.logger.error("Invalid requirements format")
                raise ValueError("Requirements missing required fields")

            self.logger.debug(f"Problem statement: {problem_statement[:200]}...")
            self.logger.debug(f"Features: {features}")
            
            # Generate new plan
            milestones = await generate_task_breakdown(
                problem_statement,
                features,
                self.llm_service
            )
            self.logger.debug(f"Generated milestones: {milestones}")
            
            resource_plan = allocate_resources(milestones)
            self.logger.debug(f"Resource allocation: {resource_plan}")
            
            timeline_options = [
                {"configuration": "1 Full Stack Developer", "total_duration": estimate_time(milestones, 1)},
                {"configuration": "2 Full Stack Developers", "total_duration": estimate_time(milestones, 2)}
            ]
            self.logger.debug(f"Timeline options: {timeline_options}")
            
            project_plan = {
                "milestones": milestones,
                "resource_allocation": resource_plan,
                "timeline_options": timeline_options
            }
            self.logger.debug(f"Complete project plan: {project_plan}")
            
            # Store in working memory
            working_memory_entry = {
                "active_project_plan": project_plan,
                "current_phase": "planning",
                "last_updated": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in working memory: {working_memory_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content=working_memory_entry
            )
            
            # Store in long-term memory
            long_term_entry = {
                "requirement_analysis": requirements,
                "project_plan": project_plan,
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            self.logger.debug(f"Storing in long-term memory: {long_term_entry}")
            
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=long_term_entry,
                metadata={
                    "type": "project_plan",
                    "importance": 0.9,
                    "contains_milestones": True
                }
            )
            
            result = {"project_plan": project_plan, "status": "completed"}
            self.logger.debug(f"generate_project_plan returning: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in generate_project_plan: {str(e)}", exc_info=True)
            raise


    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the agent's activities and findings.
        
        Returns:
            Dict[str, Any]: Report containing project analysis and planning details
        """
        self.logger.info("Starting report generation")
        self.logger.debug(f"Agent ID: {self.agent_id}, Current Status: {self.status}")
        
        try:
            # Retrieve working memory for current state
            self.logger.debug("Retrieving working memory")
            working_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING
            )
            self.logger.debug(f"Retrieved working memory entries: {len(working_memory)}")
            if working_memory:
                self.logger.debug(f"Working memory content sample: {working_memory[0].content}")
            
            # Retrieve long-term memory for project plan
            self.logger.debug("Retrieving long-term memory for project plan")
            long_term_memory = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"type": "project_plan"},
                sort_by="timestamp",
                limit=1
            )
            self.logger.debug(f"Retrieved long-term memory entries: {len(long_term_memory)}")
            if long_term_memory:
                self.logger.debug(f"Long-term memory content sample: {long_term_memory[0].content}")
            
            # Compile report
            self.logger.debug("Compiling report")
            current_state = working_memory[0].content if working_memory else {}
            project_plan = long_term_memory[0].content if long_term_memory else {}
            
            report = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": self.status,
                "current_state": current_state,
                "project_plan": project_plan,
                "metrics": {
                    "memory_usage": {
                        "working_memory": len(working_memory),
                        "long_term_memory": len(long_term_memory)
                    },
                    "execution_status": {
                        "current_phase": current_state.get("current_phase", "unknown"),
                        "last_updated": current_state.get("last_updated", "unknown")
                    }
                }
            }
            
            self.logger.debug(f"Generated report structure: {json.dumps(report, indent=2)}")
            self.logger.info("Report generation completed successfully")
            
            # Log memory metrics
            self.logger.info(f"Memory usage - Working: {len(working_memory)}, Long-term: {len(long_term_memory)}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}", exc_info=True)
            self.logger.debug("Exception details:", exc_info=True)  # Full traceback
            raise