from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("team_lead.llm.prompts")

@trace_method
def format_task_coordination_prompt(
    project_description: str,
    project_plan: Dict[str, Any],
    tasks: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Format prompt for task coordination analysis.
    
    Args:
        project_description: Project description
        project_plan: Project plan from Project Manager
        tasks: Optional list of already analyzed tasks
        
    Returns:
        str: Formatted prompt for task coordination
    """
    logger.debug("Formatting task coordination prompt")
    
    try:
        # Format project plan for readability
        milestones_text = ""
        for idx, milestone in enumerate(project_plan.get("milestones", [])):
            milestone_name = milestone.get("name", f"Milestone {idx+1}")
            milestones_text += f"Milestone {idx+1}: {milestone_name}\n"
            
            for task in milestone.get("tasks", []):
                task_id = task.get("id", "")
                task_name = task.get("name", "")
                dependencies = ", ".join(task.get("dependencies", []))
                effort = task.get("effort", "MEDIUM")
                
                milestones_text += f"  - Task {task_id}: {task_name} (Effort: {effort}, Dependencies: {dependencies})\n"
        
        # Format existing tasks if provided
        tasks_text = ""
        if tasks:
            tasks_text = "\nPreviously Analyzed Tasks:\n"
            for task in tasks:
                task_id = task.get("id", "")
                task_name = task.get("name", "")
                milestone = task.get("milestone", "")
                
                tasks_text += f"  - Task {task_id}: {task_name} (Milestone: {milestone})\n"
        
        prompt = f"""
        As a Team Lead AI, analyze the following project to create a detailed task breakdown and coordination plan:

        PROJECT DESCRIPTION:
        {project_description}

        PROJECT PLAN:
        {milestones_text}
        {tasks_text}

        I need you to:
        1. Break down the project into atomic tasks, ensuring each task is well-defined and manageable
        2. Identify dependencies between tasks
        3. Determine which agent role (Solution Architect, Full Stack Developer, or QA/Test) is best suited for each task
        4. Create a prioritized execution plan that optimizes parallel work and manages dependencies
        5. Estimate a timeline for execution

        Format your response as a JSON object with:
        {{
            "tasks": [
                {{
                    "id": "task_id",
                    "name": "Task name",
                    "description": "Detailed description",
                    "milestone": "Parent milestone",
                    "dependencies": ["task_id1", "task_id2"],
                    "estimated_effort": "LOW/MEDIUM/HIGH",
                    "suitable_agent": "solution_architect/full_stack_developer/qa_test"
                }}
            ],
            "execution_plan": {{
                "phases": [
                    {{
                        "phase": 1,
                        "tasks": ["task_id1", "task_id2"],
                        "estimated_duration": "duration in days"
                    }}
                ],
                "critical_path": ["task_id1", "task_id3", "task_id5"],
                "parallel_opportunities": [
                    ["task_id2", "task_id4"]
                ]
            }}
        }}
        """
        
        logger.debug("Task coordination prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting task coordination prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, analyze the following project to create a detailed task breakdown and coordination plan:

        PROJECT DESCRIPTION:
        {project_description}

        I need you to:
        1. Break down the project into atomic tasks
        2. Identify dependencies between tasks
        3. Determine which agent role is best suited for each task
        4. Create a prioritized execution plan
        5. Estimate a timeline for execution

        Format your response as a structured JSON object.
        """

@trace_method
def format_agent_selection_prompt(
    task: Dict[str, Any],
    available_agents: List[str],
    agent_capabilities: Dict[str, Any]
) -> str:
    """
    Format prompt for agent selection for a task.
    
    Args:
        task: Task information
        available_agents: List of available agent IDs
        agent_capabilities: Dictionary of agent capabilities
        
    Returns:
        str: Formatted prompt for agent selection
    """
    logger.debug(f"Formatting agent selection prompt for task {task.get('id', '')}")
    
    try:
        # Format task details
        task_id = task.get("id", "")
        task_name = task.get("name", "")
        task_description = task.get("description", "")
        task_milestone = task.get("milestone", "")
        task_dependencies = ", ".join(task.get("dependencies", []))
        task_effort = task.get("estimated_effort", "MEDIUM")
        
        # Format agent capabilities
        agents_text = ""
        for agent_id in available_agents:
            capabilities = agent_capabilities.get(agent_id, {})
            agent_type = capabilities.get("agent_type", "unknown")
            strengths = ", ".join(capabilities.get("strengths", []))
            
            agents_text += f"Agent ID: {agent_id}\n"
            agents_text += f"Type: {agent_type}\n"
            agents_text += f"Strengths: {strengths}\n\n"
        
        prompt = f"""
        As a Team Lead AI, select the most appropriate agent for the following task:

        TASK DETAILS:
        Task ID: {task_id}
        Task Name: {task_name}
        Description: {task_description}
        Milestone: {task_milestone}
        Dependencies: {task_dependencies}
        Estimated Effort: {task_effort}

        AVAILABLE AGENTS:
        {agents_text}

        Select the best agent for this task considering:
        1. Agent capabilities and strengths
        2. Task requirements and complexity
        3. Current workload and availability
        4. Task dependencies and sequence

        Format your response as a JSON object with:
        {{
            "selected_agent_id": "agent_id",
            "reasoning": "Explanation of why this agent was selected",
            "confidence": "A number between 0 and 1 indicating your confidence in this selection",
            "fallback_agent_id": "alternative agent if primary is unavailable"
        }}
        """
        
        logger.debug("Agent selection prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting agent selection prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, select the most appropriate agent for task {task.get('id', '')} - {task.get('name', '')}.

        Format your response as a JSON object with selected_agent_id, reasoning, confidence, and fallback_agent_id.
        """

@trace_method
def format_progress_analysis_prompt(
    execution_plan: Dict[str, Any],
    current_progress: Dict[str, Any],
    task_statuses: Dict[str, str]
) -> str:
    """
    Format prompt for analyzing project progress.
    
    Args:
        execution_plan: Execution plan for the project
        current_progress: Current progress tracking data
        task_statuses: Dictionary mapping task IDs to status
        
    Returns:
        str: Formatted prompt for progress analysis
    """
    logger.debug("Formatting progress analysis prompt")
    
    try:
        # Format execution plan phases
        phases_text = ""
        for phase in execution_plan.get("phases", []):
            phase_number = phase.get("phase", 0)
            phase_tasks = ", ".join(phase.get("tasks", []))
            phase_duration = phase.get("estimated_duration", "unknown")
            
            phases_text += f"Phase {phase_number} (Duration: {phase_duration}):\n"
            phases_text += f"  Tasks: {phase_tasks}\n"
        
        # Format task statuses
        tasks_text = ""
        for task_id, status in task_statuses.items():
            tasks_text += f"  - Task {task_id}: {status}\n"
        
        # Format current progress metrics
        completion_percentage = current_progress.get("completion_percentage", 0)
        task_summary = current_progress.get("task_summary", {})
        total_tasks = task_summary.get("total", 0)
        completed_tasks = task_summary.get("completed", 0)
        in_progress_tasks = task_summary.get("in_progress", 0)
        blocked_tasks = task_summary.get("blocked", 0)
        
        prompt = f"""
        As a Team Lead AI, analyze the current project progress and provide recommendations:

        EXECUTION PLAN:
        {phases_text}

        CURRENT PROGRESS:
        Overall Completion: {completion_percentage}%
        Total Tasks: {total_tasks}
        Completed Tasks: {completed_tasks}
        In-Progress Tasks: {in_progress_tasks}
        Blocked Tasks: {blocked_tasks}

        TASK STATUSES:
        {tasks_text}

        Provide a detailed analysis of the project progress, addressing:
        1. Overall project health (on track, at risk, blocked)
        2. Issues that need immediate attention
        3. Bottlenecks or blocked tasks that need resolution
        4. Resource allocation recommendations
        5. Timeline adjustments if necessary
        6. Specific actions to keep the project on track

        Format your response as a JSON object with:
        {{
            "project_health": "on_track/at_risk/blocked",
            "completion_assessment": "assessment of current completion percentage",
            "critical_issues": [
                {{
                    "issue": "Description of the issue",
                    "impact": "Impact on the project",
                    "recommendation": "Recommended action"
                }}
            ],
            "bottlenecks": ["task_id1", "task_id2"],
            "resource_recommendations": [
                {{
                    "recommendation": "Resource adjustment recommendation",
                    "reasoning": "Reason for this recommendation"
                }}
            ],
            "timeline_adjustments": {{
                "necessary": true/false,
                "adjustment_days": number,
                "explanation": "Explanation of adjustment"
            }},
            "action_items": [
                {{
                    "action": "Specific action to take",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ]
        }}
        """
        
        logger.debug("Progress analysis prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting progress analysis prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, analyze the current project progress with {completed_tasks}/{total_tasks} tasks completed ({completion_percentage}%).

        Format your response as a JSON object with project health assessment and recommendations.
        """

@trace_method
def format_deliverable_integration_prompt(
    task: Dict[str, Any],
    deliverable: Dict[str, Any],
    related_deliverables: List[Dict[str, Any]]
) -> str:
    """
    Format prompt for analyzing and integrating deliverables.
    
    Args:
        task: Task information
        deliverable: The main deliverable to analyze
        related_deliverables: List of related deliverables
        
    Returns:
        str: Formatted prompt for deliverable integration
    """
    logger.debug(f"Formatting deliverable integration prompt for task {task.get('id', '')}")
    
    try:
        # Format task details
        task_id = task.get("id", "")
        task_name = task.get("name", "")
        
        # Format main deliverable details
        deliverable_id = deliverable.get("id", "")
        deliverable_type = deliverable.get("deliverable_type", "unknown")
        deliverable_agent = deliverable.get("source_agent_id", "")
        
        # Summarize content based on type
        content_summary = ""
        content = deliverable.get("content", {})
        
        if isinstance(content, dict):
            for key, value in content.items():
                content_summary += f"  - {key}: {str(value)[:100]}...\n"
        elif isinstance(content, str):
            content_summary = content[:500] + "..." if len(content) > 500 else content
        else:
            content_summary = str(content)[:500] + "..."
        
        # Format related deliverables
        related_text = ""
        for idx, related in enumerate(related_deliverables):
            related_id = related.get("id", "")
            related_type = related.get("deliverable_type", "")
            related_agent = related.get("source_agent_id", "")
            
            related_text += f"Related Deliverable {idx+1}:\n"
            related_text += f"  ID: {related_id}\n"
            related_text += f"  Type: {related_type}\n"
            related_text += f"  Agent: {related_agent}\n\n"
        
        prompt = f"""
        As a Team Lead AI, analyze the following deliverable and determine how to integrate it with related deliverables:

        TASK DETAILS:
        Task ID: {task_id}
        Task Name: {task_name}

        MAIN DELIVERABLE:
        Deliverable ID: {deliverable_id}
        Type: {deliverable_type}
        Source Agent: {deliverable_agent}
        
        CONTENT SUMMARY:
        {content_summary}

        RELATED DELIVERABLES:
        {related_text}

        Analyze this deliverable to:
        1. Determine if it meets the task requirements
        2. Identify any quality issues or concerns
        3. Assess how it integrates with related deliverables
        4. Recommend any necessary adjustments

        Format your response as a JSON object with:
        {{
            "acceptance": "accept/revise/reject",
            "quality_assessment": "Assessment of the deliverable quality",
            "integration_issues": [
                {{
                    "issue": "Description of an integration issue",
                    "severity": "HIGH/MEDIUM/LOW",
                    "resolution": "Suggested resolution approach"
                }}
            ],
            "recommended_adjustments": [
                {{
                    "adjustment": "Specific adjustment needed",
                    "reason": "Reason this adjustment is necessary"
                }}
            ],
            "combined_deliverable_approach": "Approach for combining with related deliverables",
            "next_steps": [
                "Specific next steps for this deliverable"
            ]
        }}
        """
        
        logger.debug("Deliverable integration prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting deliverable integration prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, analyze the deliverable for task {task.get('id', '')} to determine if it meets requirements and how to integrate it.

        Format your response as a JSON object with acceptance status and integration approach.
        """

@trace_method
def format_result_compilation_prompt(
    project_description: str,
    deliverables: Dict[str, Dict[str, Any]],
    component_structure: Dict[str, Any]
) -> str:
    """
    Format prompt for compiling final project results.
    
    Args:
        project_description: Project description
        deliverables: Dictionary of deliverables
        component_structure: Target component structure for the project
        
    Returns:
        str: Formatted prompt for result compilation
    """
    logger.debug("Formatting result compilation prompt")
    
    try:
        # Format deliverables summary
        deliverables_text = ""
        for deliv_id, deliverable in deliverables.items():
            deliv_type = deliverable.get("deliverable_type", "unknown")
            deliv_agent = deliverable.get("source_agent_id", "")
            deliv_task = deliverable.get("task_id", "")
            
            deliverables_text += f"Deliverable ID: {deliv_id}\n"
            deliverables_text += f"Type: {deliv_type}\n"
            deliverables_text += f"Agent: {deliv_agent}\n"
            deliverables_text += f"Task: {deliv_task}\n\n"
        
        # Format component structure
        structure_text = ""
        for component_type, directories in component_structure.get("directories", {}).items():
            structure_text += f"Component Type: {component_type}\n"
            structure_text += f"Directories: {', '.join(directories)}\n\n"
        
        prompt = f"""
        As a Team Lead AI, compile the following deliverables into a cohesive project result:

        PROJECT DESCRIPTION:
        {project_description}

        DELIVERABLES SUMMARY:
        {deliverables_text}

        TARGET PROJECT STRUCTURE:
        {structure_text}

        Your task is to:
        1. Organize all deliverables according to the target project structure
        2. Ensure consistency and compatibility between components
        3. Identify and resolve any conflicts or gaps
        4. Create a comprehensive project compilation plan

        Format your response as a JSON object with:
        {{
            "compilation_plan": {{
                "directory_structure": {{
                    "root_directory": "root_dir_name",
                    "subdirectories": [
                        {{
                            "path": "path/to/directory",
                            "purpose": "Purpose of this directory",
                            "contains": ["deliverable_id1", "deliverable_id2"]
                        }}
                    ]
                }},
                "file_mappings": [
                    {{
                        "deliverable_id": "deliverable_id",
                        "target_path": "path/relative/to/root",
                        "transformations_needed": ["transformation1", "transformation2"]
                    }}
                ],
                "integration_points": [
                    {{
                        "components": ["component1", "component2"],
                        "integration_approach": "Approach to integrate these components"
                    }}
                ]
            }},
            "conflict_resolutions": [
                {{
                    "conflict": "Description of the conflict",
                    "resolution": "Resolution approach",
                    "affected_deliverables": ["deliverable_id1", "deliverable_id2"]
                }}
            ],
            "gap_mitigations": [
                {{
                    "gap": "Description of an identified gap",
                    "mitigation": "Approach to address this gap",
                    "criticality": "HIGH/MEDIUM/LOW"
                }}
            ],
            "final_project_structure": {{
                "components": [
                    {{
                        "name": "Component name",
                        "path": "path/in/project",
                        "source_deliverables": ["deliverable_id1", "deliverable_id2"],
                        "description": "Component description"
                    }}
                ]
            }}
        }}
        """
        
        logger.debug("Result compilation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting result compilation prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, compile the project deliverables into a cohesive result based on the project description and target structure.

        Format your response as a JSON object with a compilation plan and project structure.
        """

@trace_method
def format_task_instruction_prompt(
    task: Dict[str, Any],
    agent_type: str,
    context: Dict[str, Any]
) -> str:
    """
    Format task instruction prompt for an agent.
    
    Args:
        task: Task information
        agent_type: Type of the agent receiving instructions
        context: Additional context for the task
        
    Returns:
        str: Formatted task instruction prompt
    """
    logger.debug(f"Formatting task instruction prompt for {agent_type} on task {task.get('id', '')}")
    
    try:
        # Format task details
        task_id = task.get("id", "")
        task_name = task.get("name", "")
        task_description = task.get("description", "")
        task_milestone = task.get("milestone", "")
        task_dependencies = ", ".join(task.get("dependencies", []))
        task_effort = task.get("estimated_effort", "MEDIUM")
        
        # Format context based on agent type
        context_text = ""
        
        if agent_type == "solution_architect":
            # Add architecture context
            architecture_context = context.get("architecture_context", {})
            requirements = architecture_context.get("requirements", [])
            constraints = architecture_context.get("constraints", [])
            
            context_text += "Architecture Context:\n"
            context_text += "Requirements:\n"
            for req in requirements:
                context_text += f"  - {req}\n"
            
            context_text += "Constraints:\n"
            for constraint in constraints:
                context_text += f"  - {constraint}\n"
            
        elif agent_type == "full_stack_developer":
            # Add development context
            dev_context = context.get("development_context", {})
            architecture = dev_context.get("architecture", "")
            tech_stack = dev_context.get("tech_stack", [])
            
            context_text += "Development Context:\n"
            context_text += f"Architecture: {architecture}\n"
            context_text += "Tech Stack:\n"
            for tech in tech_stack:
                context_text += f"  - {tech}\n"
            
        elif agent_type == "qa_test":
            # Add testing context
            test_context = context.get("test_context", {})
            test_requirements = test_context.get("test_requirements", [])
            test_environment = test_context.get("test_environment", "")
            
            context_text += "Testing Context:\n"
            context_text += f"Test Environment: {test_environment}\n"
            context_text += "Test Requirements:\n"
            for req in test_requirements:
                context_text += f"  - {req}\n"
        
        # Format deliverables
        deliverables = context.get("required_deliverables", [])
        deliverables_text = "Required Deliverables:\n"
        for deliverable in deliverables:
            deliverables_text += f"  - {deliverable}\n"
        
        # Format dependencies
        dependencies_context = context.get("dependencies_context", {})
        dependency_details = ""
        
        if dependencies_context:
            dependency_details = "Dependency Information:\n"
            for dep_id, details in dependencies_context.items():
                dep_name = details.get("name", "")
                dep_status = details.get("status", "")
                dep_agent = details.get("agent", "")
                
                dependency_details += f"  - Dependency {dep_id}: {dep_name} (Status: {dep_status}, Agent: {dep_agent})\n"
        
        prompt = f"""
        As a {agent_type.replace('_', ' ').title()}, you are assigned the following task:

        TASK DETAILS:
        Task ID: {task_id}
        Task Name: {task_name}
        Description: {task_description}
        Milestone: {task_milestone}
        Dependencies: {task_dependencies}
        Estimated Effort: {task_effort}

        {context_text}
        {deliverables_text}
        {dependency_details}

        Your objective is to complete this task according to the requirements.
        Please provide:
        1. A detailed plan for how you will approach this task
        2. Any questions or clarifications you need before proceeding
        3. The expected deliverables, with clear format and content specifications
        4. Any dependencies or constraints that might affect your work

        When you have completed the task, please provide the deliverables in a well-structured format
        that clearly identifies the components and their relationships.
        """
        
        logger.debug("Task instruction prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting task instruction prompt: {str(e)}", exc_info=True)
        return f"""
        As a {agent_type.replace('_', ' ').title()}, you are assigned task {task.get('id', '')} - {task.get('name', '')}.
        
        Please complete this task and provide the deliverables in a well-structured format.
        """

@trace_method
def format_agent_feedback_prompt(
    task: Dict[str, Any],
    deliverable: Dict[str, Any],
    feedback_points: List[str]
) -> str:
    """
    Format prompt for providing feedback to an agent on their deliverable.
    
    Args:
        task: Task information
        deliverable: The deliverable to provide feedback on
        feedback_points: List of feedback points to address
        
    Returns:
        str: Formatted prompt for agent feedback
    """
    logger.debug(f"Formatting agent feedback prompt for task {task.get('id', '')}")
    
    try:
        # Format task details
        task_id = task.get("id", "")
        task_name = task.get("name", "")
        
        # Format deliverable details
        deliverable_id = deliverable.get("id", "")
        deliverable_type = deliverable.get("deliverable_type", "unknown")
        deliverable_agent = deliverable.get("source_agent_id", "")
        
        # Format feedback points
        feedback_text = "Feedback Points:\n"
        for idx, point in enumerate(feedback_points):
            feedback_text += f"{idx+1}. {point}\n"
        
        prompt = f"""
        As a Team Lead AI, provide constructive feedback to an agent regarding their deliverable:

        TASK DETAILS:
        Task ID: {task_id}
        Task Name: {task_name}

        DELIVERABLE INFORMATION:
        Deliverable ID: {deliverable_id}
        Type: {deliverable_type}
        Agent: {deliverable_agent}

        {feedback_text}

        Create a constructive and helpful feedback message that:
        1. Acknowledges the work done and positive aspects
        2. Clearly explains the areas needing improvement
        3. Provides specific suggestions for how to address each feedback point
        4. Maintains a supportive and collaborative tone
        5. Sets clear expectations for any needed revisions

        Format your response as a JSON object with:
        {{
            "feedback_message": "Complete feedback message",
            "positive_aspects": [
                "Positive aspect of the deliverable"
            ],
            "improvement_areas": [
                {{
                    "area": "Area needing improvement",
                    "suggestion": "Specific suggestion for improvement",
                    "priority": "HIGH/MEDIUM/LOW"
                }}
            ],
            "revision_instructions": "Clear instructions for any needed revisions",
            "questions": [
                "Any questions for the agent to consider"
            ]
        }}
        """
        
        logger.debug("Agent feedback prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting agent feedback prompt: {str(e)}", exc_info=True)
        return f"""
        As a Team Lead AI, provide constructive feedback on the deliverable for task {task.get('id', '')}.

        Format your response as a JSON object with feedback message and improvement suggestions.
        """