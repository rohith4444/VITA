from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import copy
import networkx as nx
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.team_lead.progress_tracker")

class TaskStatus(Enum):
    """Enum representing the possible states of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(Enum):
    """Enum representing risk levels for tasks."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@trace_method
def update_task_status(
    task_id: str,
    tasks: List[Dict[str, Any]],
    new_status: Union[TaskStatus, str],
    completion_percentage: float = None,
    notes: str = None,
    update_timestamp: str = None
) -> Dict[str, Any]:
    """
    Update the status of a specific task.
    
    Args:
        task_id: ID of the task to update
        tasks: List of all tasks
        new_status: New status for the task (TaskStatus enum or string)
        completion_percentage: Optional percentage of completion (0-100)
        notes: Optional notes about the update
        update_timestamp: Optional timestamp for the update
        
    Returns:
        Dict[str, Any]: Updated task with progress information
        
    Raises:
        ValueError: If task_id is not found or invalid status
    """
    logger.info(f"Updating status for task {task_id}")
    
    # Convert string status to enum if needed
    if isinstance(new_status, str):
        try:
            new_status = TaskStatus(new_status)
        except ValueError:
            logger.error(f"Invalid status string: {new_status}")
            raise ValueError(f"Invalid status: {new_status}. Must be one of {[s.value for s in TaskStatus]}")
    
    # Validate completion percentage
    if completion_percentage is not None and (completion_percentage < 0 or completion_percentage > 100):
        logger.error(f"Invalid completion percentage: {completion_percentage}")
        raise ValueError("Completion percentage must be between 0 and 100")
    
    # Default update timestamp to now
    if not update_timestamp:
        update_timestamp = datetime.utcnow().isoformat()
    
    # Find the task
    updated_task = None
    for task in tasks:
        if task["id"] == task_id:
            updated_task = task
            break
    
    if not updated_task:
        logger.error(f"Task {task_id} not found")
        raise ValueError(f"Task ID {task_id} not found")
    
    # Create a copy to avoid modifying the original
    updated_task = copy.deepcopy(updated_task)
    
    # Initialize progress tracking if not present
    if "progress" not in updated_task:
        updated_task["progress"] = {
            "status": TaskStatus.PENDING.value,
            "completion_percentage": 0,
            "updates": [],
            "latest_update_timestamp": None,
            "start_timestamp": None,
            "completion_timestamp": None
        }
    
    # Handle special status transitions
    if new_status == TaskStatus.IN_PROGRESS and updated_task["progress"]["status"] == TaskStatus.PENDING.value:
        # Task is starting for the first time
        updated_task["progress"]["start_timestamp"] = update_timestamp
    
    elif new_status == TaskStatus.COMPLETED:
        # Task is completed
        updated_task["progress"]["completion_timestamp"] = update_timestamp
        # Force completion percentage to 100
        completion_percentage = 100
    
    # Update task status
    updated_task["progress"]["status"] = new_status.value
    
    # Update completion percentage if provided
    if completion_percentage is not None:
        updated_task["progress"]["completion_percentage"] = completion_percentage
    
    # Add update to history
    update_entry = {
        "timestamp": update_timestamp,
        "status": new_status.value,
        "completion_percentage": updated_task["progress"]["completion_percentage"],
        "notes": notes
    }
    updated_task["progress"]["updates"].append(update_entry)
    updated_task["progress"]["latest_update_timestamp"] = update_timestamp
    
    logger.info(f"Task {task_id} updated to status {new_status.value} with {updated_task['progress']['completion_percentage']}% completion")
    return updated_task

@trace_method
def update_tasks_list(
    tasks: List[Dict[str, Any]],
    updated_task: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Update a task in the main tasks list.
    
    Args:
        tasks: List of all tasks
        updated_task: The updated task to replace in the list
        
    Returns:
        List[Dict[str, Any]]: Updated list of tasks
    """
    updated_tasks = copy.deepcopy(tasks)
    
    for i, task in enumerate(updated_tasks):
        if task["id"] == updated_task["id"]:
            updated_tasks[i] = updated_task
            break
    
    return updated_tasks

@trace_method
def track_milestone_completion(
    milestone_name: str,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Track completion of a milestone based on its constituent tasks.
    
    Args:
        milestone_name: Name of the milestone to track
        tasks: List of all tasks
        
    Returns:
        Dict[str, Any]: Milestone status with completion info
    """
    logger.info(f"Tracking completion for milestone {milestone_name}")
    
    # Find all tasks for this milestone
    milestone_tasks = [t for t in tasks if t.get("milestone") == milestone_name]
    
    if not milestone_tasks:
        logger.warning(f"No tasks found for milestone {milestone_name}")
        return {
            "milestone": milestone_name,
            "status": "unknown",
            "completion_percentage": 0,
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_in_progress": 0,
            "has_blocked_tasks": False
        }
    
    # Count tasks by status
    total_tasks = len(milestone_tasks)
    completed_tasks = 0
    in_progress_tasks = 0
    blocked_tasks = 0
    total_percentage = 0
    
    for task in milestone_tasks:
        progress = task.get("progress", {})
        status = progress.get("status", TaskStatus.PENDING.value)
        
        if status == TaskStatus.COMPLETED.value:
            completed_tasks += 1
            total_percentage += 100
        elif status == TaskStatus.IN_PROGRESS.value:
            in_progress_tasks += 1
            total_percentage += progress.get("completion_percentage", 0)
        elif status == TaskStatus.BLOCKED.value:
            blocked_tasks += 1
    
    # Calculate overall completion percentage
    completion_percentage = round(total_percentage / total_tasks if total_tasks > 0 else 0, 1)
    
    # Determine milestone status
    if completed_tasks == total_tasks:
        status = "completed"
    elif blocked_tasks > 0:
        status = "blocked"
    elif in_progress_tasks > 0:
        status = "in_progress"
    else:
        status = "pending"
    
    milestone_status = {
        "milestone": milestone_name,
        "status": status,
        "completion_percentage": completion_percentage,
        "tasks_total": total_tasks,
        "tasks_completed": completed_tasks,
        "tasks_in_progress": in_progress_tasks,
        "tasks_blocked": blocked_tasks,
        "has_blocked_tasks": blocked_tasks > 0
    }
    
    logger.info(f"Milestone {milestone_name} is {completion_percentage}% complete with status {status}")
    return milestone_status

@trace_method
def calculate_project_progress(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate overall project progress based on task statuses.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan
        
    Returns:
        Dict[str, Any]: Project progress summary
    """
    logger.info("Calculating overall project progress")
    
    # Extract all unique milestones
    milestones = list(set(task.get("milestone", "") for task in tasks if task.get("milestone")))
    
    # Track each milestone
    milestone_progress = []
    for milestone in milestones:
        milestone_status = track_milestone_completion(milestone, tasks)
        milestone_progress.append(milestone_status)
    
    # Calculate overall statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("progress", {}).get("status") == TaskStatus.COMPLETED.value)
    in_progress_tasks = sum(1 for task in tasks if task.get("progress", {}).get("status") == TaskStatus.IN_PROGRESS.value)
    blocked_tasks = sum(1 for task in tasks if task.get("progress", {}).get("status") == TaskStatus.BLOCKED.value)
    failed_tasks = sum(1 for task in tasks if task.get("progress", {}).get("status") == TaskStatus.FAILED.value)
    pending_tasks = total_tasks - completed_tasks - in_progress_tasks - blocked_tasks - failed_tasks
    
    # Calculate overall completion percentage
    total_percentage = 0
    for task in tasks:
        progress = task.get("progress", {})
        status = progress.get("status", TaskStatus.PENDING.value)
        
        if status == TaskStatus.COMPLETED.value:
            total_percentage += 100
        elif status == TaskStatus.IN_PROGRESS.value:
            total_percentage += progress.get("completion_percentage", 0)
    
    overall_percentage = round(total_percentage / total_tasks if total_tasks > 0 else 0, 1)
    
    # Determine overall status
    if completed_tasks == total_tasks:
        overall_status = "completed"
    elif blocked_tasks > 0:
        overall_status = "blocked"
    elif failed_tasks > 0:
        overall_status = "issues"
    elif in_progress_tasks > 0:
        overall_status = "in_progress"
    else:
        overall_status = "pending"
    
    # Check critical path progress
    critical_path = execution_plan.get("critical_path", [])
    critical_path_tasks = [t for t in tasks if t["id"] in critical_path]
    critical_path_progress = {}
    
    if critical_path_tasks:
        critical_completed = sum(1 for t in critical_path_tasks if t.get("progress", {}).get("status") == TaskStatus.COMPLETED.value)
        critical_total = len(critical_path_tasks)
        critical_percentage = round((critical_completed / critical_total) * 100 if critical_total > 0 else 0, 1)
        
        critical_path_progress = {
            "total_tasks": critical_total,
            "completed_tasks": critical_completed,
            "completion_percentage": critical_percentage,
            "critical_status": "on_track" if critical_percentage >= overall_percentage else "behind"
        }
    
    # Compile overall progress
    project_progress = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "completion_percentage": overall_percentage,
        "task_summary": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "blocked": blocked_tasks,
            "failed": failed_tasks,
            "pending": pending_tasks
        },
        "milestone_progress": milestone_progress,
        "critical_path_progress": critical_path_progress,
        "phases_summary": summarize_phase_progress(tasks, execution_plan)
    }
    
    logger.info(f"Project is {overall_percentage}% complete with status {overall_status}")
    return project_progress

@trace_method
def summarize_phase_progress(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Summarize progress by execution phases.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan
        
    Returns:
        List[Dict[str, Any]]: Summary of progress for each phase
    """
    phase_summaries = []
    
    execution_phases = execution_plan.get("execution_phases", [])
    for phase in execution_phases:
        phase_number = phase.get("phase", 0)
        phase_tasks_ids = [task["task_id"] for task in phase.get("tasks", [])]
        phase_tasks = [t for t in tasks if t["id"] in phase_tasks_ids]
        
        if not phase_tasks:
            continue
        
        # Calculate phase statistics
        total_phase_tasks = len(phase_tasks)
        completed_phase_tasks = sum(1 for t in phase_tasks if t.get("progress", {}).get("status") == TaskStatus.COMPLETED.value)
        
        # Calculate phase percentage
        total_percentage = 0
        for task in phase_tasks:
            progress = task.get("progress", {})
            status = progress.get("status", TaskStatus.PENDING.value)
            
            if status == TaskStatus.COMPLETED.value:
                total_percentage += 100
            elif status == TaskStatus.IN_PROGRESS.value:
                total_percentage += progress.get("completion_percentage", 0)
        
        phase_percentage = round(total_percentage / total_phase_tasks if total_phase_tasks > 0 else 0, 1)
        
        # Determine phase status
        if completed_phase_tasks == total_phase_tasks:
            phase_status = "completed"
        elif any(t.get("progress", {}).get("status") == TaskStatus.BLOCKED.value for t in phase_tasks):
            phase_status = "blocked"
        elif any(t.get("progress", {}).get("status") == TaskStatus.IN_PROGRESS.value for t in phase_tasks):
            phase_status = "in_progress"
        else:
            phase_status = "pending"
        
        phase_summary = {
            "phase": phase_number,
            "status": phase_status,
            "completion_percentage": phase_percentage,
            "tasks_total": total_phase_tasks,
            "tasks_completed": completed_phase_tasks
        }
        
        phase_summaries.append(phase_summary)
    
    return phase_summaries

@trace_method
def identify_bottlenecks(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Identify tasks that are causing delays or blocking progress.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan
        
    Returns:
        List[Dict[str, Any]]: Identified bottleneck tasks with impact analysis
    """
    logger.info("Identifying project bottlenecks")
    
    bottlenecks = []
    
    # Build a dependency graph
    G = nx.DiGraph()
    
    # Add all tasks as nodes
    for task in tasks:
        task_id = task["id"]
        G.add_node(task_id, task_data=task)
    
    # Add dependencies as edges
    for task in tasks:
        task_id = task["id"]
        dependencies = task.get("dependency_info", {}).get("predecessors", [])
        
        for dep_id in dependencies:
            if G.has_node(dep_id):
                G.add_edge(dep_id, task_id)
    
    # Check for explicitly blocked tasks
    for task in tasks:
        if task.get("progress", {}).get("status") == TaskStatus.BLOCKED.value:
            # This task is explicitly blocked
            task_id = task["id"]
            successor_count = sum(1 for _ in nx.dfs_preorder_nodes(G, task_id)) - 1  # Exclude self
            
            bottlenecks.append({
                "task_id": task_id,
                "task_name": task.get("name", ""),
                "bottleneck_type": "explicitly_blocked",
                "status": TaskStatus.BLOCKED.value,
                "blocked_task_count": successor_count,
                "impact_level": "high" if successor_count > 2 else "medium",
                "notes": task.get("progress", {}).get("updates", [{}])[-1].get("notes", "No details available")
            })
    
    # Check for incomplete tasks with completed successors
    for task in tasks:
        task_id = task["id"]
        status = task.get("progress", {}).get("status", TaskStatus.PENDING.value)
        
        if status not in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            # This task is not completed, check if it's blocking completed successors
            successors = list(G.successors(task_id)) if G.has_node(task_id) else []
            completed_successors = []
            
            for succ_id in successors:
                succ_task = next((t for t in tasks if t["id"] == succ_id), None)
                if succ_task and succ_task.get("progress", {}).get("status") == TaskStatus.COMPLETED.value:
                    completed_successors.append(succ_id)
            
            if completed_successors:
                bottlenecks.append({
                    "task_id": task_id,
                    "task_name": task.get("name", ""),
                    "bottleneck_type": "blocking_completed_successors",
                    "status": status,
                    "blocked_task_count": len(completed_successors),
                    "impact_level": "medium",
                    "notes": f"Task is preventing proper sequence completion"
                })
    
    # Check for delayed critical path tasks
    critical_path = execution_plan.get("critical_path", [])
    
    for task_id in critical_path:
        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            continue
            
        status = task.get("progress", {}).get("status", TaskStatus.PENDING.value)
        
        if status == TaskStatus.IN_PROGRESS.value:
            # Check if it's taking longer than expected
            start_time = task.get("progress", {}).get("start_timestamp")
            if not start_time:
                continue
                
            try:
                start_date = datetime.fromisoformat(start_time)
                current_date = datetime.utcnow()
                days_in_progress = (current_date - start_date).days
                
                # Estimate expected duration based on effort
                effort = task.get("effort", "MEDIUM")
                expected_days = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(effort, 2)
                
                if days_in_progress > expected_days:
                    bottlenecks.append({
                        "task_id": task_id,
                        "task_name": task.get("name", ""),
                        "bottleneck_type": "delayed_critical_task",
                        "status": status,
                        "blocked_task_count": sum(1 for t in tasks if task_id in t.get("dependency_info", {}).get("predecessors", [])),
                        "impact_level": "critical",
                        "notes": f"Critical path task taking longer than expected ({days_in_progress} days vs. {expected_days} expected)"
                    })
            except (ValueError, TypeError):
                pass  # Skip if date parsing fails
    
    # Sort bottlenecks by impact level
    impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    bottlenecks.sort(key=lambda b: impact_order.get(b["impact_level"], 999))
    
    logger.info(f"Identified {len(bottlenecks)} bottlenecks in the project")
    return bottlenecks

@trace_method
def analyze_timeline_adherence(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare actual progress against planned timeline.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan with timeline
        
    Returns:
        Dict[str, Any]: Timeline variance analysis
    """
    logger.info("Analyzing timeline adherence")
    
    # Get the timeline from the execution plan
    timeline = execution_plan.get("timeline", {})
    if not timeline:
        logger.warning("No timeline found in execution plan")
        return {
            "status": "unknown",
            "overall_variance_days": 0,
            "is_on_schedule": False,
            "phases_analysis": []
        }
    
    # Get the planned phases timeline
    phases_timeline = timeline.get("phases", [])
    
    # Calculate current date
    current_date = datetime.utcnow()
    
    # Get estimated start date
    estimated_start = timeline.get("estimated_start_date")
    try:
        start_date = datetime.fromisoformat(estimated_start)
    except (ValueError, TypeError):
        start_date = current_date
        logger.warning("Invalid start date in timeline, using current date")
    
    # Calculate project days elapsed
    days_elapsed = (current_date - start_date).days
    if days_elapsed < 0:
        days_elapsed = 0  # Project hasn't started yet
    
    # Analyze each phase
    phases_analysis = []
    overall_delay = 0
    
    for phase_timeline in phases_timeline:
        phase_number = phase_timeline.get("phase", 0)
        planned_start = phase_timeline.get("start_day", 0)
        planned_end = phase_timeline.get("end_day", 0)
        
        # Find phase tasks
        phase_tasks_ids = []
        for phase in execution_plan.get("execution_phases", []):
            if phase.get("phase") == phase_number:
                phase_tasks_ids = [task["task_id"] for task in phase.get("tasks", [])]
                break
        
        phase_tasks = [t for t in tasks if t["id"] in phase_tasks_ids]
        
        # Phase status
        phase_completed = all(
            t.get("progress", {}).get("status") == TaskStatus.COMPLETED.value
            for t in phase_tasks
        ) if phase_tasks else False
        
        phase_in_progress = any(
            t.get("progress", {}).get("status") == TaskStatus.IN_PROGRESS.value
            for t in phase_tasks
        ) if phase_tasks else False
        
        # Actual dates logic
        actual_start = None
        actual_end = None
        
        for task in phase_tasks:
            progress = task.get("progress", {})
            task_start = progress.get("start_timestamp")
            task_end = progress.get("completion_timestamp")
            
            if task_start:
                try:
                    task_start_date = datetime.fromisoformat(task_start)
                    if actual_start is None or task_start_date < actual_start:
                        actual_start = task_start_date
                except (ValueError, TypeError):
                    pass
                    
            if task_end:
                try:
                    task_end_date = datetime.fromisoformat(task_end)
                    if actual_end is None or task_end_date > actual_end:
                        actual_end = task_end_date
                except (ValueError, TypeError):
                    pass
        
        # Calculate variances
        start_variance = None
        end_variance = None
        
        if actual_start:
            planned_start_date = start_date + timedelta(days=planned_start)
            start_variance = (actual_start - planned_start_date).days
        
        if actual_end:
            planned_end_date = start_date + timedelta(days=planned_end)
            end_variance = (actual_end - planned_end_date).days
        
        # Determine phase status
        if phase_completed:
            if end_variance is not None:
                phase_status = "completed_late" if end_variance > 0 else "completed_early" if end_variance < 0 else "completed_on_time"
            else:
                phase_status = "completed"
        elif phase_in_progress:
            if days_elapsed > planned_end:
                phase_status = "delayed"
            elif days_elapsed >= planned_start:
                phase_status = "in_progress"
            else:
                phase_status = "ahead"
        else:  # Not started
            if days_elapsed > planned_start:
                phase_status = "delayed"
            else:
                phase_status = "pending"
        
        # Add to phases analysis
        phase_analysis = {
            "phase": phase_number,
            "status": phase_status,
            "planned_start_day": planned_start,
            "planned_end_day": planned_end,
            "actual_start_day": (actual_start - start_date).days if actual_start else None,
            "actual_end_day": (actual_end - start_date).days if actual_end else None,
            "start_variance_days": start_variance,
            "end_variance_days": end_variance
        }
        
        phases_analysis.append(phase_analysis)
        
        # Update overall delay based on the latest phase that should be in progress or completed
        if days_elapsed >= planned_start:
            if phase_status in ["delayed", "completed_late"]:
                variance = max(end_variance or 0, 
                              (days_elapsed - planned_end) if not phase_completed else 0)
                if variance > overall_delay:
                    overall_delay = variance
    
    # Determine current expected phase
    current_expected_phase = None
    for phase in reversed(phases_timeline):
        if days_elapsed >= phase.get("start_day", 0):
            current_expected_phase = phase.get("phase", 0)
            break
    
    # Determine current actual phase
    current_actual_phase = None
    for phase in phases_analysis:
        if phase["status"] in ["in_progress", "delayed"]:
            current_actual_phase = phase["phase"]
            break
    
    if current_actual_phase is None:
        # Find the highest completed phase
        completed_phases = [p["phase"] for p in phases_analysis if p["status"] in ["completed", "completed_early", "completed_on_time", "completed_late"]]
        current_actual_phase = max(completed_phases) if completed_phases else 0
    
    # Overall status
    is_on_schedule = overall_delay <= 0
    if current_actual_phase is not None and current_expected_phase is not None:
        is_ahead = current_actual_phase > current_expected_phase
        is_behind = current_actual_phase < current_expected_phase
    else:
        is_ahead = False
        is_behind = overall_delay > 0
    
    if is_ahead:
        status = "ahead"
    elif is_behind:
        status = "behind"
    elif is_on_schedule:
        status = "on_schedule"
    else:
        status = "unknown"
    
    # Create result
    timeline_analysis = {
        "status": status,
        "overall_variance_days": overall_delay,
        "is_on_schedule": is_on_schedule,
        "days_elapsed": days_elapsed,
        "current_expected_phase": current_expected_phase,
        "current_actual_phase": current_actual_phase,
        "phases_analysis": phases_analysis
    }
    
    logger.info(f"Timeline analysis completed: Project is {timeline_analysis['status']} with variance of {overall_delay} days")
    return timeline_analysis

@trace_method
def detect_at_risk_tasks(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any],
    timeline_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Identify tasks that are at risk of missing deadlines.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan with timeline
        timeline_analysis: Result from analyze_timeline_adherence
        
    Returns:
        List[Dict[str, Any]]: At-risk tasks with risk assessment
    """
    logger.info("Detecting at-risk tasks")
    
    at_risk_tasks = []
    
    # Use timeline analysis to establish context
    overall_variance = timeline_analysis.get("overall_variance_days", 0)
    is_behind_schedule = timeline_analysis.get("status") == "behind"
    
    # Critical path takes priority
    critical_path = execution_plan.get("critical_path", [])
    
    # Timeline information
    timeline = execution_plan.get("timeline", {})
    phases_timeline = timeline.get("phases", [])
    
    # Map tasks to phases
    task_phase_map = {}
    
    for phase in execution_plan.get("execution_phases", []):
        phase_number = phase.get("phase", 0)
        for task_info in phase.get("tasks", []):
            task_phase_map[task_info["task_id"]] = phase_number
    
    # Examine each task
    for task in tasks:
        task_id = task["id"]
        progress = task.get("progress", {})
        status = progress.get("status", TaskStatus.PENDING.value)
        
        # Skip completed or failed tasks
        if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            continue
        
        # Risk factors
        risk_factors = []
        risk_level = RiskLevel.NONE
        
        # 1. Critical path tasks are automatically higher risk
        is_critical = task_id in critical_path
        if is_critical:
            risk_factors.append("critical_path_task")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # 2. Check timeline for this task's phase
        phase = task_phase_map.get(task_id)
        phase_timeline = next((p for p in phases_timeline if p.get("phase") == phase), None)
        
        if phase_timeline:
            phase_end_day = phase_timeline.get("end_day", 0)
            
            # Current implementation of timeline uses days from start
            start_date = datetime.utcnow()
            if timeline.get("estimated_start_date"):
                try:
                    start_date = datetime.fromisoformat(timeline.get("estimated_start_date"))
                except (ValueError, TypeError):
                    pass
                    
            days_elapsed = (datetime.utcnow() - start_date).days
            days_remaining = phase_end_day - days_elapsed
            
            # Task should be in progress or done by now
            if days_remaining <= 0 and status == TaskStatus.PENDING.value:
                risk_factors.append("overdue_not_started")
                risk_level = max(risk_level, RiskLevel.HIGH)
            elif days_remaining <= 0 and status == TaskStatus.IN_PROGRESS.value:
                risk_factors.append("overdue_in_progress")
                risk_level = max(risk_level, RiskLevel.MEDIUM)
            elif days_remaining <= 2:  # Close to deadline
                risk_factors.append("approaching_deadline")
                if status == TaskStatus.PENDING.value:
                    risk_level = max(risk_level, RiskLevel.HIGH)
                else:
                    risk_level = max(risk_level, RiskLevel.MEDIUM)
            
            # Consider effort level
            effort = task.get("effort", "MEDIUM")
            if effort == "HIGH" and days_remaining <= 3:
                risk_factors.append("high_effort_short_timeline")
                risk_level = max(risk_level, RiskLevel.HIGH)
        
        # 3. Check dependencies
        dependencies = task.get("dependency_info", {}).get("predecessors", [])
        blocked_by = []
        
        for dep_id in dependencies:
            dep_task = next((t for t in tasks if t["id"] == dep_id), None)
            if dep_task:
                dep_status = dep_task.get("progress", {}).get("status", TaskStatus.PENDING.value)
                if dep_status not in [TaskStatus.COMPLETED.value]:
                    blocked_by.append(dep_id)
                    
                    # If dependency is at risk or blocked, this task is higher risk
                    if dep_status == TaskStatus.BLOCKED.value:
                        risk_factors.append("blocked_dependency")
                        risk_level = max(risk_level, RiskLevel.HIGH)
                    elif dep_status == TaskStatus.FAILED.value:
                        risk_factors.append("failed_dependency")
                        risk_level = max(risk_level, RiskLevel.CRITICAL)
        
        if blocked_by and status != TaskStatus.BLOCKED.value:
            risk_factors.append("waiting_on_dependencies")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # 4. Explicitly blocked tasks are critical risk
        if status == TaskStatus.BLOCKED.value:
            risk_factors.append("explicitly_blocked")
            risk_level = max(risk_level, RiskLevel.CRITICAL)
        
        # 5. Consider project level timeline status
        if is_behind_schedule and overall_variance > 0:
            if is_critical:
                risk_factors.append("project_behind_schedule")
                risk_level = max(risk_level, RiskLevel.HIGH)
        
        # Only add to at-risk list if there's some risk
        if risk_level != RiskLevel.NONE:
            at_risk_tasks.append({
                "task_id": task_id,
                "task_name": task.get("name", ""),
                "current_status": status,
                "risk_level": risk_level.value,
                "risk_factors": risk_factors,
                "milestone": task.get("milestone", ""),
                "is_critical_path": is_critical,
                "blocked_by": blocked_by
            })
    
    # Sort by risk level
    risk_level_order = {
        RiskLevel.CRITICAL.value: 0,
        RiskLevel.HIGH.value: 1,
        RiskLevel.MEDIUM.value: 2,
        RiskLevel.LOW.value: 3,
        RiskLevel.NONE.value: 4
    }
    
    at_risk_tasks.sort(key=lambda t: (risk_level_order.get(t["risk_level"], 999), t["is_critical_path"]))
    
    logger.info(f"Detected {len(at_risk_tasks)} at-risk tasks")
    return at_risk_tasks

@trace_method
def generate_progress_report(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any],
    project_progress: Dict[str, Any] = None,
    bottlenecks: List[Dict[str, Any]] = None,
    timeline_analysis: Dict[str, Any] = None,
    at_risk_tasks: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive progress report for the project.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan
        project_progress: Optional pre-calculated project progress
        bottlenecks: Optional pre-identified bottlenecks
        timeline_analysis: Optional pre-calculated timeline analysis
        at_risk_tasks: Optional pre-identified at-risk tasks
        
    Returns:
        Dict[str, Any]: Comprehensive progress report
    """
    logger.info("Generating progress report")
    
    # Calculate required data if not provided
    if project_progress is None:
        project_progress = calculate_project_progress(tasks, execution_plan)
        
    if bottlenecks is None:
        bottlenecks = identify_bottlenecks(tasks, execution_plan)
        
    if timeline_analysis is None:
        timeline_analysis = analyze_timeline_adherence(tasks, execution_plan)
        
    if at_risk_tasks is None:
        at_risk_tasks = detect_at_risk_tasks(tasks, execution_plan, timeline_analysis)
    
    # Extract key metrics
    completion_percentage = project_progress.get("completion_percentage", 0)
    overall_status = project_progress.get("overall_status", "unknown")
    task_summary = project_progress.get("task_summary", {})
    critical_path_progress = project_progress.get("critical_path_progress", {})
    timeline_status = timeline_analysis.get("status", "unknown")
    variance_days = timeline_analysis.get("overall_variance_days", 0)
    
    # Calculate high-level summary
    high_risk_count = sum(1 for task in at_risk_tasks if task["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value])
    critical_bottlenecks = sum(1 for bottleneck in bottlenecks if bottleneck["impact_level"] == "critical")
    
    # Determine overall health
    if overall_status == "completed":
        health = "COMPLETED"
    elif high_risk_count > 2 or critical_bottlenecks > 0 or timeline_status == "behind" and variance_days > 5:
        health = "AT RISK"
    elif high_risk_count > 0 or timeline_status == "behind":
        health = "NEEDS ATTENTION"
    else:
        health = "ON TRACK"
    
    # Recent activity
    recent_updates = []
    for task in tasks:
        progress = task.get("progress", {})
        updates = progress.get("updates", [])
        
        for update in updates:
            if "timestamp" in update:
                try:
                    update_time = datetime.fromisoformat(update["timestamp"])
                    # Consider updates in last 3 days as recent
                    if (datetime.utcnow() - update_time).days <= 3:
                        recent_updates.append({
                            "task_id": task["id"],
                            "task_name": task.get("name", ""),
                            "timestamp": update["timestamp"],
                            "status": update["status"],
                            "completion_percentage": update.get("completion_percentage", 0),
                            "notes": update.get("notes", "")
                        })
                except (ValueError, TypeError):
                    pass
    
    # Sort recent updates by timestamp (newest first)
    recent_updates.sort(key=lambda u: u["timestamp"], reverse=True)
    
    # Milestone summary
    milestone_summary = []
    for milestone in project_progress.get("milestone_progress", []):
        milestone_summary.append({
            "name": milestone.get("milestone", ""),
            "status": milestone.get("status", ""),
            "completion_percentage": milestone.get("completion_percentage", 0),
            "tasks_completed": f"{milestone.get('tasks_completed', 0)}/{milestone.get('tasks_total', 0)}"
        })
    
    # Create visualization data
    visualization_data = create_progress_visualization(tasks, execution_plan, project_progress)
    
    # Assemble report
    report = {
        "report_id": f"progress_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat(),
        "project_health": health,
        "executive_summary": {
            "completion_percentage": completion_percentage,
            "status": overall_status,
            "timeline_status": timeline_status,
            "variance_days": variance_days,
            "critical_path_status": critical_path_progress.get("critical_status", "unknown"),
            "at_risk_tasks": high_risk_count,
            "blocked_tasks": task_summary.get("blocked", 0)
        },
        "milestone_summary": milestone_summary,
        "recent_activity": recent_updates[:10],  # Limit to 10 most recent
        "bottlenecks": [
            {
                "task_name": b["task_name"],
                "impact": b["impact_level"],
                "type": b["bottleneck_type"],
                "notes": b["notes"]
            } for b in bottlenecks[:5]  # Limit to top 5
        ],
        "at_risk_tasks": [
            {
                "task_name": t["task_name"],
                "risk_level": t["risk_level"],
                "factors": t["risk_factors"],
                "is_critical": t["is_critical_path"]
            } for t in at_risk_tasks[:5]  # Limit to top 5
        ],
        "timeline_analysis": {
            "status": timeline_status,
            "variance_days": variance_days,
            "current_phase": timeline_analysis.get("current_actual_phase", 0),
            "expected_phase": timeline_analysis.get("current_expected_phase", 0)
        },
        "task_statistics": task_summary,
        "visualization_data": visualization_data,
        "recommendations": generate_recommendations(bottlenecks, at_risk_tasks, timeline_analysis)
    }
    
    logger.info("Progress report generated successfully")
    return report

@trace_method
def generate_recommendations(
    bottlenecks: List[Dict[str, Any]],
    at_risk_tasks: List[Dict[str, Any]],
    timeline_analysis: Dict[str, Any]
) -> List[str]:
    """
    Generate recommendations based on project status.
    
    Args:
        bottlenecks: Identified bottlenecks
        at_risk_tasks: At-risk tasks
        timeline_analysis: Timeline analysis data
        
    Returns:
        List[str]: List of recommendations
    """
    recommendations = []
    
    # Check for critical bottlenecks
    critical_bottlenecks = [b for b in bottlenecks if b["impact_level"] == "critical"]
    if critical_bottlenecks:
        recommendations.append(
            f"Address {len(critical_bottlenecks)} critical bottleneck(s) immediately, starting with task '{critical_bottlenecks[0]['task_name']}'"
        )
    
    # Check for critical-risk tasks
    critical_risks = [t for t in at_risk_tasks if t["risk_level"] == RiskLevel.CRITICAL.value]
    if critical_risks:
        recommendations.append(
            f"Prioritize {len(critical_risks)} critical-risk task(s), especially '{critical_risks[0]['task_name']}'"
        )
    
    # Check timeline status
    timeline_status = timeline_analysis.get("status")
    variance_days = timeline_analysis.get("overall_variance_days", 0)
    
    if timeline_status == "behind" and variance_days > 5:
        recommendations.append(
            f"Consider adjusting project timeline to account for {variance_days} day(s) delay"
        )
    elif timeline_status == "behind" and variance_days > 0:
        recommendations.append(
            f"Implement recovery plan to address {variance_days} day(s) delay"
        )
    
    # Check for blocked tasks
    blocked_tasks = [t for t in at_risk_tasks if "explicitly_blocked" in t.get("risk_factors", [])]
    if blocked_tasks:
        recommendations.append(
            f"Remove blockers for {len(blocked_tasks)} task(s) to restore project flow"
        )
    
    # Check for dependency chains
    dependency_issues = [t for t in at_risk_tasks if any(f in t.get("risk_factors", []) for f in ["blocked_dependency", "waiting_on_dependencies"])]
    if dependency_issues:
        recommendations.append(
            "Review task dependencies to optimize parallel work opportunities"
        )
    
    # Add default recommendations if none were generated
    if not recommendations:
        if timeline_status == "on_schedule":
            recommendations.append("Continue current progress to maintain on-time delivery")
        elif timeline_status == "ahead":
            recommendations.append("Consider reallocating resources to optimize project efficiency")
        else:
            recommendations.append("Conduct detailed review of project status to identify improvement opportunities")
    
    return recommendations

@trace_method
def create_progress_visualization(
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any],
    project_progress: Dict[str, Any],
    timeline_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate visualization data structures for progress reporting.
    
    Args:
        tasks: List of all tasks with status
        execution_plan: The project execution plan
        project_progress: Project progress data
        
    Returns:
        Dict[str, Any]: Visualization data structures
    """
    logger.info("Creating progress visualization data")
    
    visualizations = {}
    
    # 1. Burndown chart data
    burndown_data = []
    timeline = execution_plan.get("timeline", {})
    total_duration = timeline.get("total_duration_days", 30)
    total_tasks = len(tasks)
    
    # Get actual completed tasks per day
    completion_dates = {}
    for task in tasks:
        progress = task.get("progress", {})
        completion_timestamp = progress.get("completion_timestamp")
        
        if completion_timestamp and progress.get("status") == TaskStatus.COMPLETED.value:
            try:
                completion_date = datetime.fromisoformat(completion_timestamp).date()
                completion_dates[completion_date] = completion_dates.get(completion_date, 0) + 1
            except (ValueError, TypeError):
                pass
    
    # Create ideal burndown
    start_date = datetime.utcnow().date()
    if timeline.get("estimated_start_date"):
        try:
            start_date = datetime.fromisoformat(timeline.get("estimated_start_date")).date()
        except (ValueError, TypeError):
            pass
    
    # Create day-by-day burndown
    tasks_remaining = total_tasks
    for day in range(total_duration + 1):
        current_date = start_date + timedelta(days=day)
        
        # Ideal remaining (linear progression)
        ideal_remaining = max(0, total_tasks - (total_tasks * day // total_duration))
        
        # Actual remaining
        completed_today = 0
        if current_date <= datetime.utcnow().date():
            completed_today = completion_dates.get(current_date, 0)
            tasks_remaining -= completed_today
        
        burndown_data.append({
            "day": day,
            "date": current_date.isoformat(),
            "ideal_remaining": ideal_remaining,
            "actual_remaining": tasks_remaining,
            "completed_today": completed_today
        })
    
    visualizations["burndown_chart"] = burndown_data
    
    # 2. Status distribution data
    status_counts = {
        "completed": 0,
        "in_progress": 0,
        "blocked": 0,
        "failed": 0,
        "cancelled": 0,
        "pending": 0
    }
    
    for task in tasks:
        status = task.get("progress", {}).get("status", TaskStatus.PENDING.value)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    status_distribution = [
        {"status": status, "count": count}
        for status, count in status_counts.items()
    ]
    
    visualizations["status_distribution"] = status_distribution
    
    # 3. Milestone progress data
    milestone_data = []
    
    for milestone in project_progress.get("milestone_progress", []):
        milestone_data.append({
            "milestone": milestone.get("milestone", ""),
            "completion_percentage": milestone.get("completion_percentage", 0),
            "tasks_total": milestone.get("tasks_total", 0),
            "tasks_completed": milestone.get("tasks_completed", 0)
        })
    
    visualizations["milestone_progress"] = milestone_data
    
    # 4. Timeline variance chart
    timeline_data = []
    
    for phase_analysis in timeline_analysis.get("phases_analysis", []):
        phase = phase_analysis.get("phase", 0)
        planned_start = phase_analysis.get("planned_start_day", 0)
        planned_end = phase_analysis.get("planned_end_day", 0)
        actual_start = phase_analysis.get("actual_start_day")
        actual_end = phase_analysis.get("actual_end_day")
        
        timeline_data.append({
            "phase": phase,
            "planned_start": planned_start,
            "planned_end": planned_end,
            "actual_start": actual_start,
            "actual_end": actual_end,
            "start_variance": phase_analysis.get("start_variance_days"),
            "end_variance": phase_analysis.get("end_variance_days"),
            "status": phase_analysis.get("status", "pending")
        })
    
    visualizations["timeline_variance"] = timeline_data
    
    logger.info("Progress visualization data created successfully")
    return visualizations

@trace_method
def handle_task_completion_events(
    task_id: str,
    tasks: List[Dict[str, Any]],
    execution_plan: Dict[str, Any],
    completion_data: Dict[str, Any],
    agent_id: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process task completion events and update project state.
    
    Args:
        task_id: ID of the completed task
        tasks: List of all tasks
        execution_plan: The project execution plan
        completion_data: Data about the completion (output, success status)
        agent_id: ID of the agent that completed the task
        
    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Any]]: 
            - Updated tasks list
            - Event data for triggered events
    """
    logger.info(f"Handling completion event for task {task_id}")
    
    # Update task status to completed
    updated_task = update_task_status(
        task_id=task_id,
        tasks=tasks,
        new_status=TaskStatus.COMPLETED,
        completion_percentage=100,
        notes=f"Completed by agent {agent_id}",
        update_timestamp=completion_data.get("timestamp", datetime.utcnow().isoformat())
    )
    
    # Update the tasks list
    updated_tasks = update_tasks_list(tasks, updated_task)
    
    # Check for milestone completion
    milestone = updated_task.get("milestone")
    milestone_status = None
    
    if milestone:
        milestone_status = track_milestone_completion(milestone, updated_tasks)
    
    # Check for phase completion
    phase_completed = False
    current_phase = None
    
    for phase in execution_plan.get("execution_phases", []):
        phase_tasks = [task["task_id"] for task in phase.get("tasks", [])]
        if task_id in phase_tasks:
            current_phase = phase.get("phase")
            
            # Check if all tasks in this phase are complete
            phase_tasks_data = [t for t in updated_tasks if t["id"] in phase_tasks]
            phase_completed = all(t.get("progress", {}).get("status") == TaskStatus.COMPLETED.value for t in phase_tasks_data)
            break
    
    # Check for checkpoint triggering
    checkpoint_triggered = None
    
    for checkpoint in execution_plan.get("checkpoints", []):
        if checkpoint.get("after_phase") == current_phase and phase_completed:
            checkpoint_triggered = checkpoint.get("checkpoint_id")
            break
    
    # Find tasks that can now be started (dependencies met)
    unblocked_tasks = []
    
    for task in updated_tasks:
        # Skip if already in progress or completed
        status = task.get("progress", {}).get("status", TaskStatus.PENDING.value)
        if status not in [TaskStatus.PENDING.value, TaskStatus.BLOCKED.value]:
            continue
            
        # Check if this task depends on the completed task
        dependencies = task.get("dependency_info", {}).get("predecessors", [])
        if task_id in dependencies:
            # Check if all dependencies are now met
            all_dependencies_met = True
            
            for dep_id in dependencies:
                dep_task = next((t for t in updated_tasks if t["id"] == dep_id), None)
                if not dep_task or dep_task.get("progress", {}).get("status") != TaskStatus.COMPLETED.value:
                    all_dependencies_met = False
                    break
            
            if all_dependencies_met:
                unblocked_tasks.append(task["id"])
    
    # Create event data
    event_data = {
        "task_completed": {
            "task_id": task_id,
            "task_name": updated_task.get("name", ""),
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        },
        "milestone_status": milestone_status,
        "phase_completed": phase_completed,
        "current_phase": current_phase,
        "checkpoint_triggered": checkpoint_triggered,
        "unblocked_tasks": unblocked_tasks
    }
    
    logger.info(f"Task completion processed. Unblocked {len(unblocked_tasks)} tasks")
    return updated_tasks, event_data

@trace_method
def manage_checkpoints(
    checkpoint_id: str,
    execution_plan: Dict[str, Any],
    tasks: List[Dict[str, Any]],
    project_progress: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create and verify project checkpoints at designated milestones.
    
    Args:
        checkpoint_id: ID of the checkpoint to manage
        execution_plan: The project execution plan
        tasks: List of all tasks
        project_progress: Optional pre-calculated project progress
        
    Returns:
        Dict[str, Any]: Checkpoint verification data
    """
    logger.info(f"Managing checkpoint {checkpoint_id}")
    
    # Find checkpoint in execution plan
    checkpoint_data = None
    for checkpoint in execution_plan.get("checkpoints", []):
        if checkpoint.get("checkpoint_id") == checkpoint_id:
            checkpoint_data = checkpoint
            break
    
    if not checkpoint_data:
        logger.error(f"Checkpoint {checkpoint_id} not found in execution plan")
        return {
            "checkpoint_id": checkpoint_id,
            "status": "invalid",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Checkpoint not found in execution plan"
        }
    
    # Calculate project progress if not provided
    if project_progress is None:
        project_progress = calculate_project_progress(tasks, execution_plan)
    
    # Verify milestone completion
    milestone_name = checkpoint_data.get("milestone_reached", "")
    milestone_status = None
    
    if milestone_name:
        milestone_progress = next((m for m in project_progress.get("milestone_progress", []) 
                                if m.get("milestone") == milestone_name), None)
        
        if milestone_progress:
            milestone_status = milestone_progress
    
    # Verify phase completion
    phase = checkpoint_data.get("after_phase")
    phase_completed = False
    
    if phase is not None:
        phase_summary = next((p for p in project_progress.get("phases_summary", [])
                            if p.get("phase") == phase), None)
        
        if phase_summary:
            phase_completed = phase_summary.get("status") == "completed"
    
    # Check critical path status
    critical_path_progress = project_progress.get("critical_path_progress", {})
    critical_path_on_track = critical_path_progress.get("critical_status") == "on_track"
    
    # Determine checkpoint status
    if phase_completed and (not milestone_name or (milestone_status and milestone_status.get("status") == "completed")):
        status = "verified"
        message = f"Checkpoint {checkpoint_id} successfully reached"
    elif phase_completed:
        status = "partially_verified"
        message = f"Phase completed but milestone '{milestone_name}' not fully completed"
    else:
        status = "not_verified"
        message = f"Phase {phase} not completed yet"
    
    # Generate checkpoint data
    checkpoint_verification = {
        "checkpoint_id": checkpoint_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "milestone_status": milestone_status,
        "phase_completed": phase_completed,
        "critical_path_on_track": critical_path_on_track,
        "completion_percentage": project_progress.get("completion_percentage", 0),
        "overall_status": project_progress.get("overall_status", "unknown")
    }
    
    logger.info(f"Checkpoint {checkpoint_id} verification: {status}")
    return checkpoint_verification