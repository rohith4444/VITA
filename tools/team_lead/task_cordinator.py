from typing import Dict, List, Any, Tuple, Optional
import networkx as nx
from datetime import datetime, timedelta
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.project_manager.llm.pm_service import LLMService

# Initialize logger
logger = setup_logger("tools.team_lead.task_coordinator")

@trace_method
def analyze_project_plan(project_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the project plan to understand its structure and extract metadata.
    
    Args:
        project_plan: Project plan from Project Manager agent
        
    Returns:
        Dict[str, Any]: Enhanced project plan with analysis metadata
    """
    logger.info("Starting project plan analysis")
    
    try:
        analyzed_plan = project_plan.copy()
        
        # Extract milestones
        milestones = analyzed_plan.get("milestones", [])
        
        # Count tasks per milestone
        task_counts = {}
        total_tasks = 0
        
        for milestone in milestones:
            milestone_name = milestone.get("name", "Unnamed Milestone")
            tasks = milestone.get("tasks", [])
            task_count = len(tasks)
            task_counts[milestone_name] = task_count
            total_tasks += task_count
            
            # Add task count to milestone
            milestone["task_count"] = task_count
        
        # Extract resource allocations
        resource_allocation = analyzed_plan.get("resource_allocation", {})
        
        # Add analysis metadata
        analyzed_plan["analysis"] = {
            "total_milestones": len(milestones),
            "total_tasks": total_tasks,
            "task_counts_by_milestone": task_counts,
            "resource_types": list(resource_allocation.keys()),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Project plan analysis completed with {total_tasks} tasks across {len(milestones)} milestones")
        return analyzed_plan
        
    except Exception as e:
        logger.error(f"Error analyzing project plan: {str(e)}", exc_info=True)
        # Return original plan if analysis fails
        return project_plan

@trace_method
def break_down_tasks(analyzed_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Decompose the project into atomic tasks.
    
    Args:
        analyzed_plan: Analyzed project plan
        
    Returns:
        List[Dict[str, Any]]: List of atomic tasks with metadata
    """
    logger.info("Breaking down project into atomic tasks")
    
    tasks = []
    
    try:
        milestones = analyzed_plan.get("milestones", [])
        
        for milestone_idx, milestone in enumerate(milestones):
            milestone_name = milestone.get("name", f"Milestone {milestone_idx+1}")
            milestone_tasks = milestone.get("tasks", [])
            
            for task in milestone_tasks:
                # Create an enhanced task with metadata
                enhanced_task = {
                    "id": task.get("id", f"task_{len(tasks)+1}"),
                    "name": task.get("name", "Unnamed Task"),
                    "milestone": milestone_name,
                    "milestone_index": milestone_idx,
                    "dependencies": task.get("dependencies", []),
                    "effort": task.get("effort", "MEDIUM"),
                    "description": task.get("description", f"Task from milestone: {milestone_name}"),
                    "status": "pending",
                    "agent_skill_requirements": determine_skill_requirements(task)
                }
                
                tasks.append(enhanced_task)
        
        logger.info(f"Successfully broke down project into {len(tasks)} atomic tasks")
        return tasks
        
    except Exception as e:
        logger.error(f"Error breaking down tasks: {str(e)}", exc_info=True)
        return []

@trace_method
def determine_skill_requirements(task: Dict[str, Any]) -> Dict[str, float]:
    """
    Determine the skill requirements for a task based on its description and properties.
    
    Args:
        task: Task information
        
    Returns:
        Dict[str, float]: Dictionary mapping skill types to required proficiency (0.0-1.0)
    """
    skill_requirements = {
        "solution_architect": 0.0,
        "full_stack_developer": 0.0,
        "qa_test": 0.0,
        "project_manager": 0.0
    }
    
    try:
        task_name = task.get("name", "").lower()
        
        # Analyze task name for relevant keywords
        if any(keyword in task_name for keyword in ["architect", "design", "system", "structure"]):
            skill_requirements["solution_architect"] = 0.8
            
        if any(keyword in task_name for keyword in ["develop", "implement", "code", "build", "create"]):
            skill_requirements["full_stack_developer"] = 0.8
            
        if any(keyword in task_name for keyword in ["test", "qa", "quality", "validation", "verify"]):
            skill_requirements["qa_test"] = 0.8
            
        if any(keyword in task_name for keyword in ["plan", "coordinate", "schedule", "manage"]):
            skill_requirements["project_manager"] = 0.8
        
        # Adjust based on effort level
        effort = task.get("effort", "MEDIUM")
        if effort == "HIGH":
            # Increase the highest skill requirement
            max_skill = max(skill_requirements, key=skill_requirements.get)
            skill_requirements[max_skill] = min(1.0, skill_requirements[max_skill] + 0.2)
        
        # Ensure at least one skill has a minimum value
        if all(value < 0.5 for value in skill_requirements.values()):
            skill_requirements["full_stack_developer"] = 0.5
        
        return skill_requirements
        
    except Exception as e:
        logger.error(f"Error determining skill requirements: {str(e)}", exc_info=True)
        # Default to full stack developer if determination fails
        return {"full_stack_developer": 0.5}

@trace_method
def identify_dependencies(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Determine dependencies between tasks and enhance tasks with dependency information.
    
    Args:
        tasks: List of atomic tasks
        
    Returns:
        List[Dict[str, Any]]: Tasks enhanced with dependency information
    """
    logger.info("Identifying dependencies between tasks")
    
    try:
        # Create a task ID lookup
        task_map = {task["id"]: task for task in tasks}
        
        # Process explicit dependencies
        for task in tasks:
            # Initialize dependency metadata
            task["dependency_info"] = {
                "predecessors": task.get("dependencies", []),
                "successors": [],
                "is_blocker": False,
                "is_blocked": len(task.get("dependencies", [])) > 0
            }
            
            # Add implicit milestone dependencies
            milestone_idx = task.get("milestone_index", 0)
            if milestone_idx > 0:
                # Find tasks from previous milestones that don't have successors yet
                for potential_predecessor in tasks:
                    if potential_predecessor["milestone_index"] < milestone_idx:
                        # Only add if there's a logical connection
                        if is_logical_dependency(potential_predecessor, task):
                            if potential_predecessor["id"] not in task["dependency_info"]["predecessors"]:
                                task["dependency_info"]["predecessors"].append(potential_predecessor["id"])
                                task["dependency_info"]["is_blocked"] = True
        
        # Identify successors
        for task in tasks:
            for predecessor_id in task["dependency_info"]["predecessors"]:
                if predecessor_id in task_map:
                    predecessor = task_map[predecessor_id]
                    if "dependency_info" in predecessor and task["id"] not in predecessor["dependency_info"]["successors"]:
                        predecessor["dependency_info"]["successors"].append(task["id"])
                        predecessor["dependency_info"]["is_blocker"] = True
        
        # Detect circular dependencies
        if is_circular_dependency(tasks):
            logger.warning("Circular dependencies detected in task structure")
        
        logger.info("Successfully identified dependencies between tasks")
        return tasks
        
    except Exception as e:
        logger.error(f"Error identifying dependencies: {str(e)}", exc_info=True)
        return tasks

@trace_method
def is_logical_dependency(predecessor: Dict[str, Any], successor: Dict[str, Any]) -> bool:
    """
    Determine if there's a logical dependency between tasks based on their properties.
    
    Args:
        predecessor: Potential predecessor task
        successor: Potential successor task
        
    Returns:
        bool: True if there's a logical dependency
    """
    # Check if tasks are related based on keywords
    predecessor_name = predecessor.get("name", "").lower()
    successor_name = successor.get("name", "").lower()
    
    # Look for common terms that indicate relationship
    predecessor_terms = set(predecessor_name.split())
    successor_terms = set(successor_name.split())
    common_terms = predecessor_terms.intersection(successor_terms)
    
    # If there are multiple common terms, likely related
    if len(common_terms) >= 2:
        return True
    
    # Check logical sequences
    if ("design" in predecessor_name and "implement" in successor_name) or \
       ("implement" in predecessor_name and "test" in successor_name) or \
       ("create" in predecessor_name and "use" in successor_name) or \
       ("setup" in predecessor_name and "configure" in successor_name):
        return True
    
    # Default to false - no logical dependency detected
    return False

@trace_method
def is_circular_dependency(tasks: List[Dict[str, Any]]) -> bool:
    """
    Detect circular dependencies in task relationships.
    
    Args:
        tasks: List of tasks with dependency information
        
    Returns:
        bool: True if circular dependencies are detected
    """
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add tasks as nodes
        for task in tasks:
            G.add_node(task["id"])
        
        # Add dependencies as edges
        for task in tasks:
            for predecessor_id in task.get("dependency_info", {}).get("predecessors", []):
                G.add_edge(predecessor_id, task["id"])
        
        # Check for cycles
        return not nx.is_directed_acyclic_graph(G)
        
    except Exception as e:
        logger.error(f"Error checking circular dependencies: {str(e)}", exc_info=True)
        return False

@trace_method
def create_execution_graph(tasks_with_deps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a directed acyclic graph (DAG) of task execution.
    
    Args:
        tasks_with_deps: Tasks with dependency information
        
    Returns:
        Dict[str, Any]: Execution graph with timing information
    """
    logger.info("Creating execution graph")
    
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add tasks as nodes with attributes
        for task in tasks_with_deps:
            G.add_node(task["id"], 
                      name=task.get("name", ""),
                      effort=task.get("effort", "MEDIUM"),
                      milestone=task.get("milestone", ""),
                      task_data=task)
        
        # Add dependencies as edges
        for task in tasks_with_deps:
            for predecessor_id in task.get("dependency_info", {}).get("predecessors", []):
                if G.has_node(predecessor_id) and G.has_node(task["id"]):
                    G.add_edge(predecessor_id, task["id"])
        
        # Calculate earliest start and finish times
        earliest_times = calculate_earliest_times(G)
        
        # Calculate latest start and finish times
        latest_times = calculate_latest_times(G)
        
        # Find critical path
        critical_path = find_critical_path(G, earliest_times, latest_times)
        
        # Create execution graph structure
        execution_graph = {
            "nodes": {node: {
                "task": G.nodes[node]["task_data"],
                "earliest_start": earliest_times[node]["earliest_start"],
                "earliest_finish": earliest_times[node]["earliest_finish"],
                "latest_start": latest_times[node]["latest_start"],
                "latest_finish": latest_times[node]["latest_finish"],
                "is_critical": node in critical_path
            } for node in G.nodes},
            "edges": list(G.edges()),
            "critical_path": critical_path,
            "parallel_groups": identify_parallel_groups(G, earliest_times)
        }
        
        logger.info(f"Created execution graph with {len(execution_graph['nodes'])} nodes and {len(execution_graph['edges'])} dependencies")
        return execution_graph
        
    except Exception as e:
        logger.error(f"Error creating execution graph: {str(e)}", exc_info=True)
        # Return a basic graph structure if creation fails
        return {
            "nodes": {task["id"]: {"task": task} for task in tasks_with_deps},
            "edges": [],
            "critical_path": [],
            "parallel_groups": []
        }

@trace_method
def calculate_earliest_times(graph: nx.DiGraph) -> Dict[str, Dict[str, int]]:
    """
    Calculate earliest start and finish times for tasks in the graph.
    
    Args:
        graph: Task dependency graph
        
    Returns:
        Dict[str, Dict[str, int]]: Dictionary with earliest times for each task
    """
    # Initialize earliest times
    earliest_times = {}
    for node in graph.nodes:
        earliest_times[node] = {"earliest_start": 0, "earliest_finish": 0}
    
    # Map effort levels to durations
    effort_to_duration = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }
    
    # Topological sort to process nodes in dependency order
    for node in nx.topological_sort(graph):
        # Default duration based on effort
        duration = effort_to_duration.get(graph.nodes[node].get("effort", "MEDIUM"), 2)
        
        # If node has predecessors, the earliest start is the max of predecessors' earliest finish
        if graph.in_edges(node):
            earliest_times[node]["earliest_start"] = max(
                earliest_times[pred]["earliest_finish"] 
                for pred, _ in graph.in_edges(node)
            )
        
        # Calculate earliest finish
        earliest_times[node]["earliest_finish"] = earliest_times[node]["earliest_start"] + duration
    
    return earliest_times

@trace_method
def calculate_latest_times(graph: nx.DiGraph) -> Dict[str, Dict[str, int]]:
    """
    Calculate latest start and finish times for tasks in the graph.
    
    Args:
        graph: Task dependency graph
        
    Returns:
        Dict[str, Dict[str, int]]: Dictionary with latest times for each task
    """
    # First calculate earliest times to get project duration
    earliest_times = calculate_earliest_times(graph)
    
    # Find project end time (max of all earliest finish times)
    project_end = max(times["earliest_finish"] for times in earliest_times.values())
    
    # Initialize latest times (set to project end as default)
    latest_times = {}
    for node in graph.nodes:
        latest_times[node] = {"latest_start": project_end, "latest_finish": project_end}
    
    # Map effort levels to durations
    effort_to_duration = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }
    
    # Reverse topological sort to process nodes in reverse dependency order
    for node in reversed(list(nx.topological_sort(graph))):
        # Default duration based on effort
        duration = effort_to_duration.get(graph.nodes[node].get("effort", "MEDIUM"), 2)
        
        # If node has successors, the latest finish is the min of successors' latest start
        if graph.out_edges(node):
            latest_times[node]["latest_finish"] = min(
                latest_times[succ]["latest_start"] 
                for _, succ in graph.out_edges(node)
            )
        else:
            # For end nodes, latest finish is the project end
            latest_times[node]["latest_finish"] = project_end
        
        # Calculate latest start
        latest_times[node]["latest_start"] = latest_times[node]["latest_finish"] - duration
    
    return latest_times

@trace_method
def find_critical_path(
    graph: nx.DiGraph, 
    earliest_times: Dict[str, Dict[str, int]], 
    latest_times: Dict[str, Dict[str, int]]
) -> List[str]:
    """
    Find the critical path in the task graph.
    
    Args:
        graph: Task dependency graph
        earliest_times: Dictionary with earliest times for each task
        latest_times: Dictionary with latest times for each task
        
    Returns:
        List[str]: List of task IDs in the critical path
    """
    critical_path = []
    
    for node in graph.nodes:
        # A node is on the critical path if its slack is zero
        # Slack = Latest Start - Earliest Start (or Latest Finish - Earliest Finish)
        if (latest_times[node]["latest_start"] == earliest_times[node]["earliest_start"]):
            critical_path.append(node)
    
    # Sort the critical path based on earliest start times
    critical_path.sort(key=lambda node: earliest_times[node]["earliest_start"])
    
    return critical_path

@trace_method
def identify_parallel_groups(
    graph: nx.DiGraph,
    earliest_times: Dict[str, Dict[str, int]]
) -> List[List[str]]:
    """
    Identify groups of tasks that can be executed in parallel.
    
    Args:
        graph: Task dependency graph
        earliest_times: Dictionary with earliest times for each task
        
    Returns:
        List[List[str]]: List of parallel task groups
    """
    # Group tasks by earliest start time
    time_groups = {}
    
    for node in graph.nodes:
        earliest_start = earliest_times[node]["earliest_start"]
        if earliest_start not in time_groups:
            time_groups[earliest_start] = []
        time_groups[earliest_start].append(node)
    
    # Convert to list of lists
    parallel_groups = [group for _, group in sorted(time_groups.items())]
    
    return parallel_groups

@trace_method
def prioritize_tasks(execution_graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assign priority levels to tasks.
    
    Args:
        execution_graph: Execution graph with timing information
        
    Returns:
        Dict[str, Any]: Execution graph with priority information
    """
    logger.info("Prioritizing tasks")
    
    try:
        prioritized_graph = execution_graph.copy()
        
        # Define priority levels
        PRIORITY_CRITICAL = "CRITICAL"
        PRIORITY_HIGH = "HIGH"
        PRIORITY_MEDIUM = "MEDIUM"
        PRIORITY_LOW = "LOW"
        
        # Get critical path
        critical_path = execution_graph.get("critical_path", [])
        
        # Prioritize all nodes
        for node_id, node_data in prioritized_graph["nodes"].items():
            # Initialize priority field
            node_data["priority"] = PRIORITY_MEDIUM
            
            # Critical path tasks get highest priority
            if node_id in critical_path:
                node_data["priority"] = PRIORITY_CRITICAL
                continue
                
            # Check if task is a blocker for critical path
            is_blocker = False
            for critical_node in critical_path:
                if node_id in node_data["task"].get("dependency_info", {}).get("predecessors", []):
                    is_blocker = True
                    break
                    
            if is_blocker:
                node_data["priority"] = PRIORITY_HIGH
                continue
                
            # Check task effort
            if node_data["task"].get("effort", "MEDIUM") == "HIGH":
                node_data["priority"] = PRIORITY_HIGH
                continue
                
            # Lower priority for tasks with large slack
            earliest_start = node_data.get("earliest_start", 0)
            latest_start = node_data.get("latest_start", 0)
            
            if latest_start - earliest_start > 3:
                node_data["priority"] = PRIORITY_LOW
        
        logger.info("Successfully prioritized tasks")
        return prioritized_graph
        
    except Exception as e:
        logger.error(f"Error prioritizing tasks: {str(e)}", exc_info=True)
        return execution_graph

@trace_method
def map_tasks_to_agents(prioritized_graph: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Determine which agent should handle each task.
    
    Args:
        prioritized_graph: Prioritized execution graph
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping agent types to their assigned tasks
    """
    logger.info("Mapping tasks to agents")
    
    try:
        agent_tasks = {
            "solution_architect": [],
            "full_stack_developer": [],
            "qa_test": [],
            "project_manager": []
        }
        
        # First pass: assign tasks based on skill requirements
        for node_id, node_data in prioritized_graph["nodes"].items():
            task = node_data["task"]
            
            # Find the best agent for this task
            best_agent = "full_stack_developer"  # Default
            best_score = 0.0
            
            if "agent_skill_requirements" in task:
                for agent, score in task["agent_skill_requirements"].items():
                    if score > best_score:
                        best_score = score
                        best_agent = agent
            
            # Add task to agent with task metadata
            agent_tasks[best_agent].append({
                "task_id": node_id,
                "task_name": task.get("name", ""),
                "priority": node_data.get("priority", "MEDIUM"),
                "earliest_start": node_data.get("earliest_start", 0),
                "task_data": task
            })
        
        # Balance workload
        agent_tasks = balance_workload(agent_tasks, prioritized_graph)
        
        logger.info(f"Successfully mapped {sum(len(tasks) for tasks in agent_tasks.values())} tasks to agents")
        return agent_tasks
        
    except Exception as e:
        logger.error(f"Error mapping tasks to agents: {str(e)}", exc_info=True)
        # Return basic mapping if assignment fails
        return {
            "solution_architect": [],
            "full_stack_developer": [],
            "qa_test": [],
            "project_manager": []
        }

@trace_method
def balance_workload(
    agent_tasks: Dict[str, List[Dict[str, Any]]],
    prioritized_graph: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Redistribute tasks to balance workload across agents.
    
    Args:
        agent_tasks: Initial agent-to-tasks mapping
        prioritized_graph: Prioritized execution graph
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Balanced agent-to-tasks mapping
    """
    balanced_tasks = {agent: tasks.copy() for agent, tasks in agent_tasks.items()}
    
    # Count tasks per agent
    task_counts = {agent: len(tasks) for agent, tasks in balanced_tasks.items()}
    
    # Find agents with most and least tasks
    max_agent = max(task_counts, key=task_counts.get)
    min_agent = min(task_counts, key=task_counts.get)
    
    # Only rebalance if there's a significant difference
    while task_counts[max_agent] - task_counts[min_agent] > 2:
        # Find transferable tasks from max_agent
        transferable_tasks = []
        
        for task in balanced_tasks[max_agent]:
            # Only consider LOW or MEDIUM priority tasks
            if task.get("priority", "MEDIUM") not in ["CRITICAL", "HIGH"]:
                transferable_tasks.append(task)
        
        # Sort by priority (transfer lower priority first)
        transferable_tasks.sort(key=lambda t: {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}[t.get("priority", "MEDIUM")])
        
        # Transfer a task if possible
        if transferable_tasks:
            task_to_transfer = transferable_tasks[0]
            balanced_tasks[max_agent].remove(task_to_transfer)
            balanced_tasks[min_agent].append(task_to_transfer)
            
            # Update counts
            task_counts = {agent: len(tasks) for agent, tasks in balanced_tasks.items()}
            max_agent = max(task_counts, key=task_counts.get)
            min_agent = min(task_counts, key=task_counts.get)
        else:
            # No transferable tasks, break the loop
            break
    
    return balanced_tasks

@trace_method
def generate_agent_instructions(
    agent_tasks: Dict[str, List[Dict[str, Any]]],
    prioritized_graph: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create specific instructions for each agent.
    
    Args:
        agent_tasks: Agent-to-tasks mapping
        prioritized_graph: Prioritized execution graph
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Structured instructions for each agent
    """
    logger.info("Generating agent instructions")
    
    try:
        agent_instructions = {}
        
        for agent, tasks in agent_tasks.items():
            agent_instructions[agent] = []
            
            for task in tasks:
                task_id = task["task_id"]
                task_data = task["task_data"]
                
                # Get node data from prioritized graph
                node_data = prioritized_graph["nodes"].get(task_id, {})
                
                # Get predecessors
                predecessors = []
                for pred_id in task_data.get("dependency_info", {}).get("predecessors", []):
                    # Find which agent has this predecessor
                    pred_agent = None
                    for a, a_tasks in agent_tasks.items():
                        if any(t["task_id"] == pred_id for t in a_tasks):
                            pred_agent = a
                            break
                    
                    if pred_agent:
                        predecessors.append({
                            "task_id": pred_id,
                            "agent": pred_agent
                        })
                
                # Create instruction with context
                instruction = {
                    "task_id": task_id,
                    "task_name": task_data.get("name", ""),
                    "description": task_data.get("description", ""),
                    "milestone": task_data.get("milestone", ""),
                    "priority": node_data.get("priority", "MEDIUM"),
                    "earliest_start": node_data.get("earliest_start", 0),
                    "latest_start": node_data.get("latest_start", 0),
                    "is_critical": node_data.get("is_critical", False),
                    "dependencies": {
                        "predecessors": predecessors,
                        "is_blocked": task_data.get("dependency_info", {}).get("is_blocked", False)
                    },
                    "context": {
                        "effort": task_data.get("effort", "MEDIUM"),
                        "milestone_index": task_data.get("milestone_index", 0)
                    }
                }
                
                agent_instructions[agent].append(instruction)
            
            # Sort instructions by priority and timing
            agent_instructions[agent].sort(
                key=lambda i: (
                    {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[i.get("priority", "MEDIUM")],
                    i.get("earliest_start", 0)
                )
            )
        
        logger.info("Successfully generated agent instructions")
        return agent_instructions
        
    except Exception as e:
        logger.error(f"Error generating agent instructions: {str(e)}", exc_info=True)
        return {agent: [] for agent in agent_tasks.keys()}

@trace_method
def create_execution_plan(
    agent_instructions: Dict[str, List[Dict[str, Any]]],
    prioritized_graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Finalize complete execution plan for the project.
    
    Args:
        agent_instructions: Structured instructions for each agent
        prioritized_graph: Prioritized execution graph
        
    Returns:
        Dict[str, Any]: Complete execution plan ready for implementation
    """
    logger.info("Creating execution plan")
    
    try:
        # Create sequence groups (time-based phases)
        parallel_groups = prioritized_graph.get("parallel_groups", [])
        
        execution_phases = []
        for idx, group in enumerate(parallel_groups):
            phase_tasks = []
            
            for task_id in group:
                # Find which agent has this task
                agent_with_task = None
                task_instruction = None
                
                for agent, instructions in agent_instructions.items():
                    for instruction in instructions:
                        if instruction["task_id"] == task_id:
                            agent_with_task = agent
                            task_instruction = instruction
                            break
                    if agent_with_task:
                        break
                
                if agent_with_task and task_instruction:
                    phase_tasks.append({
                        "task_id": task_id,
                        "task_name": task_instruction["task_name"],
                        "agent": agent_with_task,
                        "priority": task_instruction["priority"],
                        "is_critical": task_instruction["is_critical"]
                    })
            
            # Only add non-empty phases
            if phase_tasks:
                execution_phases.append({
                    "phase": idx + 1,
                    "tasks": phase_tasks
                })
        
        # Create checkpoints after every 2-3 phases
        checkpoints = []
        for i in range(1, len(execution_phases), 3):
            checkpoints.append({
                "checkpoint_id": f"checkpoint_{len(checkpoints) + 1}",
                "after_phase": i,
                "milestone_reached": determine_milestone_at_phase(i, prioritized_graph)
            })
        
        # Create execution plan
        execution_plan = {
            "agent_assignments": agent_instructions,
            "execution_phases": execution_phases,
            "checkpoints": checkpoints,
            "critical_path": prioritized_graph.get("critical_path", []),
            "error_handling": {
                "retry_strategy": "Retry failed tasks up to 2 times",
                "fallback_strategy": "Escalate to Team Lead for manual intervention"
            },
            "monitoring": {
                "frequency": "After each phase",
                "metrics": ["Task completion", "Timeline adherence", "Quality gates"]
            },
            "coordination": {
                "sync_points": [phase["phase"] for phase in execution_phases if any(task["is_critical"] for task in phase["tasks"])],
                "hand_off_strategy": "Explicit deliverable verification"
            }
        }
        
        logger.info("Successfully created execution plan")
        return execution_plan
        
    except Exception as e:
        logger.error(f"Error creating execution plan: {str(e)}", exc_info=True)
        return {
            "agent_assignments": agent_instructions,
            "execution_phases": [],
            "checkpoints": [],
            "critical_path": prioritized_graph.get("critical_path", []),
            "error_handling": {
                "retry_strategy": "Retry failed tasks up to 2 times",
                "fallback_strategy": "Escalate to Team Lead for manual intervention"
            }
        }

@trace_method
def determine_milestone_at_phase(phase_idx: int, prioritized_graph: Dict[str, Any]) -> str:
    """
    Determine which milestone is reached at a given phase.
    
    Args:
        phase_idx: Index of the phase
        prioritized_graph: Prioritized execution graph
        
    Returns:
        str: Milestone name or description
    """
    try:
        # Get nodes at this phase
        nodes = prioritized_graph.get("nodes", {})
        phase_tasks = []
        
        # Find tasks that would be in this phase
        for node_id, node_data in nodes.items():
            if node_data.get("earliest_start", 0) <= phase_idx:
                phase_tasks.append(node_data["task"])
        
        # Get highest milestone_index that's complete at this phase
        milestone_indices = [task.get("milestone_index", 0) for task in phase_tasks]
        if milestone_indices:
            highest_milestone_idx = max(milestone_indices)
            # Find a task with this milestone_index to get the name
            for task in phase_tasks:
                if task.get("milestone_index", 0) == highest_milestone_idx:
                    return task.get("milestone", f"Phase {phase_idx} completion")
        
        return f"Phase {phase_idx} completion"
        
    except Exception as e:
        logger.error(f"Error determining milestone at phase {phase_idx}: {str(e)}", exc_info=True)
        return f"Phase {phase_idx} completion"

@trace_method
def estimate_execution_timeline(execution_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate time required for plan execution.
    
    Args:
        execution_plan: Execution plan
        
    Returns:
        Dict[str, Any]: Execution plan with timeline estimates
    """
    logger.info("Estimating execution timeline")
    
    try:
        # Copy the execution plan
        plan_with_timeline = execution_plan.copy()
        
        # Get phases
        execution_phases = plan_with_timeline.get("execution_phases", [])
        
        # Map effort levels to day estimates
        effort_to_days = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3
        }
        
        # Calculate time estimates for each phase
        timeline = []
        cumulative_days = 0
        
        for phase in execution_phases:
            phase_tasks = phase.get("tasks", [])
            
            # Find the longest task in this phase
            max_days = 0
            for task in phase_tasks:
                # Get the task data from agent assignments
                task_id = task.get("task_id", "")
                agent = task.get("agent", "")
                
                # Find task in agent assignments
                task_data = None
                for instruction in plan_with_timeline.get("agent_assignments", {}).get(agent, []):
                    if instruction.get("task_id") == task_id:
                        task_data = instruction
                        break
                
                if task_data:
                    effort = task_data.get("context", {}).get("effort", "MEDIUM")
                    days = effort_to_days.get(effort, 2)
                    max_days = max(max_days, days)
            
            # Add this phase to timeline
            phase_start = cumulative_days
            phase_end = phase_start + max_days
            
            timeline.append({
                "phase": phase.get("phase", 0),
                "start_day": phase_start,
                "end_day": phase_end,
                "duration_days": max_days
            })
            
            cumulative_days = phase_end
        
        # Add timeline information
        plan_with_timeline["timeline"] = {
            "phases": timeline,
            "total_duration_days": cumulative_days,
            "estimated_start_date": datetime.utcnow().isoformat(),
            "estimated_end_date": (datetime.utcnow() + timedelta(days=cumulative_days)).isoformat()
        }
        
        # Update checkpoint timing information
        updated_checkpoints = []
        for checkpoint in plan_with_timeline.get("checkpoints", []):
            after_phase = checkpoint.get("after_phase", 0)
            
            # Find when this phase ends
            checkpoint_day = 0
            for phase_time in timeline:
                if phase_time.get("phase", 0) == after_phase:
                    checkpoint_day = phase_time.get("end_day", 0)
                    break
            
            updated_checkpoints.append({
                **checkpoint,
                "day": checkpoint_day,
                "estimated_date": (datetime.utcnow() + timedelta(days=checkpoint_day)).isoformat()
            })
        
        plan_with_timeline["checkpoints"] = updated_checkpoints
        
        logger.info(f"Estimated total execution time: {cumulative_days} days")
        return plan_with_timeline
        
    except Exception as e:
        logger.error(f"Error estimating execution timeline: {str(e)}", exc_info=True)
        return execution_plan

@trace_method
def validate_plan(execution_plan_with_timeline: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Final validation of the execution plan.
    
    Args:
        execution_plan_with_timeline: Execution plan with timeline
        
    Returns:
        Tuple[bool, Dict[str, Any], List[str]]: 
            - Validation status
            - Potentially modified plan
            - List of validation issues
    """
    logger.info("Validating execution plan")
    
    issues = []
    valid = True
    validated_plan = execution_plan_with_timeline.copy()
    
    try:
        # Check that all critical path tasks are assigned
        critical_path = validated_plan.get("critical_path", [])
        assigned_tasks = []
        
        for agent, instructions in validated_plan.get("agent_assignments", {}).items():
            for instruction in instructions:
                assigned_tasks.append(instruction.get("task_id", ""))
        
        for task_id in critical_path:
            if task_id not in assigned_tasks:
                valid = False
                issues.append(f"Critical path task {task_id} is not assigned to any agent")
        
        # Check that all phases have at least one task
        for idx, phase in enumerate(validated_plan.get("execution_phases", [])):
            if not phase.get("tasks", []):
                valid = False
                issues.append(f"Phase {idx+1} has no tasks assigned")
        
        # Check that timeline is reasonable
        timeline = validated_plan.get("timeline", {})
        total_duration = timeline.get("total_duration_days", 0)
        
        if total_duration <= 0:
            valid = False
            issues.append("Timeline duration must be positive")
        
        if total_duration > 90:  # Arbitrary limit for example
            valid = False
            issues.append(f"Timeline duration of {total_duration} days exceeds maximum recommended duration")
        
        # Add validation status to plan
        validated_plan["validation"] = {
            "is_valid": valid,
            "issues": issues,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        if valid:
            logger.info("Execution plan validation successful")
        else:
            logger.warning(f"Execution plan validation failed with {len(issues)} issues")
            
        return valid, validated_plan, issues
        
    except Exception as e:
        logger.error(f"Error validating execution plan: {str(e)}", exc_info=True)
        issues.append(f"Exception during validation: {str(e)}")
        
        validated_plan["validation"] = {
            "is_valid": False,
            "issues": issues,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        return False, validated_plan, issues

@trace_method
def coordinate_project_execution(
    project_plan: Dict[str, Any],
    llm_service: Optional[LLMService] = None
) -> Dict[str, Any]:
    """
    Main entry point to coordinate project execution.
    
    Args:
        project_plan: Project plan from Project Manager agent
        llm_service: Optional LLM service for enhanced coordination
        
    Returns:
        Dict[str, Any]: Complete execution plan with assignments
    """
    logger.info("Starting project execution coordination")
    
    try:
        # Step 1: Analyze project plan
        analyzed_plan = analyze_project_plan(project_plan)
        
        # Step 2: Break down into atomic tasks
        tasks = break_down_tasks(analyzed_plan)
        
        # Step 3: Identify dependencies
        tasks_with_deps = identify_dependencies(tasks)
        
        # Step 4: Create execution graph
        execution_graph = create_execution_graph(tasks_with_deps)
        
        # Step 5: Prioritize tasks
        prioritized_graph = prioritize_tasks(execution_graph)
        
        # Step 6: Map tasks to agents
        agent_tasks = map_tasks_to_agents(prioritized_graph)
        
        # Step 7: Generate agent instructions
        agent_instructions = generate_agent_instructions(agent_tasks, prioritized_graph)
        
        # Step 8: Create execution plan
        execution_plan = create_execution_plan(agent_instructions, prioritized_graph)
        
        # Step 9: Estimate timeline
        plan_with_timeline = estimate_execution_timeline(execution_plan)
        
        # Step 10: Validate plan
        valid, validated_plan, issues = validate_plan(plan_with_timeline)
        
        if not valid:
            logger.warning(f"Generated plan has validation issues: {issues}")
        
        logger.info("Project execution coordination completed successfully")
        return validated_plan
        
    except Exception as e:
        logger.error(f"Error coordinating project execution: {str(e)}", exc_info=True)
        # Return a basic error plan
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }