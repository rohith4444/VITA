from typing import Dict, Any, List
from datetime import datetime
from core.logging.logger import setup_logger
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from memory.memory_manager import MemoryManager
from tools.project_manager.generate_task_breakdown import generate_task_breakdown
from tools.project_manager.task_estimator import estimate_task_complexity
from tools.project_manager.resource_allocator import allocate_resources
from tools.project_manager.timeline_generator import estimate_time
from langgraph.graph import StateGraph, END

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent responsible for project planning using LangGraph."""
    
    def __init__(self, agent_id: str, name: str, memory_manager: MemoryManager):
        super().__init__(agent_id, name, memory_manager)
        self.logger = setup_logger(f"project_manager.{self.agent_id}")
        self.llm_service = LLMService()
    
    def add_graph_nodes(self, graph: StateGraph) -> None:
        """Defines processing nodes for the Project Manager Agent."""
        
        graph.add_node("start", self.receive_input)
        graph.add_node("analyze_requirements", self.analyze_requirements)
        graph.add_node("generate_project_plan", self.generate_project_plan)

        graph.add_edge("start", "analyze_requirements")
        graph.add_edge("analyze_requirements", "generate_project_plan")
        graph.add_edge("generate_project_plan", END)

    def receive_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles project input processing."""
        self.logger.info("Receiving project input")
        input_data = state["input"]
        self.update_status("receiving_project_input")
        return {"input": input_data, "status": "analyzing_requirements"}

    def analyze_requirements(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes and structures project requirements."""
        self.logger.info("Analyzing project requirements")
        project_description = state["input"]
        response = self.llm_service.analyze_requirements(project_description)
        self.update_memory("working", {"requirement_analysis": response})
        return {"requirements": response, "status": "generating_project_plan"}

    def generate_project_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a structured project plan."""
        self.logger.info("Generating project plan")
        requirements = state["requirements"]
        milestones = generate_task_breakdown(requirements, self.llm_service)
        resource_plan = allocate_resources(milestones)
        timeline_options = [
            {"configuration": "1 Full Stack Developer", "total_duration": estimate_time(milestones, 1)},
            {"configuration": "2 Full Stack Developers", "total_duration": estimate_time(milestones, 2)}
        ]
        project_plan = {"milestones": milestones, "resource_allocation": resource_plan, "timeline_options": timeline_options}
        self.update_memory("working", {"project_plan": project_plan})
        return {"project_plan": project_plan, "status": "completed"}
