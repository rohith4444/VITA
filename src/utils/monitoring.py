from datetime import datetime
from functools import wraps
from typing import Dict, List
from src.utils.logger import setup_logger

logger = setup_logger("monitoring")

class MonitoringManager:
    """Manages monitoring metadata across the system."""
    
    def __init__(self):
        self.logger = logger
        
    def generate_run_name(self, agent_name: str, operation: str) -> str:
        """Generate a unique run name with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{agent_name}_{operation}_{timestamp}"
    
    def get_base_metadata(self, agent_name: str) -> Dict[str, str]:
        """Get base metadata for monitoring."""
        return {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_tags(self, agent_name: str) -> List[str]:
        """Get relevant tags based on agent type."""
        base_tags = ["VITA", agent_name]
        
        agent_specific_tags = {
            "Python Coder": ["programming", "software"],
            "Mechatronic Engineer": ["hardware", "engineering"],
            "Supervisor": ["routing", "management"]
        }
        
        return base_tags + agent_specific_tags.get(agent_name, [])

def monitor_agent(f):
    """Decorator to add monitoring metadata to agent operations."""
    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        monitoring = MonitoringManager()
        
        # Add monitoring metadata to the kwargs
        kwargs["config"] = {
            "run_name": monitoring.generate_run_name(self.name, f.__name__),
            "tags": monitoring.get_agent_tags(self.name),
            "metadata": monitoring.get_base_metadata(self.name)
        }
        
        # Add query to metadata if present
        if 'query' in kwargs:
            kwargs["config"]["metadata"]["query"] = kwargs['query']
        elif args and isinstance(args[0], str):
            kwargs["config"]["metadata"]["query"] = args[0]

        try:
            response = await f(self, *args, **kwargs)
            return response
        except TypeError as e:
            if 'config' in str(e):
                # If method doesn't accept config, try without it
                kwargs.pop('config', None)
                response = await f(self, *args, **kwargs)
                return response
            raise
        except Exception as e:
            logger.error(f"Error in monitored operation: {str(e)}")
            raise
            
    return wrapper