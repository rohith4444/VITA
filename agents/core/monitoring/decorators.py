import time
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, ParamSpec
from datetime import datetime, UTC 
from core.logging.logger import setup_logger
from .service import monitoring_service
from core.tracing.service import trace_method

# Type variables for generic function signatures
P = ParamSpec('P')
R = TypeVar('R')

# Initialize logger
logger = setup_logger("monitoring.decorators")

@trace_method
def monitor_llm(run_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to monitor LLM (Language Model) operations.
    Tracks request/response metrics including tokens, duration, cost, and success status.

    Args:
        run_name (Optional[str]): Custom name for the monitoring run. If not provided,
            uses the function name with timestamp.
        metadata (Optional[Dict[str, Any]]): Additional metadata to include in monitoring.
            Can include custom fields relevant to the LLM operation.

    Returns:
        Callable: Decorated function that includes monitoring capabilities.

    Example:
        @monitor_llm(run_name="generate_text", metadata={"model_version": "1.0"})
        async def generate_response(prompt: str) -> str:
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            timestamp =  datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
            current_run_name = f"llm_{run_name}_{timestamp}"  # Add llm_ prefix
            run_id = None
            duration_ms = 0
            
            try:
                enhanced_metadata = {
                    "function": func.__name__,
                    "start_time": timestamp,
                    "monitoring_type": "llm",  # Explicitly mark as LLM monitoring
                    **(metadata or {})
                }
                
                run_id = await monitoring_service.start_run(current_run_name, enhanced_metadata)
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract token counts and model info
                input_tokens = getattr(result, 'usage', {}).get('prompt_tokens', 0)
                output_tokens = getattr(result, 'usage', {}).get('completion_tokens', 0)
                model = getattr(result, 'model', 'gpt-4')
                
                await monitoring_service.log_llm_metrics(
                    run_id=run_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "function": func.__name__,
                        "result_type": type(result).__name__,
                        "execution_time": duration_ms
                    }
                )

                # Mark run as completed
                await monitoring_service.end_run(
                    run_id,
                    metadata={
                        "status": "completed",
                        "success": True,
                        "duration_ms": duration_ms,
                        "end_time": datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if run_id:
                    try:
                        await monitoring_service.log_llm_metrics(
                            run_id=run_id,
                            model="unknown",
                            input_tokens=0,
                            output_tokens=0,
                            duration_ms=duration_ms,
                            success=False,
                            metadata={
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "function": func.__name__,
                                "execution_time": duration_ms
                            }
                        )

                        # Mark run as failed
                        await monitoring_service.end_run(
                            run_id,
                            metadata={
                                "status": "error",
                                "error": str(e),
                                "duration_ms": duration_ms,
                                "end_time": datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                            }
                        )

                    except Exception as log_error:
                        logger.error(f"Error logging LLM metrics: {str(log_error)}", exc_info=True)
                
                logger.error(f"Error in monitored LLM operation: {str(e)}", exc_info=True)
                raise
                    
        return wrapper
    return decorator


@trace_method
def monitor_operation(
    operation_type: str, 
    metadata: Optional[Dict[str, Any]] = None, 
    **kwargs  # Catch any additional keyword arguments
):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs_inner: P.kwargs) -> R:
            # Remove any tracing-specific arguments
            kwargs_inner.pop('include_in_parent', None)
            
            start_time = time.time()
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            run_name = f"{operation_type}_{func.__name__}_{timestamp}"
            run_id = None
            duration_ms = 0
            
            try:
                enhanced_metadata = {
                    "operation_type": operation_type,
                    "function": func.__name__,
                    "start_time": timestamp,
                    **(metadata or {})
                }
                
                run_id = await monitoring_service.start_run(run_name, enhanced_metadata)
                result = await func(*args, **kwargs_inner)
                duration_ms = (time.time() - start_time) * 1000
                
                await monitoring_service.log_operation_metrics(
                    run_id=run_id,
                    operation_type=operation_type,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "function": func.__name__,
                        "result_type": type(result).__name__,
                        "execution_time": duration_ms,
                        **(metadata or {})
                    }
                )

                # Mark run as completed
                await monitoring_service.end_run(
                    run_id,
                    metadata={
                        "status": "completed",
                        "success": True,
                        "duration_ms": duration_ms,
                        "end_time": datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if run_id:
                    try:
                        await monitoring_service.log_operation_metrics(
                            run_id=run_id,
                            operation_type=operation_type,
                            duration_ms=duration_ms,
                            success=False,
                            metadata={
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "function": func.__name__,
                                "execution_time": duration_ms,
                                **(metadata or {})
                            }
                        )

                        # Mark run as completed
                        await monitoring_service.end_run(
                            run_id,
                            metadata={
                                "status": "completed",
                                "success": True,
                                "duration_ms": duration_ms,
                                "end_time": datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                            }
                        )
                
                    except Exception as log_error:
                        logger.error(f"Error logging operation metrics: {str(log_error)}", exc_info=True)
                
                logger.error(f"Error in monitored operation: {str(e)}", exc_info=True)
                raise
                
        return wrapper
    return decorator