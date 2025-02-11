from datetime import timedelta
from typing import Dict, Any, List
from enum import Enum

class TaskPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class TaskType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    TESTING = "testing"
    DOCUMENTATION = "documentation"

class TaskBreakdownService:
    """Service for handling task management application task breakdown."""

    def generate_detailed_tasks(self, features: List[str]) -> Dict[str, Any]:
        """
        Generate detailed task breakdown for the task management application.
        
        Args:
            features: List of requested features
        """
        phases = self._get_base_phases()
        
        # Add feature-specific tasks
        for feature in features:
            feature_tasks = self._get_feature_specific_tasks(feature)
            self._integrate_feature_tasks(phases, feature_tasks)
        
        # Add dependencies
        self._update_dependencies(phases)
        
        return phases

    def _get_base_phases(self) -> Dict[str, Any]:
        """Get base project phases with core tasks."""
        return {
            "planning": {
                "name": "Planning Phase",
                "tasks": self._get_planning_tasks(),
                "dependencies": []
            },
            "design": {
                "name": "Design Phase",
                "tasks": self._get_design_tasks(),
                "dependencies": ["planning"]
            },
            "development": {
                "name": "Development Phase",
                "tasks": self._get_development_tasks(),
                "dependencies": ["design"]
            },
            "testing": {
                "name": "Testing Phase",
                "tasks": self._get_testing_tasks(),
                "dependencies": ["development"]
            },
            "deployment": {
                "name": "Deployment Phase",
                "tasks": self._get_deployment_tasks(),
                "dependencies": ["testing"]
            }
        }

    def _get_planning_tasks(self) -> List[Dict[str, Any]]:
        """Get detailed planning phase tasks."""
        return [
            {
                "id": "PLAN-001",
                "name": "Requirements Analysis",
                "description": "Analyze and document detailed project requirements",
                "type": TaskType.DOCUMENTATION,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=3),
                "resources": ["Project Manager", "Solution Architect"],
                "deliverables": ["Requirements Document", "Feature List"],
                "subtasks": [
                    {
                        "id": "PLAN-001-1",
                        "name": "User Story Creation",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "PLAN-001-2",
                        "name": "Acceptance Criteria Definition",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "PLAN-001-3",
                        "name": "Technical Requirements Specification",
                        "duration": timedelta(days=1)
                    }
                ]
            },
            {
                "id": "PLAN-002",
                "name": "Architecture Planning",
                "description": "Design system architecture and select technologies",
                "type": TaskType.DOCUMENTATION,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=4),
                "resources": ["Solution Architect"],
                "deliverables": ["Architecture Document", "Tech Stack Selection"],
                "dependencies": ["PLAN-001"],
                "subtasks": [
                    {
                        "id": "PLAN-002-1",
                        "name": "Technology Stack Selection",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "PLAN-002-2",
                        "name": "System Architecture Design",
                        "duration": timedelta(days=2)
                    },
                    {
                        "id": "PLAN-002-3",
                        "name": "Security Architecture Planning",
                        "duration": timedelta(days=1)
                    }
                ]
            }
        ]

    def _get_design_tasks(self) -> List[Dict[str, Any]]:
        """Get detailed design phase tasks."""
        return [
            {
                "id": "DES-001",
                "name": "Database Schema Design",
                "description": "Design database schema for task management system",
                "type": TaskType.DATABASE,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=3),
                "resources": ["Backend Developer"],
                "deliverables": ["Database Schema", "ERD Diagram"],
                "dependencies": ["PLAN-002"],
                "subtasks": [
                    {
                        "id": "DES-001-1",
                        "name": "Entity Relationship Design",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DES-001-2",
                        "name": "Schema Optimization",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DES-001-3",
                        "name": "Index Planning",
                        "duration": timedelta(days=1)
                    }
                ]
            },
            {
                "id": "DES-002",
                "name": "API Design",
                "description": "Design RESTful API endpoints",
                "type": TaskType.BACKEND,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=3),
                "resources": ["Backend Developer"],
                "deliverables": ["API Documentation", "Endpoint Specifications"],
                "dependencies": ["DES-001"],
                "subtasks": [
                    {
                        "id": "DES-002-1",
                        "name": "Endpoint Definition",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DES-002-2",
                        "name": "Authentication Design",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DES-002-3",
                        "name": "API Documentation",
                        "duration": timedelta(days=1)
                    }
                ]
            }
        ]

    def _get_development_tasks(self) -> List[Dict[str, Any]]:
        """Get detailed development phase tasks."""
        return [
            {
                "id": "DEV-001",
                "name": "Backend Core Implementation",
                "description": "Implement core backend functionality",
                "type": TaskType.BACKEND,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=5),
                "resources": ["Backend Developer"],
                "deliverables": ["Core Backend Services", "Database Integration"],
                "dependencies": ["DES-002"],
                "subtasks": [
                    {
                        "id": "DEV-001-1",
                        "name": "Database Setup",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DEV-001-2",
                        "name": "Authentication Implementation",
                        "duration": timedelta(days=2)
                    },
                    {
                        "id": "DEV-001-3",
                        "name": "Core API Implementation",
                        "duration": timedelta(days=2)
                    }
                ]
            },
            {
                "id": "DEV-002",
                "name": "Frontend Core Implementation",
                "description": "Implement core frontend functionality",
                "type": TaskType.FRONTEND,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=5),
                "resources": ["Frontend Developer"],
                "deliverables": ["Core UI Components", "Basic Functionality"],
                "dependencies": ["DEV-001"],
                "subtasks": [
                    {
                        "id": "DEV-002-1",
                        "name": "Project Setup",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DEV-002-2",
                        "name": "Core Components",
                        "duration": timedelta(days=2)
                    },
                    {
                        "id": "DEV-002-3",
                        "name": "API Integration",
                        "duration": timedelta(days=2)
                    }
                ]
            }
        ]

    def _get_testing_tasks(self) -> List[Dict[str, Any]]:
        """Get detailed testing phase tasks."""
        return [
            {
                "id": "TEST-001",
                "name": "Backend Testing",
                "description": "Implement and run backend tests",
                "type": TaskType.TESTING,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=3),
                "resources": ["QA Engineer", "Backend Developer"],
                "deliverables": ["Test Cases", "Test Results"],
                "dependencies": ["DEV-001"],
                "subtasks": [
                    {
                        "id": "TEST-001-1",
                        "name": "Unit Tests",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "TEST-001-2",
                        "name": "Integration Tests",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "TEST-001-3",
                        "name": "API Tests",
                        "duration": timedelta(days=1)
                    }
                ]
            },
            {
                "id": "TEST-002",
                "name": "Frontend Testing",
                "description": "Implement and run frontend tests",
                "type": TaskType.TESTING,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=3),
                "resources": ["QA Engineer", "Frontend Developer"],
                "deliverables": ["Test Cases", "Test Results"],
                "dependencies": ["DEV-002"],
                "subtasks": [
                    {
                        "id": "TEST-002-1",
                        "name": "Component Tests",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "TEST-002-2",
                        "name": "E2E Tests",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "TEST-002-3",
                        "name": "UI Tests",
                        "duration": timedelta(days=1)
                    }
                ]
            }
        ]

    def _get_deployment_tasks(self) -> List[Dict[str, Any]]:
        """Get detailed deployment phase tasks."""
        return [
            {
                "id": "DEP-001",
                "name": "Infrastructure Setup",
                "description": "Set up deployment infrastructure",
                "type": TaskType.DEVOPS,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=2),
                "resources": ["DevOps Engineer"],
                "deliverables": ["Infrastructure Configuration", "Deployment Scripts"],
                "dependencies": ["TEST-001", "TEST-002"],
                "subtasks": [
                    {
                        "id": "DEP-001-1",
                        "name": "Cloud Setup",
                        "duration": timedelta(days=1)
                    },
                    {
                        "id": "DEP-001-2",
                        "name": "CI/CD Setup",
                        "duration": timedelta(days=1)
                    }
                ]
            },
            {
                "id": "DEP-002",
                "name": "Application Deployment",
                "description": "Deploy application to production",
                "type": TaskType.DEVOPS,
                "priority": TaskPriority.HIGH,
                "duration": timedelta(days=1),
                "resources": ["DevOps Engineer"],
                "deliverables": ["Deployed Application", "Deployment Documentation"],
                "dependencies": ["DEP-001"],
                "subtasks": [
                    {
                        "id": "DEP-002-1",
                        "name": "Database Migration",
                        "duration": timedelta(hours=2)
                    },
                    {
                        "id": "DEP-002-2",
                        "name": "Application Deployment",
                        "duration": timedelta(hours=4)
                    },
                    {
                        "id": "DEP-002-3",
                        "name": "Post-deployment Testing",
                        "duration": timedelta(hours=2)
                    }
                ]
            }
        ]

    def _get_feature_specific_tasks(self, feature: str) -> List[Dict[str, Any]]:
        """Get tasks specific to a feature."""
        # Implementation for feature-specific tasks
        feature_tasks = {
            "notifications": self._get_notification_tasks(),
            "file_attachments": self._get_file_attachment_tasks(),
            "reporting": self._get_reporting_tasks(),
            # Add more features as needed
        }
        return feature_tasks.get(feature, [])

    def _integrate_feature_tasks(self, phases: Dict[str, Any], feature_tasks: List[Dict[str, Any]]):
        """Integrate feature-specific tasks into phases."""
        for task in feature_tasks:
            phase = task.pop("phase", "development")
            phases[phase]["tasks"].append(task)

    def _update_dependencies(self, phases: Dict[str, Any]):
        """Update task dependencies based on phase relationships."""
        for phase_name, phase in phases.items():
            for task in phase["tasks"]:
                if not task.get("dependencies"):
                    task["dependencies"] = []
                # Add phase dependencies
                if phase.get("dependencies"):
                    previous_phase_tasks = []
                    for dep_phase in phase["dependencies"]:
                        previous_phase_tasks.extend(
                            [t["id"] for t in phases[dep_phase]["tasks"]]
                        )
                    task["dependencies"].extend(previous_phase_tasks)