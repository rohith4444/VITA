from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
import networkx as nx

class TimelineService:
    """Service for timeline generation and resource management."""

    def create_timeline(self, tasks: List[Dict[str, Any]], start_date: datetime) -> Dict[str, Any]:
        """
        Generate a project timeline with critical path calculation.
        
        Args:
            tasks: List of project tasks with dependencies
            start_date: Project start date
        """
        # Create directed graph for critical path calculation
        G = self._create_dependency_graph(tasks)
        critical_path = self._calculate_critical_path(G, tasks)
        
        # Calculate earliest start and finish times
        timeline = self._calculate_task_dates(tasks, start_date)
        
        # Identify milestones
        milestones = self._identify_milestones(timeline)
        
        return {
            "timeline": timeline,
            "critical_path": critical_path,
            "milestones": milestones,
            "start_date": start_date,
            "end_date": self._calculate_end_date(timeline)
        }

    def allocate_resources(self, timeline: Dict[str, Any], resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Allocate resources to tasks and balance workload.
        
        Args:
            timeline: Project timeline with tasks
            resources: Available resources with skills and capacity
        """
        # Create resource availability timeline
        resource_timeline = self._initialize_resource_timeline(resources, timeline)
        
        # Allocate resources to tasks
        allocation = self._allocate_tasks_to_resources(timeline["timeline"], resource_timeline)
        
        # Balance resource loading
        balanced_allocation = self._balance_resources(allocation)
        
        # Calculate resource utilization
        utilization = self._calculate_resource_utilization(balanced_allocation)
        
        return {
            "allocation": balanced_allocation,
            "utilization": utilization,
            "overallocated_resources": self._identify_overallocated_resources(utilization)
        }

    def _create_dependency_graph(self, tasks: List[Dict[str, Any]]) -> nx.DiGraph:
        """Create a directed graph representing task dependencies."""
        G = nx.DiGraph()
        
        for task in tasks:
            G.add_node(task["id"], duration=task["duration"])
            for dep in task.get("dependencies", []):
                G.add_edge(dep, task["id"])
        
        return G

    def _calculate_critical_path(self, G: nx.DiGraph, tasks: List[Dict[str, Any]]) -> List[str]:
        """Calculate the critical path using networkx."""
        task_dict = {task["id"]: task for task in tasks}
        
        # Convert durations to weights
        for u, v in G.edges():
            G[u][v]["weight"] = task_dict[v]["duration"].days
        
        try:
            critical_path = nx.dag_longest_path(G)
            return critical_path
        except nx.NetworkXError:
            # Handle cycles in dependencies
            return []

    def _calculate_task_dates(self, tasks: List[Dict[str, Any]], start_date: datetime) -> List[Dict[str, Any]]:
        """Calculate earliest start and finish dates for tasks."""
        task_dates = []
        task_dict = {task["id"]: task for task in tasks}
        
        def get_task_earliest_start(task_id: str, memo: Dict[str, datetime]) -> datetime:
            if task_id in memo:
                return memo[task_id]
            
            task = task_dict[task_id]
            if not task.get("dependencies"):
                memo[task_id] = start_date
                return start_date
            
            # Get maximum end date of dependencies
            dep_dates = [
                get_task_earliest_start(dep, memo) + task_dict[dep]["duration"]
                for dep in task["dependencies"]
            ]
            
            earliest_start = max(dep_dates) if dep_dates else start_date
            memo[task_id] = earliest_start
            return earliest_start
        
        memo = {}
        for task in tasks:
            earliest_start = get_task_earliest_start(task["id"], memo)
            task_dates.append({
                **task,
                "earliest_start": earliest_start,
                "earliest_finish": earliest_start + task["duration"]
            })
        
        return task_dates

    def _identify_milestones(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify project milestones."""
        milestones = []
        
        # Phase end milestones
        phase_ends = defaultdict(list)
        for task in timeline:
            phase = task.get("phase", "unknown")
            phase_ends[phase].append(task["earliest_finish"])
        
        for phase, dates in phase_ends.items():
            milestones.append({
                "name": f"{phase.capitalize()} Phase Complete",
                "date": max(dates),
                "type": "phase_end"
            })
        
        # Critical deliverable milestones
        for task in timeline:
            if task.get("priority") == "HIGH" and task.get("deliverables"):
                milestones.append({
                    "name": f"Complete {task['name']}",
                    "date": task["earliest_finish"],
                    "type": "deliverable",
                    "deliverables": task["deliverables"]
                })
        
        return sorted(milestones, key=lambda x: x["date"])

    def _initialize_resource_timeline(
        self, resources: List[Dict[str, Any]], timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initialize resource availability timeline."""
        start_date = timeline["start_date"]
        end_date = timeline["end_date"]
        days = (end_date - start_date).days + 1
        
        availability = {}
        for resource in resources:
            availability[resource["id"]] = {
                "capacity": resource["capacity"],
                "skills": resource["skills"],
                "daily_allocation": [0] * days
            }
        
        return availability

    def _allocate_tasks_to_resources(
        self, tasks: List[Dict[str, Any]], resource_timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Allocate tasks to resources based on skills and availability."""
        allocation = defaultdict(list)
        
        for task in tasks:
            required_skills = task.get("required_skills", [])
            duration = task["duration"].days
            
            # Find suitable resources
            suitable_resources = []
            for resource_id, resource in resource_timeline.items():
                if all(skill in resource["skills"] for skill in required_skills):
                    suitable_resources.append(resource_id)
            
            if suitable_resources:
                # Allocate to resource with least current allocation
                resource_id = min(
                    suitable_resources,
                    key=lambda r: sum(resource_timeline[r]["daily_allocation"])
                )
                
                allocation[resource_id].append(task)
        
        return dict(allocation)

    def _balance_resources(self, allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Balance resource workload."""
        balanced = {}
        
        for resource_id, tasks in allocation.items():
            # Sort tasks by priority and dependencies
            sorted_tasks = sorted(
                tasks,
                key=lambda x: (
                    x.get("priority", "LOW"),
                    len(x.get("dependencies", []))
                ),
                reverse=True
            )
            
            balanced[resource_id] = sorted_tasks
        
        return balanced

    def _calculate_resource_utilization(self, allocation: Dict[str, Any]) -> Dict[str, float]:
        """Calculate resource utilization percentages."""
        utilization = {}
        
        for resource_id, tasks in allocation.items():
            total_days = sum(task["duration"].days for task in tasks)
            utilization[resource_id] = total_days / 20  # Assuming 20 working days/month
        
        return utilization

    def _identify_overallocated_resources(self, utilization: Dict[str, float]) -> List[str]:
        """Identify resources with over 100% utilization."""
        return [
            resource_id
            for resource_id, util in utilization.items()
            if util > 1.0
        ]

    def _calculate_end_date(self, timeline: List[Dict[str, Any]]) -> datetime:
        """Calculate project end date based on task finish dates."""
        return max(task["earliest_finish"] for task in timeline)