from typing import Dict, Any
from datetime import datetime
from core.logging.logger import setup_logger
from core.monitoring.decorators import monitor_operation
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from memory.memory_manager import MemoryManager
from memory.base import MemoryType
from tools.project_manager.generate_task_breakdown import generate_task_breakdown
from tools.project_manager.resource_allocator import allocate_resources
from tools.project_manager.timeline_generator import estimate_time
from langgraph.graph import StateGraph, END
from state_graph import ProjectManagerGraphState

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent responsible for project planning using LangGraph."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        self.logger = setup_logger(f"project_manager.{agent_id}")
        self.logger.info(f"Initializing ProjectManagerAgent with ID: {agent_id}")
        try:
            super().__init__(agent_id, name, memory_manager)
            self.llm_service = LLMService()
            self.logger.info("ProjectManagerAgent initialization completed")
        except Exception as e:
            self.logger.error(f"Failed to initialize ProjectManagerAgent: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="graph_setup")
    def add_graph_nodes(self, graph: StateGraph) -> None:
        """Defines processing nodes for the Project Manager Agent."""
        self.logger.debug("Adding graph nodes to ProjectManagerAgent")
        try:
            graph.add_node("start", self.receive_input)
            graph.add_node("analyze_requirements", self.analyze_requirements)
            graph.add_node("generate_project_plan", self.generate_project_plan)

            graph.add_edge("start", "analyze_requirements")
            graph.add_edge("analyze_requirements", "generate_project_plan")
            graph.add_edge("generate_project_plan", END)
            
            self.logger.info("Successfully added all graph nodes and edges")
        except Exception as e:
            self.logger.error(f"Failed to add graph nodes: {str(e)}", exc_info=True)
            raise

    @monitor_operation(operation_type="receive_input", 
                      metadata={"phase": "initialization"})
    async def receive_input(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Handles project input processing."""
        self.logger.info("Receiving project input")
        try:
            input_data = state["input"]
            
            # Store initial request in short-term memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "initial_request": input_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.update_status("receiving_project_input")
            return {"input": input_data, "status": "analyzing_requirements"}
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="analyze_requirements",
        metadata={
            "phase": "analysis",
            "memory_operations": {
                "working_memory": "read_write",
                "long_term_memory": "write",
            },
            "tools_used": [],
            "expected_outputs": ["structured_requirements", "features_list"]
        }
    )
    async def analyze_requirements(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Analyzes and structures project requirements."""
        self.logger.info("Analyzing project requirements")
        try:
            project_description = state["input"]
            
            # Check working memory for similar previous analysis
            previous_analyses = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                query={"project_description": project_description}
            )
            
            if previous_analyses:
                self.logger.info("Found previous analysis in working memory")
                response = previous_analyses[0].content
            else:
                # Perform new analysis
                response = await self.llm_service.analyze_requirements(project_description)
                
                # Store in working memory for active processing
                await self.memory_manager.store(
                    agent_id=self.agent_id,
                    memory_type=MemoryType.WORKING,
                    content={
                        "project_description": project_description,
                        "requirement_analysis": response,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Store in long-term memory for future reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "project_description": project_description,
                    "requirement_analysis": response,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "type": "requirement_analysis",
                    "importance": 0.8
                }
            )
            
            return {"requirements": response, "status": "generating_project_plan"}
            
        except Exception as e:
            self.logger.error(f"Error analyzing requirements: {str(e)}", exc_info=True)
            raise

    @monitor_operation(
        operation_type="generate_project_plan",
        metadata={
            "phase": "planning",
            "memory_operations": {
                "long_term_memory": "read_write",
                "working_memory": "write"
            },
            "tools_used": [
                "task_breakdown_generator",
                "resource_allocator",
                "timeline_estimator"
            ],
            "tool_configurations": {
                "reference_plans_enabled": True,
                "resource_allocation_mode": "skill_based",
                "timeline_estimation_type": "effort_based"
            },
            "expected_outputs": ["milestones", "resource_plan", "timeline_options"]
        }
    )
    async def generate_project_plan(self, state: ProjectManagerGraphState) -> Dict[str, Any]:
        """Generates a structured project plan."""
        self.logger.info("Generating project plan")
        try:
            requirements = state["requirements"]
            
            # Check long-term memory for similar projects
            similar_projects = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query={"requirement_analysis": requirements},
                sort_by="timestamp",
                limit=5
            )
            
            # Use similar projects to inform current planning
            reference_plans = [
                proj.content.get("project_plan")
                for proj in similar_projects
                if "project_plan" in proj.content
            ]
            
            # Generate new plan
            milestones = await generate_task_breakdown(
                requirements,
                self.llm_service,
                reference_plans=reference_plans
            )
            
            resource_plan = await allocate_resources(milestones)
            timeline_options = [
                {"configuration": "1 Full Stack Developer", "total_duration": estimate_time(milestones, 1)},
                {"configuration": "2 Full Stack Developers", "total_duration": estimate_time(milestones, 2)}
            ]
            
            project_plan = {
                "milestones": milestones,
                "resource_allocation": resource_plan,
                "timeline_options": timeline_options
            }
            
            # Store in working memory for active use
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "active_project_plan": project_plan,
                    "current_phase": "planning",
                    "last_updated": datetime.utcnow().isoformat()
                }
            )
            
            # Store in long-term memory for future reference
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "requirement_analysis": requirements,
                    "project_plan": project_plan,
                    "generation_timestamp": datetime.utcnow().isoformat(),
                    "reference_projects": [p.content.get("project_description") for p in similar_projects]
                },
                metadata={
                    "type": "project_plan",
                    "importance": 0.9,
                    "contains_milestones": True
                }
            )
            
            return {"project_plan": project_plan, "status": "completed"}
            
        except Exception as e:
            self.logger.error(f"Error generating project plan: {str(e)}", exc_info=True)
            raise