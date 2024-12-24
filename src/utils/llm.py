# src/utils/llm.py
from langchain_openai import ChatOpenAI
from configs.model_config import LLMConfig, DEFAULT_LLM_CONFIG
from src.utils.env_loader import load_env_variables

# Load environment variables
env_vars = load_env_variables()

class LLMManager:
    """Manager class for LLM instances."""
    
    _instance = None
    _llm_instances = {}
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_llm(self, config: LLMConfig = DEFAULT_LLM_CONFIG) -> ChatOpenAI:
        """Get or create an LLM instance with given configuration."""
        # Create a unique key for this configuration
        config_key = (
            config.model_name,
            config.temperature,
            config.max_tokens,
            config.top_p,
            config.frequency_penalty,
            config.presence_penalty
        )
        
        # Return existing instance if available
        if config_key in self._llm_instances:
            return self._llm_instances[config_key]
        
        # Create new instance
        llm = ChatOpenAI(
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty
        )
        
        # Cache the instance
        self._llm_instances[config_key] = llm
        return llm

def get_llm(config: LLMConfig = DEFAULT_LLM_CONFIG) -> ChatOpenAI:
    """Convenience function to get LLM instance."""
    return LLMManager.get_instance().get_llm(config)

# Create a default instance that matches the original setup
chatgpt = get_llm(DEFAULT_LLM_CONFIG)