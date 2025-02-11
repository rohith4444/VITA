from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from .task_breakdown import TaskBreakdownService
from .timeline_service import TimelineService
from agents.core.llm.prompts import REQUIREMENT_ANALYSIS_TEMPLATE, TASK_BREAKDOWN_TEMPLATE

class ResourceType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DESIGNER = "designer"
    QA = "qa"
    DEVOPS = "devops"

class TaskComplexity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class ProjectPhase(Enum):
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent responsible for project planning and oversight."""

    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        self.current_project = None
        self.project_plan = None
        self.team_allocation = {}
        self.risk_registry = []
        self.llm_service = LLMService() 
        self.task_service = TaskBreakdownService()
        self.timeline_service = TimelineService()
        
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process initial project input and generate analysis.
        
        Args:
            input_data: Dictionary containing project requirements and constraints
        """
        await self.update_status("analyzing_requirements")
        
        # Store project info in working memory
        await self.update_memory("working", {
            "project_info": input_data,
            "analysis_timestamp": datetime.utcnow()
        })
        
        # Analyze requirements using LLM (to be implemented)
        analysis_result = await self._analyze_requirements(input_data)
        
        # Generate initial project plan
        self.project_plan = await self._generate_project_plan(analysis_result)
        
        return {
            "status": "success",
            "analysis": analysis_result,
            "project_plan": self.project_plan
        }

    async def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project requirements using LLM."""
        try:
            analysis = await self.llm_service.analyze_requirements(
                requirements,
                REQUIREMENT_ANALYSIS_TEMPLATE
            )
            
            # Store analysis in memory
            await self.update_memory("working", {
                "requirement_analysis": analysis,
                "analysis_timestamp": datetime.utcnow()
            })
            
            return analysis
        except Exception as e:
            await self.update_memory("working", {
                "analysis_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise Exception(f"Error in requirement analysis: {str(e)}")
        
    async def _generate_project_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed project plan based on analysis."""
        return {
            "phases": self._break_down_tasks(analysis),
            "timeline": self._create_timeline(analysis),
            "resource_allocation": self._allocate_resources(analysis),
            "risk_mitigation": self._create_risk_mitigation_plan(analysis)
        }

    async def reflect(self) -> Dict[str, Any]:
        """Perform self-reflection on current project status and plans."""
        current_state = await self.get_memory("working")
        
        reflection = {
            "timestamp": datetime.utcnow(),
            "plan_feasibility": self._assess_plan_feasibility(),
            "resource_optimization": self._check_resource_optimization(),
            "risk_assessment": self._update_risk_assessment(),
            "recommendations": []
        }
        
        # Store reflection in episodic memory
        await self.update_memory("episodic", reflection)
        
        return reflection

    async def assign_tasks(self) -> Dict[str, Any]:
        """Assign tasks to team members and tools."""
        if not self.project_plan:
            raise ValueError("Project plan must be generated before assigning tasks")

        assignments = {
            "team_tasks": self._assign_team_tasks(),
            "tool_assignments": self._assign_tools(),
            "timeline": self._create_detailed_timeline()
        }

        await self.update_memory("working", {
            "current_assignments": assignments
        })

        return assignments

    async def monitor_progress(self) -> Dict[str, Any]:
        """Monitor project progress and identify issues."""
        current_state = await self.get_memory("working")
        
        progress_report = {
            "timestamp": datetime.utcnow(),
            "completion_status": self._check_completion_status(),
            "blockers": self._identify_blockers(),
            "timeline_status": self._check_timeline_status()
        }
        
        await self.update_memory("short_term", progress_report)
        
        return progress_report

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive project status report."""
        working_memory = await self.get_memory("working")
        progress_data = await self.get_memory("short_term")
        
        return {
            "timestamp": datetime.utcnow(),
            "project_status": self.status,
            "current_phase": working_memory.get("current_phase"),
            "progress": progress_data,
            "risks": self.risk_registry,
            "next_steps": self._determine_next_steps()
        }

    # Helper methods (to be implemented based on specific needs)
    def _calculate_duration(self, requirements: Dict[str, Any]) -> timedelta:
        """
        Calculate estimated project duration based on requirements and complexity.
        Specific to task management application development.
        """
        base_duration = timedelta(days=30)  # Base duration for a standard task management app
        
        # Adjust based on features
        feature_complexity = {
            "user_auth": 5,
            "task_management": 7,
            "project_organization": 5,
            "collaboration": 7,
            "file_attachments": 3,
            "notifications": 4,
            "analytics": 8,
            "api_integration": 6
        }
        
        total_complexity_days = sum(
            feature_complexity[feature] 
            for feature in requirements.get("features", [])
            if feature in feature_complexity
        )
        
        # Adjust for team size
        team_size = requirements.get("team_size", 3)
        team_adjustment = 1 + (1 / team_size)  # Smaller teams need more time
        
        # Adjust for complexity level
        complexity_multiplier = {
            TaskComplexity.LOW: 0.8,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 1.5
        }.get(requirements.get("complexity", TaskComplexity.MEDIUM), 1.0)
        
        total_duration = base_duration + timedelta(days=total_complexity_days)
        total_duration = total_duration * team_adjustment * complexity_multiplier
        
        return total_duration


    def _identify_required_resources(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify required resources for the task management application.
        """
        # Base resource requirements
        base_resources = [
            {
                "type": ResourceType.FRONTEND,
                "skills": ["React", "TypeScript", "TailwindCSS"],
                "count": 1,
                "allocation_percentage": 100
            },
            {
                "type": ResourceType.BACKEND,
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "count": 1,
                "allocation_percentage": 100
            }
        ]
        
        # Additional resources based on features
        features = requirements.get("features", [])
        
        if "ui_design" in features:
            base_resources.append({
                "type": ResourceType.DESIGNER,
                "skills": ["UI/UX", "Figma"],
                "count": 1,
                "allocation_percentage": 50
            })
        
        if "automated_testing" in features:
            base_resources.append({
                "type": ResourceType.QA,
                "skills": ["Pytest", "Selenium", "API Testing"],
                "count": 1,
                "allocation_percentage": 50
            })
        
        if "deployment" in features:
            base_resources.append({
                "type": ResourceType.DEVOPS,
                "skills": ["Docker", "AWS", "CI/CD"],
                "count": 1,
                "allocation_percentage": 30
            })
        
        return base_resources
    
    def _identify_initial_risks(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify initial project risks for the task management application.
        """
        risks = [
            {
                "id": "RISK-001",
                "category": "Technical",
                "description": "Database performance issues with large number of tasks",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Implement proper indexing and pagination"
            },
            {
                "id": "RISK-002",
                "category": "Technical",
                "description": "Real-time updates scalability challenges",
                "probability": "medium",
                "impact": "medium",
                "mitigation": "Use WebSocket connection pooling and implement fallback mechanisms"
            },
            {
                "id": "RISK-003",
                "category": "Security",
                "description": "Data privacy and access control vulnerabilities",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Implement robust authentication and authorization"
            }
        ]
        
        # Add feature-specific risks
        features = requirements.get("features", [])
        
        if "file_attachments" in features:
            risks.append({
                "id": "RISK-004",
                "category": "Security",
                "description": "File upload vulnerabilities",
                "probability": "high",
                "impact": "high",
                "mitigation": "Implement strict file validation and virus scanning"
            })
        
        if "api_integration" in features:
            risks.append({
                "id": "RISK-005",
                "category": "Integration",
                "description": "Third-party API reliability",
                "probability": "medium",
                "impact": "medium",
                "mitigation": "Implement retry mechanisms and fallback options"
            })
        
        return risks

    async def _break_down_tasks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down the project into detailed tasks, using LLM first and falling back to predefined structure if needed."""
        try:
            # First attempt to get tasks from LLM
            tasks = await self.llm_service.generate_task_breakdown(
                analysis,
                TASK_BREAKDOWN_TEMPLATE
            )
            
            # Store tasks in memory
            await self.update_memory("working", {
                "task_breakdown": tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "source": "llm"
            })
            
            return tasks
            
        except Exception as e:
            # Log the error
            await self.update_memory("working", {
                "breakdown_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            
            # Fall back to predefined task structure
            predefined_tasks = self._get_predefined_tasks()
            
            await self.update_memory("working", {
                "task_breakdown": predefined_tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "source": "predefined"
            })
            
            return predefined_tasks
    def _get_predefined_tasks(self) -> List[Dict[str, Any]]:
        """Predefined task breakdown for fallback."""
        features = self.current_project.get("features", [])
        return self.task_service.generate_detailed_tasks(features)
    
    async def _create_timeline(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create project timeline with critical path."""
        try:
            tasks = await self._break_down_tasks(analysis)
            start_date = datetime.now()
            
            timeline = self.timeline_service.create_timeline(tasks, start_date)
            
            # Store in working memory
            await self.update_memory("working", {
                "timeline": timeline,
                "timeline_timestamp": datetime.utcnow()
            })
            
            return timeline
        except Exception as e:
            await self.update_memory("working", {
                "timeline_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise Exception(f"Error in timeline creation: {str(e)}")

    async def _allocate_resources(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate and balance resources."""
        try:
            timeline = await self._create_timeline(analysis)
            resources = self._identify_required_resources(analysis)
            
            allocation = self.timeline_service.allocate_resources(timeline, resources)
            
            # Store in working memory
            await self.update_memory("working", {
                "resource_allocation": allocation,
                "allocation_timestamp": datetime.utcnow()
            })
            
            return allocation
        except Exception as e:
            await self.update_memory("working", {
                "allocation_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise Exception(f"Error in resource allocation: {str(e)}")