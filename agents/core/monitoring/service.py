from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from langsmith import Client, utils as ls_utils
from langchain_core.tracers.langchain import LangChainTracer
from core.logging.logger import setup_logger
from backend.config import config
from .metrics import MetricsManager, MetricType

class MonitoringService:
    """
    Central monitoring service for tracking and recording metrics of AI operations.
    
    This service provides:
    - Metric collection for LLM operations and general tasks
    - Integration with LangSmith for advanced monitoring
    - Run lifecycle management
    - Historical metrics storage
    
    Attributes:
        metrics_manager: Manager for creating and handling metrics
        langsmith_client: Client for LangSmith integration
        _active_runs: Dictionary of currently active monitoring runs
        _metrics_history: List of completed monitoring runs
    """
    
    def __init__(self):
        """Initialize the monitoring service and its components."""
        self.logger = setup_logger("monitoring.service")
        self.logger.info("Initializing MonitoringService")
        
        try:
            self.metrics_manager = MetricsManager()
            
            # Initialize state tracking
            self._active_runs: Dict[str, Dict[str, Any]] = {}
            self._metrics_history: List[Dict[str, Any]] = []
            
            # Initialize LangSmith integration
            self.client = None
            self.langsmith_client = None
            self.tracer = None

            if config.MONITORING_ENABLED:
                self._init_langsmith()
            else:
                self.logger.info("Monitoring is disabled")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize MonitoringService: {str(e)}", exc_info=True)
            raise
            
    def _init_langsmith(self) -> None:
        """Initialize LangSmith integration if enabled."""
        try:
            self.client = Client(
                api_key=config.LANGSMITH_API_KEY,
                api_url=config.LANGCHAIN_ENDPOINT
            )
            self.langsmith_client = self.client
            self.tracer = LangChainTracer(
                project_name=config.LANGCHAIN_PROJECT,
                client=self.client
            )
            self.logger.info(f"LangSmith initialized for project: {config.LANGCHAIN_PROJECT}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LangSmith: {str(e)}", exc_info=True)
            self.client = None
            self.langsmith_client = None
            self.tracer = None

    async def _update_langsmith_run(
        self,
        run_id: str,
        metadata: Dict[str, Any],
        status: str = "success"
    ) -> None:
        """
        Update a LangSmith run with handling for common errors.
        
        Args:
            run_id: LangSmith run identifier
            metadata: Data to update in the run
            status: Current status of the run
        """
        if not self.langsmith_client:
            return

        try:
            self.langsmith_client.update_run(
                run_id=run_id,
                status=status,
                outputs={},
                extra_metadata=metadata
            )
        except ls_utils.LangSmithConflictError:
            # Run was already updated - this is expected behavior
            self.logger.debug(f"LangSmith run {run_id} was already updated")
        except Exception as e:
            self.logger.error(f"Unexpected error updating LangSmith run: {str(e)}", exc_info=True)

    async def start_run(self, run_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new monitoring run.
        
        Args:
            run_name: Name for the monitoring run
            metadata: Optional metadata about the run
            
        Returns:
            str: Run ID for the started run
            
        Raises:
            Exception: If run creation fails
        """
        try:
            timestamp = datetime.utcnow()
            run_id = f"{run_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            run_data = {
                "run_id": run_id,
                "start_time": timestamp,
                "name": run_name,
                "metadata": metadata or {},
                "metrics": [],
                "status": "active"
            }
            
            self._active_runs[run_id] = run_data
            
            if self.langsmith_client:
                try:
                    run = self.langsmith_client.create_run(
                        name=run_name,
                        run_type="chain",
                        inputs={},
                        extra_metadata=metadata or {},
                        start_time=timestamp
                    )
                    run_data['langsmith_run_id'] = getattr(run, 'id', str(uuid.uuid4()))
                except Exception as e:
                    self.logger.error(f"Failed to create LangSmith run: {str(e)}", exc_info=True)
            
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
            if run_id not in self._active_runs:
                self.logger.error(f"No active run found with ID: {run_id}", exc_info=True)
                return
            
            run_data = self._active_runs[run_id]
            end_time = datetime.utcnow()
            duration = (end_time - run_data["start_time"]).total_seconds() * 1000
            
            run_data.update({
                "end_time": end_time,
                "duration_ms": duration,
                "completion_metadata": metadata or {},
                "status": "completed"
            })
            
            # Move to history and cleanup
            self._metrics_history.append(run_data)
            del self._active_runs[run_id]
            
            if 'langsmith_run_id' in run_data:
                await self._update_langsmith_run(
                    run_data['langsmith_run_id'],
                    metadata=metadata or {},
                    status="success"
                )
                    
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
        
        Args:
            run_id: Run identifier
            model: Name of the LLM model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
            metadata: Additional operation metadata
        """
        try:
            cost = self.metrics_manager.calculate_cost(model, input_tokens, output_tokens)
            
            metrics = self.metrics_manager.create_llm_metrics(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                success=success,
                cost=cost,
                metadata=metadata
            )
            
            if run_id in self._active_runs:
                run_data = self._active_runs[run_id]
                
                run_data.setdefault("metrics", []).append({
                    "type": MetricType.LLM_REQUEST.value,
                    "timestamp": datetime.utcnow(),
                    "data": metrics.dict()
                })
                
                if 'langsmith_run_id' in run_data:
                    await self._update_langsmith_run(
                        run_data['langsmith_run_id'],
                        metadata={
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
            else:
                self.logger.error(f"No active run found for logging LLM metrics. Run ID: {run_id}")
            
            self.logger.debug(
                f"Logged LLM metrics for run {run_id}: "
                f"{input_tokens + output_tokens} tokens, ${cost:.4f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging LLM metrics: {str(e)}", exc_info=True)
            raise

    async def log_operation_metrics(
        self,
        run_id: str,
        operation_type: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log metrics for general operations.
        
        Args:
            run_id: Run identifier
            operation_type: Type of operation being monitored
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
            metadata: Additional operation metadata
        """
        try:
            enhanced_metadata = {
                "operation_context": {
                    "type": operation_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration_ms": duration_ms,
                    "success": success
                },
                "memory_stats": {
                    "working_memory_size": metadata.get("working_memory_size", 0) if metadata else 0,
                    "long_term_memory_size": metadata.get("long_term_memory_size", 0) if metadata else 0
                },
                "tool_usage": {
                    "tools_invoked": metadata.get("tools_used", []) if metadata else [],
                    "tool_configs": metadata.get("tool_configurations", {}) if metadata else {}
                },
                "operation_details": metadata or {}
            }

            if run_id in self._active_runs:
                run_data = self._active_runs[run_id]
                
                run_data.setdefault("metrics", []).append({
                    "type": MetricType.OPERATION_REQUEST.value,
                    "timestamp": datetime.utcnow(),
                    "data": enhanced_metadata
                })

                if 'langsmith_run_id' in run_data:
                    await self._update_langsmith_run(
                        run_data['langsmith_run_id'],
                        metadata={
                            "operation_metrics": enhanced_metadata
                        }
                    )
            else:
                self.logger.error(f"No active run found for logging operation metrics. Run ID: {run_id}")
            
            self.logger.debug(f"Logged operation metrics for run {run_id}: {operation_type}, {duration_ms}ms")
                
        except Exception as e:
            self.logger.error(f"Error logging operation metrics: {str(e)}", exc_info=True)
            raise

    def get_run_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific run.
        
        Args:
            run_id: ID of the run to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Run metrics if found, None otherwise
        """
        try:
            if run_id in self._active_runs:
                return self._active_runs[run_id]
            
            for run in self._metrics_history:
                if run["run_id"] == run_id:
                    return run
            
            self.logger.error(f"No metrics found for run: {run_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving run metrics: {str(e)}", exc_info=True)
            return None

# Create singleton instance
monitoring_service = MonitoringService()