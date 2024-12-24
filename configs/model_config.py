# configs/model_config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    model_name: str = "gpt-4"  # Default model
    temperature: float = 0.0    # Default to deterministic outputs
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

# Default configurations
DEFAULT_LLM_CONFIG = LLMConfig(
    model_name="gpt-4",
    temperature=0.0
)

FAST_LLM_CONFIG = LLMConfig(
    model_name="gpt-3.5-turbo",
    temperature=0.0
)