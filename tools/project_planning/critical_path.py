# tools/project_planning/critical_path.py

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import networkx as nx
from enum import Enum
from .base import (
    BaseProjectPlanningTool,
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    ProjectPhase,
    PlanningError
)

class PathType(Enum):
    CRITICAL = "critical"
    NEAR_CRITICAL = "near_critical"
    NON_CRITICAL = "non_critical"

class SlackType(Enum):
    TOTAL = "total"
    FREE = "free"
    INDEPENDENT = "independent"

class CriticalPathAnalyzer(BaseProjectPlanningTool):
    """Tool for analyzing and managing project critical path."""

    def __init__(self):
        super().__init__("CriticalPathAnalyzer")
        self.graph = None
        self.critical_path = None
        self.slack_values = {}
        
    def analyze_critical_path(self, 
                            tasks: List[Dict[str, Any]], 
                            start_date: datetime) -> Dict[str, Any]:
        """
        Perform comprehensive critical path analysis.
        
        Args:
            tasks: List of project tasks with dependencies
            start_date: Project start date
            
        Returns:
            Dictionary containing critical path analysis
        """
        self.logger.info("Starting critical path analysis")
        try:
            # Create network graph
            self.graph = self._create_network_graph(tasks)
            
            # Calculate critical path
            self.critical_path = self._calculate_critical_path()
            
            # Calculate slack times
            self.slack_values = self._calculate_slack_times(tasks, start_date)
            
            # Perform full analysis
            analysis = {
                "critical_path": {
                    "tasks": self.critical_path,
                    "duration": self._calculate_path_duration(self.critical_path),
                    "risk_level": self._assess_critical_path_risk()
                },
                "near_critical_paths": self._identify_near_critical_paths(),
                "slack_analysis": self.slack_values,
                "path_compression": self._analyze_compression_options(),
                "risk_areas": self._identify_risk_areas(),
                "metrics": self._calculate_path_metrics(),
                "recommendations": self._generate_recommendations()
            }
            
            self.logger.info("Critical path analysis completed")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in critical path analysis: {str(e)}")
            raise PlanningError(f"Critical path analysis failed: {str(e)}")

    def _create_network_graph(self, tasks: List[Dict[str, Any]]) -> nx.DiGraph:
        """Create network graph from tasks."""
        self.logger.debug("Creating network graph")
        try:
            G = nx.DiGraph()
            
            # Add nodes
            for task in tasks:
                G.add_node(
                    task["id"],
                    **{k: v for k, v in task.items() if k != "dependencies"}
                )
            
            # Add edges
            for task in tasks:
                for dep in task.get("dependencies", []):
                    G.add_edge(dep, task["id"])
            
            self.logger.debug(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            return G
            
        except Exception as e:
            self.logger.error(f"Error creating network graph: {str(e)}")
            raise

    def _calculate_critical_path(self) -> List[str]:
        """Calculate the critical path using longest path algorithm."""
        self.logger.debug("Calculating critical path")
        try:
            if not nx.is_directed_acyclic_graph(self.graph):
                raise PlanningError("Graph contains cycles")
            
            # Find start and end nodes
            start_nodes = [n for n in self.graph.nodes() if not list(self.graph.predecessors(n))]
            end_nodes = [n for n in self.graph.nodes() if not list(self.graph.successors(n))]
            
            # Calculate longest path
            critical_path = None
            max_duration = timedelta(days=0)
            
            for start in start_nodes:
                for end in end_nodes:
                    for path in nx.all_simple_paths(self.graph, start, end):
                        duration = self._calculate_path_duration(path)
                        if duration > max_duration:
                            max_duration = duration
                            critical_path = path
            
            self.logger.info(f"Critical path identified with duration: {max_duration.days} days")
            return critical_path
            
        except Exception as e:
            self.logger.error(f"Error calculating critical path: {str(e)}")
            raise

    def _calculate_slack_times(self, 
                             tasks: List[Dict[str, Any]], 
                             start_date: datetime) -> Dict[str, Dict[str, timedelta]]:
        """Calculate different types of slack for each task."""
        self.logger.debug("Calculating slack times")
        try:
            slack_times = {}
            earliest_starts = self._calculate_earliest_starts(start_date)
            latest_starts = self._calculate_latest_starts(start_date)
            
            for task_id in self.graph.nodes():
                task_data = self.graph.nodes[task_id]
                duration = task_data["duration"]
                
                # Calculate total slack
                total_slack = latest_starts[task_id] - earliest_starts[task_id]
                
                # Calculate free slack
                free_slack = self._calculate_free_slack(
                    task_id,
                    earliest_starts,
                    duration
                )
                
                slack_times[task_id] = {
                    "total_slack": total_slack,
                    "free_slack": free_slack,
                    "is_critical": total_slack.days == 0
                }
            
            self.logger.debug(f"Calculated slack times for {len(slack_times)} tasks")
            return slack_times
            
        except Exception as e:
            self.logger.error(f"Error calculating slack times: {str(e)}")
            raise

    def _calculate_earliest_starts(self, start_date: datetime) -> Dict[str, datetime]:
        """Calculate earliest start times for all tasks."""
        self.logger.debug("Calculating earliest start times")
        earliest_starts = {}
        
        try:
            for task_id in nx.topological_sort(self.graph):
                if not list(self.graph.predecessors(task_id)):
                    earliest_starts[task_id] = start_date
                else:
                    # Find max of predecessor finish times
                    pred_finish_times = []
                    for pred in self.graph.predecessors(task_id):
                        pred_duration = self.graph.nodes[pred]["duration"]
                        pred_finish = earliest_starts[pred] + pred_duration
                        pred_finish_times.append(pred_finish)
                    
                    earliest_starts[task_id] = max(pred_finish_times)
            
            return earliest_starts
            
        except Exception as e:
            self.logger.error(f"Error calculating earliest starts: {str(e)}")
            raise

    def _calculate_latest_starts(self, start_date: datetime) -> Dict[str, datetime]:
        """Calculate latest start times for all tasks."""
        self.logger.debug("Calculating latest start times")
        latest_starts = {}
        
        try:
            # First, calculate project end date
            end_date = start_date
            for task_id in self.graph.nodes():
                task_data = self.graph.nodes[task_id]
                earliest_start = self._calculate_earliest_starts(start_date)[task_id]
                task_end = earliest_start + task_data["duration"]
                end_date = max(end_date, task_end)
            
            # Calculate latest starts backwards
            for task_id in reversed(list(nx.topological_sort(self.graph))):
                if not list(self.graph.successors(task_id)):
                    # End tasks can start as late as end_date minus their duration
                    task_duration = self.graph.nodes[task_id]["duration"]
                    latest_starts[task_id] = end_date - task_duration
                else:
                    # Find min of successor start times
                    succ_start_times = []
                    for succ in self.graph.successors(task_id):
                        succ_start = latest_starts[succ]
                        task_duration = self.graph.nodes[task_id]["duration"]
                        latest_start = succ_start - task_duration
                        succ_start_times.append(latest_start)
                    
                    latest_starts[task_id] = min(succ_start_times)
            
            return latest_starts
            
        except Exception as e:
            self.logger.error(f"Error calculating latest starts: {str(e)}")
            raise

    def _calculate_free_slack(self, 
                            task_id: str,
                            earliest_starts: Dict[str, datetime],
                            duration: timedelta) -> timedelta:
        """Calculate free slack for a task."""
        try:
            if not list(self.graph.successors(task_id)):
                return timedelta(days=0)
            
            # Find earliest successor start
            earliest_succ_start = min(
                earliest_starts[succ]
                for succ in self.graph.successors(task_id)
            )
            
            # Calculate free slack
            task_finish = earliest_starts[task_id] + duration
            free_slack = earliest_succ_start - task_finish
            
            return max(timedelta(days=0), free_slack)
            
        except Exception as e:
            self.logger.error(f"Error calculating free slack: {str(e)}")
            return timedelta(days=0)

    def _identify_near_critical_paths(self) -> List[Dict[str, Any]]:
        """Identify paths that are close to becoming critical."""
        self.logger.debug("Identifying near-critical paths")
        try:
            near_critical = []
            critical_duration = self._calculate_path_duration(self.critical_path)
            threshold = timedelta(days=critical_duration.days * 0.1)  # 10% threshold
            
            # Find all paths
            start_nodes = [n for n in self.graph.nodes() if not list(self.graph.predecessors(n))]
            end_nodes = [n for n in self.graph.nodes() if not list(self.graph.successors(n))]
            
            for start in start_nodes:
                for end in end_nodes:
                    for path in nx.all_simple_paths(self.graph, start, end):
                        if path != self.critical_path:
                            duration = self._calculate_path_duration(path)
                            if critical_duration - duration <= threshold:
                                near_critical.append({
                                    "path": path,
                                    "duration": duration,
                                    "gap_to_critical": critical_duration - duration,
                                    "risk_level": "HIGH" if critical_duration - duration <= threshold/2 else "MEDIUM"
                                })
            
            self.logger.debug(f"Found {len(near_critical)} near-critical paths")
            return sorted(near_critical, key=lambda x: x["gap_to_critical"])
            
        except Exception as e:
            self.logger.error(f"Error identifying near-critical paths: {str(e)}")
            return []

    def _analyze_compression_options(self) -> Dict[str, Any]:
        """Analyze options for compressing the critical path."""
        self.logger.debug("Analyzing compression options")
        try:
            options = {
                "task_compression": [],
                "parallel_execution": [],
                "resource_optimization": []
            }
            
            # Analyze task compression possibilities
            for task_id in self.critical_path:
                task_data = self.graph.nodes[task_id]
                if task_data["duration"].days > 1:
                    options["task_compression"].append({
                        "task_id": task_id,
                        "current_duration": task_data["duration"].days,
                        "potential_reduction": task_data["duration"].days * 0.2,
                        "method": "Add resources",
                        "risk_level": "MEDIUM"
                    })
            
            # Analyze parallel execution possibilities
            for i in range(len(self.critical_path)-1):
                task_id = self.critical_path[i]
                next_task = self.critical_path[i+1]
                if not any(self.graph.has_edge(task_id, n) for n in self.graph.nodes() if n != next_task):
                    options["parallel_execution"].append({
                        "tasks": [task_id, next_task],
                        "potential_saving": min(
                            self.graph.nodes[task_id]["duration"].days,
                            self.graph.nodes[next_task]["duration"].days
                        ),
                        "risk_level": "HIGH"
                    })
            
            # Analyze resource optimization
            critical_tasks = [self.graph.nodes[task_id] for task_id in self.critical_path]
            resource_usage = {}
            for task in critical_tasks:
                for resource in task.get("resources", []):
                    resource_usage[resource] = resource_usage.get(resource, 0) + 1
            
            for resource, count in resource_usage.items():
                if count > 1:
                    options["resource_optimization"].append({
                        "resource": resource,
                        "usage_count": count,
                        "recommendation": "Consider resource optimization or addition",
                        "potential_impact": "MEDIUM"
                    })
            
            return options
            
        except Exception as e:
            self.logger.error(f"Error analyzing compression options: {str(e)}")
            return {"task_compression": [], "parallel_execution": [], "resource_optimization": []}
        
    def _calculate_path_duration(self, path: List[str]) -> timedelta:
        """Calculate the total duration of a path."""
        try:
            return sum(
                (self.graph.nodes[task_id]["duration"] for task_id in path),
                start=timedelta()
            )
        except Exception as e:
            self.logger.error(f"Error calculating path duration: {str(e)}")
            return timedelta()

    def _assess_critical_path_risk(self) -> Dict[str, Any]:
        """Assess risks associated with the critical path."""
        self.logger.debug("Assessing critical path risks")
        try:
            risk_assessment = {
                "overall_risk_level": "MEDIUM",
                "risk_factors": [],
                "contingency_needed": False
            }
            
            # Check duration
            path_duration = self._calculate_path_duration(self.critical_path)
            if path_duration.days > 30:
                risk_assessment["risk_factors"].append({
                    "factor": "Long Duration",
                    "level": "HIGH",
                    "description": "Critical path exceeds 30 days"
                })
            
            # Check complexity
            complex_tasks = sum(
                1 for task_id in self.critical_path
                if self.graph.nodes[task_id].get("complexity", TaskComplexity.MEDIUM) 
                in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH]
            )
            if complex_tasks > len(self.critical_path) * 0.3:
                risk_assessment["risk_factors"].append({
                    "factor": "High Complexity",
                    "level": "HIGH",
                    "description": f"{complex_tasks} complex tasks on critical path"
                })
            
            # Check resource dependencies
            resource_dependencies = self._analyze_resource_dependencies()
            if resource_dependencies["high_dependency_count"] > 0:
                risk_assessment["risk_factors"].append({
                    "factor": "Resource Dependencies",
                    "level": "MEDIUM",
                    "description": "Multiple tasks dependent on same resources"
                })
            
            # Update overall risk level
            if any(factor["level"] == "HIGH" for factor in risk_assessment["risk_factors"]):
                risk_assessment["overall_risk_level"] = "HIGH"
                risk_assessment["contingency_needed"] = True
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing critical path risk: {str(e)}")
            return {"overall_risk_level": "UNKNOWN", "risk_factors": [], "contingency_needed": True}

    def _analyze_resource_dependencies(self) -> Dict[str, Any]:
        """Analyze resource dependencies in critical path."""
        self.logger.debug("Analyzing resource dependencies")
        try:
            resource_usage = {}
            high_dependency_resources = []
            
            # Count resource usage
            for task_id in self.critical_path:
                task_data = self.graph.nodes[task_id]
                for resource in task_data.get("resources", []):
                    resource_usage[resource] = resource_usage.get(resource, 0) + 1
            
            # Identify high dependencies
            for resource, count in resource_usage.items():
                if count > 2:  # Resource used in more than 2 critical path tasks
                    high_dependency_resources.append({
                        "resource": resource,
                        "usage_count": count,
                        "impact_level": "HIGH" if count > 3 else "MEDIUM"
                    })
            
            return {
                "resource_usage": resource_usage,
                "high_dependency_resources": high_dependency_resources,
                "high_dependency_count": len(high_dependency_resources)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing resource dependencies: {str(e)}")
            return {"resource_usage": {}, "high_dependency_resources": [], "high_dependency_count": 0}

    def _identify_risk_areas(self) -> List[Dict[str, Any]]:
        """Identify risk areas in the critical path."""
        self.logger.debug("Identifying critical path risk areas")
        try:
            risk_areas = []
            
            # Check for task clusters
            current_cluster = []
            current_resources = set()
            
            for task_id in self.critical_path:
                task_data = self.graph.nodes[task_id]
                task_resources = set(task_data.get("resources", []))
                
                if task_resources & current_resources:  # Resource overlap
                    current_cluster.append(task_id)
                    current_resources.update(task_resources)
                else:
                    if len(current_cluster) > 1:
                        risk_areas.append({
                            "type": "Resource Cluster",
                            "tasks": current_cluster.copy(),
                            "resources": list(current_resources),
                            "risk_level": "HIGH" if len(current_cluster) > 2 else "MEDIUM"
                        })
                    current_cluster = [task_id]
                    current_resources = task_resources
            
            # Check for complexity clusters
            complexity_cluster = []
            for task_id in self.critical_path:
                task_data = self.graph.nodes[task_id]
                if task_data.get("complexity", TaskComplexity.MEDIUM) in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH]:
                    complexity_cluster.append(task_id)
                else:
                    if len(complexity_cluster) > 1:
                        risk_areas.append({
                            "type": "Complexity Cluster",
                            "tasks": complexity_cluster.copy(),
                            "risk_level": "HIGH"
                        })
                    complexity_cluster = []
            
            return risk_areas
            
        except Exception as e:
            self.logger.error(f"Error identifying risk areas: {str(e)}")
            return []

    def _calculate_path_metrics(self) -> Dict[str, Any]:
        """Calculate various metrics for the critical path."""
        self.logger.debug("Calculating critical path metrics")
        try:
            return {
                "total_duration": self._calculate_path_duration(self.critical_path),
                "task_count": len(self.critical_path),
                "average_task_duration": self._calculate_path_duration(self.critical_path) / len(self.critical_path),
                "high_complexity_ratio": sum(
                    1 for task_id in self.critical_path
                    if self.graph.nodes[task_id].get("complexity", TaskComplexity.MEDIUM) 
                    in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH]
                ) / len(self.critical_path),
                "resource_dependency_score": len(self._analyze_resource_dependencies()["high_dependency_resources"]),
                "risk_area_count": len(self._identify_risk_areas())
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating path metrics: {str(e)}")
            return {}