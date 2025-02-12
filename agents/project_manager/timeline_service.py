from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
import networkx as nx
from core.logging.logger import setup_logger

class TimelineService:
    """Service for timeline generation and resource management."""

    def __init__(self):
        self.logger = setup_logger("timeline.service")
        self.logger.info("Initializing TimelineService")

    def create_timeline(self, tasks: List[Dict[str, Any]], start_date: datetime) -> Dict[str, Any]:
        """Generate a project timeline with critical path calculation."""
        self.logger.info("Starting timeline creation")
        self.logger.debug(f"Processing {len(tasks)} tasks from start date: {start_date}")
        
        try:
            # Create directed graph for critical path calculation
            G = self._create_dependency_graph(tasks)
            self.logger.debug("Dependency graph created")
            
            critical_path = self._calculate_critical_path(G, tasks)
            self.logger.debug(f"Critical path calculated: {len(critical_path)} tasks")
            
            # Calculate earliest start and finish times
            timeline = self._calculate_task_dates(tasks, start_date)
            self.logger.debug("Task dates calculated")
            
            # Identify milestones
            milestones = self._identify_milestones(timeline)
            self.logger.debug(f"Identified {len(milestones)} milestones")
            
            result = {
                "timeline": timeline,
                "critical_path": critical_path,
                "milestones": milestones,
                "start_date": start_date,
                "end_date": self._calculate_end_date(timeline)
            }
            
            self.logger.info("Timeline creation completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating timeline: {str(e)}")
            raise

    def allocate_resources(self, timeline: Dict[str, Any], resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Allocate resources to tasks and balance workload."""
        self.logger.info("Starting resource allocation")
        self.logger.debug(f"Allocating {len(resources)} resources")
        
        try:
            # Create resource availability timeline
            resource_timeline = self._initialize_resource_timeline(resources, timeline)
            self.logger.debug("Resource timeline initialized")
            
            # Allocate resources to tasks
            allocation = self._allocate_tasks_to_resources(timeline["timeline"], resource_timeline)
            self.logger.debug("Initial resource allocation completed")
            
            # Balance resource loading
            balanced_allocation = self._balance_resources(allocation)
            self.logger.debug("Resource balancing completed")
            
            # Calculate resource utilization
            utilization = self._calculate_resource_utilization(balanced_allocation)
            self.logger.debug("Resource utilization calculated")
            
            overallocated = self._identify_overallocated_resources(utilization)
            if overallocated:
                self.logger.warning(f"Found {len(overallocated)} overallocated resources")
            
            result = {
                "allocation": balanced_allocation,
                "utilization": utilization,
                "overallocated_resources": overallocated
            }
            
            self.logger.info("Resource allocation completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error allocating resources: {str(e)}")
            raise

    def _create_dependency_graph(self, tasks: List[Dict[str, Any]]) -> nx.DiGraph:
        """Create a directed graph representing task dependencies."""
        self.logger.debug("Creating dependency graph")
        try:
            G = nx.DiGraph()
            
            for task in tasks:
                G.add_node(task["id"], duration=task["duration"])
                for dep in task.get("dependencies", []):
                    G.add_edge(dep, task["id"])
            
            self.logger.debug(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            return G
        except Exception as e:
            self.logger.error(f"Error creating dependency graph: {str(e)}")
            raise

    def _calculate_critical_path(self, G: nx.DiGraph, tasks: List[Dict[str, Any]]) -> List[str]:
        """Calculate the critical path using networkx."""
        self.logger.debug("Calculating critical path")
        try:
            task_dict = {task["id"]: task for task in tasks}
            
            # Convert durations to weights
            for u, v in G.edges():
                G[u][v]["weight"] = task_dict[v]["duration"].days
            
            critical_path = nx.dag_longest_path(G)
            self.logger.debug(f"Critical path calculated: {len(critical_path)} tasks")
            return critical_path
        except nx.NetworkXError as e:
            self.logger.error(f"NetworkX error calculating critical path: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error calculating critical path: {str(e)}")
            raise

    def _calculate_task_dates(self, tasks: List[Dict[str, Any]], start_date: datetime) -> List[Dict[str, Any]]:
        """Calculate earliest start and finish dates for tasks."""
        self.logger.debug(f"Calculating task dates for {len(tasks)} tasks from {start_date}")
        try:
            task_dates = []
            task_dict = {task["id"]: task for task in tasks}
            
            def get_task_earliest_start(task_id: str, memo: Dict[str, datetime]) -> datetime:
                if task_id in memo:
                    return memo[task_id]
                
                task = task_dict[task_id]
                if not task.get("dependencies"):
                    memo[task_id] = start_date
                    self.logger.debug(f"Task {task_id} has no dependencies, starting at project start")
                    return start_date
                
                # Get maximum end date of dependencies
                self.logger.debug(f"Calculating dependency dates for task {task_id}")
                dep_dates = [
                    get_task_earliest_start(dep, memo) + task_dict[dep]["duration"]
                    for dep in task["dependencies"]
                ]
                
                earliest_start = max(dep_dates) if dep_dates else start_date
                memo[task_id] = earliest_start
                self.logger.debug(f"Task {task_id} earliest start: {earliest_start}")
                return earliest_start
            
            memo = {}
            for task in tasks:
                earliest_start = get_task_earliest_start(task["id"], memo)
                earliest_finish = earliest_start + task["duration"]
                
                task_dates.append({
                    **task,
                    "earliest_start": earliest_start,
                    "earliest_finish": earliest_finish
                })
                
            self.logger.info(f"Task dates calculated for {len(tasks)} tasks")
            return task_dates
            
        except Exception as e:
            self.logger.error(f"Error calculating task dates: {str(e)}")
            raise

    def _identify_milestones(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify project milestones."""
        self.logger.debug("Identifying project milestones")
        try:
            milestones = []
            
            # Phase end milestones
            phase_ends = defaultdict(list)
            for task in timeline:
                phase = task.get("phase", "unknown")
                phase_ends[phase].append(task["earliest_finish"])
            
            self.logger.debug(f"Found {len(phase_ends)} phases for milestone creation")
            
            for phase, dates in phase_ends.items():
                milestone_date = max(dates)
                milestones.append({
                    "name": f"{phase.capitalize()} Phase Complete",
                    "date": milestone_date,
                    "type": "phase_end"
                })
                self.logger.debug(f"Added phase end milestone for {phase} at {milestone_date}")
            
            # Critical deliverable milestones
            high_priority_tasks = [
                task for task in timeline 
                if task.get("priority") == "HIGH" and task.get("deliverables")
            ]
            self.logger.debug(f"Found {len(high_priority_tasks)} high-priority tasks with deliverables")
            
            for task in high_priority_tasks:
                milestones.append({
                    "name": f"Complete {task['name']}",
                    "date": task["earliest_finish"],
                    "type": "deliverable",
                    "deliverables": task["deliverables"]
                })
            
            sorted_milestones = sorted(milestones, key=lambda x: x["date"])
            self.logger.info(f"Identified {len(sorted_milestones)} total milestones")
            return sorted_milestones
            
        except Exception as e:
            self.logger.error(f"Error identifying milestones: {str(e)}")
            raise

    def _initialize_resource_timeline(
        self, resources: List[Dict[str, Any]], timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initialize resource availability timeline."""
        self.logger.debug("Initializing resource timeline")
        try:
            start_date = timeline["start_date"]
            end_date = timeline["end_date"]
            days = (end_date - start_date).days + 1
            
            self.logger.debug(f"Timeline period: {days} days ({start_date} to {end_date})")
            
            availability = {}
            for resource in resources:
                availability[resource["id"]] = {
                    "capacity": resource["capacity"],
                    "skills": resource["skills"],
                    "daily_allocation": [0] * days
                }
                self.logger.debug(f"Initialized timeline for resource {resource['id']}")
            
            self.logger.info(f"Resource timeline initialized for {len(resources)} resources")
            return availability
            
        except Exception as e:
            self.logger.error(f"Error initializing resource timeline: {str(e)}")
            raise

    def _allocate_tasks_to_resources(
        self, tasks: List[Dict[str, Any]], resource_timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Allocate tasks to resources based on skills and availability."""
        self.logger.debug(f"Allocating {len(tasks)} tasks to resources")
        try:
            allocation = defaultdict(list)
            
            for task in tasks:
                required_skills = task.get("required_skills", [])
                duration = task["duration"].days
                
                self.logger.debug(f"Finding suitable resources for task {task['id']} (duration: {duration} days)")
                
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
                    self.logger.debug(f"Task {task['id']} allocated to resource {resource_id}")
                else:
                    self.logger.warning(f"No suitable resource found for task {task['id']}")
            
            self.logger.info(f"Tasks allocated to {len(allocation)} resources")
            return dict(allocation)
            
        except Exception as e:
            self.logger.error(f"Error allocating tasks to resources: {str(e)}")
            raise

    def _balance_resources(self, allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Balance resource workload."""
        self.logger.debug("Balancing resource workload")
        try:
            balanced = {}
            
            for resource_id, tasks in allocation.items():
                self.logger.debug(f"Balancing workload for resource {resource_id}")
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
                self.logger.debug(f"Resource {resource_id}: {len(sorted_tasks)} tasks prioritized")
            
            self.logger.info("Resource workload balancing completed")
            return balanced
            
        except Exception as e:
            self.logger.error(f"Error balancing resources: {str(e)}")
            raise

    def _calculate_resource_utilization(self, allocation: Dict[str, Any]) -> Dict[str, float]:
        """Calculate resource utilization percentages."""
        self.logger.debug("Calculating resource utilization")
        try:
            utilization = {}
            
            for resource_id, tasks in allocation.items():
                total_days = sum(task["duration"].days for task in tasks)
                utilization[resource_id] = total_days / 20  # Assuming 20 working days/month
                self.logger.debug(f"Resource {resource_id} utilization: {utilization[resource_id]:.2%}")
            
            self.logger.info(f"Utilization calculated for {len(utilization)} resources")
            return utilization
            
        except Exception as e:
            self.logger.error(f"Error calculating resource utilization: {str(e)}")
            raise

    def _identify_overallocated_resources(self, utilization: Dict[str, float]) -> List[str]:
        """Identify resources with over 100% utilization."""
        self.logger.debug("Checking for overallocated resources")
        try:
            overallocated = [
                resource_id
                for resource_id, util in utilization.items()
                if util > 1.0
            ]
            
            if overallocated:
                self.logger.warning(f"Found {len(overallocated)} overallocated resources: {overallocated}")
            else:
                self.logger.info("No overallocated resources found")
                
            return overallocated
            
        except Exception as e:
            self.logger.error(f"Error identifying overallocated resources: {str(e)}")
            raise

    def _calculate_end_date(self, timeline: List[Dict[str, Any]]) -> datetime:
        """Calculate project end date based on task finish dates."""
        self.logger.debug("Calculating project end date")
        try:
            end_date = max(task["earliest_finish"] for task in timeline)
            self.logger.debug(f"Project end date calculated: {end_date}")
            return end_date
        except Exception as e:
            self.logger.error(f"Error calculating end date: {str(e)}")
            raise