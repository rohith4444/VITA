from dataclasses import dataclass
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger("ModelConfig")

@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    model_name: str = "gpt-4"         # Default model
    temperature: float = 0.0          # Default to deterministic outputs
    max_tokens: Optional[int] = None  # No token limit by default
    top_p: float = 1.0               # No nucleus sampling
    frequency_penalty: float = 0.0    # No frequency penalty
    presence_penalty: float = 0.0     # No presence penalty
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        logger.debug(f"Creating LLMConfig: {self.__dict__}")
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters."""
        try:
            if self.temperature < 0.0 or self.temperature > 2.0:
                raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")
            if self.top_p < 0.0 or self.top_p > 1.0:
                raise ValueError(f"Top_p must be between 0 and 1, got {self.top_p}")
            if self.max_tokens is not None and self.max_tokens <= 0:
                raise ValueError(f"Max_tokens must be positive, got {self.max_tokens}")
                
            logger.info("LLMConfig validation successful")
        except Exception as e:
            logger.error(f"LLMConfig validation failed: {str(e)}", exc_info=True)
            raise

# Default configurations
logger.info("Creating default LLM configurations")
DEFAULT_LLM_CONFIG = LLMConfig(
    model_name="gpt-3.5-turbo",
    temperature=0.0
)
logger.debug("DEFAULT_LLM_CONFIG created")

FAST_LLM_CONFIG = LLMConfig(
    model_name="gpt-3.5-turbo",
    temperature=0.0
)
logger.debug("FAST_LLM_CONFIG created")