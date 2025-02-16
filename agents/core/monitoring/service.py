from typing import Dict, Any, Optional, List
from datetime import datetime
import langsmith
from langchain.callbacks.tracers.langsmith import LangSmithTracer
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
            if config.MONITORING_ENABLED:
                self.client = langsmith.Client(
                    api_key=config.LANGSMITH_API_KEY,
                    api_url=config.LANGCHAIN_ENDPOINT
                )
                self.tracer = LangSmithTracer(
                    project_name=config.LANGCHAIN_PROJECT,
                    client=self.client
                )
                self.logger.info(f"LangSmith initialized for project: {config.LANGCHAIN_PROJECT}")
            else:
                self.client = None
                self.tracer = None
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
            
            if self.tracer:
                await self.tracer.astart_trace(
                    run_id=run_id,
                    run_type="chain",
                    run_name=run_name,
                    extra=metadata
                )
            
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
            
            if self.tracer:
                await self.tracer.aend_trace(
                    run_id=run_id,
                    extra=metadata
                )
            
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
        
        Args:
            run_id: Current run ID
            model: Name of the LLM model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
            metadata: Optional additional metadata
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
            
            # Add to current run
            if self._current_run and self._current_run["run_id"] == run_id:
                self._current_run["metrics"].append({
                    "type": MetricType.LLM_REQUEST.value,
                    "timestamp": datetime.utcnow(),
                    "data": metrics.dict()
                })
            
            # Log to LangSmith if enabled
            if self.tracer:
                await self.tracer.alog_metrics(
                    metrics={
                        "tokens": input_tokens + output_tokens,
                        "cost": cost,
                        "duration_ms": duration_ms,
                        "success": success
                    },
                    run_id=run_id
                )
            
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
        """Enhanced operation metrics logging."""
        try:
            # Enhance metadata with operation context
            enhanced_metadata = {
                "operation_context": {
                    "type": operation_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration_ms": duration_ms,
                    "success": success
                },
                "memory_stats": {
                    "working_memory_size": await self._get_memory_size("working"),
                    "long_term_memory_size": await self._get_memory_size("long_term")
                },
                "tool_usage": {
                    "tools_invoked": metadata.get("tools_used", []),
                    "tool_configs": metadata.get("tool_configurations", {})
                },
                "operation_details": metadata or {}
            }

            if self.tracer:
                await self.tracer.alog_metrics(
                    metrics={
                        "operation_type": operation_type,
                        "duration_ms": duration_ms,
                        "success": success,
                        "enhanced_metrics": enhanced_metadata
                    },
                    run_id=run_id
                )
            
            self.logger.debug(
                f"Logged enhanced operation metrics for run {run_id}: "
                f"{operation_type}, {duration_ms}ms"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging enhanced operation metrics: {str(e)}", exc_info=True)
            raise

        
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