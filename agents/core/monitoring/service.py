from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
import uuid
import logging
from langsmith import Client, utils as ls_utils
from langchain_core.tracers.langchain import LangChainTracer
from core.logging.logger import setup_logger
from backend.config import config
from .metrics import MetricsManager, MetricType
from core.tracing.service import trace_class


@trace_class
class MonitoringService:
    """
    Central monitoring service for tracking and recording metrics of AI operations.
    """
    def __init__(self):
        """Initialize monitoring service with enhanced tracking."""
        self.logger = setup_logger("monitoring.service")
        self.logger.setLevel(logging.DEBUG)  # Enable debug logging
        self.logger.info("Initializing MonitoringService")

        try:
            self.metrics_manager = MetricsManager()
            self._current_run = None
            self._metrics_history = []
            self.client = None
            self.langsmith_client = None
            self.tracer = None
            
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
        """Initialize LangSmith integration with enhanced error handling."""
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
            self.logger.debug("LangSmith client and tracer setup complete")
        except Exception as e:
            self.logger.error(f"Failed to initialize LangSmith: {str(e)}", exc_info=True)
            self.client = None
            self.langsmith_client = None
            self.tracer = None

    async def _update_langsmith_run(
        self,
        run_id: str,
        metadata: Dict[str, Any],
        status: str = "completed"  # Changed default to "completed"
    ) -> None:
        """Update a LangSmith run with explicit status handling."""
        if not self.langsmith_client:
            self.logger.debug("LangSmith client not available, skipping run update")
            return

        try:
            self.logger.debug(f"Updating LangSmith run {run_id} with status: {status}")
            outputs = metadata.pop("outputs", {}) if metadata else {}
            error = metadata.pop("error", None) if metadata else None
            
            self.langsmith_client.update_run(
                run_id=run_id,
                status=status,
                outputs=outputs,
                error=error,
                extra_metadata=metadata
            )
            self.logger.debug(f"Successfully updated LangSmith run {run_id}")
        except ls_utils.LangSmithConflictError:
            self.logger.debug(f"LangSmith run {run_id} was already updated")
        except Exception as e:
            self.logger.error(f"Unexpected error updating LangSmith run: {str(e)}", exc_info=True)

    async def start_run(self, run_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new monitoring run."""
        try:
            timestamp = datetime.now(UTC)
            run_id = f"{run_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Check if there's an existing run
            if self._current_run:
                self.logger.warning(f"Forcing completion of existing run: {self._current_run['run_id']}")
                await self.end_run(self._current_run['run_id'])
            
            run_data = {
                "run_id": run_id,
                "start_time": timestamp,
                "name": run_name,
                "metadata": metadata or {},
                "metrics": [],
                "status": "active"
            }

               # Set current run before LangSmith operations
            self._current_run = run_data
            
            if self.langsmith_client:
                try:
                    ls_run = self.langsmith_client.create_run(
                        name=run_name,
                        run_type="chain",
                        inputs={},
                        extra_metadata=metadata or {},
                        start_time=timestamp
                    )
                    if ls_run and hasattr(ls_run, 'id'):
                        self._current_run['langsmith_run_id'] = ls_run.id
                        self.logger.debug(f"Created LangSmith run with ID: {ls_run.id}")
                    else:
                        self.logger.warning("LangSmith run created but no ID returned")
                except Exception as e:
                    self.logger.error(f"Failed to create LangSmith run: {str(e)}", exc_info=True)
            
            self.logger.info(f"Started monitoring run: {run_id}")
            return run_id
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring run: {str(e)}", exc_info=True)
            self._current_run = None  # Reset on error
            raise

    async def end_run(self, run_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End a monitoring run with proper cleanup."""
        try:
            if not self._current_run or self._current_run["run_id"] != run_id:
                self.logger.error(f"No active run found with ID: {run_id}")
                return
            
            end_time = datetime.now(UTC)
            duration = (end_time - self._current_run["start_time"]).total_seconds() * 1000
            
            run_data = {
                **self._current_run,
                "end_time": end_time,
                "duration_ms": duration,
                "completion_metadata": metadata or {},
                "status": "completed"
            }
            
            self._metrics_history.append(run_data)
            
            if self.langsmith_client and 'langsmith_run_id' in self._current_run:
                try:
                    # Update run status
                    self.langsmith_client.update_run(
                        run_id=self._current_run['langsmith_run_id'],
                        status="success",
                        outputs={
                            "duration_ms": duration,
                            "end_time": end_time.isoformat(),
                            **((metadata or {}).get('outputs', {}))
                        },
                        extra_metadata={
                            "completion_details": metadata or {},
                            "final_status": "completed"
                        }
                    )
                    
                    # Explicitly end the run
                    self.langsmith_client.end_run(
                        run_id=self._current_run['langsmith_run_id'],
                        outputs={
                            "duration_ms": duration,
                            "end_time": end_time.isoformat()
                        }
                    )
                except Exception as update_error:
                    self.logger.warning(
                        f"Failed to update LangSmith run {self._current_run['langsmith_run_id']}: "
                        f"{str(update_error)}"
                    )
            
            self._current_run = None
            self.logger.info(f"Successfully ended run: {run_id}")
            
        except Exception as e:
            self.logger.error(f"Error ending monitoring run: {str(e)}", exc_info=True)
            self._current_run = None  # Ensure current run is reset even on error

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
        """Log LLM metrics with detailed debugging."""
        try:
            self.logger.debug(
                f"Logging LLM metrics for run {run_id}: "
                f"model={model}, tokens={input_tokens}+{output_tokens}, "
                f"duration={duration_ms}ms, success={success}"
            )
            
            if not self._current_run:
                self.logger.error(f"No active run found for logging LLM metrics. Run ID: {run_id}")
                return
                
            if self._current_run["run_id"] != run_id:
                self.logger.warning(
                    f"Run ID mismatch. Current: {self._current_run['run_id']}, "
                    f"Requested: {run_id}"
                )
                return
            
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
            
            # Store metrics in current run
            self._current_run.setdefault("metrics", []).append({
                "type": "llm",
                "data": metrics.dict()
            })
            
            # Update LangSmith if available
            if self.langsmith_client and 'langsmith_run_id' in self._current_run:
                try:
                    await self._update_langsmith_run(
                        self._current_run['langsmith_run_id'],
                        metadata={
                            "llm_metrics": metrics.dict(),
                            "status": "in_progress"
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update LangSmith metrics: {str(e)}")
            
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
        """Log metrics for general operations."""
        try:
            self.logger.debug(
                f"Logging operation metrics for run {run_id}: "
                f"type={operation_type}, duration={duration_ms}ms, success={success}"
            )
            
            if not self._current_run:
                self.logger.error(f"No active run found for logging operation metrics. Run ID: {run_id}")
                return
                
            if self._current_run["run_id"] != run_id:
                self.logger.warning(
                    f"Run ID mismatch. Current: {self._current_run['run_id']}, "
                    f"Requested: {run_id}"
                )
                return
            
            metrics_data = {
                "operation_type": operation_type,
                "duration_ms": duration_ms,
                "success": success,
                "metadata": metadata or {}
            }
            
            # Store metrics in current run
            self._current_run.setdefault("metrics", []).append({
                "type": "operation",
                "data": metrics_data
            })
            
            # Update LangSmith if available
            if self.langsmith_client and 'langsmith_run_id' in self._current_run:
                try:
                    await self._update_langsmith_run(
                        self._current_run['langsmith_run_id'],
                        metadata={
                            "operation_metrics": metrics_data,
                            "status": "in_progress"
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update LangSmith metrics: {str(e)}")
            
            self.logger.debug(
                f"Logged operation metrics for run {run_id}: "
                f"{operation_type}, {duration_ms}ms"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging operation metrics: {str(e)}", exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Cleanup on service shutdown."""
        self.logger.info("Starting monitoring service cleanup")
        if self._current_run:
            try:
                await self.end_run(
                    self._current_run["run_id"],
                    metadata={
                        "cleanup": "Service shutdown",
                        "cleanup_time": datetime.now(UTC).isoformat()
                    }
                )
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")
        self.logger.info("Monitoring service cleanup completed")

# Create singleton instance
monitoring_service = MonitoringService()