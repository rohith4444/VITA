from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer
from core.logging.logger import setup_logger
from backend.config import config
from .metrics import MetricsManager, LLMMetrics, OperationMetrics, MetricType

class MonitoringService:
    """
    Central monitoring service that handles metric collection and LangSmith integration.
    Provides unified interface for tracking LLM operations and agent activities.
    """
    
    def __init__(self):
        self.logger = setup_logger("monitoring.service")
        self.logger.info("Initializing MonitoringService")
        
        try:
            self.metrics_manager = MetricsManager()
            
            # Initialize LangSmith if monitoring is enabled
            self.client = None
            self.langsmith_client = None
            self.tracer = None

            if config.MONITORING_ENABLED:
                # Initialize LangSmith Client
                self.client = Client(
                    api_key=config.LANGSMITH_API_KEY,
                    api_url=config.LANGCHAIN_ENDPOINT
                )
                
                # Set langsmith_client explicitly
                self.langsmith_client = self.client
                
                # Initialize tracer
                self.tracer = LangChainTracer(
                    project_name=config.LANGCHAIN_PROJECT,
                    client=self.client
                )
                
                self.logger.info(f"LangSmith initialized for project: {config.LANGCHAIN_PROJECT}")
            else:
                self.logger.info("Monitoring is disabled")
            
            # Initialize metric storage
            self._current_run: Optional[Dict[str, Any]] = None
            self._metrics_history: List[Dict[str, Any]] = []
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MonitoringService: {str(e)}", exc_info=True)
            raise

    async def start_run(self, run_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new monitoring run.
        
        Args:
            run_name: Name for the monitoring run
            metadata: Optional metadata about the run
            
        Returns:
            str: Run ID for the started run
        """
        try:
            timestamp = datetime.utcnow()
            run_id = f"{run_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            self._current_run = {
                "run_id": run_id,
                "start_time": timestamp,
                "name": run_name,
                "metadata": metadata or {},
                "metrics": []
            }
            
            # Fallback to manual run creation if client method fails
            langsmith_run_id = None
            
            if self.langsmith_client is not None:
                try:
                    # Attempt to create run with more explicit parameters
                    run = self.langsmith_client.create_run(
                        name=run_name,
                        run_type="chain",
                        inputs={},  # You can pass initial inputs if needed
                        extra_metadata=metadata or {},
                        start_time=timestamp
                    )
                    
                    # Safely get run ID
                    langsmith_run_id = getattr(run, 'id', str(uuid.uuid4()))
                except Exception as e:
                    # Log the error but don't stop the entire process
                    self.logger.warning(f"Failed to create LangSmith run: {str(e)}")
                    # Generate a fallback UUID
                    langsmith_run_id = str(uuid.uuid4())
            
            # Only add langsmith_run_id if it exists
            if langsmith_run_id:
                self._current_run['langsmith_run_id'] = langsmith_run_id
            
            self.logger.info(f"Started monitoring run: {run_id}")
            return run_id
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring run: {str(e)}", exc_info=True)
            raise

    async def end_run(self, run_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        End a monitoring run and save its data.
        
        Args:
            run_id: ID of the run to end
            metadata: Optional metadata about run completion
        """
        try:
            if not self._current_run or self._current_run["run_id"] != run_id:
                self.logger.error(f"No active run found with ID: {run_id}")
                return
            
            end_time = datetime.utcnow()
            duration = (end_time - self._current_run["start_time"]).total_seconds() * 1000
            
            run_data = {
                **self._current_run,
                "end_time": end_time,
                "duration_ms": duration,
                "completion_metadata": metadata or {}
            }
            
            self._metrics_history.append(run_data)
            
            if self.langsmith_client and 'langsmith_run_id' in self._current_run:
                try:
                    # Use a more defensive update approach
                    self.langsmith_client.update_run(
                        run_id=self._current_run['langsmith_run_id'],
                        status="success",  # or "error" if there were issues
                        outputs={},  # You can pass final outputs if needed
                        extra_metadata=metadata or {}
                    )
                except Exception as update_error:
                    # Log the error but don't stop the entire process
                    self.logger.warning(
                        f"Failed to update LangSmith run {self._current_run['langsmith_run_id']}: "
                        f"{str(update_error)}")
                    
            self._current_run = None
            self.logger.info(f"Ended monitoring run: {run_id}")
            
        except Exception as e:
            self.logger.error(f"Error ending monitoring run: {str(e)}", exc_info=True)
            raise

    async def log_llm_metrics(
        self,
        run_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log metrics for an LLM operation.
        """
        try:
            # Calculate cost
            cost = self.metrics_manager.calculate_cost(model, input_tokens, output_tokens)
            
            # Create metrics
            metrics = self.metrics_manager.create_llm_metrics(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                success=success,
                cost=cost,
                metadata=metadata
            )
            
            # Safely handle current run
            if self._current_run is not None:
                # Add to current run if run_id matches
                if self._current_run.get("run_id") == run_id:
                    self._current_run.setdefault("metrics", []).append({
                        "type": MetricType.LLM_REQUEST.value,
                        "timestamp": datetime.utcnow(),
                        "data": metrics.dict()
                    })
                
                # Log to LangSmith if enabled
                if (self.langsmith_client and 
                    isinstance(self._current_run, dict) and 
                    'langsmith_run_id' in self._current_run):
                    try:
                        self.langsmith_client.update_run(
                            run_id=self._current_run['langsmith_run_id'],
                            extra_metadata={
                                "llm_metrics": {
                                    "model": model,
                                    "tokens": {
                                        "input": input_tokens,
                                        "output": output_tokens,
                                        "total": input_tokens + output_tokens
                                    },
                                    "cost": cost,
                                    "duration_ms": duration_ms,
                                    "success": success,
                                    "additional_metadata": metadata or {}
                                }
                            }
                        )
                    except Exception as update_error:
                        self.logger.warning(
                            f"Failed to update LangSmith run with LLM metrics: "
                            f"{str(update_error)}"
                        )
            else:
                # If no current run, create a new run or log a warning
                self.logger.warning(
                    f"No active run found for logging LLM metrics. "
                    f"Run ID: {run_id}, Model: {model}"
                )
            
            self.logger.debug(
                f"Logged LLM metrics for run {run_id}: "
                f"{input_tokens + output_tokens} tokens, ${cost:.4f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging LLM metrics: {str(e)}", exc_info=True)
            # Optionally, you can add a fallback mechanism or re-raise
            # raise

    async def log_operation_metrics(
        self,
        run_id: str,
        operation_type: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enhanced operation metrics logging."""
        try:
            # Safely handle metadata
            metadata = metadata or {}

            # Enhance metadata with operation context
            enhanced_metadata = {
                "operation_context": {
                    "type": operation_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration_ms": duration_ms,
                    "success": success
                },
                "memory_stats": {
                    # Replace with default values or remove if not needed
                    "working_memory_size": metadata.get("working_memory_size", 0),
                    "long_term_memory_size": metadata.get("long_term_memory_size", 0)
                },
                "tool_usage": {
                    "tools_invoked": metadata.get("tools_used", []),
                    "tool_configs": metadata.get("tool_configurations", {})
                },
                "operation_details": metadata
            }

            # Safely handle current run
            if self._current_run is not None:
                # Check if run_id matches current run
                if self._current_run.get("run_id") == run_id:
                    # Add metrics to current run
                    self._current_run.setdefault("metrics", []).append({
                        "type": MetricType.OPERATION_REQUEST.value,  # Assuming you have this enum
                        "timestamp": datetime.utcnow(),
                        "data": enhanced_metadata
                    })

                # Log to LangSmith if enabled
                if (self.langsmith_client and 
                    isinstance(self._current_run, dict) and 
                    'langsmith_run_id' in self._current_run):
                    try:
                        self.langsmith_client.update_run(
                            run_id=self._current_run['langsmith_run_id'],
                            extra_metadata={
                                "operation_metrics": enhanced_metadata
                            }
                        )
                    except Exception as update_error:
                        self.logger.warning(
                            f"Failed to update LangSmith run with operation metrics: "
                            f"{str(update_error)}"
                        )
            else:
                # If no current run, log a warning
                self.logger.warning(
                    f"No active run found for logging operation metrics. "
                    f"Run ID: {run_id}, Operation: {operation_type}"
                )
            
            self.logger.debug(
                f"Logged enhanced operation metrics for run {run_id}: "
                f"{operation_type}, {duration_ms}ms"
            )
                
        except Exception as e:
            self.logger.error(
                f"Error logging enhanced operation metrics: {str(e)}", 
                exc_info=True
            )
            # Optionally, you can add a fallback mechanism or re-raise
            # raise
        
    def get_run_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific run.
        
        Args:
            run_id: ID of the run to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Run metrics if found
        """
        try:
            # Check current run first
            if self._current_run and self._current_run["run_id"] == run_id:
                return self._current_run
            
            # Check historical runs
            for run in self._metrics_history:
                if run["run_id"] == run_id:
                    return run
            
            self.logger.warning(f"No metrics found for run: {run_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving run metrics: {str(e)}", exc_info=True)
            return None

# Create singleton instance
monitoring_service = MonitoringService()