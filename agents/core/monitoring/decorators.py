import time
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, ParamSpec
from datetime import datetime
from core.logging.logger import setup_logger
from .service import monitoring_service

# Type variables for generic function signatures
P = ParamSpec('P')
R = TypeVar('R')

# Initialize logger
logger = setup_logger("monitoring.decorators")

def monitor_llm(run_name: Optional[str] = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to monitor LLM operations.
    Tracks tokens, duration, and cost.
    
    Args:
        run_name: Optional name for the monitoring run
        
    Returns:
        Decorated function with monitoring
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            run_id = None
            duration_ms = 0
            
            try:
                # Start monitoring run
                current_run_name = run_name or f"{func.__name__}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                run_id = await monitoring_service.start_run(
                    run_name=current_run_name,
                    metadata={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                )
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract token counts from result if available
                input_tokens = getattr(result, 'usage', {}).get('prompt_tokens', 0)
                output_tokens = getattr(result, 'usage', {}).get('completion_tokens', 0)
                model = getattr(result, 'model', 'unknown')
                
                # Log metrics
                await monitoring_service.log_llm_metrics(
                    run_id=run_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "function": func.__name__,
                        "result_type": type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if run_id:
                    await monitoring_service.log_llm_metrics(
                        run_id=run_id,
                        model="unknown",
                        input_tokens=0,
                        output_tokens=0,
                        duration_ms=duration_ms,
                        success=False,
                        metadata={
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                
                logger.error(f"Error in monitored LLM operation: {str(e)}", exc_info=True)
                raise
                
            finally:
                if run_id:
                    await monitoring_service.end_run(
                        run_id,
                        metadata={"duration_ms": duration_ms}
                    )
                    
        return wrapper
    return decorator

def monitor_operation(
    operation_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to monitor general operations.
    Tracks duration and success.
    
    Args:
        operation_type: Type of operation being monitored
        metadata: Optional additional metadata
        
    Returns:
        Decorated function with monitoring
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            run_id = None
            duration_ms = 0
            
            try:
                # Start monitoring run
                run_id = await monitoring_service.start_run(
                    run_name=f"{operation_type}_{func.__name__}",
                    metadata={
                        "operation_type": operation_type,
                        "function": func.__name__,
                        **(metadata if metadata else {})
                    }
                )
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Calculate and log metrics
                duration_ms = (time.time() - start_time) * 1000
                await monitoring_service.log_operation_metrics(
                    run_id=run_id,
                    operation_type=operation_type,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "function": func.__name__,
                        "result_type": type(result).__name__,
                        **(metadata if metadata else {})
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if run_id:
                    await monitoring_service.log_operation_metrics(
                        run_id=run_id,
                        operation_type=operation_type,
                        duration_ms=duration_ms,
                        success=False,
                        metadata={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            **(metadata if metadata else {})
                        }
                    )
                
                logger.error(f"Error in monitored operation: {str(e)}", exc_info=True)
                raise
                
            finally:
                if run_id:
                    await monitoring_service.end_run(
                        run_id,
                        metadata={"duration_ms": duration_ms}
                    )
                    
        return wrapper
    return decorator