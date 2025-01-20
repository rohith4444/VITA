from langchain_openai import ChatOpenAI
from configs.model_config import LLMConfig, DEFAULT_LLM_CONFIG
from src.utils.env_loader import load_env_variables
from src.utils.logger import setup_logger

# Set up logging
logger = setup_logger("LLMManager")

# Load environment variables
logger.info("Loading environment variables")
env_vars = load_env_variables()

class LLMManager:
    """Manager class for LLM instances."""
    
    _instance = None
    _llm_instances = {}
    _logger = logger
    
    def __init__(self):
        self._logger.debug("Initializing new LLMManager instance")
        
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._logger.info("Creating new LLMManager singleton instance")
            cls._instance = cls()
        else:
            cls._logger.debug("Returning existing LLMManager instance")
        return cls._instance
    
    def get_llm(self, config: LLMConfig = DEFAULT_LLM_CONFIG) -> ChatOpenAI:
        """Get or create an LLM instance with given configuration."""
        self._logger.info(f"Requesting LLM with model: {config.model_name}")
        
        try:
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
                self._logger.debug(f"Found cached LLM instance for {config.model_name}")
                return self._llm_instances[config_key]
            
            self._logger.debug(f"Creating new LLM instance for {config.model_name}")
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
            self._logger.info(f"Successfully created and cached LLM instance for {config.model_name}")
            return llm
            
        except Exception as e:
            self._logger.error(f"Error creating LLM instance: {str(e)}", exc_info=True)
            raise

def get_llm(config: LLMConfig = DEFAULT_LLM_CONFIG) -> ChatOpenAI:
    """Convenience function to get LLM instance."""
    logger.debug("Called get_llm convenience function")
    return LLMManager.get_instance().get_llm(config)

# Create a default instance that matches the original setup
logger.info("Creating default ChatGPT instance")
chatgpt = get_llm(DEFAULT_LLM_CONFIG)