from typing import Dict, Any, List
from datetime import datetime, timedelta
from core.logging.logger import setup_logger
from agents.core.base_agent import BaseAgent
from agents.core.llm.service import LLMService
from agents.core.llm.prompts import REQUIREMENT_ANALYSIS_TEMPLATE, TASK_BREAKDOWN_TEMPLATE

# New memory-related imports
from memory.memory_manager import MemoryManager
from memory.base import MemoryType, MemoryEntry
from memory.base import MemoryType

# Import planning tools and base classes
from tools.project_planning.base import (
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    ProjectPhase,
    PlanningError,
    ResourceType  # Move ResourceType to base.py
)
from tools.project_planning.task_estimator import TaskEstimator
from tools.project_planning.timeline_generateor import TimelineGenerator, TimelineConstraint
from tools.project_planning.dependency_analyzer import DependencyAnalyzer
from tools.project_planning.critical_path import CriticalPathAnalyzer

# Import risk assessment tools
from tools.risk_assessment.base import RiskCategory, RiskProbability, RiskImpact
from tools.risk_assessment.probability_calculator import RiskProbabilityCalculator
from tools.risk_assessment.impact_assessor import ImpactAssessor

# Keep old imports temporarily for migration
from .task_breakdown import TaskBreakdownService
from .timeline_service import TimelineService

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent responsible for project planning and oversight."""

    def __init__(self, 
                 agent_id: str, 
                 name: str, 
                 memory_manager: MemoryManager):
        super().__init__(agent_id, name)
        
        # Basic project state
        self.current_project = None
        self.project_plan = None
        self.team_allocation = {}
        self.risk_registry = []
        
        # Initialize logger
        self.logger = setup_logger(f"project_manager.{self.agent_id}")
        self.logger.info(f"Initializing Project Manager Agent: {self.name}")
        
        try:
            # Initialize core services (temporary)
            self.logger.debug("Initializing legacy services")
            self._task_service = TaskBreakdownService()  # Prefix with _ to indicate deprecated
            self._timeline_service = TimelineService()    # Prefix with _ to indicate deprecated
            
            # Initialize LLM service
            self.logger.debug("Initializing LLM service")
            self.llm_service = LLMService()
            
            # Memory management
            self.memory_manager = memory_manager

            # Initialize planning tools
            self.logger.debug("Initializing planning tools")
            self.task_estimator = TaskEstimator()
            self.timeline_generator = TimelineGenerator()
            self.dependency_analyzer = DependencyAnalyzer()
            self.critical_path_analyzer = CriticalPathAnalyzer()
            
            # Initialize risk assessment tools
            self.logger.debug("Initializing risk assessment tools")
            self.risk_calculator = RiskProbabilityCalculator()
            self.impact_assessor = ImpactAssessor()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {str(e)}")
            raise RuntimeError(f"Agent initialization failed: {str(e)}")
        
    @property
    def is_ready(self) -> bool:
        """Check if agent is properly initialized and ready."""
        return all([
            self.task_estimator is not None,
            self.timeline_generator is not None,
            self.dependency_analyzer is not None,
            self.critical_path_analyzer is not None,
            self.risk_calculator is not None,
            self.impact_assessor is not None
        ])
        
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process initial project input and generate analysis."""
        self.pm_logger.info("Processing new project input")
        self.pm_logger.debug(f"Input data: {input_data}")
        
        await self.update_status("analyzing_requirements")
        
        try:
            # Store project input in working memory
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.WORKING,
                content={
                    "project_input": input_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Analyze requirements using LLM
            self.pm_logger.info("Starting requirements analysis")
            analysis_result = await self._analyze_requirements(input_data)
            
            # Generate initial project plan
            self.pm_logger.info("Generating project plan")
            self.project_plan = await self._generate_project_plan(analysis_result)
            
             # 2. Generate initial task estimates
            self.logger.info("Generating task estimates")
            task_estimates = self.task_estimator.estimate_task({
                "name": "Project Setup",
                "id": "PROJ-001",
                "duration": timedelta(days=1),
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.NOT_STARTED,
                "complexity": TaskComplexity.MEDIUM,
                "features": input_data.get("features", []),
                "constraints": input_data.get("constraints", [])
            })
            
            # 3. Generate project plan with new tools
            self.logger.info("Generating project plan")
            self.project_plan = await self._generate_project_plan_new(
                analysis_result,
                task_estimates
            )
            
            # Store results
            result = {
                "status": "success",
                "analysis": analysis_result,
                "task_estimates": task_estimates,
                "project_plan": self.project_plan
            }
            

            # Store analysis in long-term memory with importance
            await self.memory_manager.store(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                content={
                    "analysis_result": analysis_result,
                    "project_type": input_data.get("project_type")
                },
                metadata={
                    "importance": 0.7,  # High importance for project analysis
                    "source": "initial_analysis"
                }
            )
            
            self.logger.info("Project input processing completed successfully")
            return result
                
        except Exception as e:
            self.logger.error(f"Error processing project input: {str(e)}")
            await self.memory_manager.store(
            agent_id=self.agent_id,
            memory_type=MemoryType.SHORT_TERM,
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
                }
            )
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
        """Generate detailed project plan based on analysis with risk assessment."""
        self.pm_logger.info("Generating project plan with risk assessment")
        
        try:
            # Generate base components
            phases = await self._break_down_tasks(analysis)
            timeline = await self._create_timeline(analysis)
            resource_allocation = await self._allocate_resources(analysis)
            
            # Identify and assess risks
            initial_risks = self._identify_initial_risks(analysis)
            
            # Create risk mitigation plan
            risk_mitigation = self._create_risk_mitigation_plan(initial_risks)
            
            # Adjust timeline and resources based on risk assessment
            risk_adjusted_timeline = self._adjust_timeline_for_risks(timeline, initial_risks)
            risk_adjusted_resources = self._adjust_resources_for_risks(resource_allocation, initial_risks)
            
            plan = {
                "phases": phases,
                "timeline": risk_adjusted_timeline,
                "resource_allocation": risk_adjusted_resources,
                "risks": initial_risks,
                "risk_mitigation": risk_mitigation,
                "risk_metrics": {
                    "high_risk_count": len([r for r in initial_risks if r["risk_score"] >= 0.7]),
                    "medium_risk_count": len([r for r in initial_risks if 0.3 <= r["risk_score"] < 0.7]),
                    "low_risk_count": len([r for r in initial_risks if r["risk_score"] < 0.3]),
                }
            }
            
            self.pm_logger.info("Project plan generated successfully with risk assessment")
            self.pm_logger.debug(f"Risk metrics: {plan['risk_metrics']}")
            
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
        """Identify initial project risks using risk assessment tools."""
        self.pm_logger.info("Starting initial risk identification")
        try:
            initial_risks = []
            features = requirements.get("features", [])
            
            # Technical Risks Assessment
            tech_probability = self.risk_calculator.calculate_technical_probability(
                team_experience=self._calculate_team_experience_score(requirements),
                technology_maturity=0.7,  # Default for established tech stack
                complexity=0.6 if "api_integration" in features else 0.4
            )
            
            tech_impact, tech_details = self.impact_assessor.assess_impact(
                RiskCategory.TECHNICAL,
                {
                    "quality_impact": 0.7,
                    "maintenance_impact": 0.6,
                    "performance_impact": 0.8 if len(features) > 3 else 0.5
                }
            )
            
            initial_risks.append({
                "id": "RISK-001",
                "category": RiskCategory.TECHNICAL.value,
                "description": "Technical complexity and integration challenges",
                "probability": tech_probability.value,
                "impact": tech_impact.value,
                "risk_score": self.impact_assessor.calculate_risk_score(tech_probability, tech_impact),
                "details": tech_details,
                "mitigation": "Review technical architecture and implement robust testing"
            })

            # Security Risk Assessment for File Attachments
            if "file_attachments" in features:
                security_probability = RiskProbability.HIGH
                security_impact, security_details = self.impact_assessor.assess_impact(
                    RiskCategory.SECURITY,
                    {
                        "quality_impact": 0.9,
                        "maintenance_impact": 0.7,
                        "performance_impact": 0.8
                    }
                )
                
                initial_risks.append({
                    "id": "RISK-002",
                    "category": RiskCategory.SECURITY.value,
                    "description": "File upload security vulnerabilities",
                    "probability": security_probability.value,
                    "impact": security_impact.value,
                    "risk_score": self.impact_assessor.calculate_risk_score(security_probability, security_impact),
                    "details": security_details,
                    "mitigation": "Implement strict file validation and virus scanning"
                })

            # Integration Risk Assessment
            if "api_integration" in features:
                integration_probability = RiskProbability.MEDIUM
                integration_impact, integration_details = self.impact_assessor.assess_impact(
                    RiskCategory.INTEGRATION,
                    {
                        "quality_impact": 0.6,
                        "maintenance_impact": 0.7,
                        "performance_impact": 0.7
                    }
                )
                
                initial_risks.append({
                    "id": "RISK-003",
                    "category": RiskCategory.INTEGRATION.value,
                    "description": "Third-party API reliability and integration issues",
                    "probability": integration_probability.value,
                    "impact": integration_impact.value,
                    "risk_score": self.impact_assessor.calculate_risk_score(integration_probability, integration_impact),
                    "details": integration_details,
                    "mitigation": "Implement retry mechanisms and fallback options"
                })
            
            # Sort risks by risk score
            initial_risks.sort(key=lambda x: x["risk_score"], reverse=True)
            
            self.pm_logger.info(f"Identified {len(initial_risks)} initial risks")
            self.pm_logger.debug(f"Risk details: {initial_risks}")
            
            # Update risk registry
            self.risk_registry = initial_risks
            
            return initial_risks
            
        except Exception as e:
            self.pm_logger.error(f"Error identifying initial risks: {str(e)}")
            raise

    async def _break_down_tasks_new(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down project into detailed tasks using new TaskEstimator."""
        self.logger.info("Starting task breakdown with new estimator")
        try:
            # Extract requirements from analysis
            requirements = {
                "features": analysis.get("understood_requirements", []),
                "technical_considerations": analysis.get("technical_considerations", []),
                "constraints": analysis.get("constraints", [])
            }
            
            # Generate base task structure
            base_tasks = []
            for phase in ProjectPhase:
                phase_tasks = self._generate_phase_tasks(phase, requirements)
                base_tasks.extend(phase_tasks)
            
            # Estimate each task
            estimated_tasks = []
            for task in base_tasks:
                # Prepare task for estimation
                estimation_input = {
                    "id": task["id"],
                    "name": task["name"],
                    "duration": task.get("duration", timedelta(days=1)),
                    "priority": task.get("priority", TaskPriority.MEDIUM),
                    "status": TaskStatus.NOT_STARTED,
                    "complexity": task.get("complexity", TaskComplexity.MEDIUM),
                    "phase": task.get("phase"),
                    "features": requirements["features"],
                    "constraints": requirements["constraints"]
                }
                
                # Get task estimation
                task_estimate = self.task_estimator.estimate_task(estimation_input)
                
                # Merge estimation with task data
                estimated_task = {
                    **task,
                    "estimated_duration": task_estimate["adjusted_duration"],
                    "effort_days": task_estimate["effort_days"],
                    "confidence_score": task_estimate["confidence_score"],
                    "risk_level": task_estimate["risk_level"],
                    "recommended_buffer": task_estimate["recommended_buffer"]
                }
                estimated_tasks.append(estimated_task)

            # Store in working memory
            await self.update_memory("working", {
                "task_breakdown": estimated_tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "estimation_confidence": sum(t["confidence_score"] for t in estimated_tasks) / len(estimated_tasks)
            })
            
            self.logger.info(f"Task breakdown completed: {len(estimated_tasks)} tasks generated")
            self.logger.debug(f"Average estimation confidence: {sum(t['confidence_score'] for t in estimated_tasks) / len(estimated_tasks):.2f}")
            
            return estimated_tasks
            
        except Exception as e:
            self.logger.error(f"Error in new task breakdown: {str(e)}")
            # Fallback to old method if needed
            self.logger.warning("Falling back to legacy task breakdown")
            return await self._break_down_tasks(analysis)

    def _generate_phase_tasks(self, phase: ProjectPhase, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tasks for a specific project phase."""
        self.logger.debug(f"Generating tasks for phase: {phase.value}")
        
        tasks = []
        phase_prefix = phase.value.upper()[:3]
        
        if phase == ProjectPhase.PLANNING:
            tasks = [
                {
                    "id": f"{phase_prefix}-001",
                    "name": "Requirements Analysis",
                    "description": "Analyze and document detailed project requirements",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "resources": ["Project Manager", "Solution Architect"]
                },
                {
                    "id": f"{phase_prefix}-002",
                    "name": "Architecture Planning",
                    "description": "Design system architecture and select technologies",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": [f"{phase_prefix}-001"],
                    "resources": ["Solution Architect"]
                }
            ]
        elif phase == ProjectPhase.DESIGN:
            tasks = [
                {
                    "id": f"{phase_prefix}-001",
                    "name": "Database Schema Design",
                    "description": "Design database schema and data models",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": ["PLA-002"],
                    "resources": ["Backend Developer"]
                },
                {
                    "id": f"{phase_prefix}-002",
                    "name": "API Design",
                    "description": "Design API endpoints and interfaces",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": [f"{phase_prefix}-001"],
                    "resources": ["Backend Developer"]
                }
            ]
            
            # Add UI design if needed
            if any("ui" in feature.lower() for feature in requirements["features"]):
                tasks.append({
                    "id": f"{phase_prefix}-003",
                    "name": "UI/UX Design",
                    "description": "Design user interface and user experience",
                    "phase": phase,
                    "type": ResourceType.DESIGNER,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": ["PLA-002"],
                    "resources": ["UI Designer"]
                })
        
        elif phase == ProjectPhase.DEVELOPMENT:
            # Core backend tasks
            tasks = [
                {
                    "id": f"{phase_prefix}-001",
                    "name": "Database Implementation",
                    "description": "Implement database schema and migrations",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": ["DES-001"],
                    "resources": ["Backend Developer"]
                },
                {
                    "id": f"{phase_prefix}-002",
                    "name": "Core API Implementation",
                    "description": "Implement core API endpoints and business logic",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": ["DES-002", f"{phase_prefix}-001"],
                    "resources": ["Backend Developer"]
                }
            ]
            
            # Add frontend tasks if UI is involved
            if any("ui" in feature.lower() for feature in requirements["features"]):
                tasks.extend([
                    {
                        "id": f"{phase_prefix}-003",
                        "name": "Frontend Core Implementation",
                        "description": "Implement core UI components and layout",
                        "phase": phase,
                        "type": ResourceType.FRONTEND,
                        "priority": TaskPriority.HIGH,
                        "complexity": TaskComplexity.MEDIUM,
                        "dependencies": ["DES-003"],
                        "resources": ["Frontend Developer"]
                    },
                    {
                        "id": f"{phase_prefix}-004",
                        "name": "API Integration",
                        "description": "Integrate frontend with backend APIs",
                        "phase": phase,
                        "type": ResourceType.FRONTEND,
                        "priority": TaskPriority.HIGH,
                        "complexity": TaskComplexity.MEDIUM,
                        "dependencies": [f"{phase_prefix}-002", f"{phase_prefix}-003"],
                        "resources": ["Frontend Developer"]
                    }
                ])
            
            # Add authentication if required
            if any("auth" in feature.lower() for feature in requirements["features"]):
                tasks.append({
                    "id": f"{phase_prefix}-005",
                    "name": "Authentication Implementation",
                    "description": "Implement user authentication and authorization",
                    "phase": phase,
                    "type": ResourceType.BACKEND,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": [f"{phase_prefix}-002"],
                    "resources": ["Backend Developer"]
                })
                
        elif phase == ProjectPhase.TESTING:
            tasks = [
                {
                    "id": f"{phase_prefix}-001",
                    "name": "Backend Unit Testing",
                    "description": "Create and execute backend unit tests",
                    "phase": phase,
                    "type": ResourceType.QA,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": ["DEV-002"],
                    "resources": ["Backend Developer", "QA Engineer"]
                },
                {
                    "id": f"{phase_prefix}-002",
                    "name": "API Integration Testing",
                    "description": "Test API integrations and endpoints",
                    "phase": phase,
                    "type": ResourceType.QA,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": ["DEV-002"],
                    "resources": ["QA Engineer"]
                }
            ]
            
            # Add frontend testing if UI exists
            if any("ui" in feature.lower() for feature in requirements["features"]):
                tasks.extend([
                    {
                        "id": f"{phase_prefix}-003",
                        "name": "Frontend Unit Testing",
                        "description": "Create and execute frontend component tests",
                        "phase": phase,
                        "type": ResourceType.QA,
                        "priority": TaskPriority.HIGH,
                        "complexity": TaskComplexity.MEDIUM,
                        "dependencies": ["DEV-003"],
                        "resources": ["Frontend Developer", "QA Engineer"]
                    },
                    {
                        "id": f"{phase_prefix}-004",
                        "name": "E2E Testing",
                        "description": "Perform end-to-end testing",
                        "phase": phase,
                        "type": ResourceType.QA,
                        "priority": TaskPriority.HIGH,
                        "complexity": TaskComplexity.HIGH,
                        "dependencies": [f"{phase_prefix}-001", f"{phase_prefix}-002", f"{phase_prefix}-003"],
                        "resources": ["QA Engineer"]
                    }
                ])
                
        elif phase == ProjectPhase.DEPLOYMENT:
            tasks = [
                {
                    "id": f"{phase_prefix}-001",
                    "name": "Infrastructure Setup",
                    "description": "Set up production infrastructure",
                    "phase": phase,
                    "type": ResourceType.DEVOPS,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": ["TES-002"],
                    "resources": ["DevOps Engineer"]
                },
                {
                    "id": f"{phase_prefix}-002",
                    "name": "CI/CD Pipeline Setup",
                    "description": "Configure continuous integration and deployment",
                    "phase": phase,
                    "type": ResourceType.DEVOPS,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": [f"{phase_prefix}-001"],
                    "resources": ["DevOps Engineer"]
                },
                {
                    "id": f"{phase_prefix}-003",
                    "name": "Production Deployment",
                    "description": "Deploy application to production",
                    "phase": phase,
                    "type": ResourceType.DEVOPS,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.HIGH,
                    "dependencies": [f"{phase_prefix}-002"],
                    "resources": ["DevOps Engineer"]
                },
                {
                    "id": f"{phase_prefix}-004",
                    "name": "Post-Deployment Verification",
                    "description": "Verify production deployment",
                    "phase": phase,
                    "type": ResourceType.DEVOPS,
                    "priority": TaskPriority.HIGH,
                    "complexity": TaskComplexity.MEDIUM,
                    "dependencies": [f"{phase_prefix}-003"],
                    "resources": ["DevOps Engineer", "QA Engineer"]
                }
            ]
        
        self.logger.debug(f"Generated {len(tasks)} tasks for {phase.value}")
        return tasks

    async def _break_down_tasks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down project into detailed tasks."""
        self.logger.info("Starting task breakdown")
        try:
            # Try new implementation first
            self.logger.debug("Attempting task breakdown with new estimator")
            if self.is_ready:
                return await self._break_down_tasks_new(analysis)
            
            # Fallback to LLM if new implementation fails or not ready
            self.logger.debug("Attempting task breakdown using LLM")
            tasks = await self.llm_service.generate_task_breakdown(
                analysis,
                TASK_BREAKDOWN_TEMPLATE
            )
            
            await self.update_memory("working", {
                "task_breakdown": tasks,
                "breakdown_timestamp": datetime.utcnow(),
                "source": "llm"
            })
            
            self.logger.info("Task breakdown completed using LLM")
            return tasks
            
        except Exception as e:
            self.logger.warning(f"Primary task breakdown methods failed: {str(e)}, falling back to predefined tasks")
            
            await self.update_memory("working", {
                "breakdown_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            
            # Fallback to old service as last resort
            try:
                predefined_tasks = self._task_service.generate_detailed_tasks(
                    analysis.get("understood_requirements", [])
                )
                
                await self.update_memory("working", {
                    "task_breakdown": predefined_tasks,
                    "breakdown_timestamp": datetime.utcnow(),
                    "source": "predefined"
                })
                
                self.logger.info("Task breakdown completed using predefined structure")
                return predefined_tasks
                
            except Exception as fallback_error:
                self.logger.error(f"All task breakdown methods failed: {str(fallback_error)}")
                raise


    async def _create_timeline_new(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create project timeline using new TimelineGenerator."""
        self.logger.info("Creating project timeline with new generator")
        try:
            # Get tasks
            tasks = await self._break_down_tasks_new(analysis)
            
            # Create timeline constraints
            constraints = TimelineConstraint(
                start_date=datetime.now(),
                end_date=datetime.now() + self._calculate_duration(analysis),
                fixed_milestones=self._get_fixed_milestones(analysis),
                blackout_periods=self._get_blackout_periods(analysis)
            )
            
            # Generate timeline
            self.logger.debug("Generating timeline with constraints")
            timeline = self.timeline_generator.generate_timeline(
                tasks=tasks,
                constraints=constraints,
                resource_calendar=self._create_resource_calendar(analysis)
            )
            
            # Analyze critical path
            critical_path_analysis = self.critical_path_analyzer.analyze_critical_path(
                tasks=tasks,
                start_date=timeline["start_date"]
            )
            
            # Merge timeline with critical path analysis
            complete_timeline = {
                **timeline,
                "critical_path_analysis": critical_path_analysis,
                "metrics": {
                    "total_duration": (timeline["end_date"] - timeline["start_date"]).days,
                    "critical_path_length": len(critical_path_analysis["critical_path"]["tasks"]),
                    "total_slack": critical_path_analysis["metrics"]["total_slack_days"],
                    "milestone_count": len(timeline["milestones"])
                }
            }
            
            # Store in working memory
            await self.update_memory("working", {
                "timeline": complete_timeline,
                "timeline_timestamp": datetime.utcnow()
            })
            
            self.logger.info("Timeline created successfully")
            self.logger.debug(f"Timeline metrics: {complete_timeline['metrics']}")
            
            return complete_timeline
            
        except Exception as e:
            self.logger.error(f"Error creating timeline: {str(e)}")
            raise

    def _get_fixed_milestones(self, analysis: Dict[str, Any]) -> Dict[str, datetime]:
        """Extract fixed milestones from analysis."""
        self.logger.debug("Extracting fixed milestones")
        try:
            fixed_milestones = {}
            
            # Check for fixed dates in requirements
            for requirement in analysis.get("understood_requirements", []):
                if "by" in requirement.lower() or "deadline" in requirement.lower():
                    # You would need more sophisticated date parsing here
                    # This is just a placeholder
                    self.logger.debug(f"Found potential milestone in requirement: {requirement}")
            
            # Add phase completion milestones
            project_duration = self._calculate_duration(analysis)
            current_date = datetime.now()
            
            phase_milestones = {
                "PLAN-002": current_date + (project_duration * 0.1),  # Planning completion
                "DES-002": current_date + (project_duration * 0.3),  # Design completion
                "DEV-004": current_date + (project_duration * 0.7),  # Development completion
                "TES-004": current_date + (project_duration * 0.9),  # Testing completion
            }
            
            fixed_milestones.update(phase_milestones)
            self.logger.debug(f"Created {len(fixed_milestones)} fixed milestones")
            
            return fixed_milestones
            
        except Exception as e:
            self.logger.error(f"Error getting fixed milestones: {str(e)}")
            return {}

    def _get_blackout_periods(self, analysis: Dict[str, Any]) -> List[Dict[str, datetime]]:
        """Identify blackout periods for the project."""
        self.logger.debug("Identifying blackout periods")
        try:
            blackout_periods = []
            
            # Add standard holidays
            # This would need to be more sophisticated in a real implementation
            holidays = [
                {
                    "start": datetime(2025, 12, 24),
                    "end": datetime(2025, 12, 26)
                },
                {
                    "start": datetime(2025, 12, 31),
                    "end": datetime(2026, 1, 2)
                }
            ]
            
            # Add team-specific blackout periods
            team_constraints = analysis.get("resource_constraints", [])
            for constraint in team_constraints:
                if "unavailable" in constraint.lower():
                    # Parse dates from constraint
                    # This would need more sophisticated parsing
                    self.logger.debug(f"Found team constraint: {constraint}")
            
            blackout_periods.extend(holidays)
            self.logger.debug(f"Identified {len(blackout_periods)} blackout periods")
            
            return blackout_periods
            
        except Exception as e:
            self.logger.error(f"Error getting blackout periods: {str(e)}")
            return []

    def _create_resource_calendar(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create resource availability calendar."""
        self.logger.debug("Creating resource calendar")
        try:
            # Get resources
            resources = self._identify_required_resources(analysis)
            
            calendar = {}
            for resource in resources:
                # Create availability calendar for each resource
                resource_id = resource["type"].value
                calendar[resource_id] = {
                    "availability": self._generate_resource_availability(resource),
                    "capacity": resource["allocation_percentage"] / 100,
                    "skills": resource["skills"]
                }
            
            self.logger.debug(f"Created calendar for {len(calendar)} resources")
            return calendar
            
        except Exception as e:
            self.logger.error(f"Error creating resource calendar: {str(e)}")
            return {}
        

    def _generate_resource_availability(self, resource: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate availability calendar for a resource."""
        self.logger.debug(f"Generating availability for resource type: {resource['type'].value}")
        try:
            availability = {}
            current_date = datetime.now()
            
            # Generate for next 6 months
            for i in range(180):  # 6 months
                date = current_date + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                # Basic availability (weekdays only)
                is_weekend = date.weekday() >= 5
                
                availability[date_str] = {
                    "available": not is_weekend,
                    "capacity": 0 if is_weekend else resource["allocation_percentage"] / 100,
                    "blackout": False
                }
            
            self.logger.debug(f"Generated {len(availability)} days of availability")
            return availability
            
        except Exception as e:
            self.logger.error(f"Error generating resource availability: {str(e)}")
            return {}
        
    async def _create_timeline(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create project timeline with critical path."""
        self.logger.info("Creating project timeline")
        try:
            # Try new implementation first
            if self.is_ready and self.timeline_generator:
                self.logger.debug("Using new timeline generator")
                return await self._create_timeline_new(analysis)
            
            # Fallback to old service
            self.logger.warning("Falling back to legacy timeline service")
            tasks = await self._break_down_tasks(analysis)
            start_date = datetime.now()
            
            self.logger.debug(f"Creating timeline for {len(tasks)} tasks")
            timeline = self._timeline_service.create_timeline(tasks, start_date)
            
            await self.update_memory("working", {
                "timeline": timeline,
                "timeline_timestamp": datetime.utcnow()
            })
            
            self.logger.info("Timeline created successfully using legacy service")
            return timeline
            
        except Exception as e:
            self.logger.error(f"Error creating timeline: {str(e)}")
            await self.update_memory("working", {
                "timeline_error": str(e),
                "error_timestamp": datetime.utcnow()
            })
            raise
    
    async def _allocate_resources_new(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate and balance resources using new tools."""
        self.logger.info("Starting enhanced resource allocation")
        try:
            # Get timeline and tasks
            timeline = await self._create_timeline_new(analysis)
            tasks = timeline["tasks"]
            
            # Get resource requirements
            resources = self._identify_required_resources(analysis)
            resource_calendar = self._create_resource_calendar(analysis)
            
            # Initial allocation
            initial_allocation = self._perform_initial_allocation(
                tasks, 
                resources, 
                timeline["critical_path_analysis"]["critical_path"]["tasks"]
            )
            
            # Balance resources
            balanced_allocation = self._balance_resource_allocation(
                initial_allocation,
                resource_calendar,
                timeline["start_date"],
                timeline["end_date"]
            )
            
            # Check for overallocation
            overallocation_analysis = self._analyze_resource_overallocation(
                balanced_allocation,
                resources
            )
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_resource_optimization_suggestions(
                balanced_allocation,
                overallocation_analysis,
                timeline
            )
            
            # Prepare final allocation result
            allocation_result = {
                "allocation": balanced_allocation,
                "resource_utilization": self._calculate_resource_utilization(balanced_allocation),
                "overallocation": overallocation_analysis,
                "optimization_suggestions": optimization_suggestions,
                "metrics": {
                    "total_allocated_hours": self._calculate_total_allocated_hours(balanced_allocation),
                    "resource_efficiency": self._calculate_resource_efficiency(balanced_allocation, resources),
                    "critical_path_resource_coverage": self._calculate_critical_path_coverage(
                        balanced_allocation,
                        timeline["critical_path_analysis"]["critical_path"]["tasks"]
                    )
                }
            }
            
            # Store in working memory
            await self.update_memory("working", {
                "resource_allocation": allocation_result,
                "allocation_timestamp": datetime.utcnow()
            })
            
            self.logger.info("Resource allocation completed successfully")
            return allocation_result
            
        except Exception as e:
            self.logger.error(f"Error in resource allocation: {str(e)}")
            raise

    def _perform_initial_allocation(self, 
                                  tasks: List[Dict[str, Any]], 
                                  resources: List[Dict[str, Any]],
                                  critical_path_tasks: List[str]) -> Dict[str, Any]:
        """Perform initial resource allocation prioritizing critical path."""
        self.logger.debug("Performing initial resource allocation")
        try:
            allocation = {}
            
            # Sort tasks by priority (critical path first)
            sorted_tasks = sorted(
                tasks,
                key=lambda t: (
                    t["id"] in critical_path_tasks,  # Critical path tasks first
                    t.get("priority", TaskPriority.MEDIUM).value,  # Then by priority
                    t.get("complexity", TaskComplexity.MEDIUM).value  # Then by complexity
                ),
                reverse=True
            )
            
            # Create resource skill map
            resource_skills = {
                r["type"].value: set(r["skills"]) 
                for r in resources
            }
            
            # Allocate tasks
            for task in sorted_tasks:
                required_skills = set(task.get("required_skills", []))
                best_resource = None
                best_match_score = -1
                
                for resource in resources:
                    resource_id = resource["type"].value
                    skill_match_score = len(
                        resource_skills[resource_id] & required_skills
                    ) / max(len(required_skills), 1)
                    
                    if skill_match_score > best_match_score:
                        best_match_score = skill_match_score
                        best_resource = resource_id
                
                if best_resource:
                    if best_resource not in allocation:
                        allocation[best_resource] = []
                    allocation[best_resource].append(task)
            
            self.logger.debug(f"Initial allocation completed for {len(sorted_tasks)} tasks")
            return allocation
            
        except Exception as e:
            self.logger.error(f"Error in initial allocation: {str(e)}")
            raise

    def _balance_resource_allocation(self,
                                   initial_allocation: Dict[str, List[Dict[str, Any]]],
                                   resource_calendar: Dict[str, Any],
                                   start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Balance resource allocation to optimize workload."""
        self.logger.debug("Balancing resource allocation")
        try:
            balanced_allocation = {}
            
            for resource_id, tasks in initial_allocation.items():
                # Get resource capacity
                resource_capacity = resource_calendar[resource_id]["capacity"]
                
                # Sort tasks by priority and dependencies
                sorted_tasks = sorted(
                    tasks,
                    key=lambda t: (
                        t.get("priority", TaskPriority.MEDIUM).value,
                        len(t.get("dependencies", [])),
                        t.get("complexity", TaskComplexity.MEDIUM).value
                    ),
                    reverse=True
                )
                
                # Calculate daily allocations
                daily_allocation = self._calculate_daily_allocation(
                    sorted_tasks,
                    resource_capacity,
                    start_date,
                    end_date
                )
                
                balanced_allocation[resource_id] = {
                    "tasks": sorted_tasks,
                    "daily_allocation": daily_allocation
                }
            
            self.logger.debug(f"Resource balancing completed for {len(initial_allocation)} resources")
            return balanced_allocation
            
        except Exception as e:
            self.logger.error(f"Error balancing resources: {str(e)}")
            raise

    def _analyze_resource_overallocation(self,
                                       allocation: Dict[str, Any],
                                       resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze resource overallocation issues."""
        self.logger.debug("Analyzing resource overallocation")
        try:
            overallocation_issues = []
            
            for resource_id, allocation_data in allocation.items():
                daily_allocation = allocation_data["daily_allocation"]
                resource_info = next(
                    (r for r in resources if r["type"].value == resource_id),
                    None
                )
                
                if resource_info:
                    max_capacity = resource_info["allocation_percentage"] / 100
                    
                    # Check each day for overallocation
                    for date, allocation_percentage in daily_allocation.items():
                        if allocation_percentage > max_capacity:
                            overallocation_issues.append({
                                "resource_id": resource_id,
                                "date": date,
                                "allocated": allocation_percentage,
                                "capacity": max_capacity,
                                "overallocation_percentage": (
                                    (allocation_percentage - max_capacity) / max_capacity * 100
                                )
                            })
            
            self.logger.debug(f"Found {len(overallocation_issues)} overallocation issues")
            return overallocation_issues
            
        except Exception as e:
            self.logger.error(f"Error analyzing overallocation: {str(e)}")
            raise

    def _calculate_daily_allocation(self,
                               tasks: List[Dict[str, Any]],
                               resource_capacity: float,
                               start_date: datetime,
                               end_date: datetime) -> Dict[str, float]:
        """Calculate daily allocation percentages for a resource."""
        self.logger.debug("Calculating daily resource allocation")
        try:
            daily_allocation = {}
            days = (end_date - start_date).days + 1
            
            # Initialize daily allocation
            current_date = start_date
            for _ in range(days):
                date_str = current_date.strftime("%Y-%m-%d")
                daily_allocation[date_str] = 0.0
                current_date += timedelta(days=1)
            
            # Allocate tasks
            for task in tasks:
                task_start = task["earliest_start"]
                task_duration = task["duration"].days
                task_effort = task.get("effort_days", task_duration)
                
                # Calculate daily effort
                daily_effort = task_effort / task_duration
                
                # Allocate to days
                current_date = task_start
                for _ in range(task_duration):
                    date_str = current_date.strftime("%Y-%m-%d")
                    if date_str in daily_allocation:
                        daily_allocation[date_str] += (daily_effort / resource_capacity)
                    current_date += timedelta(days=1)
            
            self.logger.debug(f"Daily allocation calculated for {len(tasks)} tasks")
            return daily_allocation
            
        except Exception as e:
            self.logger.error(f"Error calculating daily allocation: {str(e)}")
            raise

    def _generate_resource_optimization_suggestions(self,
                                                  allocation: Dict[str, Any],
                                                  overallocation: List[Dict[str, Any]],
                                                  timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for optimizing resource allocation."""
        self.logger.debug("Generating resource optimization suggestions")
        try:
            suggestions = []
            
            # Check for overallocation patterns
            if overallocation:
                by_resource = {}
                for issue in overallocation:
                    resource_id = issue["resource_id"]
                    if resource_id not in by_resource:
                        by_resource[resource_id] = []
                    by_resource[resource_id].append(issue)
                
                for resource_id, issues in by_resource.items():
                    if len(issues) > 5:  # Significant overallocation
                        suggestions.append({
                            "type": "resource_addition",
                            "resource_id": resource_id,
                            "priority": "HIGH",
                            "suggestion": "Consider adding additional resource",
                            "impact": f"Would resolve {len(issues)} overallocation issues"
                        })
            
            # Check for skill bottlenecks
            skill_requirements = self._analyze_skill_requirements(allocation)
            for skill, count in skill_requirements.items():
                if count > 10:  # High demand for skill
                    suggestions.append({
                        "type": "skill_bottleneck",
                        "skill": skill,
                        "priority": "MEDIUM",
                        "suggestion": "Consider training additional resources",
                        "impact": f"Would improve allocation of {count} tasks"
                    })
            
            # Check for timeline optimization
            critical_path = timeline["critical_path_analysis"]["critical_path"]["tasks"]
            if any(task["id"] in critical_path for task in overallocation):
                suggestions.append({
                    "type": "timeline_adjustment",
                    "priority": "HIGH",
                    "suggestion": "Consider timeline adjustment for critical path tasks",
                    "impact": "Would reduce resource constraints on critical path"
                })
            
            self.logger.debug(f"Generated {len(suggestions)} optimization suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating optimization suggestions: {str(e)}")
            raise

    def _analyze_skill_requirements(self, allocation: Dict[str, Any]) -> Dict[str, int]:
        """Analyze skill requirements across all tasks."""
        self.logger.debug("Analyzing skill requirements")
        try:
            skill_counts = {}
            
            for resource_data in allocation.values():
                for task in resource_data["tasks"]:
                    for skill in task.get("required_skills", []):
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            self.logger.debug(f"Analyzed requirements for {len(skill_counts)} skills")
            return skill_counts
            
        except Exception as e:
            self.logger.error(f"Error analyzing skill requirements: {str(e)}")
            raise

    def _calculate_resource_efficiency(self, 
                                     allocation: Dict[str, Any],
                                     resources: List[Dict[str, Any]]) -> float:
        """Calculate overall resource efficiency."""
        self.logger.debug("Calculating resource efficiency")
        try:
            total_capacity = 0
            total_utilization = 0
            
            for resource_id, allocation_data in allocation.items():
                resource_info = next(
                    (r for r in resources if r["type"].value == resource_id),
                    None
                )
                
                if resource_info:
                    capacity = resource_info["allocation_percentage"] / 100
                    daily_allocation = allocation_data["daily_allocation"]
                    
                    total_capacity += capacity * len(daily_allocation)
                    total_utilization += sum(daily_allocation.values())
            
            efficiency = total_utilization / total_capacity if total_capacity > 0 else 0
            self.logger.debug(f"Calculated resource efficiency: {efficiency:.2%}")
            return efficiency
            
        except Exception as e:
            self.logger.error(f"Error calculating resource efficiency: {str(e)}")
            raise

    def _calculate_critical_path_coverage(self,
                                        allocation: Dict[str, Any],
                                        critical_path_tasks: List[str]) -> float:
        """Calculate resource coverage for critical path tasks."""
        self.logger.debug("Calculating critical path resource coverage")
        try:
            covered_tasks = set()
            
            for allocation_data in allocation.values():
                task_ids = {task["id"] for task in allocation_data["tasks"]}
                covered_tasks.update(task_ids & set(critical_path_tasks))
            
            coverage = len(covered_tasks) / len(critical_path_tasks)
            self.logger.debug(f"Critical path coverage: {coverage:.2%}")
            return coverage
            
        except Exception as e:
            self.logger.error(f"Error calculating critical path coverage: {str(e)}")
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


    async def retrieve_similar_project_memories(self, current_project: Dict[str, Any]) -> List[MemoryEntry]:
        """Retrieve memories of similar past projects."""
        try:
            # Create a query based on current project characteristics
            query = {
                "project_type": current_project.get("project_type"),
                "complexity": current_project.get("complexity")
            }
            
            # Retrieve similar project memories
            similar_projects = await self.memory_manager.retrieve(
                agent_id=self.agent_id,
                memory_type=MemoryType.LONG_TERM,
                query=query,
                sort_by="importance",
                limit=5  # Top 5 most important similar projects
            )
            
            return similar_projects
        except Exception as e:
            self.logger.error(f"Error retrieving project memories: {str(e)}")
            return []
        

    async def consolidate_project_memories(self) -> bool:
        """Consolidate important short-term memories to long-term storage."""
        try:
            # Consolidate memories with importance threshold of 0.5
            return await self.memory_manager.consolidate_to_long_term(
                agent_id=self.agent_id,
                importance_threshold=0.5
            )
        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {str(e)}")
            return False
        

    @classmethod
    async def create(self, cls, 
                    agent_id: str, 
                    name: str, 
                    db_url: str) -> 'ProjectManagerAgent':
        """
        Async factory method to create a ProjectManagerAgent with memory management.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Agent name
            db_url: Database connection string for long-term memory
        
        Returns:
            ProjectManagerAgent: Initialized agent with memory management
        """
        try:
            # Create memory manager
            memory_manager = await MemoryManager.create(db_url)
            
            # Create agent instance
            agent = cls(agent_id, name, memory_manager)
            
            return agent
        except Exception as e:
            self.logger.error(f"Failed to create ProjectManagerAgent: {str(e)}")
            raise