from core.logging.logger import setup_logger

logger = setup_logger("task_estimator")

def estimate_task_complexity(task_name: str) -> str:
    """Determine task complexity based on heuristics."""
    logger.info(f"Estimating complexity for task: {task_name}")

    if "authentication" in task_name.lower() or "database" in task_name.lower():
        return "HIGH"
    elif "UI" in task_name.lower() or "frontend" in task_name.lower():
        return "MEDIUM"
    else:
        return "LOW"
