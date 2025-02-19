from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from core.logging.logger import setup_logger
from core.tracing.service import trace_class

# Initialize logger
logger = setup_logger("monitoring.metrics")


class MetricType(Enum):
    """Types of metrics that can be collected."""
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    AGENT_OPERATION = "agent_operation"
    MEMORY_OPERATION = "memory_operation"
    TOOL_EXECUTION = "tool_execution"
    OPERATION_REQUEST = "operation_request"

class LLMMetrics(BaseModel):
    """Metrics specific to LLM operations."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    duration_ms: float
    success: bool
    cost: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OperationMetrics(BaseModel):
    """Metrics for general operations like agent actions or tool usage."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation_type: str
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


@trace_class
class MetricsManager:
    """Manages metric collection and aggregation."""
    
    def __init__(self):
        self.logger = setup_logger("monitoring.metrics.manager")
        self.logger.info("Initializing MetricsManager")

    def create_llm_metrics(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool,
        cost: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMMetrics:
        """Create metrics for an LLM operation."""
        try:
            metrics = LLMMetrics(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                duration_ms=duration_ms,
                success=success,
                cost=cost,
                metadata=metadata or {}
            )
            self.logger.debug(f"Created LLM metrics: {metrics.dict()}")
            return metrics
        except Exception as e:
            self.logger.error(f"Error creating LLM metrics: {str(e)}", exc_info=True)
            raise

    def create_operation_metrics(
        self,
        operation_type: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationMetrics:
        """Create metrics for a general operation."""
        try:
            metrics = OperationMetrics(
                operation_type=operation_type,
                duration_ms=duration_ms,
                success=success,
                metadata=metadata or {}
            )
            self.logger.debug(f"Created operation metrics: {metrics.dict()}")
            return metrics
        except Exception as e:
            self.logger.error(f"Error creating operation metrics: {str(e)}", exc_info=True)
            raise

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of an LLM operation based on token usage."""
        # Cost per 1K tokens as of 2024
        COST_PER_1K_TOKENS = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }
        
        try:
            if model not in COST_PER_1K_TOKENS:
                self.logger.warning(f"Unknown model {model}, cost calculation not available")
                return 0.0
                
            model_costs = COST_PER_1K_TOKENS[model]
            input_cost = (input_tokens / 1000) * model_costs["input"]
            output_cost = (output_tokens / 1000) * model_costs["output"]
            total_cost = input_cost + output_cost
            
            self.logger.debug(
                f"Calculated cost for {model}: ${total_cost:.4f} "
                f"(Input: ${input_cost:.4f}, Output: ${output_cost:.4f})"
            )
            return total_cost
            
        except Exception as e:
            self.logger.error(f"Error calculating cost: {str(e)}", exc_info=True)
            return 0.0