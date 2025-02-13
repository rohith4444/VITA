# tools/project_planning/timeline_generator.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx
from .base import (
    BaseProjectPlanningTool,
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    ProjectPhase,
    PlanningError
)

class TimelineConstraint:
    """Class representing timeline constraints."""
    def __init__(self, 
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 fixed_milestones: Optional[Dict[str, datetime]] = None,
                 blackout_periods: Optional[List[Dict[str, datetime]]] = None):
        self.start_date = start_date
        self.end_date = end_date
        self.fixed_milestones = fixed_milestones or {}
        self.blackout_periods = blackout_periods or []

class TimelineGenerator(BaseProjectPlanningTool):
    """Enhanced tool for generating and managing project timelines."""
    
    def __init__(self):
        super().__init__("TimelineGenerator")
        self.current_timeline = None
        self.constraints = None
    
    def generate_timeline(self, 
                         tasks: List[Dict[str, Any]], 
                         constraints: TimelineConstraint,
                         resource_calendar: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive project timeline with constraints and resource consideration.
        
        Args:
            tasks: List of project tasks
            constraints: Timeline constraints
            resource_calendar: Optional resource availability calendar
        
        Returns:
            Dictionary containing timeline details
        """
        self.logger.info("Starting timeline generation")
        try:
            self.constraints = constraints
            
            # Validate dates and constraints
            if not self._validate_constraints(tasks, constraints):
                raise PlanningError("Invalid timeline constraints")
            
            # Create dependency graph and calculate critical path
            G = self._create_dependency_graph(tasks)
            critical_path = self._calculate_critical_path(G, tasks)
            
            # Calculate task dates considering constraints
            timeline = self._calculate_task_dates(tasks, constraints.start_date, resource_calendar)
            
            # Identify key milestones
            milestones = self._identify_milestones(timeline)
            
            # Calculate schedule metrics
            metrics = self._calculate_schedule_metrics(timeline, critical_path)
            
            # Generate the complete timeline
            self.current_timeline = {
                "tasks": timeline,
                "critical_path": critical_path,
                "milestones": milestones,
                "start_date": constraints.start_date,
                "end_date": self._calculate_end_date(timeline),
                "metrics": metrics,
                "constraints_satisfied": self._verify_constraints(timeline, constraints)
            }
            
            self.logger.info("Timeline generation completed successfully")
            self.logger.debug(f"Timeline metrics: {metrics}")
            
            return self.current_timeline
            
        except Exception as e:
            self.logger.error(f"Error generating timeline: {str(e)}")
            raise PlanningError(f"Timeline generation failed: {str(e)}")
    
    def _validate_constraints(self, tasks: List[Dict[str, Any]], constraints: TimelineConstraint) -> bool:
        """Validate timeline constraints against tasks."""
        try:
            if not constraints.start_date:
                self.logger.error("Start date not specified")
                return False
            
            # Validate fixed milestones
            for task_id, fixed_date in constraints.fixed_milestones.items():
                task = next((t for t in tasks if t["id"] == task_id), None)
                if not task:
                    self.logger.error(f"Fixed milestone task {task_id} not found")
                    return False
            
            # Validate blackout periods
            for period in constraints.blackout_periods:
                if period["start"] >= period["end"]:
                    self.logger.error("Invalid blackout period")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating constraints: {str(e)}")
            return False
    
    def _calculate_task_dates(self, 
                            tasks: List[Dict[str, Any]], 
                            start_date: datetime,
                            resource_calendar: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Calculate task dates considering constraints and resources."""
        try:
            task_dates = []
            task_dict = {task["id"]: task for task in tasks}
            memo = {}
            
            def get_earliest_start(task_id: str) -> datetime:
                # Check memoization
                if task_id in memo:
                    return memo[task_id]
                
                task = task_dict[task_id]
                earliest_date = start_date
                
                # Check fixed milestone constraints
                if task_id in self.constraints.fixed_milestones:
                    return self.constraints.fixed_milestones[task_id]
                
                # Calculate based on dependencies
                if task.get("dependencies"):
                    dep_dates = []
                    for dep_id in task["dependencies"]:
                        dep_start = get_earliest_start(dep_id)
                        dep_task = task_dict[dep_id]
                        dep_finish = dep_start + dep_task["duration"]
                        dep_dates.append(dep_finish)
                    
                    if dep_dates:
                        earliest_date = max(dep_dates)
                
                # Adjust for blackout periods
                earliest_date = self._adjust_for_blackouts(earliest_date)
                
                # Adjust for resource availability if calendar provided
                if resource_calendar:
                    earliest_date = self._adjust_for_resources(
                        earliest_date, 
                        task, 
                        resource_calendar
                    )
                
                memo[task_id] = earliest_date
                return earliest_date
            
            # Calculate dates for all tasks
            for task in tasks:
                earliest_start = get_earliest_start(task["id"])
                task_dates.append({
                    **task,
                    "earliest_start": earliest_start,
                    "earliest_finish": earliest_start + task["duration"],
                    "baseline_start": earliest_start,
                    "baseline_finish": earliest_start + task["duration"]
                })
            
            return task_dates
            
        except Exception as e:
            self.logger.error(f"Error calculating task dates: {str(e)}")
            raise

    def _adjust_for_blackouts(self, date: datetime) -> datetime:
        """Adjust date to account for blackout periods."""
        adjusted_date = date
        
        for period in self.constraints.blackout_periods:
            if period["start"] <= adjusted_date <= period["end"]:
                adjusted_date = period["end"] + timedelta(days=1)
        
        return adjusted_date
    
    def _adjust_for_resources(self, 
                            date: datetime, 
                            task: Dict[str, Any],
                            resource_calendar: Dict[str, Any]) -> datetime:
        """Adjust date based on resource availability."""
        try:
            resources = task.get("resources", [])
            if not resources:
                return date
            
            # Find earliest date when all required resources are available
            max_date = date
            for resource in resources:
                if resource in resource_calendar:
                    availability = resource_calendar[resource]
                    resource_date = self._find_next_available_slot(
                        date,
                        task["duration"],
                        availability
                    )
                    max_date = max(max_date, resource_date)
            
            return max_date
            
        except Exception as e:
            self.logger.error(f"Error adjusting for resources: {str(e)}")
            return date
    
    def _calculate_schedule_metrics(self, 
                                 timeline: List[Dict[str, Any]], 
                                 critical_path: List[str]) -> Dict[str, Any]:
        """Calculate schedule performance metrics."""
        try:
            total_duration = (self._calculate_end_date(timeline) - 
                            self.constraints.start_date).days
            
            critical_tasks = [t for t in timeline if t["id"] in critical_path]
            critical_path_duration = sum(t["duration"].days for t in critical_tasks)
            
            return {
                "total_duration_days": total_duration,
                "critical_path_duration": critical_path_duration,
                "total_slack_days": total_duration - critical_path_duration,
                "schedule_flexibility": round(
                    (total_duration - critical_path_duration) / total_duration, 2
                ),
                "milestone_count": len([t for t in timeline if t.get("is_milestone")]),
                "critical_tasks_count": len(critical_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating schedule metrics: {str(e)}")
            return {}
        
    def _verify_constraints(self, 
                          timeline: List[Dict[str, Any]], 
                          constraints: TimelineConstraint) -> Dict[str, Any]:
        """Verify that timeline meets all constraints."""
        try:
            verification = {
                "all_constraints_met": True,
                "violations": [],
                "warnings": []
            }
            
            # Check end date constraint
            if constraints.end_date:
                timeline_end = self._calculate_end_date(timeline)
                if timeline_end > constraints.end_date:
                    verification["all_constraints_met"] = False
                    verification["violations"].append({
                        "type": "end_date",
                        "message": f"Timeline exceeds end date by {(timeline_end - constraints.end_date).days} days"
                    })
            
            # Check fixed milestone constraints
            for task_id, fixed_date in constraints.fixed_milestones.items():
                task = next((t for t in timeline if t["id"] == task_id), None)
                if task and task["earliest_start"] != fixed_date:
                    verification["all_constraints_met"] = False
                    verification["violations"].append({
                        "type": "fixed_milestone",
                        "task_id": task_id,
                        "message": "Milestone date not met"
                    })
            
            # Check resource overallocation
            resource_allocations = self._calculate_resource_allocations(timeline)
            for resource, allocation in resource_allocations.items():
                if max(allocation.values()) > 100:
                    verification["warnings"].append({
                        "type": "resource_overallocation",
                        "resource": resource,
                        "message": "Resource overallocated"
                    })
            
            return verification
            
        except Exception as e:
            self.logger.error(f"Error verifying constraints: {str(e)}")
            return {"all_constraints_met": False, "violations": [str(e)], "warnings": []}

    def _calculate_resource_allocations(self, timeline: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate resource allocations per day."""
        try:
            allocations = defaultdict(lambda: defaultdict(float))
            
            for task in timeline:
                start_date = task["earliest_start"]
                duration = task["duration"].days
                resources = task.get("resources", [])
                
                for day in range(duration):
                    current_date = start_date + timedelta(days=day)
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    for resource in resources:
                        allocations[resource][date_str] += 100 / len(resources)
            
            return dict(allocations)
            
        except Exception as e:
            self.logger.error(f"Error calculating resource allocations: {str(e)}")
            return {}

    def _find_next_available_slot(self, 
                                start_date: datetime, 
                                duration: timedelta,
                                availability: Dict[str, Any]) -> datetime:
        """Find next available time slot for a resource."""
        try:
            current_date = start_date
            
            while True:
                # Check if slot is available for the entire duration
                slot_available = True
                for day in range(duration.days):
                    check_date = current_date + timedelta(days=day)
                    date_str = check_date.strftime("%Y-%m-%d")
                    
                    # Check availability and capacity
                    if not availability.get(date_str, {}).get("available", True):
                        slot_available = False
                        break
                    
                    if availability.get(date_str, {}).get("capacity", 100) < 100:
                        slot_available = False
                        break
                
                if slot_available:
                    return current_date
                
                current_date += timedelta(days=1)
            
        except Exception as e:
            self.logger.error(f"Error finding available slot: {str(e)}")
            return start_date

    def update_progress(self, 
                       task_id: str, 
                       progress: float, 
                       actual_start: Optional[datetime] = None,
                       actual_finish: Optional[datetime] = None) -> Dict[str, Any]:
        """Update task progress and recalculate timeline if needed."""
        try:
            if not self.current_timeline:
                raise PlanningError("No active timeline")
            
            # Find the task
            task = next((t for t in self.current_timeline["tasks"] if t["id"] == task_id), None)
            if not task:
                raise PlanningError(f"Task {task_id} not found")
            
            # Update task
            task["progress"] = progress
            if actual_start:
                task["actual_start"] = actual_start
            if actual_finish:
                task["actual_finish"] = actual_finish
            
            # Recalculate if needed
            if progress < 100 and actual_finish:
                self.logger.warning(f"Task {task_id} marked as not complete but has actual finish date")
            
            # Update dependent tasks if needed
            if actual_finish and actual_finish > task["earliest_finish"]:
                self._propagate_delay(task, actual_finish - task["earliest_finish"])
            
            return self.current_timeline
            
        except Exception as e:
            self.logger.error(f"Error updating progress: {str(e)}")
            raise

    def _propagate_delay(self, task: Dict[str, Any], delay: timedelta) -> None:
        """Propagate delays to dependent tasks."""
        try:
            # Find all dependent tasks
            dependent_tasks = [
                t for t in self.current_timeline["tasks"]
                if task["id"] in t.get("dependencies", [])
            ]
            
            for dep_task in dependent_tasks:
                # Update task dates
                dep_task["earliest_start"] += delay
                dep_task["earliest_finish"] += delay
                
                # Recursively propagate to next level of dependencies
                self._propagate_delay(dep_task, delay)
                
            self.logger.debug(f"Propagated {delay.days} day delay to {len(dependent_tasks)} dependent tasks")
            
        except Exception as e:
            self.logger.error(f"Error propagating delay: {str(e)}")
            raise

    def compress_schedule(self, max_duration: timedelta) -> Dict[str, Any]:
        """
        Attempt to compress the schedule to meet a maximum duration.
        Returns compression suggestions and updated timeline.
        """
        try:
            if not self.current_timeline:
                raise PlanningError("No active timeline")
            
            current_duration = (self._calculate_end_date(self.current_timeline["tasks"]) - 
                              self.constraints.start_date)
            
            if current_duration <= max_duration:
                return {
                    "compression_needed": False,
                    "current_duration": current_duration,
                    "suggestions": []
                }
            
            compression_needed = (current_duration - max_duration).days
            self.logger.info(f"Schedule compression needed: {compression_needed} days")
            
            suggestions = []
            
            # Analyze critical path tasks
            critical_tasks = [
                t for t in self.current_timeline["tasks"]
                if t["id"] in self.current_timeline["critical_path"]
            ]
            
            for task in critical_tasks:
                # Check for possible compression methods
                if task["duration"].days > 1:
                    suggestions.append({
                        "task_id": task["id"],
                        "type": "fast_tracking",
                        "potential_savings": task["duration"].days * 0.3,
                        "risk_level": "HIGH",
                        "description": f"Fast track task {task['name']} by adding resources"
                    })
                
                # Check for parallel execution possibilities
                if task.get("dependencies"):
                    suggestions.append({
                        "task_id": task["id"],
                        "type": "parallel_execution",
                        "potential_savings": task["duration"].days * 0.5,
                        "risk_level": "MEDIUM",
                        "description": f"Execute {task['name']} in parallel with dependencies"
                    })
            
            return {
                "compression_needed": True,
                "days_to_compress": compression_needed,
                "current_duration": current_duration,
                "target_duration": max_duration,
                "suggestions": sorted(
                    suggestions,
                    key=lambda x: x["potential_savings"],
                    reverse=True
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error compressing schedule: {str(e)}")
            raise

    def analyze_critical_path(self) -> Dict[str, Any]:
        """Perform detailed analysis of the critical path."""
        try:
            if not self.current_timeline:
                raise PlanningError("No active timeline")
            
            critical_tasks = [
                t for t in self.current_timeline["tasks"]
                if t["id"] in self.current_timeline["critical_path"]
            ]
            
            analysis = {
                "critical_path_length": len(critical_tasks),
                "total_duration": sum(t["duration"].days for t in critical_tasks),
                "high_risk_tasks": [
                    t for t in critical_tasks 
                    if t.get("priority") == TaskPriority.HIGH
                ],
                "resource_bottlenecks": self._identify_resource_bottlenecks(critical_tasks),
                "compression_opportunities": self._identify_compression_opportunities(critical_tasks),
                "risk_areas": self._identify_risk_areas(critical_tasks)
            }
            
            self.logger.info("Critical path analysis completed")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing critical path: {str(e)}")
            raise

    def _identify_resource_bottlenecks(self, critical_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify resource bottlenecks in critical path tasks."""
        bottlenecks = []
        resource_usage = defaultdict(list)
        
        try:
            # Group tasks by resource
            for task in critical_tasks:
                for resource in task.get("resources", []):
                    resource_usage[resource].append(task)
            
            # Identify bottlenecks
            for resource, tasks in resource_usage.items():
                if len(tasks) > 1:
                    bottlenecks.append({
                        "resource": resource,
                        "task_count": len(tasks),
                        "total_duration": sum(t["duration"].days for t in tasks),
                        "tasks": [t["id"] for t in tasks]
                    })
            
            return sorted(bottlenecks, key=lambda x: x["total_duration"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error identifying resource bottlenecks: {str(e)}")
            return []

    def _identify_compression_opportunities(self, critical_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify opportunities for schedule compression in critical path."""
        opportunities = []
        
        try:
            for task in critical_tasks:
                if task["duration"].days >= 3:
                    opportunities.append({
                        "task_id": task["id"],
                        "current_duration": task["duration"].days,
                        "potential_compression": task["duration"].days * 0.2,
                        "method": "Add resources",
                        "risk_level": "MEDIUM"
                    })
                
                if task.get("dependencies"):
                    opportunities.append({
                        "task_id": task["id"],
                        "current_duration": task["duration"].days,
                        "potential_compression": task["duration"].days * 0.3,
                        "method": "Parallel execution",
                        "risk_level": "HIGH"
                    })
            
            return sorted(opportunities, key=lambda x: x["potential_compression"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error identifying compression opportunities: {str(e)}")
            return []

    def _identify_risk_areas(self, critical_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify risk areas in critical path tasks."""
        risk_areas = []
        
        try:
            for task in critical_tasks:
                risks = []
                
                # Check duration risks
                if task["duration"].days > 5:
                    risks.append("Long duration")
                
                # Check resource risks
                if len(task.get("resources", [])) > 2:
                    risks.append("Multiple resource dependencies")
                
                # Check dependency risks
                if len(task.get("dependencies", [])) > 2:
                    risks.append("Multiple task dependencies")
                
                if risks:
                    risk_areas.append({
                        "task_id": task["id"],
                        "risks": risks,
                        "priority": task.get("priority", TaskPriority.MEDIUM).name,
                        "impact_level": "HIGH" if len(risks) > 1 else "MEDIUM"
                    })
            
            return sorted(risk_areas, key=lambda x: len(x["risks"]), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error identifying risk areas: {str(e)}")
            return []