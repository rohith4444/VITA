from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from core.logging.logger import setup_logger
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from .task_breakdown import TaskBreakdownService
from .timeline_service import TimelineService
from agents.core.llm.prompts import REQUIREMENT_ANALYSIS_TEMPLATE, TASK_BREAKDOWN_TEMPLATE

# Enum definitions remain the same
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
        # Initialize project manager specific logger
        self.pm_logger = setup_logger(f"project_manager.{self.agent_id}")
        self.pm_logger.info(f"Project Manager Agent initialized: {self.name}")
        
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process initial project input and generate analysis."""
        self.pm_logger.info("Processing new project input")
        self.pm_logger.debug(f"Input data: {input_data}")
        
        await self.update_status("analyzing_requirements")
        
        try:
            # Store project info in working memory
            await self.update_memory("working", {
                "project_info": input_data,
                "analysis_timestamp": datetime.utcnow()
            })
            
            # Analyze requirements using LLM
            self.pm_logger.info("Starting requirements analysis")
            analysis_result = await self._analyze_requirements(input_data)
            
            # Generate initial project plan
            self.pm_logger.info("Generating project plan")
            self.project_plan = await self._generate_project_plan(analysis_result)
            
            self.pm_logger.info("Project input processing completed successfully")
            return {
                "status": "success",
                "analysis": analysis_result,
                "project_plan": self.project_plan
            }
        except Exception as e:
            self.pm_logger.error(f"Error processing project input: {str(e)}")
            raise

    async def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project requirements using LLM."""
        self.pm_logger.info("Analyzing requirements")
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
            
            self.pm_logger.info("Requirements analysis completed successfully")
            return analysis
        except Exception as e:
            self.pm_logger.error(f"Error in requirement analysis: {str(e)}")
            await self.update_memory("working", {
                "analysis_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise

    async def _generate_project_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed project plan based on analysis."""
        self.pm_logger.info("Generating project plan")
        try:
            plan = {
                "phases": await self._break_down_tasks(analysis),
                "timeline": await self._create_timeline(analysis),
                "resource_allocation": await self._allocate_resources(analysis),
                "risk_mitigation": self._create_risk_mitigation_plan(analysis)
            }
            self.pm_logger.info("Project plan generated successfully")
            return plan
        except Exception as e:
            self.pm_logger.error(f"Error generating project plan: {str(e)}")
            raise


    async def reflect(self) -> Dict[str, Any]:
        """Perform self-reflection on current project status and plans."""
        self.pm_logger.info("Starting project reflection")
        try:
            current_state = await self.get_memory("working")
            self.pm_logger.debug("Retrieved current working memory state")
            
            reflection = {
                "timestamp": datetime.utcnow(),
                "plan_feasibility": self._assess_plan_feasibility(),
                "resource_optimization": self._check_resource_optimization(),
                "risk_assessment": self._update_risk_assessment(),
                "recommendations": []
            }
            
            # Store reflection in episodic memory
            await self.update_memory("episodic", reflection)
            self.pm_logger.info("Reflection completed and stored in episodic memory")
            
            return reflection
        except Exception as e:
            self.pm_logger.error(f"Error during reflection: {str(e)}")
            raise

    async def assign_tasks(self) -> Dict[str, Any]:
        """Assign tasks to team members and tools."""
        self.pm_logger.info("Starting task assignment")
        
        if not self.project_plan:
            self.pm_logger.error("Cannot assign tasks: Project plan not generated")
            raise ValueError("Project plan must be generated before assigning tasks")

        try:
            self.pm_logger.debug("Creating task assignments")
            assignments = {
                "team_tasks": self._assign_team_tasks(),
                "tool_assignments": self._assign_tools(),
                "timeline": self._create_detailed_timeline()
            }

            await self.update_memory("working", {
                "current_assignments": assignments
            })
            self.pm_logger.info("Task assignments completed successfully")

            return assignments
        except Exception as e:
            self.pm_logger.error(f"Error during task assignment: {str(e)}")
            raise

    async def monitor_progress(self) -> Dict[str, Any]:
        """Monitor project progress and identify issues."""
        self.pm_logger.info("Starting progress monitoring")
        try:
            current_state = await self.get_memory("working")
            self.pm_logger.debug("Retrieved current state from working memory")
            
            self.pm_logger.debug("Generating progress report")
            progress_report = {
                "timestamp": datetime.utcnow(),
                "completion_status": self._check_completion_status(),
                "blockers": self._identify_blockers(),
                "timeline_status": self._check_timeline_status()
            }
            
            await self.update_memory("short_term", progress_report)
            self.pm_logger.info("Progress report generated and stored")
            
            return progress_report
        except Exception as e:
            self.pm_logger.error(f"Error monitoring progress: {str(e)}")
            raise

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive project status report."""
        self.pm_logger.info("Generating project status report")
        try:
            working_memory = await self.get_memory("working")
            progress_data = await self.get_memory("short_term")
            self.pm_logger.debug("Retrieved memory data for report generation")
            
            report = {
                "timestamp": datetime.utcnow(),
                "project_status": self.status,
                "current_phase": working_memory.get("current_phase"),
                "progress": progress_data,
                "risks": self.risk_registry,
                "next_steps": self._determine_next_steps()
            }
            
            self.pm_logger.info("Project status report generated successfully")
            return report
        except Exception as e:
            self.pm_logger.error(f"Error generating project report: {str(e)}")
            raise

    def _calculate_duration(self, requirements: Dict[str, Any]) -> timedelta:
        """Calculate estimated project duration based on requirements and complexity."""
        self.pm_logger.debug("Calculating project duration")
        try:
            base_duration = timedelta(days=30)
            
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
            
            team_size = requirements.get("team_size", 3)
            team_adjustment = 1 + (1 / team_size)
            
            complexity_multiplier = {
                TaskComplexity.LOW: 0.8,
                TaskComplexity.MEDIUM: 1.0,
                TaskComplexity.HIGH: 1.5
            }.get(requirements.get("complexity", TaskComplexity.MEDIUM), 1.0)
            
            total_duration = base_duration + timedelta(days=total_complexity_days)
            total_duration = total_duration * team_adjustment * complexity_multiplier
            
            self.pm_logger.info(f"Calculated project duration: {total_duration.days} days")
            return total_duration
        except Exception as e:
            self.pm_logger.error(f"Error calculating project duration: {str(e)}")
            raise

    def _identify_required_resources(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify required resources for the task management application."""
        self.pm_logger.info("Identifying required resources")
        try:
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
            
            features = requirements.get("features", [])
            self.pm_logger.debug(f"Analyzing features for resource requirements: {features}")
            
            # Add additional resources based on features
            if "ui_design" in features:
                self.pm_logger.debug("Adding UI/UX designer resource")
                base_resources.append({
                    "type": ResourceType.DESIGNER,
                    "skills": ["UI/UX", "Figma"],
                    "count": 1,
                    "allocation_percentage": 50
                })
            
            if "automated_testing" in features:
                self.pm_logger.debug("Adding QA resource")
                base_resources.append({
                    "type": ResourceType.QA,
                    "skills": ["Pytest", "Selenium", "API Testing"],
                    "count": 1,
                    "allocation_percentage": 50
                })
            
            if "deployment" in features:
                self.pm_logger.debug("Adding DevOps resource")
                base_resources.append({
                    "type": ResourceType.DEVOPS,
                    "skills": ["Docker", "AWS", "CI/CD"],
                    "count": 1,
                    "allocation_percentage": 30
                })
            
            self.pm_logger.info(f"Identified {len(base_resources)} required resources")
            return base_resources
        except Exception as e:
            self.pm_logger.error(f"Error identifying required resources: {str(e)}")
            raise

    def _identify_initial_risks(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify initial project risks."""
        self.pm_logger.info("Starting initial risk identification")
        try:
            risks = [
                {
                    "id": "RISK-001",
                    "category": "Technical",
                    "description": "Database performance issues with large number of tasks",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation": "Implement proper indexing and pagination"
                },
                # ... other base risks ...
            ]
            
            features = requirements.get("features", [])
            self.pm_logger.debug(f"Analyzing features for potential risks: {features}")
            
            if "file_attachments" in features:
                self.pm_logger.debug("Adding file upload security risk")
                risks.append({
                    "id": "RISK-004",
                    "category": "Security",
                    "description": "File upload vulnerabilities",
                    "probability": "high",
                    "impact": "high",
                    "mitigation": "Implement strict file validation and virus scanning"
                })
            
            if "api_integration" in features:
                self.pm_logger.debug("Adding API integration risk")
                risks.append({
                    "id": "RISK-005",
                    "category": "Integration",
                    "description": "Third-party API reliability",
                    "probability": "medium",
                    "impact": "medium",
                    "mitigation": "Implement retry mechanisms and fallback options"
                })
            
            self.pm_logger.info(f"Identified {len(risks)} initial risks")
            return risks
        except Exception as e:
            self.pm_logger.error(f"Error identifying initial risks: {str(e)}")
            raise

    async def _break_down_tasks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down project into detailed tasks."""
        self.pm_logger.info("Starting task breakdown")
        try:
            self.pm_logger.debug("Attempting task breakdown using LLM")
            tasks = await self.llm_service.generate_task_breakdown(
                analysis,
                TASK_BREAKDOWN_TEMPLATE
            )
            
            await self.update_memory("working", {
                "task_breakdown": tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "source": "llm"
            })
            
            self.pm_logger.info("Task breakdown completed using LLM")
            return tasks
            
        except Exception as e:
            self.pm_logger.warning(f"LLM task breakdown failed: {str(e)}, falling back to predefined tasks")
            
            await self.update_memory("working", {
                "breakdown_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            
            predefined_tasks = self._get_predefined_tasks()
            
            await self.update_memory("working", {
                "task_breakdown": predefined_tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "source": "predefined"
            })
            
            self.pm_logger.info("Task breakdown completed using predefined structure")
            return predefined_tasks

    async def _create_timeline(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create project timeline with critical path."""
        self.pm_logger.info("Creating project timeline")
        try:
            tasks = await self._break_down_tasks(analysis)
            start_date = datetime.now()
            
            self.pm_logger.debug(f"Creating timeline for {len(tasks)} tasks")
            timeline = self.timeline_service.create_timeline(tasks, start_date)
            
            await self.update_memory("working", {
                "timeline": timeline,
                "timeline_timestamp": datetime.utcnow()
            })
            
            self.pm_logger.info("Timeline created successfully")
            return timeline
        except Exception as e:
            self.pm_logger.error(f"Error creating timeline: {str(e)}")
            await self.update_memory("working", {
                "timeline_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise

    async def _allocate_resources(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate and balance resources."""
        self.pm_logger.info("Starting resource allocation")
        try:
            timeline = await self._create_timeline(analysis)
            resources = self._identify_required_resources(analysis)
            
            self.pm_logger.debug(f"Allocating {len(resources)} resources to timeline")
            allocation = self.timeline_service.allocate_resources(timeline, resources)
            
            await self.update_memory("working", {
                "resource_allocation": allocation,
                "allocation_timestamp": datetime.utcnow()
            })
            
            self.pm_logger.info("Resource allocation completed successfully")
            return allocation
        except Exception as e:
            self.pm_logger.error(f"Error in resource allocation: {str(e)}")
            await self.update_memory("working", {
                "allocation_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise