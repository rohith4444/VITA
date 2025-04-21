from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import math
import json
import re
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.scrum_master.progress_visualizer")

class VisualizationType(Enum):
    """Enum representing different types of visualizations."""
    PROGRESS_BAR = "progress_bar"         # Simple progress bar
    BURNDOWN_CHART = "burndown_chart"     # Burndown chart for sprints/projects
    GANTT_CHART = "gantt_chart"           # Gantt chart for timeline
    STATUS_CHART = "status_chart"         # Status distribution
    MILESTONE_CHART = "milestone_chart"   # Milestone completion
    DEPENDENCY_GRAPH = "dependency_graph" # Task dependency graph
    TEAM_WORKLOAD = "team_workload"       # Team workload distribution
    TREND_CHART = "trend_chart"           # Trend analysis chart

class OutputFormat(Enum):
    """Enum representing output formats for visualizations."""
    TEXT = "text"       # Plain text/ASCII visualization
    SVG = "svg"         # SVG visualization
    MARKDOWN = "markdown" # Markdown-formatted visualization
    JSON = "json"       # JSON data for client-side rendering

class ColorScheme(Enum):
    """Enum representing color schemes for visualizations."""
    DEFAULT = "default"     # Blues/greens for general use
    STATUS = "status"       # Red/yellow/green for status indicators
    TEAM = "team"           # Varied colors for team differentiation
    PRIORITY = "priority"   # Colors based on priority levels
    ACCESSIBILITY = "accessibility" # High contrast, color-blind friendly

@trace_method
def generate_progress_bar(
    percentage: float,
    width: int = 20,
    format: str = "text",
    color_scheme: str = "default"
) -> str:
    """
    Generate a progress bar visualization.
    
    Args:
        percentage: Percentage completion (0-100)
        width: Width of the progress bar (character count for text, pixels for SVG)
        format: Output format (text, svg)
        color_scheme: Color scheme to use
        
    Returns:
        str: Progress bar visualization in the specified format
    """
    logger.debug(f"Generating {format} progress bar for {percentage:.1f}%")
    
    # Validate percentage
    percentage = max(0, min(100, percentage))
    
    # Handle text format
    if format.lower() == "text":
        filled_length = int(width * percentage / 100)
        bar = '█' * filled_length + '░' * (width - filled_length)
        return f"[{bar}] {percentage:.1f}%"
        
    # Handle SVG format
    elif format.lower() == "svg":
        # Set colors based on scheme
        if color_scheme.lower() == "status":
            if percentage < 30:
                fill_color = "#ff6b6b"  # Red for low progress
            elif percentage < 70:
                fill_color = "#feca57"  # Yellow for medium progress
            else:
                fill_color = "#1dd1a1"  # Green for high progress
        else:  # Default scheme
            fill_color = "#48dbfb"  # Blue for default
            
        # Create SVG with rounded corners and percentage text
        svg = f"""<svg width="{width + 40}" height="30" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="5" width="{width}" height="20" rx="5" ry="5" fill="#f1f2f6" />
  <rect x="0" y="5" width="{width * percentage / 100}" height="20" rx="5" ry="5" fill="{fill_color}" />
  <text x="{width + 10}" y="20" font-family="Arial" font-size="12" fill="#333">{percentage:.1f}%</text>
</svg>"""
        return svg
        
    # Handle markdown format
    elif format.lower() == "markdown":
        filled_length = int(width * percentage / 100)
        bar = '▓' * filled_length + '░' * (width - filled_length)
        return f"`{bar}` **{percentage:.1f}%**"
        
    # Default to text if format not recognized
    filled_length = int(width * percentage / 100)
    bar = '#' * filled_length + '-' * (width - filled_length)
    return f"[{bar}] {percentage:.1f}%"

@trace_method
def create_burndown_chart(
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a burndown chart visualization.
    
    Args:
        data: Dictionary containing burndown data with:
            - planned: List of planned values by day
            - actual: List of actual values by day
            - dates: List of date labels
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure with SVG and metadata
    """
    logger.info("Creating burndown chart")
    
    # Default options
    opts = {
        "width": 500,
        "height": 300,
        "padding": 40,
        "title": "Burndown Chart",
        "format": "svg",
        "color_scheme": "default"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Extract data
    planned = data.get("planned", [])
    actual = data.get("actual", [])
    dates = data.get("dates", [])
    
    # Validate data
    if not planned or not actual:
        logger.warning("Missing burndown data")
        return {"error": "Missing required burndown data"}
    
    # Fill dates if not provided
    if not dates:
        dates = [f"Day {i+1}" for i in range(len(planned))]
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_burndown(planned, actual, dates, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_burndown(planned, actual, dates, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "burndown_chart",
            "data": {
                "planned": planned,
                "actual": actual,
                "dates": dates
            },
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_burndown(planned, actual, dates, opts)

def _create_text_burndown(
    planned: List[float],
    actual: List[float],
    dates: List[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based burndown chart."""
    height = 10  # Height in lines
    width = min(len(planned), 30)  # Width in characters
    
    # Find max value for scaling
    max_value = max(max(planned), max(actual) if actual else 0)
    
    # Create empty chart
    chart = []
    for _ in range(height):
        chart.append([' ' for _ in range(width)])
    
    # Plot planned line
    for i in range(min(len(planned), width)):
        y = height - 1 - int((planned[i] / max_value) * (height - 1))
        y = max(0, min(height - 1, y))  # Ensure y is within bounds
        chart[y][i] = '*'
    
    # Plot actual line
    for i in range(min(len(actual), width)):
        y = height - 1 - int((actual[i] / max_value) * (height - 1))
        y = max(0, min(height - 1, y))  # Ensure y is within bounds
        chart[y][i] = '+'
    
    # Convert to string
    chart_str = options["title"] + "\n"
    for row in chart:
        chart_str += '|' + ''.join(row) + '|\n'
    
    # Add legend
    chart_str += f"Legend: * Planned, + Actual\n"
    chart_str += f"Maximum value: {max_value}\n"
    
    return {
        "type": "burndown_chart",
        "format": "text",
        "visualization": chart_str
    }

def _create_svg_burndown(
    planned: List[float],
    actual: List[float],
    dates: List[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG burndown chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    
    # Calculate chart dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    
    # Find max value for scaling
    max_value = max(max(planned), max(actual) if actual else 0) * 1.1  # Add 10% margin
    
    # Calculate scales
    x_scale = chart_width / (len(planned) - 1) if len(planned) > 1 else chart_width
    y_scale = chart_height / max_value if max_value > 0 else chart_height
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .axis-label {{ font-size: 12px; }}
        .legend {{ font-size: 12px; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
    
    <!-- Y-axis -->
    <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#333" stroke-width="1"/>
    
    <!-- X-axis -->
    <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#333" stroke-width="1"/>
"""
    
    # Add y-axis labels
    for i in range(5):
        value = max_value * (4 - i) / 4
        y_pos = padding + i * chart_height / 4
        svg += f'    <text x="{padding-5}" y="{y_pos+4}" text-anchor="end" class="axis-label">{value:.1f}</text>\n'
        svg += f'    <line x1="{padding-2}" y1="{y_pos}" x2="{padding}" y2="{y_pos}" stroke="#333" stroke-width="1"/>\n'
    
    # Add x-axis labels (first, middle, last)
    if len(dates) > 0:
        svg += f'    <text x="{padding}" y="{height-padding+15}" text-anchor="middle" class="axis-label">{dates[0]}</text>\n'
        
    if len(dates) > 2:
        middle_idx = len(dates) // 2
        middle_x = padding + middle_idx * x_scale
        svg += f'    <text x="{middle_x}" y="{height-padding+15}" text-anchor="middle" class="axis-label">{dates[middle_idx]}</text>\n'
        
    if len(dates) > 1:
        svg += f'    <text x="{width-padding}" y="{height-padding+15}" text-anchor="middle" class="axis-label">{dates[-1]}</text>\n'
    
    # Plot planned line
    if len(planned) > 0:
        planned_points = []
        for i, value in enumerate(planned):
            x = padding + i * x_scale
            y = height - padding - value * y_scale
            planned_points.append(f"{x},{y}")
        
        planned_path = " ".join(planned_points)
        svg += f'    <polyline points="{planned_path}" fill="none" stroke="#3498db" stroke-width="2"/>\n'
    
    # Plot actual line
    if len(actual) > 0:
        actual_points = []
        for i, value in enumerate(actual):
            x = padding + i * x_scale
            y = height - padding - value * y_scale
            actual_points.append(f"{x},{y}")
        
        actual_path = " ".join(actual_points)
        svg += f'    <polyline points="{actual_path}" fill="none" stroke="#e74c3c" stroke-width="2"/>\n'
    
    # Add legend
    svg += f'    <rect x="{width-padding-100}" y="{padding}" width="10" height="10" fill="none" stroke="#3498db" stroke-width="2"/>\n'
    svg += f'    <text x="{width-padding-85}" y="{padding+9}" class="legend">Planned</text>\n'
    svg += f'    <rect x="{width-padding-100}" y="{padding+20}" width="10" height="10" fill="none" stroke="#e74c3c" stroke-width="2"/>\n'
    svg += f'    <text x="{width-padding-85}" y="{padding+29}" class="legend">Actual</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "burndown_chart",
        "format": "svg",
        "visualization": svg
    }

@trace_method
def create_gantt_chart(
    tasks: List[Dict[str, Any]],
    timeline: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a Gantt chart visualization.
    
    Args:
        tasks: List of tasks with:
            - id: Task identifier
            - name: Task name
            - start: Start date or day number
            - end: End date or day number
            - progress: Completion percentage
            - dependencies: List of dependent task IDs
        timeline: Timeline information with:
            - start_date: Project start date
            - end_date: Project end date
            - current_date: Current date marker
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure with SVG and metadata
    """
    logger.info("Creating Gantt chart")
    
    # Default options
    opts = {
        "width": 800,
        "height": 30 * len(tasks) + 60,  # Scale height by task count
        "padding": 150,
        "title": "Project Timeline",
        "format": "svg",
        "color_scheme": "default",
        "show_dependencies": True
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate tasks
    if not tasks:
        logger.warning("No tasks provided for Gantt chart")
        return {"error": "No tasks provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_gantt(tasks, timeline, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_gantt(tasks, timeline, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "gantt_chart",
            "data": {
                "tasks": tasks,
                "timeline": timeline
            },
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_gantt(tasks, timeline, opts)

def _create_text_gantt(
    tasks: List[Dict[str, Any]],
    timeline: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based Gantt chart."""
    # Determine chart width and time span
    width = 50  # Character width for the timeline portion
    start_date = timeline.get("start_date", 0)
    end_date = timeline.get("end_date", max([task.get("end", 0) for task in tasks]))
    current_date = timeline.get("current_date", None)
    
    # Calculate time span (convert to integers if dates are provided)
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).timestamp()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).timestamp()
        if isinstance(current_date, str):
            current_date = datetime.fromisoformat(current_date).timestamp()
    except (ValueError, TypeError):
        # If date conversion fails, just use as numbers
        pass
    
    time_span = end_date - start_date if end_date > start_date else 1
    
    # Build the Gantt chart
    chart = []
    chart.append(options["title"])
    chart.append("")
    
    # Add header with time markers
    timeline_header = " " * 30  # Space for task names
    for i in range(width):
        marker_position = start_date + (i / width) * time_span
        if i % 5 == 0:  # Add marker every 5 characters
            marker = str(int(marker_position))[-1]  # Just use last digit for simplicity
            timeline_header += marker
        else:
            timeline_header += " "
    chart.append(timeline_header)
    
    # Add a header divider
    chart.append("-" * 30 + "|" + "-" * width)
    
    # Add tasks
    for task in tasks:
        task_name = task.get("name", "Task")
        task_start = task.get("start", start_date)
        task_end = task.get("end", task_start)
        progress = task.get("progress", 0)
        
        # Calculate task position
        try:
            if isinstance(task_start, str):
                task_start = datetime.fromisoformat(task_start).timestamp()
            if isinstance(task_end, str):
                task_end = datetime.fromisoformat(task_end).timestamp()
        except (ValueError, TypeError):
            # If date conversion fails, just use as numbers
            pass
        
        # Normalize positions to chart width
        start_pos = int(((task_start - start_date) / time_span) * width)
        end_pos = int(((task_end - start_date) / time_span) * width)
        start_pos = max(0, min(width, start_pos))
        end_pos = max(0, min(width, end_pos))
        
        # Calculate progress position
        progress_pos = start_pos + int((end_pos - start_pos) * progress / 100)
        
        # Create bar
        task_line = f"{task_name:<30}|" + " " * start_pos
        
        if start_pos < end_pos:
            # Add progress indicator
            for i in range(start_pos, end_pos + 1):
                if i < progress_pos:
                    task_line += "#"  # Completed portion
                else:
                    task_line += "="  # Incomplete portion
        else:
            # Handle zero-length tasks (milestones)
            task_line += "*"
        
        # Complete the line
        task_line += " " * (width - len(task_line) + 31)  # +31 for name and separator
        chart.append(task_line)
    
    # Add current date marker if provided
    if current_date is not None:
        current_pos = int(((current_date - start_date) / time_span) * width)
        current_pos = max(0, min(width, current_pos))
        
        # Add marker to the chart
        current_line = " " * 30 + "|" + " " * current_pos + "^" + " " * (width - current_pos - 1)
        chart.append("")
        chart.append(current_line)
        chart.append(" " * 30 + "|" + " " * current_pos + "TODAY")
    
    # Add legend
    chart.append("")
    chart.append("Legend: # Completed, = Remaining, * Milestone")
    
    return {
        "type": "gantt_chart",
        "format": "text",
        "visualization": "\n".join(chart)
    }

def _create_svg_gantt(
    tasks: List[Dict[str, Any]],
    timeline: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG Gantt chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    show_dependencies = options.get("show_dependencies", True)
    
    # Extract timeline info
    start_date = timeline.get("start_date", 0)
    end_date = timeline.get("end_date", max([task.get("end", 0) for task in tasks]))
    current_date = timeline.get("current_date", None)
    
    # Calculate time span (convert to integers if dates are provided)
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).timestamp()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).timestamp()
        if isinstance(current_date, str) and current_date:
            current_date = datetime.fromisoformat(current_date).timestamp()
    except (ValueError, TypeError):
        # If date conversion fails, just use as numbers
        pass
    
    time_span = end_date - start_date if end_date > start_date else 1
    
    # Calculate scales
    chart_width = width - padding - 20
    task_height = 20
    row_height = 30
    
    # Generate basic SVG structure
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .task-label {{ font-size: 12px; text-anchor: end; }}
        .milestone {{ fill: #9b59b6; }}
        .bar {{ fill: #3498db; }}
        .progress {{ fill: #2ecc71; }}
        .dependency {{ stroke: #95a5a6; stroke-width: 1; stroke-dasharray: 2,2; }}
        .today-line {{ stroke: #e74c3c; stroke-width: 2; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
"""
    
    # Add time axis
    axis_y = 50
    svg += f'    <line x1="{padding}" y1="{axis_y}" x2="{padding+chart_width}" y2="{axis_y}" stroke="#333" stroke-width="1"/>\n'
    
    # Add time markers
    markers = 5
    for i in range(markers + 1):
        x_pos = padding + (i / markers) * chart_width
        tick_time = start_date + (i / markers) * time_span
        
        # Format date if it's a timestamp
        if tick_time > 1000000000:  # Assume it's a timestamp if large number
            date_str = datetime.fromtimestamp(tick_time).strftime("%m/%d")
        else:
            date_str = f"Day {int(tick_time)}"
            
        svg += f'    <line x1="{x_pos}" y1="{axis_y-3}" x2="{x_pos}" y2="{axis_y+3}" stroke="#333" stroke-width="1"/>\n'
        svg += f'    <text x="{x_pos}" y="{axis_y-8}" text-anchor="middle" font-size="10">{date_str}</text>\n'
    
    # Store dependencies to draw them last (on top)
    dependencies = []
    
    # Add tasks
    for i, task in enumerate(tasks):
        task_name = task.get("name", f"Task {i+1}")
        task_id = task.get("id", f"task_{i+1}")
        task_start = task.get("start", start_date)
        task_end = task.get("end", task_start)
        progress = task.get("progress", 0)
        task_deps = task.get("dependencies", [])
        
        # Calculate task position
        try:
            if isinstance(task_start, str):
                task_start = datetime.fromisoformat(task_start).timestamp()
            if isinstance(task_end, str):
                task_end = datetime.fromisoformat(task_end).timestamp()
        except (ValueError, TypeError):
            # If date conversion fails, just use as numbers
            pass
        
        # Normalize positions to chart width
        start_pos = ((task_start - start_date) / time_span) * chart_width
        end_pos = ((task_end - start_date) / time_span) * chart_width
        duration = max(end_pos - start_pos, 1)  # Ensure minimum width
        
        # Calculate positions
        x = padding + start_pos
        y = 60 + i * row_height
        
        # Check if this is a milestone (zero duration task)
        is_milestone = task_start == task_end or duration <= 1
        
        # Add task label
        svg += f'    <text x="{padding-5}" y="{y+task_height/2+4}" class="task-label">{task_name}</text>\n'
        
        if is_milestone:
            # Draw milestone diamond
            diamond_size = 10
            svg += f'    <polygon points="{x},{y+task_height/2-diamond_size} {x+diamond_size},{y+task_height/2} {x},{y+task_height/2+diamond_size} {x-diamond_size},{y+task_height/2}" class="milestone" />\n'
        else:
            # Draw task bar
            svg += f'    <rect x="{x}" y="{y}" width="{duration}" height="{task_height}" rx="3" class="bar" id="{task_id}" />\n'
            
            # Draw progress bar if there's progress
            if progress > 0:
                progress_width = (progress / 100) * duration
                svg += f'    <rect x="{x}" y="{y}" width="{progress_width}" height="{task_height}" rx="3" class="progress" />\n'
        
        # Store dependencies for later drawing
        if show_dependencies:
            task_y_center = y + task_height / 2
            task_dict = {
                "id": task_id,
                "x": x + (0 if is_milestone else duration),
                "y": task_y_center,
                "dependencies": task_deps
            }
            dependencies.append(task_dict)
    
    # Draw dependencies
    if show_dependencies:
        for task in dependencies:
            for dep_id in task["dependencies"]:
                # Find the predecessor task
                pred = next((t for t in dependencies if t["id"] == dep_id), None)
                if pred:
                    # Draw an arrow from predecessor to this task
                    svg += f'    <line x1="{pred["x"]}" y1="{pred["y"]}" x2="{task["x"]}" y2="{task["y"]}" class="dependency" />\n'
                    
                    # Add arrowhead
                    svg += f'    <polygon points="{task["x"]-5},{task["y"]-3} {task["x"]},{task["y"]} {task["x"]-5},{task["y"]+3}" fill="#95a5a6" />\n'
    
    # Add current date marker if provided
    if current_date is not None:
        current_pos = padding + ((current_date - start_date) / time_span) * chart_width
        svg += f'    <line x1="{current_pos}" y1="50" x2="{current_pos}" y2="{height-20}" class="today-line" />\n'
        svg += f'    <text x="{current_pos+5}" y="45" fill="#e74c3c" font-size="10">Today</text>\n'
    
    # Add legend
    legend_y = height - 20
    svg += f'    <rect x="{padding}" y="{legend_y}" width="15" height="10" class="bar" />\n'
    svg += f'    <text x="{padding+20}" y="{legend_y+8}" font-size="10">Task</text>\n'
    
    svg += f'    <rect x="{padding+70}" y="{legend_y}" width="15" height="10" class="progress" />\n'
    svg += f'    <text x="{padding+90}" y="{legend_y+8}" font-size="10">Progress</text>\n'
    
    svg += f'    <polygon points="{padding+160},{legend_y-5} {padding+170},{legend_y} {padding+160},{legend_y+5} {padding+150},{legend_y}" class="milestone" />\n'
    svg += f'    <text x="{padding+175}" y="{legend_y+8}" font-size="10">Milestone</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "gantt_chart",
        "format": "svg",
        "visualization": svg
    }

@trace_method
def create_status_distribution(
    statuses: Dict[str, int],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a status distribution chart.
    
    Args:
        statuses: Dictionary mapping status names to counts
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure with SVG and metadata
    """
    logger.info("Creating status distribution chart")
    
    # Default options
    opts = {
        "width": 400,
        "height": 300,
        "padding": 40,
        "title": "Status Distribution",
        "format": "svg",
        "color_scheme": "status"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate data
    if not statuses:
        logger.warning("No status data provided")
        return {"error": "No status data provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_status_chart(statuses, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_status_chart(statuses, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_status_chart(statuses, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "status_chart",
            "data": statuses,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_status_chart(statuses, opts)

# Completing the status_distribution functions first

def _create_text_status_chart(
    statuses: Dict[str, int],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based status distribution chart."""
    # Calculate total for percentages
    total = sum(statuses.values())
    if total == 0:
        total = 1  # Avoid division by zero
    
    # Calculate max for bar scaling
    max_status_name_length = max(len(name) for name in statuses.keys())
    max_count = max(statuses.values()) if statuses else 0
    bar_width = options.get("width", 40) - max_status_name_length - 10
    
    # Create chart
    chart_lines = [options.get("title", "Status Distribution")]
    chart_lines.append("")
    chart_lines.append(f"{'Status':<{max_status_name_length+2}}{'Count':>8}  {'%':>5}  {'Bar'}")
    chart_lines.append("-" * (max_status_name_length + 25 + bar_width))
    
    # Sort statuses by count (descending)
    sorted_statuses = sorted(statuses.items(), key=lambda x: x[1], reverse=True)
    
    # Add each status with its bar
    for status, count in sorted_statuses:
        percentage = (count / total) * 100
        bar_length = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = '#' * bar_length
        chart_lines.append(f"{status:<{max_status_name_length+2}}{count:>8}  {percentage:>4.1f}%  {bar}")
    
    # Add total
    chart_lines.append("-" * (max_status_name_length + 25 + bar_width))
    chart_lines.append(f"{'Total':<{max_status_name_length+2}}{total:>8}  {100:>4.1f}%")
    
    return {
        "type": "status_chart",
        "format": "text",
        "visualization": "\n".join(chart_lines)
    }

def _create_svg_status_chart(
    statuses: Dict[str, int],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG status distribution chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    color_scheme = options.get("color_scheme", "default")
    
    # Calculate dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    
    # Calculate total for percentages
    total = sum(statuses.values())
    if total == 0:
        total = 1  # Avoid division by zero
    
    # Determine colors based on scheme
    if color_scheme == "status":
        colors = {
            "completed": "#2ecc71",  # Green
            "in_progress": "#3498db",  # Blue
            "pending": "#f39c12",  # Orange
            "blocked": "#e74c3c",  # Red
            "review": "#9b59b6",  # Purple
            "testing": "#1abc9c"   # Teal
        }
        default_colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c", "#34495e"]
    else:  # Default color scheme
        default_colors = ["#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#e74c3c", "#34495e"]
        colors = {}
    
    # Sort statuses by count (descending)
    sorted_statuses = sorted(statuses.items(), key=lambda x: x[1], reverse=True)
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .label {{ font-size: 12px; }}
        .value {{ font-size: 12px; font-weight: bold; }}
        .bar {{ fill-opacity: 0.8; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
"""
    
    # Add bars
    bar_height = min(30, (chart_height - 50) / len(statuses) - 10)
    text_offset = bar_height / 2 + 4
    
    for i, (status, count) in enumerate(sorted_statuses):
        percentage = (count / total) * 100
        bar_width = (count / total) * chart_width
        
        y_position = padding + 30 + i * (bar_height + 10)
        
        # Determine color
        if status.lower() in colors:
            color = colors[status.lower()]
        else:
            color = default_colors[i % len(default_colors)]
        
        # Add bar
        svg += f'    <rect x="{padding}" y="{y_position}" width="{bar_width}" height="{bar_height}" rx="3" class="bar" fill="{color}" />\n'
        
        # Add label
        svg += f'    <text x="{padding-5}" y="{y_position+text_offset}" text-anchor="end" class="label">{status}</text>\n'
        
        # Add value
        svg += f'    <text x="{padding+bar_width+5}" y="{y_position+text_offset}" class="value">{count} ({percentage:.1f}%)</text>\n'
    
    # Add legend if there are multiple statuses
    if len(statuses) > 1:
        legend_y = height - 20
        legend_items_per_row = 3
        legend_item_width = width / legend_items_per_row
        
        for i, (status, _) in enumerate(sorted_statuses):
            row = i // legend_items_per_row
            col = i % legend_items_per_row
            
            x_pos = padding + col * legend_item_width
            y_pos = legend_y + row * 20
            
            # Determine color
            if status.lower() in colors:
                color = colors[status.lower()]
            else:
                color = default_colors[i % len(default_colors)]
            
            # Add legend item
            svg += f'    <rect x="{x_pos}" y="{y_pos-10}" width="10" height="10" fill="{color}" />\n'
            svg += f'    <text x="{x_pos+15}" y="{y_pos}" font-size="10">{status}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "status_chart",
        "format": "svg",
        "visualization": svg
    }

def _create_markdown_status_chart(
    statuses: Dict[str, int],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted status distribution chart."""
    # Calculate total for percentages
    total = sum(statuses.values())
    if total == 0:
        total = 1  # Avoid division by zero
    
    # Sort statuses by count (descending)
    sorted_statuses = sorted(statuses.items(), key=lambda x: x[1], reverse=True)
    
    # Create markdown table
    markdown = f"## {options.get('title', 'Status Distribution')}\n\n"
    markdown += "| Status | Count | Percentage |\n"
    markdown += "|--------|------:|-----------:|\n"
    
    for status, count in sorted_statuses:
        percentage = (count / total) * 100
        markdown += f"| {status} | {count} | {percentage:.1f}% |\n"
    
    # Add total
    markdown += f"| **Total** | **{total}** | **100.0%** |\n\n"
    
    # Add a simple bar chart using emoji blocks
    max_count = max(statuses.values()) if statuses else 0
    bar_width = 20  # Maximum number of bar characters
    
    markdown += "### Visual Representation\n\n"
    for status, count in sorted_statuses:
        bar_length = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = '█' * bar_length
        markdown += f"{status}: {bar} ({count})\n\n"
    
    return {
        "type": "status_chart",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_milestone_chart(
    milestones: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a milestone completion chart.
    
    Args:
        milestones: List of milestones with:
            - name: Milestone name
            - completion: Percentage completion (0-100)
            - due_date: Due date (string or timestamp)
            - status: Current status
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating milestone chart")
    
    # Default options
    opts = {
        "width": 600,
        "height": 300,
        "padding": 40,
        "title": "Milestone Progress",
        "format": "svg",
        "color_scheme": "default"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate milestones
    if not milestones:
        logger.warning("No milestone data provided")
        return {"error": "No milestone data provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_milestone_chart(milestones, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_milestone_chart(milestones, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_milestone_chart(milestones, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "milestone_chart",
            "data": milestones,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_milestone_chart(milestones, opts)

def _create_text_milestone_chart(
    milestones: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based milestone chart."""
    max_name_length = max(len(m.get("name", "Milestone")) for m in milestones)
    max_name_length = min(max_name_length, 30)  # Limit to 30 chars
    bar_width = options.get("width", 40) - max_name_length - 10
    
    # Create chart
    chart_lines = [options.get("title", "Milestone Progress")]
    chart_lines.append("")
    chart_lines.append(f"{'Milestone':<{max_name_length+2}}{'Status':<10}{'Completion':>10}  {'Bar'}")
    chart_lines.append("-" * (max_name_length + 27 + bar_width))
    
    # Sort milestones by due date if available
    try:
        sorted_milestones = sorted(milestones, key=lambda m: m.get("due_date", "9999-12-31"))
    except:
        # If sorting by date fails, keep original order
        sorted_milestones = milestones
    
    # Add each milestone with its progress bar
    for milestone in sorted_milestones:
        name = milestone.get("name", "Milestone")[:max_name_length]
        status = milestone.get("status", "pending")
        completion = milestone.get("completion", 0)
        
        # Create progress bar
        filled_length = int(bar_width * completion / 100)
        bar = '#' * filled_length + '-' * (bar_width - filled_length)
        
        chart_lines.append(f"{name:<{max_name_length+2}}{status:<10}{completion:>9.1f}%  [{bar}]")
    
    chart_lines.append("")
    chart_lines.append("Legend: # Completed, - Remaining")
    
    return {
        "type": "milestone_chart",
        "format": "text",
        "visualization": "\n".join(chart_lines)
    }

def _create_svg_milestone_chart(
    milestones: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG milestone chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    color_scheme = options.get("color_scheme", "default")
    
    # Calculate dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    
    # Determine colors based on scheme
    if color_scheme == "status":
        status_colors = {
            "completed": "#2ecc71",  # Green
            "in_progress": "#3498db",  # Blue
            "pending": "#f39c12",  # Orange
            "delayed": "#e74c3c",  # Red
            "on_track": "#2ecc71",  # Green
            "at_risk": "#f39c12"    # Orange
        }
        progress_color = "#2ecc71"  # Green
        background_color = "#ecf0f1"  # Light gray
    else:  # Default color scheme
        status_colors = {
            "completed": "#3498db",  # Blue
            "in_progress": "#3498db",  # Blue
            "pending": "#95a5a6",  # Gray
            "delayed": "#e74c3c",  # Red
            "on_track": "#2ecc71",  # Green
            "at_risk": "#f39c12"    # Orange
        }
        progress_color = "#3498db"  # Blue
        background_color = "#ecf0f1"  # Light gray
    
    # Sort milestones by due date if available
    try:
        sorted_milestones = sorted(milestones, key=lambda m: m.get("due_date", "9999-12-31"))
    except:
        # If sorting by date fails, keep original order
        sorted_milestones = milestones
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .milestone-name {{ font-size: 12px; text-anchor: end; }}
        .status {{ font-size: 10px; }}
        .percentage {{ font-size: 10px; font-weight: bold; text-anchor: middle; }}
        .date {{ font-size: 10px; text-anchor: start; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
"""
    
    # Add milestone bars
    bar_height = 20
    max_bars = min(len(sorted_milestones), int((chart_height - 40) / (bar_height + 10)))
    y_offset = padding + 30
    
    for i, milestone in enumerate(sorted_milestones[:max_bars]):
        name = milestone.get("name", f"Milestone {i+1}")
        status = milestone.get("status", "pending").lower()
        completion = milestone.get("completion", 0)
        due_date = milestone.get("due_date", "")
        
        # Format due date if it's a timestamp or ISO date
        if due_date:
            try:
                if isinstance(due_date, (int, float)) and due_date > 1000000000:
                    # Convert timestamp to date string
                    due_date = datetime.fromtimestamp(due_date).strftime("%Y-%m-%d")
                elif isinstance(due_date, str) and '-' in due_date:
                    # Already a date string, use as is
                    pass
                else:
                    # Some other format, use as is
                    pass
            except:
                # If date conversion fails, use as is
                pass
        
        y_position = y_offset + i * (bar_height + 10)
        
        # Determine color based on status
        color = status_colors.get(status, progress_color)
        
        # Add milestone name
        svg += f'    <text x="{padding-5}" y="{y_position+bar_height/2+4}" class="milestone-name">{name}</text>\n'
        
        # Add background bar
        svg += f'    <rect x="{padding}" y="{y_position}" width="{chart_width}" height="{bar_height}" rx="3" fill="{background_color}" />\n'
        
        # Add progress bar
        bar_width = (completion / 100) * chart_width
        svg += f'    <rect x="{padding}" y="{y_position}" width="{bar_width}" height="{bar_height}" rx="3" fill="{color}" />\n'
        
        # Add completion percentage
        svg += f'    <text x="{padding+bar_width/2}" y="{y_position+bar_height/2+4}" class="percentage" fill="white">{completion}%</text>\n'
        
        # Add status and due date
        svg += f'    <text x="{padding+chart_width+5}" y="{y_position+bar_height/2}" class="status">{status.capitalize()}</text>\n'
        if due_date:
            svg += f'    <text x="{padding+chart_width+5}" y="{y_position+bar_height/2+12}" class="date">{due_date}</text>\n'
    
    # Add legend
    legend_y = height - 20
    
    for i, (status_name, color) in enumerate(status_colors.items()):
        if i < 4:  # Limit to 4 statuses in the legend
            x_pos = padding + i * 140
            svg += f'    <rect x="{x_pos}" y="{legend_y-10}" width="10" height="10" fill="{color}" />\n'
            svg += f'    <text x="{x_pos+15}" y="{legend_y}" font-size="10">{status_name.capitalize()}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "milestone_chart",
        "format": "svg",
        "visualization": svg
    }

def _create_markdown_milestone_chart(
    milestones: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted milestone chart."""
    # Create markdown table
    markdown = f"## {options.get('title', 'Milestone Progress')}\n\n"
    markdown += "| Milestone | Status | Completion | Due Date | Progress |\n"
    markdown += "|-----------|--------|------------|----------|----------|\n"
    
    # Sort milestones by due date if available
    try:
        sorted_milestones = sorted(milestones, key=lambda m: m.get("due_date", "9999-12-31"))
    except:
        # If sorting by date fails, keep original order
        sorted_milestones = milestones
    
    for milestone in sorted_milestones:
        name = milestone.get("name", "Milestone")
        status = milestone.get("status", "pending")
        completion = milestone.get("completion", 0)
        due_date = milestone.get("due_date", "")
        
        # Create progress bar
        bar_width = 20  # Maximum number of bar characters
        filled_length = int(bar_width * completion / 100)
        bar = '█' * filled_length + '░' * (bar_width - filled_length)
        
        markdown += f"| {name} | {status} | {completion}% | {due_date} | {bar} |\n"
    
    return {
        "type": "milestone_chart",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_team_workload(
    assignments: Dict[str, List[Dict[str, Any]]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a team workload visualization.
    
    Args:
        assignments: Dictionary mapping team members to their assigned tasks:
            - Key: Team member name or ID
            - Value: List of assigned tasks with properties:
                - name: Task name
                - effort: Effort estimation (LOW, MEDIUM, HIGH or numeric value)
                - status: Current status
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating team workload visualization")
    
    # Default options
    opts = {
        "width": 600,
        "height": 400,
        "padding": 40,
        "title": "Team Workload Distribution",
        "format": "svg",
        "color_scheme": "team"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate assignments
    if not assignments:
        logger.warning("No team assignments provided")
        return {"error": "No team assignments provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_workload_chart(assignments, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_workload_chart(assignments, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_workload_chart(assignments, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "team_workload",
            "data": assignments,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_workload_chart(assignments, opts)

def _normalize_effort(effort: Any) -> float:
    """Normalize effort value to a numerical scale (0-3)."""
    if isinstance(effort, (int, float)):
        return min(3, max(0, effort))  # Clamp between 0 and 3
    
    # Handle string values
    effort_str = str(effort).upper()
    if effort_str == "LOW":
        return 1.0
    elif effort_str == "MEDIUM":
        return 2.0
    elif effort_str == "HIGH":
        return 3.0
    else:
        try:
            # Try to convert to float
            return float(effort)
        except:
            return 1.0  # Default to medium-low if unknown

def _create_text_workload_chart(
    assignments: Dict[str, List[Dict[str, Any]]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based team workload chart."""
    # Calculate total workload per team member
    workloads = {}
    task_counts = {}
    
    for member, tasks in assignments.items():
        total_effort = 0
        for task in tasks:
            effort = _normalize_effort(task.get("effort", "MEDIUM"))
            total_effort += effort
        
        workloads[member] = total_effort
        task_counts[member] = len(tasks)
    
    # Calculate max values for scaling
    max_name_length = max(len(member) for member in assignments.keys())
    max_workload = max(workloads.values()) if workloads else 1
    bar_width = options.get("width", 40) - max_name_length - 20
    
    # Create chart
    chart_lines = [options.get("title", "Team Workload Distribution")]
    chart_lines.append("")
    chart_lines.append(f"{'Team Member':<{max_name_length+2}}{'Tasks':>8}{'Workload':>10}  {'Distribution'}")
    chart_lines.append("-" * (max_name_length + 30 + bar_width))
    
    # Sort by workload (descending)
    sorted_members = sorted(workloads.keys(), key=lambda m: workloads[m], reverse=True)
    
    # Add each team member with their workload bar
    for member in sorted_members:
        workload = workloads[member]
        tasks = task_counts[member]
        
        # Create workload bar
        bar_length = int((workload / max_workload) * bar_width)
        bar = '#' * bar_length
        
        chart_lines.append(f"{member:<{max_name_length+2}}{tasks:>8}{workload:>10.1f}  {bar}")
    
    return {
        "type": "team_workload",
        "format": "text",
        "visualization": "\n".join(chart_lines)
    }

def _create_svg_workload_chart(
    assignments: Dict[str, List[Dict[str, Any]]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG team workload chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    color_scheme = options.get("color_scheme", "team")
    
    # Calculate dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    
    # Calculate total workload and categorize tasks per team member
    workloads = {}
    task_counts = {}
    task_categories = {}
    
    for member, tasks in assignments.items():
        total_effort = 0
        categories = {}
        
        for task in tasks:
            effort = _normalize_effort(task.get("effort", "MEDIUM"))
            total_effort += effort
            
            # Track categories (by status)
            status = task.get("status", "in_progress").lower()
            if status not in categories:
                categories[status] = 0
            categories[status] += effort
        
        workloads[member] = total_effort
        task_counts[member] = len(tasks)
        task_categories[member] = categories
    
    # Calculate max workload for scaling
    max_workload = max(workloads.values()) if workloads else 1
    
    # Generate color map based on scheme
    if color_scheme == "team":
        # Distinct colors for team members
        team_colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#34495e", "#d35400"]
        status_colors = {
            "completed": "#2ecc71",  # Green
            "in_progress": "#3498db",  # Blue
            "pending": "#95a5a6",  # Gray
            "blocked": "#e74c3c",  # Red
            "review": "#9b59b6",  # Purple
            "testing": "#1abc9c"   # Teal
        }
    else:
        # Default blue scheme with varying shades
        team_colors = ["#3498db", "#2980b9", "#1f618d", "#154360", "#0e2f44", "#1a5276", "#2471a3", "#2e86c1"]
        status_colors = {
            "completed": "#2ecc71",
            "in_progress": "#3498db",
            "pending": "#95a5a6",
            "blocked": "#e74c3c",
            "review": "#9b59b6",
            "testing": "#1abc9c"
        }
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .member-name {{ font-size: 12px; text-anchor: end; }}
        .task-count {{ font-size: 10px; }}
        .workload {{ font-size: 10px; font-weight: bold; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
"""
    
    # Sort by workload (descending)
    sorted_members = sorted(workloads.keys(), key=lambda m: workloads[m], reverse=True)
    
    # Determine how many members can fit
    bar_height = 25
    max_bars = min(len(sorted_members), int((chart_height - 40) / (bar_height + 10)))
    y_offset = padding + 30
    
    # Add workload bars
    for i, member in enumerate(sorted_members[:max_bars]):
        workload = workloads[member]
        tasks = task_counts[member]
        categories = task_categories[member]
        
        y_position = y_offset + i * (bar_height + 10)
        
        # Add member name
        svg += f'    <text x="{padding-5}" y="{y_position+bar_height/2+4}" class="member-name">{member}</text>\n'
        
        # Calculate bar width based on workload
        bar_width = (workload / max_workload) * chart_width
        
        # If we have category data, create stacked bar
        if categories and sum(categories.values()) > 0:
            # Sort categories for consistent ordering
            sorted_categories = sorted(categories.items(), key=lambda x: x[0])
            
            # Calculate proportional widths
            x_offset = padding
            for category, cat_effort in sorted_categories:
                cat_width = (cat_effort / workload) * bar_width
                if cat_width > 0:
                    color = status_colors.get(category, team_colors[i % len(team_colors)])
                    svg += f'    <rect x="{x_offset}" y="{y_position}" width="{cat_width}" height="{bar_height}" rx="3" fill="{color}" />\n'
                    x_offset += cat_width
        else:
            # Just use member color if no categories
            color = team_colors[i % len(team_colors)]
            svg += f'    <rect x="{padding}" y="{y_position}" width="{bar_width}" height="{bar_height}" rx="3" fill="{color}" />\n'
        
        # Add task count and workload
        svg += f'    <text x="{padding+bar_width+5}" y="{y_position+bar_height/2-5}" class="task-count">{tasks} tasks</text>\n'
        svg += f'    <text x="{padding+bar_width+5}" y="{y_position+bar_height/2+8}" class="workload">Workload: {workload:.1f}</text>\n'
    
    # Add legend for status colors if we have category data
    if any(task_categories.values()):
        legend_y = height - 20
        legend_items_per_row = 3
        legend_item_width = width / legend_items_per_row
        
        for i, (status, color) in enumerate(status_colors.items()):
            row = i // legend_items_per_row
            col = i % legend_items_per_row
            
            x_pos = padding + col * legend_item_width
            y_pos = legend_y + row * 20
            
            svg += f'    <rect x="{x_pos}" y="{y_pos-10}" width="10" height="10" fill="{color}" />\n'
            svg += f'    <text x="{x_pos+15}" y="{y_pos}" font-size="10">{status.capitalize()}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "team_workload",
        "format": "svg",
        "visualization": svg
    }

def _create_markdown_workload_chart(
    assignments: Dict[str, List[Dict[str, Any]]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted team workload chart."""
    # Calculate total workload per team member
    workloads = {}
    task_counts = {}
    
    for member, tasks in assignments.items():
        total_effort = 0
        for task in tasks:
            effort = _normalize_effort(task.get("effort", "MEDIUM"))
            total_effort += effort
        
        workloads[member] = total_effort
        task_counts[member] = len(tasks)
    
    # Calculate max workload for bar scaling
    max_workload = max(workloads.values()) if workloads else 1
    
    # Create markdown table
    markdown = f"## {options.get('title', 'Team Workload Distribution')}\n\n"
    markdown += "| Team Member | Tasks | Workload | Distribution |\n"
    markdown += "|-------------|------:|---------:|-------------:|\n"
    
    # Sort by workload (descending)
    sorted_members = sorted(workloads.keys(), key=lambda m: workloads[m], reverse=True)
    
    for member in sorted_members:
        workload = workloads[member]
        tasks = task_counts[member]
        
        # Create visualization bar
        bar_width = 20  # Maximum number of bar characters
        bar_length = int((workload / max_workload) * bar_width)
        bar = '█' * bar_length
        
        markdown += f"| {member} | {tasks} | {workload:.1f} | {bar} |\n"
    
    return {
        "type": "team_workload",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_dependency_graph(
    tasks: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a visualization of task dependencies.
    
    Args:
        tasks: List of tasks with:
            - id: Task identifier
            - name: Task name
            - dependencies: List of task IDs this task depends on
            - status: Current status
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating dependency graph")
    
    # Default options
    opts = {
        "width": 700,
        "height": 500,
        "padding": 50,
        "title": "Task Dependencies",
        "format": "svg",
        "color_scheme": "default",
        "layout": "hierarchical"  # hierarchical or radial
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate tasks
    if not tasks:
        logger.warning("No tasks provided for dependency graph")
        return {"error": "No tasks provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_dependency_graph(tasks, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_dependency_graph(tasks, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_dependency_graph(tasks, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "dependency_graph",
            "data": tasks,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_dependency_graph(tasks, opts)

def _create_text_dependency_graph(
    tasks: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based dependency graph."""
    # Build a task dictionary for lookup
    task_dict = {task.get("id", f"task_{i}"): task for i, task in enumerate(tasks)}
    
    # Create an ASCII representation
    graph_lines = [options.get("title", "Task Dependencies")]
    graph_lines.append("")
    
    # Sort tasks by dependencies (tasks with no dependencies first)
    sorted_tasks = sorted(tasks, key=lambda t: len(t.get("dependencies", [])))
    
    # Create the graph
    for task in sorted_tasks:
        task_id = task.get("id", "unknown")
        task_name = task.get("name", task_id)
        task_status = task.get("status", "unknown")
        dependencies = task.get("dependencies", [])
        
        # Add task info
        graph_lines.append(f"{task_id}: {task_name} [{task_status}]")
        
        # Add dependencies
        if dependencies:
            graph_lines.append("  Depends on:")
            for dep_id in dependencies:
                dep_name = task_dict.get(dep_id, {}).get("name", dep_id)
                dep_status = task_dict.get(dep_id, {}).get("status", "unknown")
                graph_lines.append(f"  - {dep_id}: {dep_name} [{dep_status}]")
        else:
            graph_lines.append("  No dependencies")
            
        graph_lines.append("")
    
    return {
        "type": "dependency_graph",
        "format": "text",
        "visualization": "\n".join(graph_lines)
    }

def _create_svg_dependency_graph(
    tasks: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG dependency graph."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    color_scheme = options.get("color_scheme", "default")
    layout = options.get("layout", "hierarchical")
    
    # Build a task dictionary for lookup
    task_dict = {task.get("id", f"task_{i}"): task for i, task in enumerate(tasks)}
    
    # Determine colors based on scheme
    if color_scheme == "status":
        status_colors = {
            "completed": "#2ecc71",  # Green
            "in_progress": "#3498db",  # Blue
            "pending": "#f39c12",  # Orange
            "blocked": "#e74c3c",  # Red
            "review": "#9b59b6",  # Purple
            "testing": "#1abc9c"   # Teal
        }
    else:  # Default color scheme
        status_colors = {
            "completed": "#3498db",  # Blue
            "in_progress": "#3498db",  # Blue
            "pending": "#95a5a6",  # Gray
            "blocked": "#e74c3c",  # Red
            "review": "#9b59b6",  # Purple
            "testing": "#1abc9c"   # Teal
        }
    
    # Start SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .task-label {{ font-size: 12px; }}
        .status {{ font-size: 10px; }}
        .dependency {{ stroke: #95a5a6; stroke-width: 1.5; stroke-dasharray: 3,3; marker-end: url(#arrowhead); }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
    
    <!-- Arrow marker definition -->
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#95a5a6" />
        </marker>
    </defs>
"""
    
    # Calculate node positions based on layout
    if layout == "hierarchical":
        positions = _calculate_hierarchical_positions(tasks, width, height, padding)
    else:  # Radial layout
        positions = _calculate_radial_positions(tasks, width, height, padding)
    
    # First draw dependencies (edges) so they appear behind nodes
    for task in tasks:
        task_id = task.get("id", "unknown")
        if task_id in positions and "dependencies" in task:
            source_pos = positions[task_id]
            
            for dep_id in task.get("dependencies", []):
                if dep_id in positions:
                    target_pos = positions[dep_id]
                    svg += f'    <line x1="{source_pos["x"]}" y1="{source_pos["y"]}" x2="{target_pos["x"]}" y2="{target_pos["y"]}" class="dependency" />\n'
    
    # Draw nodes
    for task in tasks:
        task_id = task.get("id", "unknown")
        if task_id in positions:
            pos = positions[task_id]
            task_name = task.get("name", task_id)
            status = task.get("status", "pending").lower()
            
            # Determine color
            color = status_colors.get(status, "#95a5a6")  # Default gray if status unknown
            
            # Draw node
            svg += f'    <circle cx="{pos["x"]}" cy="{pos["y"]}" r="20" fill="{color}" />\n'
            svg += f'    <text x="{pos["x"]}" y="{pos["y"]-25}" text-anchor="middle" class="task-label">{task_name}</text>\n'
            svg += f'    <text x="{pos["x"]}" y="{pos["y"]}" text-anchor="middle" fill="white">{task_id}</text>\n'
            svg += f'    <text x="{pos["x"]}" y="{pos["y"]+30}" text-anchor="middle" class="status">{status}</text>\n'
    
    # Add legend
    legend_y = height - 20
    for i, (status, color) in enumerate(status_colors.items()):
        if i < 5:  # Limit to 5 statuses in the legend
            x_pos = padding + i * 140
            svg += f'    <circle cx="{x_pos+5}" cy="{legend_y-5}" r="5" fill="{color}" />\n'
            svg += f'    <text x="{x_pos+15}" y="{legend_y}" font-size="10">{status.capitalize()}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "dependency_graph",
        "format": "svg",
        "visualization": svg
    }

def _calculate_hierarchical_positions(
    tasks: List[Dict[str, Any]],
    width: int,
    height: int,
    padding: int
) -> Dict[str, Dict[str, float]]:
    """
    Calculate hierarchical layout positions for tasks.
    Places dependent tasks below their dependencies.
    """
    # Build dependency graph
    graph = {}
    for task in tasks:
        task_id = task.get("id", "unknown")
        dependencies = task.get("dependencies", [])
        graph[task_id] = dependencies
    
    # Assign levels based on dependency depth
    levels = {}
    
    # First assign level 0 to nodes with no dependencies
    for task_id in graph:
        if not graph[task_id]:
            levels[task_id] = 0
    
    # Assign levels to other nodes
    unassigned = [task_id for task_id in graph if task_id not in levels]
    while unassigned:
        progress = False
        for task_id in list(unassigned):
            if all(dep in levels for dep in graph[task_id]):
                # All dependencies have assigned levels
                levels[task_id] = max([levels[dep] for dep in graph[task_id]], default=-1) + 1
                unassigned.remove(task_id)
                progress = True
        
        if not progress and unassigned:
            # Handle circular dependencies
            task_id = unassigned[0]
            levels[task_id] = 0
            unassigned.remove(task_id)
    
    # Group tasks by level
    level_groups = {}
    for task_id, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(task_id)
    
    # Calculate vertical spacing
    max_level = max(levels.values()) if levels else 0
    level_height = (height - 2 * padding) / (max_level + 1) if max_level > 0 else (height - 2 * padding)
    
    # Calculate positions for each task
    positions = {}
    for level, task_ids in level_groups.items():
        # Calculate horizontal spacing
        level_width = (width - 2 * padding) / (len(task_ids) + 1)
        
        for i, task_id in enumerate(task_ids):
            positions[task_id] = {
                "x": padding + (i + 1) * level_width,
                "y": padding + level * level_height
            }
    
    return positions

def _calculate_radial_positions(
    tasks: List[Dict[str, Any]],
    width: int, 
    height: int,
    padding: int
) -> Dict[str, Dict[str, float]]:
    """
    Calculate radial layout positions for tasks.
    Places tasks in a circular arrangement.
    """
    center_x = width / 2
    center_y = height / 2
    radius = min(width, height) / 2 - padding
    
    # Calculate positions
    positions = {}
    for i, task in enumerate(tasks):
        task_id = task.get("id", f"task_{i}")
        angle = (2 * math.pi * i) / len(tasks)
        
        positions[task_id] = {
            "x": center_x + radius * math.cos(angle),
            "y": center_y + radius * math.sin(angle)
        }
    
    return positions

def _create_markdown_dependency_graph(
    tasks: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted dependency graph."""
    # Build a task dictionary for lookup
    task_dict = {task.get("id", f"task_{i}"): task for i, task in enumerate(tasks)}
    
    # Create markdown table
    markdown = f"## {options.get('title', 'Task Dependencies')}\n\n"
    markdown += "| Task ID | Task Name | Status | Dependencies |\n"
    markdown += "|---------|-----------|--------|-------------:|\n"
    
    for task in tasks:
        task_id = task.get("id", "unknown")
        task_name = task.get("name", task_id)
        task_status = task.get("status", "unknown")
        dependencies = task.get("dependencies", [])
        
        # Format dependencies
        if dependencies:
            deps_formatted = ", ".join(dependencies)
        else:
            deps_formatted = "None"
            
        markdown += f"| {task_id} | {task_name} | {task_status} | {deps_formatted} |\n"
    
    # Add dependency visualization with mermaid.js syntax if there are dependencies
    if any(task.get("dependencies") for task in tasks):
        markdown += "\n### Dependency Diagram\n\n"
        markdown += "```mermaid\nflowchart TD\n"
        
        # Add nodes
        for task in tasks:
            task_id = task.get("id", "unknown")
            task_name = task.get("name", task_id)
            status = task.get("status", "pending").lower()
            
            # Determine style based on status
            style = "default"
            if status == "completed":
                style = "fill:#2ecc71"  # Green
            elif status == "in_progress":
                style = "fill:#3498db"  # Blue
            elif status == "blocked":
                style = "fill:#e74c3c"  # Red
            
            markdown += f"    {task_id}[\"{task_name}\"]:::status{status}\n"
        
        # Add dependencies
        for task in tasks:
            task_id = task.get("id", "unknown")
            for dep_id in task.get("dependencies", []):
                markdown += f"    {dep_id} --> {task_id}\n"
        
        # Add styles
        markdown += "    classDef statuscompleted fill:#2ecc71\n"
        markdown += "    classDef statusin_progress fill:#3498db\n"
        markdown += "    classDef statusblocked fill:#e74c3c\n"
        markdown += "    classDef statuspending fill:#f39c12\n"
        markdown += "```\n"
    
    return {
        "type": "dependency_graph",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a trend chart visualization showing changes over time.
    
    Args:
        data_points: List of data points with:
            - date/timestamp: Time reference point
            - value: Numerical value for the point
            - category: Optional category for multi-series charts
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating trend chart")
    
    # Default options
    opts = {
        "width": 600,
        "height": 300,
        "padding": 40,
        "title": "Trend Analysis",
        "format": "svg",
        "color_scheme": "default",
        "show_points": True,
        "x_label": "Time",
        "y_label": "Value"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate data
    if not data_points:
        logger.warning("No data points provided for trend chart")
        return {"error": "No data points provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_trend_chart(data_points, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_trend_chart(data_points, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_trend_chart(data_points, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "trend_chart",
            "data": data_points,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_trend_chart(data_points, opts)

def _parse_date_value(date_value: Any) -> float:
    """Parse a date value to a numeric timestamp for sorting and plotting."""
    if isinstance(date_value, (int, float)):
        return date_value
    
    # Try to parse ISO date format
    try:
        if isinstance(date_value, str):
            return datetime.fromisoformat(date_value.replace('Z', '+00:00')).timestamp()
    except ValueError:
        pass
    
    # Try other date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in date_formats:
        try:
            if isinstance(date_value, str):
                return datetime.strptime(date_value, fmt).timestamp()
        except ValueError:
            continue
    
    # Return the original value if parsing fails
    return float(date_value) if isinstance(date_value, (int, float)) else 0

def _create_text_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based trend chart."""
    # Determine date/timestamp field
    date_field = options.get("date_field", None)
    if not date_field:
        for field in ["date", "timestamp", "time", "x"]:
            if any(field in point for point in data_points):
                date_field = field
                break
        if not date_field:
            date_field = next(iter(data_points[0].keys()))  # Just use the first field
    
    # Determine value field
    value_field = options.get("value_field", None)
    if not value_field:
        for field in ["value", "y", "count", "amount"]:
            if any(field in point for point in data_points):
                value_field = field
                break
        if not value_field:
            value_field = list(data_points[0].keys())[1]  # Use the second field
    
    # Determine category field if multi-series
    category_field = options.get("category_field", None)
    if not category_field:
        for field in ["category", "series", "group", "type"]:
            if any(field in point for point in data_points):
                category_field = field
                break
    
    # Sort data points by date
    sorted_points = sorted(data_points, key=lambda p: _parse_date_value(p.get(date_field, 0)))
    
    # Group by category if applicable
    series_data = {}
    if category_field and any(category_field in point for point in data_points):
        for point in sorted_points:
            category = point.get(category_field, "Unknown")
            if category not in series_data:
                series_data[category] = []
            series_data[category].append(point)
    else:
        series_data["Value"] = sorted_points
    
    # Calculate min and max for scaling
    all_values = [float(point.get(value_field, 0)) for point in data_points if value_field in point]
    min_value = min(all_values) if all_values else 0
    max_value = max(all_values) if all_values else 0
    value_range = max_value - min_value if max_value > min_value else 1
    
    # Chart dimensions
    chart_height = 10  # lines
    chart_width = min(len(sorted_points), options.get("width", 40) - 10)
    
    # Create empty chart
    chart = []
    for _ in range(chart_height):
        chart.append([' ' for _ in range(chart_width)])
    
    # Plot each series
    series_markers = ['*', '+', 'x', 'o', '#', '@', '&']
    for i, (category, points) in enumerate(series_data.items()):
        marker = series_markers[i % len(series_markers)]
        
        # Sample points to fit chart width
        step = max(1, len(points) // chart_width)
        sampled_points = points[::step][:chart_width]
        
        for j, point in enumerate(sampled_points):
            value = float(point.get(value_field, 0))
            # Scale to chart height
            y = chart_height - 1 - int(((value - min_value) / value_range) * (chart_height - 1))
            y = max(0, min(chart_height - 1, y))  # Ensure y is within bounds
            
            if 0 <= j < chart_width:
                chart[y][j] = marker
    
    # Convert to string
    title = options.get("title", "Trend Chart")
    x_label = options.get("x_label", "Time")

@trace_method
def create_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a trend chart visualization showing changes over time.
    
    Args:
        data_points: List of data points with:
            - date/timestamp: Time reference point
            - value: Numerical value for the point
            - category: Optional category for multi-series charts
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating trend chart")
    
    # Default options
    opts = {
        "width": 600,
        "height": 300,
        "padding": 40,
        "title": "Trend Analysis",
        "format": "svg",
        "color_scheme": "default",
        "show_points": True,
        "x_label": "Time",
        "y_label": "Value"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate data
    if not data_points:
        logger.warning("No data points provided for trend chart")
        return {"error": "No data points provided"}
    
    # Handle text format
    if opts["format"].lower() == "text":
        return _create_text_trend_chart(data_points, opts)
        
    # Handle SVG format
    if opts["format"].lower() == "svg":
        return _create_svg_trend_chart(data_points, opts)
        
    # Handle markdown format
    if opts["format"].lower() == "markdown":
        return _create_markdown_trend_chart(data_points, opts)
        
    # Handle JSON format
    if opts["format"].lower() == "json":
        return {
            "type": "trend_chart",
            "data": data_points,
            "options": opts
        }
        
    # Default to text if format not recognized
    return _create_text_trend_chart(data_points, opts)

def _parse_date_value(date_value: Any) -> float:
    """Parse a date value to a numeric timestamp for sorting and plotting."""
    if isinstance(date_value, (int, float)):
        return date_value
    
    # Try to parse ISO date format
    try:
        if isinstance(date_value, str):
            return datetime.fromisoformat(date_value.replace('Z', '+00:00')).timestamp()
    except ValueError:
        pass
    
    # Try other date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in date_formats:
        try:
            if isinstance(date_value, str):
                return datetime.strptime(date_value, fmt).timestamp()
        except ValueError:
            continue
    
    # Return the original value if parsing fails
    return float(date_value) if isinstance(date_value, (int, float)) else 0

def _create_text_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based trend chart."""
    # Determine date/timestamp field
    date_field = options.get("date_field", None)
    if not date_field:
        for field in ["date", "timestamp", "time", "x"]:
            if any(field in point for point in data_points):
                date_field = field
                break
        if not date_field:
            date_field = next(iter(data_points[0].keys()))  # Just use the first field
    
    # Determine value field
    value_field = options.get("value_field", None)
    if not value_field:
        for field in ["value", "y", "count", "amount"]:
            if any(field in point for point in data_points):
                value_field = field
                break
        if not value_field:
            value_field = list(data_points[0].keys())[1]  # Use the second field
    
    # Determine category field if multi-series
    category_field = options.get("category_field", None)
    if not category_field:
        for field in ["category", "series", "group", "type"]:
            if any(field in point for point in data_points):
                category_field = field
                break
    
    # Sort data points by date
    sorted_points = sorted(data_points, key=lambda p: _parse_date_value(p.get(date_field, 0)))
    
    # Group by category if applicable
    series_data = {}
    if category_field and any(category_field in point for point in data_points):
        for point in sorted_points:
            category = point.get(category_field, "Unknown")
            if category not in series_data:
                series_data[category] = []
            series_data[category].append(point)
    else:
        series_data["Value"] = sorted_points
    
    # Calculate min and max for scaling
    all_values = [float(point.get(value_field, 0)) for point in data_points if value_field in point]
    min_value = min(all_values) if all_values else 0
    max_value = max(all_values) if all_values else 0
    value_range = max_value - min_value if max_value > min_value else 1
    
    # Chart dimensions
    chart_height = 10  # lines
    chart_width = min(len(sorted_points), options.get("width", 40) - 10)
    
    # Create empty chart
    chart = []
    for _ in range(chart_height):
        chart.append([' ' for _ in range(chart_width)])
    
    # Plot each series
    series_markers = ['*', '+', 'x', 'o', '#', '@', '&']
    for i, (category, points) in enumerate(series_data.items()):
        marker = series_markers[i % len(series_markers)]
        
        # Sample points to fit chart width
        step = max(1, len(points) // chart_width)
        sampled_points = points[::step][:chart_width]
        
        for j, point in enumerate(sampled_points):
            value = float(point.get(value_field, 0))
            # Scale to chart height
            y = chart_height - 1 - int(((value - min_value) / value_range) * (chart_height - 1))
            y = max(0, min(chart_height - 1, y))  # Ensure y is within bounds
            
            if 0 <= j < chart_width:
                chart[y][j] = marker
    
    # Convert to string
    title = options.get("title", "Trend Chart")
    x_label = options.get("x_label", "Time")
    y_label = options.get("y_label", "Value")
    chart_str = f"{title}\n\n"
    
    # Add y-axis label
    chart_str += f"{y_label}\n"
    
    # Add chart
    for row in chart:
        chart_str += '|' + ''.join(row) + '|\n'
    
    # Add x-axis
    chart_str += '+' + '-' * chart_width + '+\n'
    chart_str += f"{x_label}\n\n"
    
    # Add legend
    chart_str += "Legend:\n"
    for i, category in enumerate(series_data.keys()):
        marker = series_markers[i % len(series_markers)]
        chart_str += f"{marker} - {category}\n"
    
    return {
        "type": "trend_chart",
        "format": "text",
        "visualization": chart_str
    }

def _create_svg_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG trend chart."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    color_scheme = options.get("color_scheme", "default")
    show_points = options.get("show_points", True)
    x_label = options.get("x_label", "Time")
    y_label = options.get("y_label", "Value")
    
    # Calculate dimensions
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    
    # Determine date/timestamp field
    date_field = options.get("date_field", None)
    if not date_field:
        for field in ["date", "timestamp", "time", "x"]:
            if any(field in point for point in data_points):
                date_field = field
                break
        if not date_field:
            date_field = next(iter(data_points[0].keys()))  # Just use the first field
    
    # Determine value field
    value_field = options.get("value_field", None)
    if not value_field:
        for field in ["value", "y", "count", "amount"]:
            if any(field in point for point in data_points):
                value_field = field
                break
        if not value_field:
            value_field = list(data_points[0].keys())[1]  # Use the second field
    
    # Determine category field if multi-series
    category_field = options.get("category_field", None)
    if not category_field:
        for field in ["category", "series", "group", "type"]:
            if any(field in point for point in data_points):
                category_field = field
                break
    
    # Sort data points by date
    sorted_points = sorted(data_points, key=lambda p: _parse_date_value(p.get(date_field, 0)))
    
    # Group by category if applicable
    series_data = {}
    if category_field and any(category_field in point for point in data_points):
        for point in sorted_points:
            category = point.get(category_field, "Unknown")
            if category not in series_data:
                series_data[category] = []
            series_data[category].append(point)
    else:
        series_data["Value"] = sorted_points
    
    # Calculate min and max for scaling
    date_values = [_parse_date_value(point.get(date_field, 0)) for point in data_points]
    min_date = min(date_values) if date_values else 0
    max_date = max(date_values) if date_values else 1
    date_range = max_date - min_date if max_date > min_date else 1
    
    all_values = [float(point.get(value_field, 0)) for point in data_points if value_field in point]
    min_value = min(all_values) if all_values else 0
    max_value = max(all_values) if all_values else 0
    value_range = max_value - min_value if max_value > min_value else 1
    
    # Add a small margin to the value range
    value_margin = value_range * 0.1
    min_value -= value_margin
    max_value += value_margin
    value_range = max_value - min_value
    
    # Determine colors based on scheme
    if color_scheme == "default":
        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#34495e"]
    else:  # Custom schemes could be added here
        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c", "#34495e"]
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .axis-label {{ font-size: 12px; }}
        .legend {{ font-size: 12px; }}
        .data-point {{ stroke-width: 2; }}
        .series-line {{ fill: none; stroke-width: 2; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
    
    <!-- Y-axis -->
    <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#333" stroke-width="1"/>
    
    <!-- X-axis -->
    <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#333" stroke-width="1"/>
    
    <!-- Y-axis label -->
    <text x="{padding-30}" y="{height/2}" text-anchor="middle" transform="rotate(-90, {padding-30}, {height/2})" class="axis-label">{y_label}</text>
    
    <!-- X-axis label -->
    <text x="{width/2}" y="{height-padding+30}" text-anchor="middle" class="axis-label">{x_label}</text>
"""
    
    # Add y-axis ticks and labels
    for i in range(5):
        value = min_value + (value_range * i / 4)
        y_pos = height - padding - (i / 4) * chart_height
        
        # Format the value
        if abs(value) < 0.01 or abs(value) >= 1000:
            # Use scientific notation for very small or large numbers
            formatted_value = f"{value:.2e}"
        else:
            # Use decimal notation for normal numbers
            formatted_value = f"{value:.2f}"
        
        svg += f'    <line x1="{padding-5}" y1="{y_pos}" x2="{padding}" y2="{y_pos}" stroke="#333" stroke-width="1"/>\n'
        svg += f'    <text x="{padding-10}" y="{y_pos+4}" text-anchor="end" class="axis-label">{formatted_value}</text>\n'
    
    # Add x-axis ticks and labels
    for i in range(5):
        date_value = min_date + (date_range * i / 4)
        x_pos = padding + (i / 4) * chart_width
        
        # Format the date
        if date_value > 1000000000:  # Looks like a timestamp
            date_str = datetime.fromtimestamp(date_value).strftime("%m/%d/%y")
        else:
            date_str = f"{date_value:.1f}"
        
        svg += f'    <line x1="{x_pos}" y1="{height-padding}" x2="{x_pos}" y2="{height-padding+5}" stroke="#333" stroke-width="1"/>\n'
        svg += f'    <text x="{x_pos}" y="{height-padding+20}" text-anchor="middle" class="axis-label">{date_str}</text>\n'
    
    # Plot each series
    for i, (category, points) in enumerate(series_data.items()):
        color = colors[i % len(colors)]
        
        # Create the polyline for the series
        line_points = []
        for point in points:
            date_val = _parse_date_value(point.get(date_field, 0))
            value = float(point.get(value_field, 0))
            
            # Scale to chart dimensions
            x = padding + ((date_val - min_date) / date_range) * chart_width
            y = height - padding - ((value - min_value) / value_range) * chart_height
            
            line_points.append(f"{x},{y}")
        
        # Add the line if we have points
        if line_points:
            svg += f'    <polyline points="{" ".join(line_points)}" class="series-line" stroke="{color}" />\n'
        
        # Add points if requested
        if show_points:
            for point in points:
                date_val = _parse_date_value(point.get(date_field, 0))
                value = float(point.get(value_field, 0))
                
                # Scale to chart dimensions
                x = padding + ((date_val - min_date) / date_range) * chart_width
                y = height - padding - ((value - min_value) / value_range) * chart_height
                
                svg += f'    <circle cx="{x}" cy="{y}" r="4" class="data-point" fill="white" stroke="{color}" />\n'
    
    # Add legend
    legend_y = height - 20
    for i, category in enumerate(series_data.keys()):
        color = colors[i % len(colors)]
        x_pos = padding + i * 120
        
        svg += f'    <line x1="{x_pos}" y1="{legend_y}" x2="{x_pos+20}" y2="{legend_y}" stroke="{color}" stroke-width="2" />\n'
        svg += f'    <circle cx="{x_pos+10}" cy="{legend_y}" r="4" fill="white" stroke="{color}" stroke-width="2" />\n'
        svg += f'    <text x="{x_pos+25}" y="{legend_y+4}" class="legend">{category}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "trend_chart",
        "format": "svg",
        "visualization": svg
    }

def _create_markdown_trend_chart(
    data_points: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted trend chart."""
    # Determine date/timestamp and value fields
    date_field = options.get("date_field", None)
    if not date_field:
        for field in ["date", "timestamp", "time", "x"]:
            if any(field in point for point in data_points):
                date_field = field
                break
        if not date_field:
            date_field = next(iter(data_points[0].keys()))
    
    value_field = options.get("value_field", None)
    if not value_field:
        for field in ["value", "y", "count", "amount"]:
            if any(field in point for point in data_points):
                value_field = field
                break
        if not value_field:
            value_field = list(data_points[0].keys())[1]
    
    # Determine category field if multi-series
    category_field = options.get("category_field", None)
    if not category_field:
        for field in ["category", "series", "group", "type"]:
            if any(field in point for point in data_points):
                category_field = field
                break
    
    # Sort data points by date
    sorted_points = sorted(data_points, key=lambda p: _parse_date_value(p.get(date_field, 0)))
    
    # Create markdown table
    markdown = f"## {options.get('title', 'Trend Analysis')}\n\n"
    
    # Add table header
    if category_field and any(category_field in point for point in data_points):
        markdown += f"| {date_field} | {value_field} | {category_field} |\n"
        markdown += "|" + "-" * (len(date_field) + 2) + "|" + "-" * (len(value_field) + 2) + "|" + "-" * (len(category_field) + 2) + "|\n"
    else:
        markdown += f"| {date_field} | {value_field} |\n"
        markdown += "|" + "-" * (len(date_field) + 2) + "|" + "-" * (len(value_field) + 2) + "|\n"
    
    # Add data points
    for point in sorted_points:
        date_val = point.get(date_field, "")
        value = point.get(value_field, "")
        
        # Format date if it's a timestamp
        if isinstance(date_val, (int, float)) and date_val > 1000000000:
            date_val = datetime.fromtimestamp(date_val).strftime("%Y-%m-%d")
        
        if category_field and category_field in point:
            category = point.get(category_field, "")
            markdown += f"| {date_val} | {value} | {category} |\n"
        else:
            markdown += f"| {date_val} | {value} |\n"
    
    # Add a simple ASCII trend visualization
    if len(sorted_points) >= 2:
        markdown += "\n### Trend Visualization\n\n"
        
        # Calculate min and max for scaling
        all_values = [float(point.get(value_field, 0)) for point in sorted_points if value_field in point]
        min_value = min(all_values) if all_values else 0
        max_value = max(all_values) if all_values else 0
        value_range = max_value - min_value if max_value > min_value else 1
        
        # Group by category if applicable
        if category_field and any(category_field in point for point in sorted_points):
            categories = set(point.get(category_field, "") for point in sorted_points if category_field in point)
            
            for category in categories:
                markdown += f"\n**{category}**:\n\n"
                
                # Filter points for this category
                category_points = [p for p in sorted_points if p.get(category_field, "") == category]
                
                # Create a simple bar chart
                for point in category_points:
                    value = float(point.get(value_field, 0))
                    date_val = point.get(date_field, "")
                    
                    # Format date if it's a timestamp
                    if isinstance(date_val, (int, float)) and date_val > 1000000000:
                        date_val = datetime.fromtimestamp(date_val).strftime("%Y-%m-%d")
                    
                    # Create bar
                    bar_width = int((value - min_value) / value_range * 20) if value_range > 0 else 0
                    bar = "█" * bar_width
                    
                    markdown += f"{date_val}: {bar} ({value})\n"
        else:
            # Create a simple bar chart for single series
            for point in sorted_points:
                value = float(point.get(value_field, 0))
                date_val = point.get(date_field, "")
                
                # Format date if it's a timestamp
                if isinstance(date_val, (int, float)) and date_val > 1000000000:
                    date_val = datetime.fromtimestamp(date_val).strftime("%Y-%m-%d")
                
                # Create bar
                bar_width = int((value - min_value) / value_range * 20) if value_range > 0 else 0
                bar = "█" * bar_width
                
                markdown += f"{date_val}: {bar} ({value})\n"
    
    return {
        "type": "trend_chart",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_ascii_chart(
    data: Dict[str, Any],
    width: int = 40,
    height: int = 10,
    chart_type: str = "bar"
) -> str:
    """
    Create a simple ASCII/text-based chart.
    
    Args:
        data: Dictionary containing data to visualize
        width: Width of the chart in characters
        height: Height of the chart in lines
        chart_type: Type of chart ('bar', 'line', 'scatter')
        
    Returns:
        str: ASCII chart as a string
    """
    logger.info(f"Creating ASCII {chart_type} chart")
    
    if not data:
        return "No data to visualize"
    
    # Extract labels and values
    if isinstance(data, dict):
        labels = list(data.keys())
        values = list(data.values())
    elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
        # List of dicts with label/value pairs
        if len(data) == 0:
            return "No data to visualize"
        if "label" in data[0] and "value" in data[0]:
            labels = [item.get("label", f"Item {i}") for i, item in enumerate(data)]
            values = [item.get("value", 0) for item in data]
        else:
            # Just use the first two keys in each dict
            keys = list(data[0].keys())
            if len(keys) < 2:
                return "Insufficient data fields"
            labels = [item.get(keys[0], f"Item {i}") for i, item in enumerate(data)]
            values = [item.get(keys[1], 0) for item in data]
    else:
        return "Unsupported data format"
    
    # Normalize to numeric values
    try:
        values = [float(v) for v in values]
    except (ValueError, TypeError):
        return "Values must be numeric"
    
    # Create the appropriate chart type
    if chart_type.lower() == "bar":
        return _create_ascii_bar_chart(labels, values, width, height)
    elif chart_type.lower() == "line":
        return _create_ascii_line_chart(labels, values, width, height)
    elif chart_type.lower() == "scatter":
        return _create_ascii_scatter_chart(labels, values, width, height)
    else:
        return "Unsupported chart type. Use 'bar', 'line', or 'scatter'."

def _create_ascii_bar_chart(
    labels: List[str],
    values: List[float],
    width: int,
    height: int
) -> str:
    """Create an ASCII bar chart."""
    # Find max value for scaling
    max_value = max(values) if values else 1
    
    # Determine bar width
    bar_width = width // len(values) if values else 1
    
    # Create chart
    chart = []
    chart.append("ASCII Bar Chart")
    chart.append("")
    
    # Create the chart grid
    for i in range(height):
        # Calculate the threshold for this row
        threshold = max_value * (height - i) / height
        
        row = ""
        for value in values:
            # Add a bar character if the value exceeds the threshold
            if value >= threshold:
                row += "█" * bar_width
            else:
                row += " " * bar_width
        
        chart.append("|" + row + "|")
    
    # Add baseline
    chart.append("+" + "-" * (bar_width * len(values)) + "+")
    
    # Add labels
    label_row = ""
    for label in labels:
        # Truncate label if needed
        label_text = str(label)[:bar_width]
        label_text = label_text.center(bar_width)
        label_row += label_text
    
    chart.append(" " + label_row + " ")
    
    return "\n".join(chart)

def _create_ascii_line_chart(
    labels: List[str],
    values: List[float],
    width: int,
    height: int
) -> str:
    """Create an ASCII line chart."""
    # Find min and max values for scaling
    min_value = min(values) if values else 0
    max_value = max(values) if values else 1
    value_range = max_value - min_value if max_value > min_value else 1
    
    # Create empty chart
    chart = []
    for _ in range(height):
        chart.append([" " for _ in range(width)])
    
    # Calculate x positions
    x_positions = []
    for i in range(len(values)):
        x = int((i / (len(values) - 1 if len(values) > 1 else 1)) * (width - 1))
        x_positions.append(x)
    
    # Calculate y positions
    y_positions = []
    for value in values:
        y = height - 1 - int(((value - min_value) / value_range) * (height - 1))
        y = max(0, min(height - 1, y))  # Ensure within bounds
        y_positions.append(y)
    
    # Draw the line segments
    for i in range(len(values) - 1):
        x1, y1 = x_positions[i], y_positions[i]
        x2, y2 = x_positions[i + 1], y_positions[i + 1]
        
        # Draw a line between the points
        # (Bresenham's line algorithm)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while x1 != x2 or y1 != y2:
            if 0 <= x1 < width and 0 <= y1 < height:
                chart[y1][x1] = "*"
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    # Mark the points
    for i in range(len(values)):
        x, y = x_positions[i], y_positions[i]
        if 0 <= x < width and 0 <= y < height:
            chart[y][x] = "O"
    
    # Convert to string
    result = ["ASCII Line Chart", ""]
    for row in chart:
        result.append("|" + "".join(row) + "|")
    
    # Add baseline and labels
    result.append("+" + "-" * width + "+")
    
    # Add label indicators
    indicators = " "
    for x in x_positions:
        for i in range(width):
            if i == x:
                indicators += "^"
            else:
                indicators += " "
    result.append(indicators)
    
    # Add a sampling of labels (first, middle, last)
    if labels:
        if len(labels) > 2:
            label_str = f"{labels[0]}  {labels[len(labels) // 2]}  {labels[-1]}"

def _create_ascii_scatter_chart(
    labels: List[str],
    values: List[float],
    width: int,
    height: int
) -> str:
    """Create an ASCII scatter chart."""
    # Find min and max values for scaling
    min_value = min(values) if values else 0
    max_value = max(values) if values else 1
    value_range = max_value - min_value if max_value > min_value else 1
    
    # Create empty chart
    chart = []
    for _ in range(height):
        chart.append([" " for _ in range(width)])
    
    # Calculate point positions
    for i, value in enumerate(values):
        # Scale the x position across the width
        x = int((i / (len(values) - 1 if len(values) > 1 else 1)) * (width - 1))
        
        # Scale the y position based on value
        y = height - 1 - int(((value - min_value) / value_range) * (height - 1))
        y = max(0, min(height - 1, y))  # Ensure within bounds
        
        # Place the point marker
        if 0 <= x < width and 0 <= y < height:
            chart[y][x] = "•"
    
    # Convert to string
    result = ["ASCII Scatter Chart", ""]
    for row in chart:
        result.append("|" + "".join(row) + "|")
    
    # Add baseline and labels
    result.append("+" + "-" * width + "+")
    
    # Add label indicators (show a subset if too many)
    if len(labels) > 0:
        label_count = min(width, len(labels))
        step = max(1, len(labels) // label_count)
        
        indicator_line = " "
        for i in range(width):
            label_index = int(i * (len(labels) - 1) / (width - 1)) if width > 1 else 0
            if label_index < len(labels) and label_index % step == 0:
                indicator_line += "^"
            else:
                indicator_line += " "
        
        result.append(indicator_line)
        
        # Add a sampling of labels
        label_line = " "
        sampled_labels = [labels[i] for i in range(0, len(labels), step)]
        if len(sampled_labels) > 0:
            label_spacing = width // len(sampled_labels)
            for i, label in enumerate(sampled_labels):
                # Truncate long labels
                short_label = str(label)[:5]
                pos = 1 + i * label_spacing
                
                # Add the label if it fits
                if pos + len(short_label) < width:
                    result.append(" " + " " * pos + short_label)
    
    return "\n".join(result)

@trace_method
def create_markdown_table(
    data: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    title: str = "Data Table"
) -> str:
    """
    Generate a markdown-formatted table.
    
    Args:
        data: List of dictionaries containing data
        headers: Optional list of headers (will use dict keys if not provided)
        title: Optional table title
        
    Returns:
        str: Formatted markdown table
    """
    logger.info("Creating markdown table")
    
    if not data:
        return f"## {title}\n\nNo data available."
    
    # Extract headers from data if not provided
    if not headers:
        headers = list(data[0].keys())
    
    # Create markdown table
    markdown = f"## {title}\n\n"
    
    # Add headers
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "|-" + "-|-".join(["-" * len(header) for header in headers]) + "-|"
    
    markdown += header_row + "\n" + separator_row + "\n"
    
    # Add data rows
    for row in data:
        values = []
        for header in headers:
            value = row.get(header, "")
            # Format the value
            if isinstance(value, (float)):
                values.append(f"{value:.2f}")
            else:
                values.append(str(value))
        
        markdown += "| " + " | ".join(values) + " |\n"
    
    return markdown

@trace_method
def prepare_chart_data(
    raw_data: Dict[str, Any],
    chart_type: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Prepare raw data for visualization according to the chart type.
    
    Args:
        raw_data: Raw data to be processed
        chart_type: Type of chart the data is for
        options: Optional configuration for data preparation
        
    Returns:
        Dict[str, Any]: Processed data ready for visualization
    """
    logger.info(f"Preparing data for {chart_type} chart")
    
    # Default options
    opts = {
        "date_format": "%Y-%m-%d",
        "normalize": False,
        "aggregate": False,
        "filter_outliers": False
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Process based on chart type
    if chart_type.lower() == "burndown":
        return _prepare_burndown_data(raw_data, opts)
    elif chart_type.lower() == "gantt":
        return _prepare_gantt_data(raw_data, opts)
    elif chart_type.lower() == "status":
        return _prepare_status_data(raw_data, opts)
    elif chart_type.lower() == "milestone":
        return _prepare_milestone_data(raw_data, opts)
    elif chart_type.lower() == "dependency":
        return _prepare_dependency_data(raw_data, opts)
    elif chart_type.lower() == "trend":
        return _prepare_trend_data(raw_data, opts)
    else:
        # Return raw data if chart type not recognized
        logger.warning(f"Unknown chart type: {chart_type}, returning raw data")
        return raw_data

def _prepare_burndown_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for burndown chart."""
    # Expected raw_data structure:
    # {
    #   "tasks": [...],  # List of tasks with status and dates
    #   "start_date": "yyyy-mm-dd",
    #   "end_date": "yyyy-mm-dd",
    #   "total_points": int  # Optional, calculated if not provided
    # }
    
    # Initialize prepared data
    prepared_data = {
        "planned": [],
        "actual": [],
        "dates": []
    }
    
    try:
        # Extract tasks and dates
        tasks = raw_data.get("tasks", [])
        start_date_str = raw_data.get("start_date")
        end_date_str = raw_data.get("end_date")
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, options["date_format"]) if start_date_str else datetime.today()
        end_date = datetime.strptime(end_date_str, options["date_format"]) if end_date_str else (start_date + timedelta(days=14))
        
        # Calculate total points if not provided
        total_points = raw_data.get("total_points", 0)
        if not total_points and tasks:
            total_points = sum(task.get("points", 1) for task in tasks)
        
        # Generate daily data points
        days = (end_date - start_date).days + 1
        daily_points = total_points / days if days > 0 else 0
        
        # Calculate ideal burndown (straight line from total to 0)
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            prepared_data["dates"].append(current_date.strftime(options["date_format"]))
            prepared_data["planned"].append(total_points - (daily_points * i))
        
        # Calculate actual burndown based on task completion
        actual_remaining = total_points
        daily_completed = {}
        
        # Group completed tasks by date
        for task in tasks:
            completion_date_str = task.get("completion_date")
            if completion_date_str and task.get("status") == "completed":
                try:
                    completion_date = datetime.strptime(completion_date_str, options["date_format"])
                    day_key = completion_date.strftime(options["date_format"])
                    points = task.get("points", 1)
                    
                    if day_key in daily_completed:
                        daily_completed[day_key] += points
                    else:
                        daily_completed[day_key] = points
                except ValueError:
                    # Skip tasks with invalid dates
                    continue
        
        # Build the actual burndown line
        for date_str in prepared_data["dates"]:
            if date_str in daily_completed:
                actual_remaining -= daily_completed[date_str]
            prepared_data["actual"].append(actual_remaining)
        
        return prepared_data
    
    except Exception as e:
        logger.error(f"Error preparing burndown data: {str(e)}", exc_info=True)
        return prepared_data

def _prepare_gantt_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for Gantt chart."""
    # Expected raw_data structure:
    # {
    #   "tasks": [
    #     {"id": "...", "name": "...", "start_date": "...", "end_date": "...", "dependencies": [...], "status": "..."}
    #   ],
    #   "project_start": "yyyy-mm-dd",
    #   "project_end": "yyyy-mm-dd"
    # }
    
    try:
        # Extract tasks
        tasks = raw_data.get("tasks", [])
        project_start = raw_data.get("project_start")
        project_end = raw_data.get("project_end")
        
        # Process each task to ensure correct format
        processed_tasks = []
        
        for task in tasks:
            # Ensure each task has all required fields
            processed_task = {
                "id": task.get("id", f"task_{len(processed_tasks)}"),
                "name": task.get("name", f"Task {len(processed_tasks) + 1}"),
                "dependencies": task.get("dependencies", []),
                "status": task.get("status", "pending"),
                "progress": task.get("progress", 0),
            }
            
            # Process dates
            start_date = task.get("start_date")
            end_date = task.get("end_date")
            
            # Try to parse dates if strings
            if isinstance(start_date, str):
                try:
                    processed_task["start"] = datetime.strptime(start_date, options["date_format"]).timestamp()
                except ValueError:
                    # Use relative day number
                    processed_task["start"] = float(start_date) if start_date.isdigit() else 0
            else:
                processed_task["start"] = start_date if start_date is not None else 0
                
            if isinstance(end_date, str):
                try:
                    processed_task["end"] = datetime.strptime(end_date, options["date_format"]).timestamp()
                except ValueError:
                    # Use relative day number
                    processed_task["end"] = float(end_date) if end_date.isdigit() else processed_task["start"] + 1
            else:
                processed_task["end"] = end_date if end_date is not None else processed_task["start"] + 1
            
            processed_tasks.append(processed_task)
        
        # Prepare timeline information
        timeline = {
            "start_date": project_start,
            "end_date": project_end,
            "current_date": datetime.now().strftime(options["date_format"])
        }
        
        return {
            "tasks": processed_tasks,
            "timeline": timeline
        }
        
    except Exception as e:
        logger.error(f"Error preparing Gantt data: {str(e)}", exc_info=True)
        return {
            "tasks": [],
            "timeline": {
                "start_date": datetime.now().strftime(options["date_format"]),
                "end_date": (datetime.now() + timedelta(days=30)).strftime(options["date_format"]),
                "current_date": datetime.now().strftime(options["date_format"])
            }
        }

def _prepare_status_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for status distribution chart."""
    # Expected raw_data structure:
    # {
    #   "tasks": [{"status": "..."}, ...],
    #   "status_mapping": {"status_name": "display_name", ...}  # Optional
    # }
    
    try:
        # Extract tasks
        tasks = raw_data.get("tasks", [])
        status_mapping = raw_data.get("status_mapping", {})
        
        # Count tasks by status
        status_counts = {}
        
        for task in tasks:
            status = task.get("status", "unknown").lower()
            
            # Apply mapping if available
            display_status = status_mapping.get(status, status)
            
            if display_status in status_counts:
                status_counts[display_status] += 1
            else:
                status_counts[display_status] = 1
        
        # Filter small counts if requested
        if options.get("filter_small_counts", False):
            min_count = options.get("min_count", 1)
            status_counts = {k: v for k, v in status_counts.items() if v >= min_count}
        
        return status_counts
        
    except Exception as e:
        logger.error(f"Error preparing status data: {str(e)}", exc_info=True)
        return {"unknown": 0}

def _prepare_milestone_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for milestone chart."""
    # Expected raw_data structure:
    # {
    #   "milestones": [
    #     {"name": "...", "due_date": "...", "completion": 75, "status": "..."}
    #   ]
    # }
    
    try:
        # Extract milestones
        milestones = raw_data.get("milestones", [])
        
        # Process each milestone to ensure correct format
        processed_milestones = []
        
        for milestone in milestones:
            # Ensure each milestone has all required fields
            processed_milestone = {
                "name": milestone.get("name", f"Milestone {len(processed_milestones) + 1}"),
                "status": milestone.get("status", "pending"),
                "completion": milestone.get("completion", 0),
            }
            
            # Process due date
            due_date = milestone.get("due_date")
            
            # Try to parse date if string
            if isinstance(due_date, str):
                try:
                    processed_milestone["due_date"] = due_date
                except ValueError:
                    # Use current format
                    processed_milestone["due_date"] = due_date
            else:
                processed_milestone["due_date"] = due_date
            
            processed_milestones.append(processed_milestone)
        
        return processed_milestones
        
    except Exception as e:
        logger.error(f"Error preparing milestone data: {str(e)}", exc_info=True)
        return []

def _prepare_dependency_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for dependency graph."""
    # Expected raw_data structure:
    # {
    #   "tasks": [
    #     {"id": "...", "name": "...", "dependencies": [...], "status": "..."}
    #   ]
    # }
    
    try:
        # Extract tasks
        tasks = raw_data.get("tasks", [])
        
        # Process each task to ensure correct format
        processed_tasks = []
        
        for task in tasks:
            # Ensure each task has all required fields
            processed_task = {
                "id": task.get("id", f"task_{len(processed_tasks)}"),
                "name": task.get("name", f"Task {len(processed_tasks) + 1}"),
                "dependencies": task.get("dependencies", []),
                "status": task.get("status", "pending")
            }
            
            processed_tasks.append(processed_task)
        
        return processed_tasks
        
    except Exception as e:
        logger.error(f"Error preparing dependency data: {str(e)}", exc_info=True)
        return []

def _prepare_trend_data(
    raw_data: Dict[str, Any],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare data for trend chart."""
    # Expected raw_data structure:
    # {
    #   "data_points": [
    #     {"date": "...", "value": 75, "category": "..."}
    #   ],
    #   "date_field": "date",  # Optional
    #   "value_field": "value",  # Optional
    #   "category_field": "category"  # Optional
    # }
    
    try:
        # Extract data points
        data_points = raw_data.get("data_points", [])
        
        # Identify field names
        date_field = raw_data.get("date_field")
        if not date_field:
            for field in ["date", "timestamp", "time", "x"]:
                if any(field in point for point in data_points):
                    date_field = field
                    break
        
        value_field = raw_data.get("value_field")
        if not value_field:
            for field in ["value", "y", "count", "amount"]:
                if any(field in point for point in data_points):
                    value_field = field
                    break
        
        category_field = raw_data.get("category_field")
        if not category_field:
            for field in ["category", "series", "group", "type"]:
                if any(field in point for point in data_points):
                    category_field = field
                    break
        
        # Process dates
        if date_field:
            for point in data_points:
                if date_field in point and isinstance(point[date_field], str):
                    try:
                        # Try to parse date
                        date_val = datetime.strptime(point[date_field], options["date_format"])
                        # Store as timestamp for easier sorting
                        point[date_field] = date_val.timestamp()
                    except ValueError:
                        # Keep as is if parsing fails
                        pass
        
        # Filter outliers if requested
        if options.get("filter_outliers", False) and value_field:
            values = [float(point.get(value_field, 0)) for point in data_points if value_field in point]
            if values:
                mean = sum(values) / len(values)
                std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
                threshold = options.get("outlier_threshold", 2) * std_dev
                
                # Filter out points beyond threshold
                data_points = [p for p in data_points if abs(float(p.get(value_field, 0)) - mean) <= threshold]
        
        # Add metadata to the result
        result = {
            "data_points": data_points,
            "options": {
                "date_field": date_field,
                "value_field": value_field,
                "category_field": category_field
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error preparing trend data: {str(e)}", exc_info=True)
        return {"data_points": []}

@trace_method
def recommend_visualization(
    data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Recommend an appropriate visualization based on data and context.
    
    Args:
        data: Data to visualize
        context: Optional context information about the visualization purpose
        
    Returns:
        str: Recommended visualization type
    """
    logger.info("Recommending visualization")
    
    try:
        # Default context
        ctx = {
            "purpose": "general",
            "user_technical_level": "beginner",
            "time_focus": False,
            "comparison_focus": False,
            "distribution_focus": False,
            "relationship_focus": False,
            "output_format": "visual"
        }
        
        # Update with provided context
        if context:
            ctx.update(context)
        
        # Check for milestone data
        if "milestones" in data and isinstance(data["milestones"], list):
            return "milestone_chart"
            
        # Check for task status distribution
        if "tasks" in data and isinstance(data["tasks"], list) and all("status" in task for task in data["tasks"]):
            if ctx.get("distribution_focus", False):
                return "status_chart"
                
        # Check for time-based data with tasks
        if "tasks" in data and isinstance(data["tasks"], list) and all(("start" in task or "start_date" in task) for task in data["tasks"]):
            if ctx.get("time_focus", False):
                return "gantt_chart"
                
        # Check for dependency information
        if "tasks" in data and isinstance(data["tasks"], list) and any("dependencies" in task for task in data["tasks"]):
            if ctx.get("relationship_focus", False):
                return "dependency_graph"
                
        # Check for sprint burndown data
        if "planned" in data and "actual" in data and isinstance(data["planned"], list) and isinstance(data["actual"], list):
            return "burndown_chart"
            
        # Check for time series data
        if "data_points" in data and isinstance(data["data_points"], list) and len(data["data_points"]) > 1:
            return "trend_chart"
            
        # Check for workload data
        if isinstance(data, dict) and all(isinstance(value, list) for value in data.values()):
            return "team_workload"
            
        # Default to simple progress bar for single values
        if isinstance(data, (int, float)) or (isinstance(data, dict) and len(data) == 1 and isinstance(next(iter(data.values())), (int, float))):
            return "progress_bar"
            
        # Fall back to status chart for categorical data
        if isinstance(data, dict) and all(isinstance(value, (int, float)) for value in data.values()):
            return "status_chart"
            
        # Default recommendation
        return "status_chart"
        
    except Exception as e:
        logger.error(f"Error recommending visualization: {str(e)}", exc_info=True)
        return "status_chart"

@trace_method
def generate_progress_visualization(
    state: Dict[str, Any],
    format_type: str = "svg"
) -> Dict[str, Any]:
    """
    Generate a visualization from agent state information.
    
    Args:
        state: Agent state dictionary
        format_type: Desired output format (svg, text, markdown)
        
    Returns:
        Dict[str, Any]: Visualization result
    """
    logger.info(f"Generating progress visualization in {format_type} format")
    
    try:
        # Extract progress information from state
        progress_data = state.get("progress", {})
        
        # Default visualization to status chart if no specific data found
        visualization_type = "status_chart"
        visualization_data = {}
        context = {"output_format": format_type}
        
        # Check for specific visualization data
        if "tasks" in state:
            # We have task data, determine what to visualize
            tasks = state.get("tasks", [])
            
            # Check if we have an execution plan with timeline
            if "execution_plan" in state:
                # We can create a Gantt chart
                execution_plan = state.get("execution_plan", {})
                timeline = execution_plan.get("timeline", {})
                
                visualization_type = "gantt_chart"
                visualization_data = {
                    "tasks": tasks,
                    "timeline": timeline
                }
                context["time_focus"] = True
                
            # Check if we have milestone progress
            elif "milestone_progress" in progress_data:
                # We can create a milestone chart
                milestones = progress_data.get("milestone_progress", [])
                
                visualization_type = "milestone_chart"
                visualization_data = milestones
                
            # Check if we have task statuses for a status chart
            elif all("status" in task for task in tasks[:10]):
                # Create a status distribution chart
                statuses = {}
                for task in tasks:
                    status = task.get("status", "unknown")
                    statuses[status] = statuses.get(status, 0) + 1
                
                visualization_type = "status_chart"
                visualization_data = statuses
                context["distribution_focus"] = True
                
            # Check if we have dependencies
            elif any("dependencies" in task for task in tasks[:10]):
                # Create a dependency graph
                visualization_type = "dependency_graph"
                visualization_data = {"tasks": tasks}
                context["relationship_focus"] = True
        
        # Check for burndown data
        elif "task_summary" in progress_data:
            total = progress_data.get("task_summary", {}).get("total", 0)
            completed = progress_data.get("task_summary", {}).get("completed", 0)
            
            if total > 0:
                # Create a simple progress bar
                visualization_type = "progress_bar"
                visualization_data = (completed / total) * 100
        
        # Create recommended visualization if data is sparse
        if not visualization_data:
            # Try to extract anything useful for a visualization
            completion_percentage = progress_data.get("completion_percentage", 0)
            
            # Default to a simple progress bar
            visualization_type = "progress_bar"
            visualization_data = completion_percentage
        
        # Generate the visualization
        options = {"format": format_type}
        
        if visualization_type == "progress_bar":
            return generate_progress_bar(visualization_data, format=format_type)
        elif visualization_type == "burndown_chart":
            return create_burndown_chart(visualization_data, options)
        elif visualization_type == "gantt_chart":
            return create_gantt_chart(
                visualization_data.get("tasks", []),
                visualization_data.get("timeline", {}),
                options
            )
        elif visualization_type == "status_chart":
            return create_status_distribution(visualization_data, options)
        elif visualization_type == "milestone_chart":
            return create_milestone_chart(visualization_data, options)
        elif visualization_type == "dependency_graph":
            return create_dependency_graph(visualization_data.get("tasks", []), options)
        elif visualization_type == "team_workload":
            return create_team_workload(visualization_data, options)
        elif visualization_type == "trend_chart":
            return create_trend_chart(visualization_data.get("data_points", []), options)
        else:
            # Create a simple text summary
            completion = progress_data.get("completion_percentage", 0)
            return {
                "type": "text_summary",
                "format": "text",
                "visualization": f"Project progress: {completion:.1f}% complete"
            }
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}", exc_info=True)
        return {
            "type": "error",
            "format": format_type,
            "visualization": f"Error generating visualization: {str(e)}"
        }

@trace_method
def format_for_user(
    visualization: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a visualization for user presentation based on user preferences.
    
    Args:
        visualization: The visualization to format
        user_preferences: Optional user preference information
        
    Returns:
        Dict[str, Any]: Formatted visualization for presentation
    """
    logger.info("Formatting visualization for user presentation")
    
    try:
        # Default preferences
        prefs = {
            "technical_level": "beginner",
            "preferred_format": "visual",
            "color_scheme": "default",
            "detail_level": "medium"
        }
        
        # Update with provided preferences
        if user_preferences:
            prefs.update(user_preferences)
        
        # Get the visualization type and current format
        viz_type = visualization.get("type", "unknown")
        viz_format = visualization.get("format", "text")
        viz_content = visualization.get("visualization", "")
        
        # Determine appropriate format based on preferences
        target_format = prefs.get("preferred_format", "visual")
        
        # Convert to appropriate format if needed
        if target_format == "text" and viz_format != "text":
            # Convert to text representation
            if viz_type == "progress_bar":
                # Create a text progress bar
                percentage = 0
                if isinstance(viz_content, (int, float)):
                    percentage = viz_content
                elif isinstance(viz_content, str) and "%" in viz_content:
                    try:
                        percentage = float(viz_content.split("%")[0])
                    except:
                        percentage = 0
                
                viz_content = generate_progress_bar(percentage, format="text")
                viz_format = "text"
                
            elif viz_type in ["burndown_chart", "gantt_chart", "status_chart", "milestone_chart"]:
                # Convert to text description
                viz_content = f"Text representation of {viz_type.replace('_', ' ')}"
                viz_format = "text"
                
        elif target_format == "markdown" and viz_format != "markdown":
            # Convert to markdown representation
            if viz_type == "progress_bar":
                percentage = 0
                if isinstance(viz_content, (int, float)):
                    percentage = viz_content
                elif isinstance(viz_content, str) and "%" in viz_content:
                    try:
                        percentage = float(viz_content.split("%")[0])
                    except:
                        percentage = 0
                
                viz_content = generate_progress_bar(percentage, format="markdown")
                viz_format = "markdown"
                
        # Adjust detail level based on preferences
        if prefs.get("detail_level") == "minimal" and isinstance(viz_content, dict):
            # Simplify the content for minimal detail
            if "key_points" in viz_content:
                viz_content = {
                    "summary": viz_content.get("summary", ""),
                    "key_points": viz_content.get("key_points", [])
                }
        
        # Adjust technical terminology based on user's technical level
        if prefs.get("technical_level") == "beginner":
            # Simplify technical terms for beginners
            if isinstance(viz_content, str):
                # Replace technical terms with simpler explanations
                simple_terms = {
                    "burndown": "progress over time",
                    "velocity": "work speed",
                    "sprint": "work period",
                    "dependencies": "connections",
                    "blockers": "obstacles"
                }
                
                for term, simple in simple_terms.items():
                    viz_content = viz_content.replace(term, simple)
        
        # Create the formatted visualization
        formatted = {
            "type": viz_type,
            "format": viz_format,
            "visualization": viz_content,
            "formatted_for": prefs.get("technical_level", "beginner"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add explanation if needed for beginners
        if prefs.get("technical_level") == "beginner" and viz_type not in ["progress_bar", "text_summary"]:
            explanations = {
                "burndown_chart": "This chart shows how work is being completed over time. The downward slope shows progress.",
                "gantt_chart": "This timeline shows when each task is scheduled to start and finish.",
                "status_chart": "This chart shows how many tasks are in each status (like 'in progress' or 'completed').",
                "milestone_chart": "This shows the progress toward important project milestones.",
                "dependency_graph": "This shows how tasks depend on each other. Connected tasks must be done in a specific order.",
                "team_workload": "This shows how work is distributed across team members.",
                "trend_chart": "This shows patterns over time, helping to spot trends."
            }
            
            formatted["explanation"] = explanations.get(viz_type, "")
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting visualization: {str(e)}", exc_info=True)
        return {
            "type": "error",
            "format": "text",
            "visualization": f"Error formatting visualization: {str(e)}"
        }

@trace_method
def create_timeline(
    milestones: List[Dict[str, Any]],
    current_date: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a project timeline visualization.
    
    Args:
        milestones: List of milestone data with dates and statuses
        current_date: Optional current date string (for progress marker)
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Visualization data structure
    """
    logger.info("Creating timeline visualization")
    
    # Default options
    opts = {
        "width": 700,
        "height": 200,
        "padding": 40,
        "title": "Project Timeline",
        "format": "svg",
        "color_scheme": "default",
        "date_format": "%Y-%m-%d"
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Validate milestones
    if not milestones:
        logger.warning("No milestone data provided")
        return {"error": "No milestone data provided"}
    
    # Handle SVG format (default)
    if opts["format"].lower() != "text" and opts["format"].lower() != "markdown":
        return _create_svg_timeline(milestones, current_date, opts)
    
    # Handle text format
    elif opts["format"].lower() == "text":
        return _create_text_timeline(milestones, current_date, opts)
    
    # Handle markdown format
    elif opts["format"].lower() == "markdown":
        return _create_markdown_timeline(milestones, current_date, opts)
    
    # Default to SVG if format not recognized
    return _create_svg_timeline(milestones, current_date, opts)

def _create_svg_timeline(
    milestones: List[Dict[str, Any]],
    current_date: Optional[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an SVG timeline visualization."""
    width = options["width"]
    height = options["height"]
    padding = options["padding"]
    title = options["title"]
    date_format = options["date_format"]
    color_scheme = options.get("color_scheme", "default")
    
    # Determine timeline range
    today = datetime.now()
    current_date_obj = None
    
    if current_date:
        try:
            current_date_obj = datetime.strptime(current_date, date_format)
        except ValueError:
            current_date_obj = today
    else:
        current_date_obj = today
    
    # Parse milestone dates
    parsed_milestones = []
    for milestone in milestones:
        milestone_copy = milestone.copy()
        
        # Parse date
        date_str = milestone.get("date")
        if date_str:
            try:
                milestone_copy["date_obj"] = datetime.strptime(date_str, date_format)
            except ValueError:
                # Skip milestones with invalid dates
                continue
        else:
            # Skip milestones without dates
            continue
        
        parsed_milestones.append(milestone_copy)
    
    if not parsed_milestones:
        return {"error": "No valid milestone dates found"}
    
    # Sort milestones by date
    parsed_milestones.sort(key=lambda m: m["date_obj"])
    
    # Calculate date range
    start_date = parsed_milestones[0]["date_obj"]
    end_date = parsed_milestones[-1]["date_obj"]
    
    # Ensure the timeline includes the current date
    if current_date_obj < start_date:
        start_date = current_date_obj
    elif current_date_obj > end_date:
        end_date = current_date_obj
    
    # Add padding to date range (20% on each side)
    date_range_days = (end_date - start_date).days
    if date_range_days <= 0:
        date_range_days = 30  # Default to 30 days if all dates are the same
    
    padding_days = int(date_range_days * 0.2)
    start_date = start_date - timedelta(days=padding_days)
    end_date = end_date + timedelta(days=padding_days)
    
    # Calculate timeline dimensions
    timeline_width = width - 2 * padding
    timeline_y = height / 2
    
    # Determine colors based on scheme
    if color_scheme == "status":
        status_colors = {
            "completed": "#2ecc71",  # Green
            "in_progress": "#3498db",  # Blue
            "upcoming": "#f39c12",  # Orange
            "delayed": "#e74c3c",  # Red
            "on_track": "#2ecc71",  # Green
            "at_risk": "#f39c12"    # Orange
        }
        timeline_color = "#95a5a6"  # Gray
        current_marker_color = "#e74c3c"  # Red
    else:  # Default color scheme
        status_colors = {
            "completed": "#3498db",  # Blue
            "in_progress": "#3498db",  # Blue
            "upcoming": "#95a5a6",  # Gray
            "delayed": "#e74c3c",  # Red
            "on_track": "#2ecc71",  # Green
            "at_risk": "#f39c12"    # Orange
        }
        timeline_color = "#bdc3c7"  # Light gray
        current_marker_color = "#34495e"  # Dark blue
    
    # Generate SVG
    svg = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        text {{ font-family: Arial; }}
        .title {{ font-size: 16px; font-weight: bold; }}
        .milestone-name {{ font-size: 12px; }}
        .milestone-date {{ font-size: 10px; }}
        .current-date {{ font-size: 10px; fill: {current_marker_color}; }}
    </style>
    
    <!-- Title -->
    <text x="{width/2}" y="20" text-anchor="middle" class="title">{title}</text>
    
    <!-- Timeline Line -->
    <line x1="{padding}" y1="{timeline_y}" x2="{width-padding}" y2="{timeline_y}" stroke="{timeline_color}" stroke-width="2"/>
"""
    
    # Calculate date positions
    total_days = (end_date - start_date).days
    
    # Function to calculate x position from date
    def date_to_x(date_obj):
        days_from_start = (date_obj - start_date).days
        return padding + (days_from_start / total_days) * timeline_width if total_days > 0 else padding
    
    # Add milestone markers
    for milestone in parsed_milestones:
        milestone_name = milestone.get("name", "Milestone")
        milestone_date = milestone["date_obj"]
        milestone_status = milestone.get("status", "upcoming").lower()
        
        # Calculate position
        x_pos = date_to_x(milestone_date)
        
        # Determine color based on status
        color = status_colors.get(milestone_status, "#95a5a6")
        
        # Add milestone marker
        svg += f'    <circle cx="{x_pos}" cy="{timeline_y}" r="8" fill="{color}" />\n'
        
        # Add milestone label (alternate above/below to avoid overlap)
        if parsed_milestones.index(milestone) % 2 == 0:
            # Label above timeline
            svg += f'    <text x="{x_pos}" y="{timeline_y-20}" text-anchor="middle" class="milestone-name">{milestone_name}</text>\n'
            svg += f'    <text x="{x_pos}" y="{timeline_y-35}" text-anchor="middle" class="milestone-date">{milestone_date.strftime("%m/%d/%Y")}</text>\n'
        else:
            # Label below timeline
            svg += f'    <text x="{x_pos}" y="{timeline_y+25}" text-anchor="middle" class="milestone-name">{milestone_name}</text>\n'
            svg += f'    <text x="{x_pos}" y="{timeline_y+40}" text-anchor="middle" class="milestone-date">{milestone_date.strftime("%m/%d/%Y")}</text>\n'
    
    # Add current date marker
    current_x = date_to_x(current_date_obj)
    svg += f'    <line x1="{current_x}" y1="{timeline_y-20}" x2="{current_x}" y2="{timeline_y+20}" stroke="{current_marker_color}" stroke-width="2" stroke-dasharray="4,2" />\n'
    svg += f'    <text x="{current_x}" y="{timeline_y+60}" text-anchor="middle" class="current-date">Today: {current_date_obj.strftime("%m/%d/%Y")}</text>\n'
    
    # Add timeline scale
    months_range = set()
    # Calculate month positions
    month_positions = []
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        month_positions.append({
            "date": current_month,
            "x": date_to_x(current_month)
        })
        current_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)  # Next month
    
    # Add month markers
    for month_pos in month_positions:
        month_x = month_pos["x"]
        month_date = month_pos["date"]
        month_label = month_date.strftime("%b %Y")
        
        svg += f'    <line x1="{month_x}" y1="{timeline_y-5}" x2="{month_x}" y2="{timeline_y+5}" stroke="{timeline_color}" stroke-width="1" />\n'
        svg += f'    <text x="{month_x}" y="{timeline_y-10}" text-anchor="middle" font-size="8">{month_label}</text>\n'
    
    # Add legend
    legend_y = height - 20
    legend_items = [
        {"label": "Completed", "color": status_colors["completed"]},
        {"label": "In Progress", "color": status_colors["in_progress"]},
        {"label": "Upcoming", "color": status_colors["upcoming"]},
        {"label": "Delayed", "color": status_colors["delayed"]}
    ]
    
    for i, item in enumerate(legend_items):
        x_pos = padding + i * 120
        svg += f'    <circle cx="{x_pos+5}" cy="{legend_y}" r="5" fill="{item["color"]}" />\n'
        svg += f'    <text x="{x_pos+15}" y="{legend_y+4}" font-size="10">{item["label"]}</text>\n'
    
    svg += '</svg>'
    
    return {
        "type": "timeline",
        "format": "svg",
        "visualization": svg
    }

def _create_text_timeline(
    milestones: List[Dict[str, Any]],
    current_date: Optional[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a text-based timeline visualization."""
    date_format = options["date_format"]
    title = options["title"]
    
    # Parse milestone dates
    parsed_milestones = []
    for milestone in milestones:
        milestone_copy = milestone.copy()
        
        # Parse date
        date_str = milestone.get("date")
        if date_str:
            try:
                milestone_copy["date_obj"] = datetime.strptime(date_str, date_format)
            except ValueError:
                # Skip milestones with invalid dates
                continue
        else:
            # Skip milestones without dates
            continue
        
        parsed_milestones.append(milestone_copy)
    
    if not parsed_milestones:
        return {"error": "No valid milestone dates found"}
    
    # Sort milestones by date
    parsed_milestones.sort(key=lambda m: m["date_obj"])
    
    # Parse current date
    today = datetime.now()
    current_date_obj = None
    
    if current_date:
        try:
            current_date_obj = datetime.strptime(current_date, date_format)
        except ValueError:
            current_date_obj = today
    else:
        current_date_obj = today
    
    # Create timeline text
    timeline = [title, ""]
    
    # Add a timeline header with today marker
    today_str = current_date_obj.strftime("%Y-%m-%d")
    timeline.append(f"Today: {today_str}")
    timeline.append("")
    
    # Add each milestone with its status
    for milestone in parsed_milestones:
        name = milestone.get("name", "Milestone")
        date_obj = milestone["date_obj"]
        date_str = date_obj.strftime("%Y-%m-%d")
        status = milestone.get("status", "upcoming")
        
        # Determine relative position (past, present, future)
        if date_obj < current_date_obj:
            position = "PAST"
        elif date_obj > current_date_obj:
            position = "FUTURE"
        else:
            position = "TODAY"
        
        # Format milestone line based on status
        if status.lower() == "completed":
            milestone_line = f"[X] {date_str} - {name} ({status.upper()})"
        elif status.lower() == "in_progress":
            milestone_line = f"[~] {date_str} - {name} ({status.upper()})"
        elif status.lower() == "delayed":
            milestone_line = f"[!] {date_str} - {name} ({status.upper()})"
        else:
            milestone_line = f"[ ] {date_str} - {name} ({status.upper()})"
        
        timeline.append(milestone_line)
    
    # Add legend
    timeline.append("")
    timeline.append("Legend:")
    timeline.append("[X] Completed")
    timeline.append("[~] In Progress")
    timeline.append("[ ] Upcoming")
    timeline.append("[!] Delayed")
    
    return {
        "type": "timeline",
        "format": "text",
        "visualization": "\n".join(timeline)
    }

def _create_markdown_timeline(
    milestones: List[Dict[str, Any]],
    current_date: Optional[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a markdown-formatted timeline visualization."""
    date_format = options["date_format"]
    title = options["title"]
    
    # Parse milestone dates
    parsed_milestones = []
    for milestone in milestones:
        milestone_copy = milestone.copy()
        
        # Parse date
        date_str = milestone.get("date")
        if date_str:
            try:
                milestone_copy["date_obj"] = datetime.strptime(date_str, date_format)
            except ValueError:
                # Skip milestones with invalid dates
                continue
        else:
            # Skip milestones without dates
            continue
        
        parsed_milestones.append(milestone_copy)
    
    if not parsed_milestones:
        return {"error": "No valid milestone dates found"}
    
    # Sort milestones by date
    parsed_milestones.sort(key=lambda m: m["date_obj"])
    
    # Parse current date
    today = datetime.now()
    current_date_obj = None
    
    if current_date:
        try:
            current_date_obj = datetime.strptime(current_date, date_format)
        except ValueError:
            current_date_obj = today
    else:
        current_date_obj = today
    
    # Create markdown timeline
    markdown = f"## {title}\n\n"
    
    # Add current date marker
    today_str = current_date_obj.strftime("%Y-%m-%d")
    markdown += f"**Today: {today_str}**\n\n"
    
    # Create a table for milestones
    markdown += "| Date | Milestone | Status |\n"
    markdown += "|------|-----------|--------|\n"
    
    # Add each milestone
    for milestone in parsed_milestones:
        name = milestone.get("name", "Milestone")
        date_obj = milestone["date_obj"]
        date_str = date_obj.strftime("%Y-%m-%d")
        status = milestone.get("status", "upcoming")
        
        # Format status based on milestone status
        status_str = status.upper()
        if status.lower() == "completed":
            status_str = "✅ " + status_str
        elif status.lower() == "in_progress":
            status_str = "🔄 " + status_str
        elif status.lower() == "delayed":
            status_str = "⚠️ " + status_str
        elif status.lower() == "upcoming":
            status_str = "⏳ " + status_str
        
        # Add row to table
        markdown += f"| {date_str} | {name} | {status_str} |\n"
    
    # Add a visual timeline representation using Unicode characters
    markdown += "\n### Visual Timeline\n\n"
    
    # Calculate timeline range
    start_date = parsed_milestones[0]["date_obj"]
    end_date = parsed_milestones[-1]["date_obj"]
    
    # Ensure the timeline includes the current date
    if current_date_obj < start_date:
        start_date = current_date_obj
    elif current_date_obj > end_date:
        end_date = current_date_obj
    
    # Create a visual timeline
    timeline_width = 50  # characters
    total_days = (end_date - start_date).days or 1
    
    # Function to calculate position on timeline
    def date_to_pos(date_obj):
        days_from_start = (date_obj - start_date).days
        return int((days_from_start / total_days) * timeline_width)
    
    # Create the timeline
    timeline = ["─" for _ in range(timeline_width)]
    
    # Add current date marker
    current_pos = date_to_pos(current_date_obj)
    timeline[current_pos] = "┼"
    
    # Add milestone markers
    for milestone in parsed_milestones:
        pos = date_to_pos(milestone["date_obj"])
        
        # Use different markers based on status
        status = milestone.get("status", "").lower()
        if status == "completed":
            marker = "◆"
        elif status == "in_progress":
            marker = "◇"
        elif status == "delayed":
            marker = "✕"
        else:
            marker = "○"
        
        # Add marker to timeline
        if 0 <= pos < timeline_width:
            timeline[pos] = marker
    
    # Convert timeline to string
    timeline_str = "".join(timeline)
    markdown += f"`{timeline_str}`\n\n"
    
    # Add start and end dates
    markdown += f"Start: {start_date.strftime('%Y-%m-%d')} ────── Today: {today_str} ────── End: {end_date.strftime('%Y-%m-%d')}\n\n"
    
    # Add legend
    markdown += "**Legend:**\n"
    markdown += "- ◆ Completed milestone\n"
    markdown += "- ◇ In-progress milestone\n"
    markdown += "- ○ Upcoming milestone\n"
    markdown += "- ✕ Delayed milestone\n"
    markdown += "- ┼ Current date\n"
    
    return {
        "type": "timeline",
        "format": "markdown",
        "visualization": markdown
    }

@trace_method
def create_project_dashboard(
    project_state: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive project dashboard with multiple visualizations.
    
    Args:
        project_state: Complete project state information
        options: Optional visualization options
        
    Returns:
        Dict[str, Any]: Dashboard with multiple visualizations
    """
    logger.info("Creating project dashboard")
    
    # Default options
    opts = {
        "format": "svg",
        "components": ["progress", "timeline", "status", "milestones"],
        "title": "Project Dashboard",
        "detailed": True
    }
    
    # Update with provided options
    if options:
        opts.update(options)
    
    # Initialize dashboard
    dashboard = {
        "type": "dashboard",
        "format": opts["format"],
        "title": opts["title"],
        "components": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Create visualizations for each component
        components = opts["components"]
        
        # 1. Overall progress
        if "progress" in components:
            progress_percentage = project_state.get("progress", {}).get("completion_percentage", 0)
            dashboard["components"]["progress"] = generate_progress_bar(
                progress_percentage,
                format=opts["format"]
            )
        
        # 2. Timeline
        if "timeline" in components and "milestones" in project_state:
            # Extract milestone data
            milestones = project_state.get("milestones", [])
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            dashboard["components"]["timeline"] = create_timeline(
                milestones,
                current_date,
                {"format": opts["format"]}
            )
        
        # 3. Status distribution
        if "status" in components and "tasks" in project_state:
            # Extract task statuses
            tasks = project_state.get("tasks", [])
            
            # Count tasks by status
            statuses = {}
            for task in tasks:
                status = task.get("status", "unknown")
                statuses[status] = statuses.get(status, 0) + 1
            
            dashboard["components"]["status"] = create_status_distribution(
                statuses,
                {"format": opts["format"]}
            )
        
        # 4. Milestone progress
        if "milestones" in components and "milestones" in project_state:
            milestones = project_state.get("milestones", [])
            
            dashboard["components"]["milestones"] = create_milestone_chart(
                milestones,
                {"format": opts["format"]}
            )
        
        # 5. Team workload
        if "team" in components and "team_workload" in project_state:
            team_workload = project_state.get("team_workload", {})
            
            dashboard["components"]["team"] = create_team_workload(
                team_workload,
                {"format": opts["format"]}
            )
        
        # 6. Burndown chart
        if "burndown" in components and "burndown_data" in project_state:
            burndown_data = project_state.get("burndown_data", {})
            
            dashboard["components"]["burndown"] = create_burndown_chart(
                burndown_data,
                {"format": opts["format"]}
            )
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error creating project dashboard: {str(e)}", exc_info=True)
        return {
            "type": "error",
            "format": "text",
            "title": "Error Creating Dashboard",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }