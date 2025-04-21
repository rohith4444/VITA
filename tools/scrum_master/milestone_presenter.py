from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json
import uuid
import re
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.scrum_master.milestone_presenter")

class PresentationLevel(Enum):
    """Enum representing the level of detail for milestone presentations."""
    EXECUTIVE = "executive"       # High-level summary for executives
    BUSINESS = "business"         # Business-focused with moderate technical detail
    TECHNICAL = "technical"       # Technical details for knowledgeable stakeholders
    DEVELOPER = "developer"       # Full technical details for developers

class ComponentType(Enum):
    """Enum representing types of components in milestone presentations."""
    SUMMARY = "summary"           # Textual summary of milestone
    METRICS = "metrics"           # Achievement metrics
    VISUALIZATION = "visualization"  # Data visualization
    PROGRESS = "progress"         # Progress indicators
    COMPARISON = "comparison"     # Before/after comparison
    DECISIONS = "decisions"       # Decision points for users

class VisualizationType(Enum):
    """Enum representing types of visualizations for milestone data."""
    PROGRESS_BAR = "progress_bar"  # Simple progress bar
    TIMELINE = "timeline"         # Timeline of tasks and events
    COMPONENT_DIAGRAM = "component_diagram"  # Technical component relationship diagram
    FEATURE_LIST = "feature_list"  # List of completed features
    METRICS_CHART = "metrics_chart"  # Chart showing key metrics
    COMPARISON_TABLE = "comparison_table"  # Before/after comparison table

class MilestonePresentation:
    """Class representing a formatted milestone presentation for users."""
    
    def __init__(
        self,
        milestone_id: str,
        title: str,
        presentation_level: PresentationLevel,
        summary: str,
        key_points: List[str],
        visualizations: List[Dict[str, Any]],
        components: List[Dict[str, Any]],
        related_requirements: List[Dict[str, Any]] = None,
        decision_options: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.milestone_id = milestone_id
        self.title = title
        self.presentation_level = presentation_level
        self.summary = summary
        self.key_points = key_points
        self.visualizations = visualizations
        self.components = components
        self.related_requirements = related_requirements or []
        self.decision_options = decision_options or []
        self.metadata = metadata or {}
        self.generated_at = datetime.utcnow().isoformat()
        
        logger.debug(f"Created milestone presentation {self.id} for milestone {milestone_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert milestone presentation to dictionary for serialization."""
        return {
            "id": self.id,
            "milestone_id": self.milestone_id,
            "title": self.title,
            "presentation_level": self.presentation_level.value,
            "summary": self.summary,
            "key_points": self.key_points,
            "visualizations": self.visualizations,
            "components": self.components,
            "related_requirements": self.related_requirements,
            "decision_options": self.decision_options,
            "metadata": self.metadata,
            "generated_at": self.generated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MilestonePresentation':
        """Create a milestone presentation instance from a dictionary."""
        presentation = cls(
            milestone_id=data["milestone_id"],
            title=data["title"],
            presentation_level=PresentationLevel(data["presentation_level"]),
            summary=data["summary"],
            key_points=data["key_points"],
            visualizations=data["visualizations"],
            components=data["components"],
            related_requirements=data.get("related_requirements", []),
            decision_options=data.get("decision_options", []),
            metadata=data.get("metadata", {})
        )
        presentation.id = data.get("id", presentation.id)
        presentation.generated_at = data.get("generated_at", presentation.generated_at)
        return presentation

@trace_method
def format_milestone_for_user(
    milestone_data: Dict[str, Any],
    user_preferences: Dict[str, Any] = None,
    project_context: Dict[str, Any] = None
) -> MilestonePresentation:
    """
    Convert technical milestone data to a user-friendly presentation format.
    
    Args:
        milestone_data: Technical milestone information from the Team Lead agent
        user_preferences: User preferences for presentation style, detail level, etc.
        project_context: Broader project context including requirements, history, etc.
        
    Returns:
        MilestonePresentation: Formatted milestone presentation
    """
    logger.info(f"Formatting milestone {milestone_data.get('id', 'unknown')} for user presentation")
    
    # Default user preferences if not provided
    user_preferences = user_preferences or {
        "presentation_level": PresentationLevel.BUSINESS.value,
        "visualization_preference": "medium",
        "technical_detail": "medium",
        "use_analogies": True
    }
    
    # Extract milestone details
    milestone_id = milestone_data.get("id", str(uuid.uuid4()))
    milestone_name = milestone_data.get("name", "Project Milestone")
    milestone_description = milestone_data.get("description", "")
    completion_percentage = milestone_data.get("completion_percentage", 0)
    components = milestone_data.get("components", [])
    tasks = milestone_data.get("tasks", [])
    
    # Determine presentation level
    presentation_level_str = user_preferences.get("presentation_level", PresentationLevel.BUSINESS.value)
    try:
        presentation_level = PresentationLevel(presentation_level_str)
    except ValueError:
        logger.warning(f"Invalid presentation level: {presentation_level_str}, defaulting to BUSINESS")
        presentation_level = PresentationLevel.BUSINESS
    
    # Generate appropriate title
    title = _generate_milestone_title(milestone_name, presentation_level)
    
    # Generate summary based on presentation level
    summary = _generate_milestone_summary(
        milestone_name,
        milestone_description,
        completion_percentage,
        presentation_level,
        project_context
    )
    
    # Extract key points
    key_points = extract_key_points(milestone_data, presentation_level)
    
    # Create visualizations
    visualization_preference = user_preferences.get("visualization_preference", "medium")
    visualizations = create_visualizations(
        milestone_data,
        visualization_preference,
        presentation_level
    )
    
    # Create components (sections of the presentation)
    component_list = _create_presentation_components(
        milestone_data,
        presentation_level,
        user_preferences,
        project_context
    )
    
    # Relate to requirements
    related_requirements = relate_to_requirements(
        milestone_data,
        project_context
    )
    
    # Prepare decision options if needed
    decision_options = []
    if milestone_data.get("requires_decisions", False):
        decision_options = prepare_approval_options(milestone_data)
    
    # Create presentation
    presentation = MilestonePresentation(
        milestone_id=milestone_id,
        title=title,
        presentation_level=presentation_level,
        summary=summary,
        key_points=key_points,
        visualizations=visualizations,
        components=component_list,
        related_requirements=related_requirements,
        decision_options=decision_options,
        metadata={
            "original_milestone": {
                "id": milestone_id,
                "name": milestone_name,
                "completion_percentage": completion_percentage
            },
            "user_preferences": user_preferences
        }
    )
    
    logger.info(f"Successfully formatted milestone {milestone_id} for user presentation")
    return presentation

@trace_method
def _generate_milestone_title(
    milestone_name: str,
    presentation_level: PresentationLevel
) -> str:
    """
    Generate an appropriate title for the milestone presentation.
    
    Args:
        milestone_name: Original technical milestone name
        presentation_level: Presentation detail level
        
    Returns:
        str: User-friendly milestone title
    """
    # Clean up technical prefixes/suffixes
    clean_name = re.sub(r'(milestone[_\-\s]*\d+[_\-\s]*)', '', milestone_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'(v\d+\.\d+)', '', clean_name)
    clean_name = clean_name.strip()
    
    # Capitalize the first letter of each word
    clean_name = ' '.join(word.capitalize() for word in clean_name.split())
    
    # Add appropriate prefix based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        title = f"Executive Summary: {clean_name}"
    elif presentation_level == PresentationLevel.BUSINESS:
        title = f"Project Achievement: {clean_name}"
    elif presentation_level == PresentationLevel.TECHNICAL:
        title = f"Technical Milestone: {clean_name}"
    elif presentation_level == PresentationLevel.DEVELOPER:
        title = f"Development Milestone: {clean_name}"
    else:
        title = f"Project Milestone: {clean_name}"
    
    return title

@trace_method
def _generate_milestone_summary(
    milestone_name: str,
    milestone_description: str,
    completion_percentage: float,
    presentation_level: PresentationLevel,
    project_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a user-friendly summary of the milestone.
    
    Args:
        milestone_name: Original milestone name
        milestone_description: Technical milestone description
        completion_percentage: Percentage of milestone completion
        presentation_level: Presentation detail level
        project_context: Optional project context
        
    Returns:
        str: User-friendly milestone summary
    """
    # Extract project name from context if available
    project_name = "the project"
    if project_context and "project_name" in project_context:
        project_name = project_context["project_name"]
    
    # Basic summary template
    basic_summary = f"This milestone represents {completion_percentage}% completion of {milestone_name}."
    
    # Enhance summary based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Focus on business value and high-level achievements
        summary = f"""
        {basic_summary} This is a key achievement for {project_name}, representing significant progress 
        toward our business objectives. The team has successfully delivered core functionality 
        that will enable the next phase of development.
        """
    elif presentation_level == PresentationLevel.BUSINESS:
        # Balance technical and business aspects
        summary = f"""
        {basic_summary} This milestone delivers important functionality for {project_name}, 
        with the completion of several key features. The technical team has built the necessary 
        components while maintaining focus on the project requirements and business goals.
        """
    elif presentation_level == PresentationLevel.TECHNICAL:
        # More technical details while still being accessible
        summary = f"""
        {basic_summary} In this milestone, the development team has implemented the core technical 
        components needed for {project_name}. This includes architecture foundations, key 
        interfaces, and critical functionality that enables further development.
        """
    elif presentation_level == PresentationLevel.DEVELOPER:
        # Full technical details
        summary = f"""
        {basic_summary} This milestone encompasses the implementation of several critical 
        technical components and subsystems. The development team has built, tested, and 
        integrated these components according to the architectural specifications and 
        technical requirements.
        """
    else:
        summary = basic_summary
    
    # Incorporate the original description if it's not too technical
    if milestone_description and len(milestone_description) > 10:
        # Simplify the description based on presentation level
        simplified_description = _simplify_technical_text(
            milestone_description, 
            presentation_level
        )
        summary += f"\n\n{simplified_description}"
    
    # Clean up whitespace
    summary = re.sub(r'\s+', ' ', summary).strip()
    
    return summary

@trace_method
def _simplify_technical_text(
    text: str,
    presentation_level: PresentationLevel
) -> str:
    """
    Simplify technical text based on the presentation level.
    
    Args:
        text: Technical text to simplify
        presentation_level: Presentation detail level
        
    Returns:
        str: Simplified text
    """
    # For executive level, drastically simplify and shorten
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Remove technical terms and jargon
        simplified = re.sub(r'\b(implemented|integrated|deployed|configured|developed)\b', 'created', text)
        simplified = re.sub(r'\b(architecture|infrastructure|backend|frontend|database|API|interface)\b', 'system', simplified)
        
        # Limit length
        if len(simplified) > 100:
            simplified = simplified[:97] + "..."
            
    # For business level, moderate simplification
    elif presentation_level == PresentationLevel.BUSINESS:
        # Simplify some technical terms
        simplified = re.sub(r'\b(implemented|integrated)\b', 'built', text)
        simplified = re.sub(r'\b(configured|developed)\b', 'created', simplified)
        
        # Limit length less strictly
        if len(simplified) > 200:
            simplified = simplified[:197] + "..."
            
    # Technical level gets minimal simplification
    elif presentation_level == PresentationLevel.TECHNICAL:
        simplified = text
        
        # Very light length limit
        if len(simplified) > 300:
            simplified = simplified[:297] + "..."
            
    # Developer level gets the full text
    else:
        simplified = text
    
    return simplified

@trace_method
def extract_key_points(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> List[str]:
    """
    Extract the most important aspects of a milestone.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        List[str]: List of key points
    """
    logger.info("Extracting key points from milestone data")
    
    key_points = []
    
    # Extract completed tasks
    completed_tasks = [
        task for task in milestone_data.get("tasks", [])
        if task.get("status") == "completed"
    ]
    
    # Get components with high completion
    key_components = [
        comp for comp in milestone_data.get("components", [])
        if comp.get("completion_percentage", 0) >= 80
    ]
    
    # Extract achievements
    achievements = milestone_data.get("achievements", [])
    
    # Add overall completion as a key point
    completion_percentage = milestone_data.get("completion_percentage", 0)
    if presentation_level == PresentationLevel.EXECUTIVE:
        key_points.append(f"Overall milestone is {completion_percentage}% complete")
    else:
        key_points.append(f"Milestone {milestone_data.get('name', 'unknown')} is {completion_percentage}% complete")
    
    # Add achievements as key points
    for achievement in achievements:
        # Format based on presentation level
        if presentation_level == PresentationLevel.EXECUTIVE:
            # Business value focus
            if "business_value" in achievement:
                key_points.append(achievement["business_value"])
        elif presentation_level == PresentationLevel.BUSINESS:
            # Feature focus
            if "feature" in achievement:
                key_points.append(f"Completed {achievement['feature']}")
        elif presentation_level == PresentationLevel.TECHNICAL:
            # Technical achievement focus
            if "technical_achievement" in achievement:
                key_points.append(achievement["technical_achievement"])
        else:  # DEVELOPER
            # Implementation details
            if "implementation_detail" in achievement:
                key_points.append(achievement["implementation_detail"])
    
    # Add completed tasks as key points
    if completed_tasks:
        if presentation_level in [PresentationLevel.EXECUTIVE, PresentationLevel.BUSINESS]:
            # Group tasks by category for higher levels
            task_categories = {}
            for task in completed_tasks:
                category = task.get("category", "Other")
                if category not in task_categories:
                    task_categories[category] = 0
                task_categories[category] += 1
            
            for category, count in task_categories.items():
                key_points.append(f"Completed {count} tasks in {category}")
        else:
            # List individual important tasks for technical levels
            for task in completed_tasks[:5]:  # Limit to 5 tasks
                key_points.append(f"Completed: {task.get('name', 'task')}")
    
    # Add component information
    if key_components:
        if presentation_level in [PresentationLevel.EXECUTIVE, PresentationLevel.BUSINESS]:
            # Just mention the number of components
            key_points.append(f"Delivered {len(key_components)} key components")
        else:
            # List the components
            for comp in key_components[:3]:  # Limit to 3 components
                key_points.append(f"Completed component: {comp.get('name', 'component')}")
    
    # Add next steps
    next_steps = milestone_data.get("next_steps", [])
    if next_steps and len(next_steps) > 0:
        if presentation_level in [PresentationLevel.EXECUTIVE, PresentationLevel.BUSINESS]:
            key_points.append(f"Next focus: {next_steps[0]}")
        else:
            key_points.append(f"Next development step: {next_steps[0]}")
    
    logger.debug(f"Extracted {len(key_points)} key points")
    return key_points

@trace_method
def create_visualizations(
    milestone_data: Dict[str, Any],
    visualization_preference: str,
    presentation_level: PresentationLevel
) -> List[Dict[str, Any]]:
    """
    Generate visual representations of milestone progress or achievements.
    
    Args:
        milestone_data: Technical milestone information
        visualization_preference: User preference for visualization density (minimal, medium, detailed)
        presentation_level: Presentation detail level
        
    Returns:
        List[Dict[str, Any]]: List of visualization specifications
    """
    logger.info("Creating visualizations for milestone data")
    
    visualizations = []
    
    # Determine number of visualizations based on preference
    max_visualizations = 1  # Default minimal
    if visualization_preference == "medium":
        max_visualizations = 2
    elif visualization_preference == "detailed":
        max_visualizations = 4
    
    # Always include a progress visualization
    progress_viz = _create_progress_visualization(milestone_data, presentation_level)
    if progress_viz:
        visualizations.append(progress_viz)
    
    # Add component completion chart if we have components and space for more visualizations
    if len(visualizations) < max_visualizations and milestone_data.get("components", []):
        component_viz = _create_component_visualization(milestone_data, presentation_level)
        if component_viz:
            visualizations.append(component_viz)
    
    # Add timeline if appropriate and we have space
    if len(visualizations) < max_visualizations and milestone_data.get("timeline", {}):
        timeline_viz = _create_timeline_visualization(milestone_data, presentation_level)
        if timeline_viz:
            visualizations.append(timeline_viz)
    
    # Add feature comparison if appropriate and we have space
    if len(visualizations) < max_visualizations and presentation_level in [PresentationLevel.BUSINESS, PresentationLevel.TECHNICAL]:
        feature_viz = _create_feature_visualization(milestone_data, presentation_level)
        if feature_viz:
            visualizations.append(feature_viz)
    
    logger.debug(f"Created {len(visualizations)} visualizations")
    return visualizations

@trace_method
def _create_progress_visualization(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Optional[Dict[str, Any]]:
    """
    Create a progress visualization for the milestone.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        Optional[Dict[str, Any]]: Progress visualization specification or None
    """
    # Get completion percentage
    completion_percentage = milestone_data.get("completion_percentage", 0)
    
    # Get task status counts if available
    task_statuses = {}
    for task in milestone_data.get("tasks", []):
        status = task.get("status", "unknown")
        task_statuses[status] = task_statuses.get(status, 0) + 1
    
    # Create appropriate visualization based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Simple progress bar for executives
        return {
            "type": VisualizationType.PROGRESS_BAR.value,
            "title": "Milestone Progress",
            "data": {
                "percentage": completion_percentage,
                "color": "#4CAF50" if completion_percentage >= 80 else "#FFC107"
            },
            "width": 400,
            "height": 80
        }
    elif presentation_level == PresentationLevel.BUSINESS:
        # Progress bar with task summary for business users
        return {
            "type": VisualizationType.PROGRESS_BAR.value,
            "title": "Milestone Progress",
            "data": {
                "percentage": completion_percentage,
                "color": "#4CAF50" if completion_percentage >= 80 else "#FFC107",
                "task_summary": {
                    "completed": task_statuses.get("completed", 0),
                    "in_progress": task_statuses.get("in_progress", 0),
                    "pending": task_statuses.get("pending", 0)
                }
            },
            "width": 500,
            "height": 120
        }
    elif presentation_level == PresentationLevel.TECHNICAL:
        # Detailed metrics chart for technical users
        return {
            "type": VisualizationType.METRICS_CHART.value,
            "title": "Milestone Metrics",
            "data": {
                "completion_percentage": completion_percentage,
                "task_statuses": task_statuses,
                "time_spent": milestone_data.get("time_spent", {})
            },
            "width": 600,
            "height": 300
        }
    else:  # DEVELOPER
        # Component-level progress for developers
        component_progress = []
        for comp in milestone_data.get("components", []):
            component_progress.append({
                "name": comp.get("name", "Unknown"),
                "percentage": comp.get("completion_percentage", 0),
                "tasks_completed": sum(1 for t in comp.get("tasks", []) if t.get("status") == "completed"),
                "tasks_total": len(comp.get("tasks", []))
            })
        
        return {
            "type": VisualizationType.COMPONENT_DIAGRAM.value,
            "title": "Component Progress",
            "data": {
                "overall_percentage": completion_percentage,
                "components": component_progress
            },
            "width": 700,
            "height": 400
        }

@trace_method
def _create_component_visualization(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Optional[Dict[str, Any]]:
    """
    Create a visualization of component completion.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        Optional[Dict[str, Any]]: Component visualization specification or None
    """
    components = milestone_data.get("components", [])
    if not components:
        return None
    
    # Format component data
    component_data = []
    for comp in components:
        component_data.append({
            "name": comp.get("name", "Unknown"),
            "percentage": comp.get("completion_percentage", 0)
        })
    
    # Sort by completion percentage (descending)
    component_data.sort(key=lambda x: x["percentage"], reverse=True)
    
    # Limit number of components based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Only top 3 components for executives
        component_data = component_data[:3]
    elif presentation_level == PresentationLevel.BUSINESS:
        # Top 5 for business users
        component_data = component_data[:5]
    elif presentation_level == PresentationLevel.TECHNICAL:
        # Top 8 for technical users
        component_data = component_data[:8]
    
    # Create visualization
    return {
        "type": VisualizationType.METRICS_CHART.value,
        "title": "Component Completion",
        "data": {
            "components": component_data
        },
        "width": 500,
        "height": 300
    }

@trace_method
def _create_timeline_visualization(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Optional[Dict[str, Any]]:
    """
    Create a timeline visualization for the milestone.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        Optional[Dict[str, Any]]: Timeline visualization specification or None
    """
    timeline = milestone_data.get("timeline", {})
    if not timeline:
        return None
    
    # Format timeline data
    timeline_events = []
    
    # Add start event
    if "start_date" in timeline:
        timeline_events.append({
            "date": timeline["start_date"],
            "event": "Milestone Started",
            "type": "start"
        })
    
    # Add major events
    for event in timeline.get("key_events", []):
        timeline_events.append({
            "date": event.get("date", ""),
            "event": event.get("description", "Event"),
            "type": event.get("type", "event")
        })
    
    # Add completion event if available
    if "completion_date" in timeline:
        timeline_events.append({
            "date": timeline["completion_date"],
            "event": "Milestone Completed",
            "type": "completion"
        })
    
    # Sort events by date
    timeline_events.sort(key=lambda x: x["date"])
    
    # Limit detail based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Only start and completion for executives
        timeline_events = [e for e in timeline_events if e["type"] in ["start", "completion"]]
    elif presentation_level == PresentationLevel.BUSINESS:
        # Major events only for business
        timeline_events = [e for e in timeline_events if e["type"] in ["start", "completion", "major"]]
    
    # Create visualization
    return {
        "type": VisualizationType.TIMELINE.value,
        "title": "Milestone Timeline",
        "data": {
            "events": timeline_events,
            "current_date": datetime.utcnow().isoformat()
        },
        "width": 600,
        "height": 200
    }

@trace_method
def _create_feature_visualization(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Optional[Dict[str, Any]]:
    """
    Create a visualization of completed features.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        Optional[Dict[str, Any]]: Feature visualization specification or None
    """
    features = milestone_data.get("features", [])
    if not features:
        return None
    
    # Format feature data
    feature_data = []
    for feature in features:
        if feature.get("status") == "completed":
            feature_data.append({
                "name": feature.get("name", "Unknown"),
                "description": feature.get("description", ""),
                "importance": feature.get("importance", "medium")
            })
    
    if not feature_data:
        return None
    
    # Sort by importance
    importance_order = {"high": 0, "critical": 0, "medium": 1, "low": 2}
    feature_data.sort(key=lambda x: importance_order.get(x["importance"].lower(), 999))
    
    # Limit number of features based on presentation level
    if presentation_level == PresentationLevel.EXECUTIVE:
        # Only top 3 features for executives
        feature_data = feature_data[:3]
    elif presentation_level == PresentationLevel.BUSINESS:
        # Top 5 for business users
        feature_data = feature_data[:5]
    else:
        # Top 8 for technical/developer users
        feature_data = feature_data[:8]
    
    # Create visualization
    return {
        "type": VisualizationType.FEATURE_LIST.value,
        "title": "Completed Features",
        "data": {
            "features": feature_data
        },
        "width": 500,
        "height": 300
    }

@trace_method
def _create_presentation_components(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel,
    user_preferences: Dict[str, Any],
    project_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Create components (sections) for the milestone presentation.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        user_preferences: User preferences
        project_context: Optional project context
        
    Returns:
        List[Dict[str, Any]]: List of presentation components
    """
    logger.info("Creating presentation components")
    
    components = []
    
    # Determine technical detail level
    technical_detail = user_preferences.get("technical_detail", "medium")
    
    # Always add a summary component
    summary_component = {
        "type": ComponentType.SUMMARY.value,
        "title": "Summary",
        "content": _generate_milestone_summary(
            milestone_data.get("name", ""),
            milestone_data.get("description", ""),
            milestone_data.get("completion_percentage", 0),
            presentation_level,
            project_context
        )
    }
    components.append(summary_component)
    
    # Add metrics for business, technical and developer levels
    if presentation_level != PresentationLevel.EXECUTIVE:
        metrics_component = {
            "type": ComponentType.METRICS.value,
            "title": "Key Metrics",
            "metrics": _generate_metrics(milestone_data, presentation_level)
        }
        components.append(metrics_component)
    
    # Add progress component for all levels
    progress_component = {
        "type": ComponentType.PROGRESS.value,
        "title": "Progress Overview",
        "content": _generate_progress_content(milestone_data, presentation_level, technical_detail)
    }
    components.append(progress_component)
    
    # Add requirement comparison for business and technical levels
    if presentation_level in [PresentationLevel.BUSINESS, PresentationLevel.TECHNICAL]:
        comparison_component = {
            "type": ComponentType.COMPARISON.value,
            "title": "Requirements Fulfillment",
            "content": _generate_requirements_comparison(milestone_data, project_context),
            "requirements": relate_to_requirements(milestone_data, project_context)
        }
        components.append(comparison_component)
    
    # Add technical decisions component for technical and developer levels
    if presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
        decisions_component = {
            "type": ComponentType.DECISIONS.value,
            "title": "Technical Decisions",
            "content": _generate_technical_decisions_content(milestone_data, technical_detail),
            "decisions": milestone_data.get("technical_decisions", [])
        }
        components.append(decisions_component)
    
    # Add user decision options if milestone requires decisions
    if milestone_data.get("requires_decisions", False):
        options_component = {
            "type": ComponentType.DECISIONS.value,
            "title": "Action Required",
            "content": "This milestone requires your review and decision.",
            "options": prepare_approval_options(milestone_data)
        }
        components.append(options_component)
    
    logger.info(f"Created {len(components)} presentation components")
    return components

@trace_method
def _generate_metrics(
    milestone_data: Dict[str, Any], 
    presentation_level: PresentationLevel
) -> List[Dict[str, Any]]:
    """
    Generate key metrics for the milestone presentation.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        
    Returns:
        List[Dict[str, Any]]: List of metrics
    """
    logger.info("Generating metrics for milestone presentation")
    
    metrics = []
    
    # Basic metrics for all levels
    metrics.append({
        "name": "Completion",
        "value": f"{milestone_data.get('completion_percentage', 0)}%",
        "description": "Overall milestone completion"
    })
    
    # Add task metrics
    tasks = milestone_data.get("tasks", [])
    if tasks:
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        total_tasks = len(tasks)
        
        metrics.append({
            "name": "Tasks Completed",
            "value": f"{completed_tasks}/{total_tasks}",
            "description": "Tasks finished vs. total tasks"
        })
    
    # Add technical metrics for technical and developer levels
    if presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
        # Add code metrics if available
        code_metrics = milestone_data.get("code_metrics", {})
        if code_metrics:
            if "lines_of_code" in code_metrics:
                metrics.append({
                    "name": "Lines of Code",
                    "value": str(code_metrics["lines_of_code"]),
                    "description": "New lines of code written"
                })
            
            if "test_coverage" in code_metrics:
                metrics.append({
                    "name": "Test Coverage",
                    "value": f"{code_metrics['test_coverage']}%",
                    "description": "Code coverage by tests"
                })
    
    # Add timeline metrics
    timeline = milestone_data.get("timeline", {})
    if timeline:
        if "estimated_duration" in timeline and "actual_duration" in timeline:
            variance = timeline["actual_duration"] - timeline["estimated_duration"]
            variance_str = f"{variance:+d}" if variance else "0"  # Show +/- sign
            
            metrics.append({
                "name": "Timeline Variance",
                "value": f"{variance_str} days",
                "description": "Actual vs. estimated duration"
            })
    
    logger.debug(f"Generated {len(metrics)} metrics")
    return metrics

@trace_method
def _generate_progress_content(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel,
    technical_detail: str
) -> str:
    """
    Generate detailed progress content for the milestone.
    
    Args:
        milestone_data: Technical milestone information
        presentation_level: Presentation detail level
        technical_detail: Level of technical detail (low, medium, high)
        
    Returns:
        str: Formatted progress content
    """
    logger.info("Generating progress content")
    
    # Get completion data
    completion_percentage = milestone_data.get("completion_percentage", 0)
    tasks = milestone_data.get("tasks", [])
    components = milestone_data.get("components", [])
    
    # Count task statuses
    task_counts = {"completed": 0, "in_progress": 0, "pending": 0, "blocked": 0}
    for task in tasks:
        status = task.get("status", "pending")
        if status in task_counts:
            task_counts[status] += 1
    
    # Base content for all levels
    if completion_percentage >= 80:
        status_description = "is nearing completion"
    elif completion_percentage >= 50:
        status_description = "is well underway"
    elif completion_percentage >= 25:
        status_description = "has made good initial progress"
    else:
        status_description = "is in its early stages"
    
    content = f"This milestone {status_description} with {completion_percentage}% of work completed. "
    
    # Add task information
    total_tasks = sum(task_counts.values())
    if total_tasks > 0:
        content += f"Of {total_tasks} total tasks, {task_counts['completed']} are completed, "
        content += f"{task_counts['in_progress']} are in progress, and {task_counts['pending']} are pending. "
        
        if task_counts["blocked"] > 0:
            content += f"There are {task_counts['blocked']} blocked tasks that require attention. "
    
    # Add component information based on presentation level
    if components and presentation_level != PresentationLevel.EXECUTIVE:
        # For business level, summarize components
        if presentation_level == PresentationLevel.BUSINESS:
            completed_components = sum(1 for c in components if c.get("completion_percentage", 0) >= 100)
            in_progress_components = sum(1 for c in components if 0 < c.get("completion_percentage", 0) < 100)
            
            content += f"\n\nThe milestone includes {len(components)} components or modules. "
            content += f"{completed_components} components are complete and {in_progress_components} are in progress. "
            
        # For technical levels, provide component details
        elif presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
            # Get component details based on technical_detail level
            if technical_detail == "high":
                # Include all components with detailed status
                content += "\n\nComponent Progress:\n"
                for component in components:
                    comp_name = component.get("name", "Unnamed component")
                    comp_percentage = component.get("completion_percentage", 0)
                    comp_description = component.get("description", "")
                    
                    content += f"- {comp_name}: {comp_percentage}% complete"
                    if comp_description and len(comp_description) > 0:
                        content += f" - {comp_description}"
                    content += "\n"
            else:
                # Just list major components with basic status
                major_components = sorted(components, key=lambda c: c.get("importance", 0), reverse=True)[:5]
                content += "\n\nMajor Component Progress:\n"
                for component in major_components:
                    comp_name = component.get("name", "Unnamed component")
                    comp_percentage = component.get("completion_percentage", 0)
                    
                    content += f"- {comp_name}: {comp_percentage}% complete\n"
    
    # Add timeline information
    timeline = milestone_data.get("timeline", {})
    if timeline:
        start_date = timeline.get("start_date", "Unknown")
        current_date = datetime.utcnow().isoformat()
        
        # Format dates for display
        try:
            start_display = datetime.fromisoformat(start_date).strftime("%B %d, %Y")
        except (ValueError, TypeError):
            start_display = start_date
            
        try:
            current_display = datetime.fromisoformat(current_date).strftime("%B %d, %Y")
        except (ValueError, TypeError):
            current_display = current_date
            
        content += f"\n\nThe milestone started on {start_display} and is currently in progress as of {current_display}. "
        
        # Add end date if available
        if "completion_date" in timeline:
            try:
                end_display = datetime.fromisoformat(timeline["completion_date"]).strftime("%B %d, %Y")
                content += f"Completion is expected by {end_display}. "
            except (ValueError, TypeError):
                content += f"Completion is expected by {timeline['completion_date']}. "
        
        # Add timeline variance for non-executive levels
        if presentation_level != PresentationLevel.EXECUTIVE:
            if "estimated_duration" in timeline and "actual_duration" in timeline:
                variance = timeline["actual_duration"] - timeline["estimated_duration"]
                if variance > 0:
                    content += f"The milestone is currently {variance} days behind schedule. "
                elif variance < 0:
                    content += f"The milestone is currently {abs(variance)} days ahead of schedule. "
                else:
                    content += "The milestone is currently on schedule. "
    
    # Clean up whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    content = content.replace(" \n", "\n").replace("\n ", "\n")
    
    logger.debug("Generated progress content")
    return content

@trace_method
def _generate_requirements_comparison(
    milestone_data: Dict[str, Any],
    project_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate content comparing milestone achievements to original requirements.
    
    Args:
        milestone_data: Technical milestone information
        project_context: Optional project context including requirements
        
    Returns:
        str: Formatted requirements comparison content
    """
    logger.info("Generating requirements comparison")
    
    # Default content if no project context
    if not project_context or "requirements" not in project_context:
        return "Requirement fulfillment information is not available."
    
    requirements = project_context.get("requirements", [])
    if not requirements:
        return "No specific requirements were defined for this project."
    
    content = "This milestone addresses the following project requirements:\n\n"
    
    # Get requirement coverage from milestone data or calculate it
    requirement_coverage = milestone_data.get("requirement_coverage", {})
    
    if not requirement_coverage and "features" in milestone_data:
        # Calculate coverage based on features
        features = milestone_data.get("features", [])
        for req in requirements:
            req_id = req.get("id", "")
            if not req_id:
                continue
                
            # Check if any feature maps to this requirement
            for feature in features:
                if req_id in feature.get("requirement_ids", []):
                    status = "complete" if feature.get("status") == "completed" else "in_progress"
                    requirement_coverage[req_id] = {
                        "status": status,
                        "percentage": 100 if status == "complete" else feature.get("completion_percentage", 0)
                    }
    
    # Format each requirement
    for req in requirements:
        req_id = req.get("id", "")
        req_desc = req.get("description", "Unknown requirement")
        
        if req_id in requirement_coverage:
            coverage = requirement_coverage[req_id]
            status = coverage.get("status", "not_started")
            percentage = coverage.get("percentage", 0)
            
            if status == "complete":
                content += f"✅ {req_desc} - Completed\n"
            elif status == "in_progress":
                content += f"🔄 {req_desc} - In progress ({percentage}% complete)\n"
            else:
                content += f"⏳ {req_desc} - Not started\n"
        else:
            content += f"⏳ {req_desc} - Not addressed in this milestone\n"
    
    logger.debug("Generated requirements comparison")
    return content

@trace_method
def _generate_technical_decisions_content(
    milestone_data: Dict[str, Any],
    technical_detail: str
) -> str:
    """
    Generate content explaining technical decisions made in the milestone.
    
    Args:
        milestone_data: Technical milestone information
        technical_detail: Level of technical detail (low, medium, high)
        
    Returns:
        str: Formatted technical decisions content
    """
    logger.info("Generating technical decisions content")
    
    technical_decisions = milestone_data.get("technical_decisions", [])
    if not technical_decisions:
        return "No significant technical decisions were documented for this milestone."
    
    content = "This milestone involved the following key technical decisions:\n\n"
    
    for decision in technical_decisions:
        decision_name = decision.get("name", "Unnamed decision")
        decision_description = decision.get("description", "")
        alternatives = decision.get("alternatives", [])
        rationale = decision.get("rationale", "")
        
        content += f"## {decision_name}\n\n"
        
        if decision_description:
            content += f"{decision_description}\n\n"
        
        # Add rationale
        if rationale:
            content += f"**Rationale**: {rationale}\n\n"
        
        # Add alternatives for high technical detail
        if technical_detail == "high" and alternatives:
            content += "**Alternatives Considered**:\n"
            for alt in alternatives:
                alt_name = alt.get("name", "")
                alt_reason = alt.get("rejection_reason", "")
                content += f"- {alt_name}"
                if alt_reason:
                    content += f": {alt_reason}"
                content += "\n"
            content += "\n"
    
    logger.debug("Generated technical decisions content")
    return content

@trace_method
def relate_to_requirements(
    milestone_data: Dict[str, Any],
    project_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Connect milestone achievements to original project requirements.
    
    Args:
        milestone_data: Technical milestone information
        project_context: Optional project context including requirements
        
    Returns:
        List[Dict[str, Any]]: List of requirement relationships
    """
    logger.info("Relating milestone to requirements")
    
    relationships = []
    
    # Return empty list if no project context
    if not project_context or "requirements" not in project_context:
        logger.warning("No project context or requirements available")
        return relationships
    
    requirements = project_context.get("requirements", [])
    if not requirements:
        logger.warning("No requirements defined in project context")
        return relationships
    
    # Get requirement coverage from milestone data
    requirement_coverage = milestone_data.get("requirement_coverage", {})
    
    # Build relationships based on requirement coverage
    for req in requirements:
        req_id = req.get("id", "")
        if not req_id:
            continue
            
        req_desc = req.get("description", "Unknown requirement")
        req_category = req.get("category", "functional")
        
        relationship = {
            "requirement_id": req_id,
            "description": req_desc,
            "category": req_category,
            "covered_by_milestone": False,
            "coverage_level": 0,
            "implemented_by": []
        }
        
        # Check if requirement is covered
        if req_id in requirement_coverage:
            coverage = requirement_coverage[req_id]
            status = coverage.get("status", "not_started")
            percentage = coverage.get("percentage", 0)
            
            relationship["covered_by_milestone"] = status != "not_started"
            relationship["coverage_level"] = percentage
            
            # Find implementing components/features
            if "components" in milestone_data:
                for comp in milestone_data["components"]:
                    comp_name = comp.get("name", "")
                    comp_reqs = comp.get("requirements", [])
                    
                    if req_id in comp_reqs:
                        relationship["implemented_by"].append({
                            "type": "component",
                            "name": comp_name,
                            "completion": comp.get("completion_percentage", 0)
                        })
            
            if "features" in milestone_data:
                for feature in milestone_data["features"]:
                    feature_name = feature.get("name", "")
                    feature_reqs = feature.get("requirement_ids", [])
                    
                    if req_id in feature_reqs:
                        relationship["implemented_by"].append({
                            "type": "feature",
                            "name": feature_name,
                            "completion": 100 if feature.get("status") == "completed" else feature.get("completion_percentage", 0)
                        })
        
        relationships.append(relationship)
    
    logger.debug(f"Created {len(relationships)} requirement relationships")
    return relationships

@trace_method
def prepare_approval_options(
    milestone_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Format decision options for user approval.
    
    Args:
        milestone_data: Technical milestone information
        
    Returns:
        List[Dict[str, Any]]: Formatted decision options
    """
    logger.info("Preparing approval options")
    
    # Default approval options
    default_options = [
        {
            "id": "approve",
            "label": "Approve",
            "description": "Accept this milestone as complete",
            "type": "positive"
        },
        {
            "id": "approve_with_feedback",
            "label": "Approve with Feedback",
            "description": "Accept the milestone but provide feedback for future work",
            "type": "positive",
            "requires_comment": True
        },
        {
            "id": "request_changes",
            "label": "Request Changes",
            "description": "Request specific changes before approving",
            "type": "negative",
            "requires_comment": True
        },
        {
            "id": "reject",
            "label": "Reject",
            "description": "Reject this milestone (requires explanation)",
            "type": "negative",
            "requires_comment": True
        }
    ]
    
    # Check if milestone has custom approval options
    custom_options = milestone_data.get("approval_options", [])
    if custom_options:
        logger.debug(f"Using {len(custom_options)} custom approval options")
        return custom_options
    
    # Check if milestone has specific decision points
    decision_points = milestone_data.get("decision_points", [])
    if decision_points:
        # Create specific decision options for each decision point
        decision_options = []
        
        for decision in decision_points:
            decision_id = decision.get("id", str(uuid.uuid4())[:8])
            decision_question = decision.get("question", "Make a decision")
            decision_context = decision.get("context", "")
            decision_choices = decision.get("options", [])
            
            # Create decision option group
            decision_group = {
                "id": f"decision_{decision_id}",
                "question": decision_question,
                "context": decision_context,
                "choices": []
            }
            
            # Add choices or use yes/no if none provided
            if decision_choices:
                for choice in decision_choices:
                    decision_group["choices"].append({
                        "id": choice.get("id", str(uuid.uuid4())[:8]),
                        "label": choice.get("label", ""),
                        "description": choice.get("description", ""),
                        "type": choice.get("type", "neutral")
                    })
            else:
                decision_group["choices"] = [
                    {
                        "id": f"{decision_id}_yes",
                        "label": "Yes",
                        "description": "Agree with the proposed approach",
                        "type": "positive"
                    },
                    {
                        "id": f"{decision_id}_no",
                        "label": "No",
                        "description": "Disagree with the proposed approach",
                        "type": "negative",
                        "requires_comment": True
                    }
                ]
                
            decision_options.append(decision_group)
            
        # Always add the overall approval options
        decision_options.append({
            "id": "overall_approval",
            "question": "Overall Milestone Approval",
            "context": "Do you approve this milestone?",
            "choices": default_options
        })
        
        logger.debug(f"Created {len(decision_options)} decision option groups")
        return decision_options
    
    # If no specific decisions, return default options
    logger.debug("Using default approval options")
    return default_options

@trace_method
def create_milestone_visualization_data(
    milestone_data: Dict[str, Any],
    visualization_type: VisualizationType,
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """
    Create data for milestone visualizations.
    
    Args:
        milestone_data: Technical milestone information
        visualization_type: Type of visualization to create
        presentation_level: Presentation detail level
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info(f"Creating {visualization_type.value} visualization data")
    
    # Handle different visualization types
    if visualization_type == VisualizationType.PROGRESS_BAR:
        return _create_progress_bar_data(milestone_data, presentation_level)
    elif visualization_type == VisualizationType.TIMELINE:
        return _create_timeline_data(milestone_data, presentation_level)
    elif visualization_type == VisualizationType.COMPONENT_DIAGRAM:
        return _create_component_diagram_data(milestone_data, presentation_level)
    elif visualization_type == VisualizationType.FEATURE_LIST:
        return _create_feature_list_data(milestone_data, presentation_level)
    elif visualization_type == VisualizationType.METRICS_CHART:
        return _create_metrics_chart_data(milestone_data, presentation_level)
    elif visualization_type == VisualizationType.COMPARISON_TABLE:
        return _create_comparison_table_data(milestone_data, presentation_level)
    else:
        logger.warning(f"Unknown visualization type: {visualization_type}")
        return {"error": f"Unknown visualization type: {visualization_type}"}

@trace_method
def _create_progress_bar_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a progress bar visualization."""
    completion_percentage = milestone_data.get("completion_percentage", 0)
    
    # Determine color based on completion
    if completion_percentage >= 80:
        color = "#4CAF50"  # Green
    elif completion_percentage >= 50:
        color = "#2196F3"  # Blue
    elif completion_percentage >= 25:
        color = "#FFC107"  # Amber
    else:
        color = "#FF9800"  # Orange
    
    # Basic progress data
    progress_data = {
        "percentage": completion_percentage,
        "color": color
    }
    
    # Add task summary for non-executive levels
    if presentation_level != PresentationLevel.EXECUTIVE:
        tasks = milestone_data.get("tasks", [])
        task_statuses = {
            "completed": sum(1 for t in tasks if t.get("status") == "completed"),
            "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
            "pending": sum(1 for t in tasks if t.get("status") == "pending"),
            "blocked": sum(1 for t in tasks if t.get("status") == "blocked")
        }
        progress_data["task_summary"] = task_statuses
    
    return {
        "type": "progress_bar",
        "data": progress_data
    }

@trace_method
def _create_timeline_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a timeline visualization."""
    timeline = milestone_data.get("timeline", {})
    if not timeline:
        return {"error": "No timeline data available"}
    
    events = []
    
    # Add start date
    if "start_date" in timeline:
        events.append({
            "date": timeline["start_date"],
            "label": "Start",
            "type": "start"
        })
    
    # Add key events
    for event in timeline.get("key_events", []):
        if event.get("date") and event.get("description"):
            events.append({
                "date": event["date"],
                "label": event["description"],
                "type": event.get("type", "event")
            })
    
    # Add completion date if available
    if "completion_date" in timeline:
        events.append({
            "date": timeline["completion_date"],
            "label": "Completion",
            "type": "end"
        })
    
    # Add current date
    current_date = datetime.utcnow().isoformat()
    events.append({
        "date": current_date,
        "label": "Today",
        "type": "current"
    })
    
    # Sort events by date
    events.sort(key=lambda x: x["date"])
    
    return {
        "type": "timeline",
        "data": {
            "events": events,
            "current_date": current_date
        }
    }

# Helper functions for other visualization types would follow the same pattern
# _create_component_diagram_data, _create_feature_list_data, etc.

# This function would be used to format the milestone for different output formats
@trace_method
def format_milestone_for_output(
    milestone_presentation: MilestonePresentation,
    output_format: str = "json"
) -> Union[str, Dict[str, Any]]:
    """
    Format the milestone presentation for different output formats.
    
    Args:
        milestone_presentation: The prepared milestone presentation
        output_format: Output format (json, html, markdown, etc.)
        
    Returns:
        Union[str, Dict[str, Any]]: Formatted milestone presentation
    """
    logger.info(f"Formatting milestone for {output_format} output")
    
    if output_format == "json":
        return milestone_presentation.to_dict()
    
    elif output_format == "markdown":
        return _format_milestone_as_markdown(milestone_presentation)
    
    elif output_format == "html":
        return _format_milestone_as_html(milestone_presentation)
    
    else:
        logger.warning(f"Unknown output format: {output_format}, defaulting to json")
        return milestone_presentation.to_dict()

@trace_method
def _format_milestone_as_markdown(milestone_presentation: MilestonePresentation) -> str:
    """Format the milestone presentation as Markdown."""
    md = f"# {milestone_presentation.title}\n\n"
    
    # Add summary
    md += f"{milestone_presentation.summary}\n\n"
    
    # Add key points
    if milestone_presentation.key_points:
        md += "## Key Points\n\n"
        for point in milestone_presentation.key_points:
            md += f"* {point}\n"
        md += "\n"
    
    # Add components
    for component in milestone_presentation.components:
        md += f"## {component.get('title', 'Component')}\n\n"
        
        if component.get('type') == ComponentType.METRICS.value:
            # Format metrics
            metrics = component.get('metrics', [])
            for metric in metrics:
                md += f"* **{metric.get('name', '')}**: {metric.get('value', '')}"
                if 'description' in metric:
                    md += f" - {metric['description']}"
                md += "\n"
            md += "\n"
        else:
            # Regular content
            content = component.get('content', '')
            if content:
                md += f"{content}\n\n"
    
    # Add decision options if present
    if milestone_presentation.decision_options:
        md += "## Action Required\n\n"
        md += "This milestone requires your review and decision.\n\n"
        
        for option in milestone_presentation.decision_options:
            if 'question' in option:
                # Decision with multiple choices
                md += f"### {option['question']}\n\n"
                if 'context' in option:
                    md += f"{option['context']}\n\n"
                
                for choice in option.get('choices', []):
                    md += f"* **{choice.get('label', '')}**: {choice.get('description', '')}\n"
            else:
                # Simple option
                md += f"* **{option.get('label', '')}**: {option.get('description', '')}\n"
        md += "\n"
    
    logger.debug("Formatted milestone as Markdown")
    return md

@trace_method
def _format_milestone_as_html(milestone_presentation: MilestonePresentation) -> str:
    """Format the milestone presentation as HTML."""
    html = f"<h1>{milestone_presentation.title}</h1>\n\n"
    
    # Add summary
    html += f"<p>{milestone_presentation.summary}</p>\n\n"
    
    # Add key points
    if milestone_presentation.key_points:
        html += "<h2>Key Points</h2>\n<ul>\n"
        for point in milestone_presentation.key_points:
            html += f"<li>{point}</li>\n"
        html += "</ul>\n\n"
    
    # Add components
    for component in milestone_presentation.components:
        html += f"<h2>{component.get('title', 'Component')}</h2>\n\n"
        
        if component.get('type') == ComponentType.METRICS.value:
            # Format metrics
            metrics = component.get('metrics', [])
            html += "<ul>\n"
            for metric in metrics:
                html += f"<li><strong>{metric.get('name', '')}</strong>: {metric.get('value', '')}"
                if 'description' in metric:
                    html += f" - {metric['description']}"
                html += "</li>\n"
            html += "</ul>\n\n"
        else:
            # Regular content
            content = component.get('content', '')
            if content:
                html += f"<p>{content}</p>\n\n"
    
    # Add decision options if present
    if milestone_presentation.decision_options:
        html += "<h2>Action Required</h2>\n"
        html += "<p>This milestone requires your review and decision.</p>\n\n"
        
        for option in milestone_presentation.decision_options:
            if 'question' in option:
                # Decision with multiple choices
                html += f"<h3>{option['question']}</h3>\n"
                if 'context' in option:
                    html += f"<p>{option['context']}</p>\n"
                
                html += "<ul>\n"
                for choice in option.get('choices', []):
                    html += f"<li><strong>{choice.get('label', '')}</strong>: {choice.get('description', '')}</li>\n"
                html += "</ul>\n"
            else:
                # Simple option
                html += f"<div><strong>{option.get('label', '')}</strong>: {option.get('description', '')}</div>\n"
        html += "\n"
    
    logger.debug("Formatted milestone as HTML")
    return html

@trace_method
def _create_component_diagram_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a component diagram visualization."""
    components = milestone_data.get("components", [])
    if not components:
        return {"error": "No component data available"}
    
    component_data = []
    for comp in components:
        component_data.append({
            "id": comp.get("id", str(uuid.uuid4())[:8]),
            "name": comp.get("name", "Unknown component"),
            "completion": comp.get("completion_percentage", 0),
            "status": comp.get("status", "in_progress"),
            "dependencies": comp.get("dependencies", [])
        })
    
    # For developer level, include additional technical details
    if presentation_level == PresentationLevel.DEVELOPER:
        for comp in component_data:
            comp_details = next((c for c in components if c.get("name") == comp["name"]), {})
            if "technical_details" in comp_details:
                comp["technical_details"] = comp_details["technical_details"]
            if "apis" in comp_details:
                comp["apis"] = comp_details["apis"]
    
    return {
        "type": "component_diagram",
        "data": {
            "components": component_data,
            "overall_completion": milestone_data.get("completion_percentage", 0)
        }
    }

@trace_method
def _create_feature_list_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a feature list visualization."""
    features = milestone_data.get("features", [])
    if not features:
        return {"error": "No feature data available"}
    
    # Format features based on presentation level
    feature_data = []
    for feature in features:
        feature_item = {
            "id": feature.get("id", str(uuid.uuid4())[:8]),
            "name": feature.get("name", "Unknown feature"),
            "status": feature.get("status", "in_progress"),
            "completion": feature.get("completion_percentage", 0),
            "description": feature.get("description", "")
        }
        
        # Add business value for executive and business levels
        if presentation_level in [PresentationLevel.EXECUTIVE, PresentationLevel.BUSINESS]:
            feature_item["business_value"] = feature.get("business_value", "")
        
        # Add technical details for technical and developer levels
        if presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
            feature_item["technical_details"] = feature.get("technical_details", "")
            
            # Add implementation details for developer level
            if presentation_level == PresentationLevel.DEVELOPER:
                feature_item["implementation_notes"] = feature.get("implementation_notes", "")
        
        feature_data.append(feature_item)
    
    # Sort features by completion status and then by name
    feature_data.sort(key=lambda x: (0 if x["status"] == "completed" else 1, x["name"]))
    
    return {
        "type": "feature_list",
        "data": {
            "features": feature_data
        }
    }

@trace_method
def _create_metrics_chart_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a metrics chart visualization."""
    # Collect relevant metrics based on presentation level
    metrics = []
    
    # Basic completion metric
    metrics.append({
        "name": "Completion",
        "value": milestone_data.get("completion_percentage", 0),
        "type": "percentage"
    })
    
    # Task metrics
    tasks = milestone_data.get("tasks", [])
    if tasks:
        task_statuses = {
            "completed": sum(1 for t in tasks if t.get("status") == "completed"),
            "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
            "pending": sum(1 for t in tasks if t.get("status") == "pending"),
            "blocked": sum(1 for t in tasks if t.get("status") == "blocked")
        }
        
        metrics.append({
            "name": "Tasks",
            "value": task_statuses,
            "type": "breakdown"
        })
    
    # Timeline metrics for business level and above
    if presentation_level != PresentationLevel.EXECUTIVE:
        timeline = milestone_data.get("timeline", {})
        if timeline:
            if "estimated_duration" in timeline and "actual_duration" in timeline:
                metrics.append({
                    "name": "Timeline Variance",
                    "value": timeline["actual_duration"] - timeline["estimated_duration"],
                    "type": "variance"
                })
    
    # Technical metrics for technical and developer levels
    if presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
        code_metrics = milestone_data.get("code_metrics", {})
        if code_metrics:
            for metric_name, metric_value in code_metrics.items():
                metrics.append({
                    "name": metric_name,
                    "value": metric_value,
                    "type": "technical"
                })
    
    return {
        "type": "metrics_chart",
        "data": {
            "metrics": metrics
        }
    }

@trace_method
def _create_comparison_table_data(
    milestone_data: Dict[str, Any],
    presentation_level: PresentationLevel
) -> Dict[str, Any]:
    """Create data for a comparison table visualization."""
    # Get requirements fulfillment data
    requirement_coverage = milestone_data.get("requirement_coverage", {})
    if not requirement_coverage:
        return {"error": "No requirement coverage data available"}
    
    # Format requirements for comparison
    rows = []
    for req_id, coverage in requirement_coverage.items():
        row = {
            "id": req_id,
            "requirement": coverage.get("description", "Unknown requirement"),
            "status": coverage.get("status", "not_started"),
            "completion": coverage.get("percentage", 0)
        }
        
        # Add implementation details for technical and developer levels
        if presentation_level in [PresentationLevel.TECHNICAL, PresentationLevel.DEVELOPER]:
            row["implementation"] = coverage.get("implementation", "")
            
            # Add technical notes for developer level
            if presentation_level == PresentationLevel.DEVELOPER:
                row["technical_notes"] = coverage.get("technical_notes", "")
        
        rows.append(row)
    
    return {
        "type": "comparison_table",
        "data": {
            "title": "Requirements Fulfillment",
            "rows": rows
        }
    }

@trace_method
def create_user_friendly_milestone(
    milestone_data: Dict[str, Any],
    user_id: str,
    user_preferences: Optional[Dict[str, Any]] = None,
    project_context: Optional[Dict[str, Any]] = None,
    output_format: str = "json"
) -> Union[Dict[str, Any], str]:
    """
    Create a user-friendly milestone presentation from technical milestone data.
    This is the main entry point for other components to use this module.
    
    Args:
        milestone_data: Technical milestone information from Team Lead agent
        user_id: ID of the user receiving the presentation
        user_preferences: Optional user presentation preferences
        project_context: Optional project context including requirements
        output_format: Desired output format (json, markdown, html)
        
    Returns:
        Union[Dict[str, Any], str]: Formatted milestone presentation
    """
    logger.info(f"Creating user-friendly milestone for user {user_id}")
    
    try:
        # Get default preferences if none provided
        if not user_preferences:
            user_preferences = get_default_user_preferences(user_id)
        
        # Format milestone for user
        milestone_presentation = format_milestone_for_user(
            milestone_data=milestone_data,
            user_preferences=user_preferences,
            project_context=project_context
        )
        
        # Format for the desired output format
        formatted_output = format_milestone_for_output(
            milestone_presentation=milestone_presentation,
            output_format=output_format
        )
        
        logger.info(f"Successfully created user-friendly milestone in {output_format} format")
        return formatted_output
        
    except Exception as e:
        logger.error(f"Error creating user-friendly milestone: {str(e)}", exc_info=True)
        # Return error information
        if output_format == "json":
            return {
                "error": str(e),
                "milestone_id": milestone_data.get("id", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return f"Error creating milestone presentation: {str(e)}"

@trace_method
def get_default_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get default presentation preferences for a user.
    In a real implementation, this would retrieve stored user preferences.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dict[str, Any]: Default user preferences
    """
    logger.info(f"Getting default preferences for user {user_id}")
    
    # Default preferences - in a real system, these would be retrieved from a database
    default_preferences = {
        "presentation_level": PresentationLevel.BUSINESS.value,
        "visualization_preference": "medium",
        "technical_detail": "medium",
        "use_analogies": True
    }
    
    return default_preferences

@trace_method
def save_user_preferences(
    user_id: str,
    preferences: Dict[str, Any]
) -> bool:
    """
    Save user preferences for milestone presentations.
    In a real implementation, this would store preferences in a database.
    
    Args:
        user_id: ID of the user
        preferences: User preferences to save
        
    Returns:
        bool: Success status
    """
    logger.info(f"Saving preferences for user {user_id}")
    
    try:
        # In a real implementation, save to database
        # For now, just log the preferences
        logger.info(f"Would save preferences for user {user_id}: {preferences}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving user preferences: {str(e)}", exc_info=True)
        return False

@trace_method
def store_milestone_presentation(
    milestone_presentation: MilestonePresentation,
    storage_id: Optional[str] = None
) -> str:
    """
    Store a milestone presentation for later retrieval.
    In a real implementation, this would persist the presentation to storage.
    
    Args:
        milestone_presentation: The milestone presentation to store
        storage_id: Optional storage identifier
        
    Returns:
        str: Storage ID for the presentation
    """
    logger.info(f"Storing milestone presentation {milestone_presentation.id}")
    
    try:
        # Generate storage ID if not provided
        if not storage_id:
            storage_id = f"milestone_{milestone_presentation.milestone_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # In a real implementation, save to database or file system
        # For now, just log the storage
        logger.info(f"Would store milestone presentation at ID: {storage_id}")
        
        return storage_id
        
    except Exception as e:
        logger.error(f"Error storing milestone presentation: {str(e)}", exc_info=True)
        return f"error_{milestone_presentation.id}"