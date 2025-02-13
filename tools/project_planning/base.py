# tools/project_planning/base.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from core.logging.logger import setup_logger

class ResourceType(Enum):
    """Types of resources needed for project execution."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DESIGNER = "designer"
    QA = "qa"
    DEVOPS = "devops"

class TaskComplexity(Enum):
    """Levels of task complexity."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """Task execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"

class ProjectPhase(Enum):
    """Project execution phases."""
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    
class PlanningError(Exception):
    """Base exception for project planning errors."""
    pass

class BaseProjectPlanningTool:
    """Base class for all project planning tools."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.logger = setup_logger(f"tools.planning.{tool_name.lower()}")
        self.logger.info(f"Initializing {tool_name} tool")

    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task structure and required fields."""
        try:
            required_fields = {
                "id": str,
                "name": str,
                "duration": timedelta,
                "priority": TaskPriority,
                "status": TaskStatus
            }
            
            for field, field_type in required_fields.items():
                if field not in task:
                    self.logger.error(f"Missing required field: {field}")
                    return False
                    
                if field_type in [TaskPriority, TaskStatus] and not isinstance(task[field], field_type):
                    self.logger.error(f"Invalid type for {field}: expected {field_type}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating task: {str(e)}")
            return False

    def calculate_base_duration(self, task: Dict[str, Any]) -> timedelta:
        """Calculate base duration for a task based on complexity and type."""
        try:
            complexity = task.get("complexity", TaskComplexity.MEDIUM)
            base_duration = timedelta(days=1)  # Default 1 day
            
            # Complexity multipliers
            multipliers = {
                TaskComplexity.LOW: 0.5,
                TaskComplexity.MEDIUM: 1.0,
                TaskComplexity.HIGH: 2.0,
                TaskComplexity.VERY_HIGH: 4.0
            }
            
            adjusted_duration = base_duration * multipliers[complexity]
            
            self.logger.debug(f"Calculated base duration for task {task['id']}: {adjusted_duration}")
            return adjusted_duration
            
        except Exception as e:
            self.logger.error(f"Error calculating base duration: {str(e)}")
            return timedelta(days=1)

    def calculate_effort(self, task: Dict[str, Any]) -> float:
        """Calculate effort in person-days."""
        try:
            complexity = task.get("complexity", TaskComplexity.MEDIUM)
            priority = task.get("priority", TaskPriority.MEDIUM)
            
            # Base effort in person-days
            base_effort = complexity.value * 0.5
            
            # Priority adjustments
            priority_multipliers = {
                TaskPriority.LOW: 0.8,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.HIGH: 1.2,
                TaskPriority.CRITICAL: 1.5
            }
            
            adjusted_effort = base_effort * priority_multipliers[priority]
            
            self.logger.debug(f"Calculated effort for task {task['id']}: {adjusted_effort} person-days")
            return adjusted_effort
            
        except Exception as e:
            self.logger.error(f"Error calculating effort: {str(e)}")
            return 1.0

    def get_phase_dependencies(self, phase: ProjectPhase) -> List[ProjectPhase]:
        """Get default phase dependencies."""
        dependencies = {
            ProjectPhase.PLANNING: [],
            ProjectPhase.DESIGN: [ProjectPhase.PLANNING],
            ProjectPhase.DEVELOPMENT: [ProjectPhase.DESIGN],
            ProjectPhase.TESTING: [ProjectPhase.DEVELOPMENT],
            ProjectPhase.DEPLOYMENT: [ProjectPhase.TESTING]
        }
        return dependencies.get(phase, [])

    def validate_dates(self, start_date: datetime, end_date: datetime) -> bool:
        """Validate date ranges."""
        try:
            if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
                self.logger.error("Invalid date types")
                return False
                
            if end_date < start_date:
                self.logger.error("End date cannot be before start date")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating dates: {str(e)}")
            return False

    def calculate_slack(self, earliest_start: datetime, latest_start: datetime) -> timedelta:
        """Calculate slack time between earliest and latest start dates."""
        try:
            return latest_start - earliest_start
        except Exception as e:
            self.logger.error(f"Error calculating slack: {str(e)}")
            return timedelta(0)