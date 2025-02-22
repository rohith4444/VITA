from functools import wraps
import asyncio
import inspect
from datetime import datetime
from typing import Any, Callable, Optional
from contextvars import ContextVar
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("core.tracing.service")

# Context variable to track call depth across async boundaries
_call_depth = ContextVar('call_depth', default=0)

class TracingService:
    """Service for tracing method calls and execution paths."""
    
    def __init__(self):
        self.enabled = True
        self.include_timestamps = False
        self.include_args = False
        self.max_arg_length = 100
        self.logger = setup_logger("tracing.service")
        
    def configure(self,
                 enabled: bool = True,
                 include_timestamps: bool = False,
                 include_args: bool = False,
                 max_arg_length: int = 100) -> None:
        """Configure tracing service settings."""
        self.enabled = enabled
        self.include_timestamps = include_timestamps
        self.include_args = include_args
        self.max_arg_length = max_arg_length
        
    def _get_call_metadata(self, func: Callable, args: tuple) -> tuple[str, str]:
        """Get method name and class name from function and arguments."""
        method_name = func.__name__
        
        # Get class name if it's a method
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            return class_name, method_name
        return "", method_name
        
    def trace_method(self, func: Callable) -> Callable:
        """Decorator to trace method calls and print call hierarchy."""
        
        # Handle both async and sync functions
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self.enabled:
                    return await func(*args, **kwargs)
                    
                current_depth = _call_depth.get()
                indent = "  " * current_depth
                
                # Get method details
                class_name, method_name = self._get_call_metadata(func, args)
                display_name = f"{class_name}.{method_name}" if class_name else method_name
                
                # Print trace line (using regular ASCII characters)
                print(f"{indent}-> {display_name}")
                
                # Set new depth for nested calls
                token = _call_depth.set(current_depth + 1)
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    _call_depth.reset(token)
                    
            return async_wrapper
            
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self.enabled:
                    return func(*args, **kwargs)
                    
                current_depth = _call_depth.get()
                indent = "  " * current_depth
                
                class_name, method_name = self._get_call_metadata(func, args)
                display_name = f"{class_name}.{method_name}" if class_name else method_name
                
                # Print trace line (using regular ASCII characters)
                print(f"{indent}-> {display_name}")
                
                token = _call_depth.set(current_depth + 1)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    _call_depth.reset(token)
                    
            return sync_wrapper
            
    def trace_class(self, cls: type) -> type:
        """Class decorator to trace all methods in a class."""
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith('_'):  # Skip private/special methods
                setattr(cls, name, self.trace_method(method))
        return cls

# Create singleton instance
tracing_service = TracingService()

# Helper decorators for easier usage
def trace_method(func: Optional[Callable] = None, **kwargs):
    """Decorator for tracing individual methods."""
    if func is None:
        def decorator(f):
            tracing_service.configure(**kwargs)
            return tracing_service.trace_method(f)
        return decorator
    return tracing_service.trace_method(func)

def trace_class(cls: Optional[type] = None, **kwargs):
    """Decorator for tracing all methods in a class."""
    if cls is None:
        def decorator(c):
            tracing_service.configure(**kwargs)
            return tracing_service.trace_class(c)
        return decorator
    return tracing_service.trace_class(cls)