from dotenv import load_dotenv
import os
from src.utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger("env_loader")

def load_env_variables():
    """Load environment variables from .env file."""
    logger.info("Starting to load environment variables")
    
    try:
        # Load .env file
        logger.debug("Attempting to load .env file")
        load_dotenv()
        logger.debug(".env file loaded successfully")
        
        # Required environment variables
        required_vars = [
            'OPENAI_API_KEY',
            'HUGGINGFACEHUB_API_TOKEN',
            'TAVILY_API_KEY',
            'LANGSMITH_API_KEY'
        ]

        # Optional environment variables with defaults
        optional_vars = {
            'LANGCHAIN_TRACING_V2': 'true',
            'LANGCHAIN_PROJECT': 'VITA_Agents',
            'LANGCHAIN_ENDPOINT': 'https://api.smith.langchain.com'
        }
        
        logger.debug(f"Checking for required variables: {', '.join(required_vars)}")
        
        # Check if all required variables are present
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise EnvironmentError(
                f"{error_msg}\n"
                "Please ensure these are set in your .env file."
            )
        
        # Set optional variables with defaults if not present
        for var, default in optional_vars.items():
            if not os.getenv(var):
                os.environ[var] = default
                logger.debug(f"Setting default value for {var}")
        
        # Create environment variables dictionary
        env_vars = {
            # Required variables
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'HUGGINGFACEHUB_API_TOKEN': os.getenv('HUGGINGFACEHUB_API_TOKEN'),
            'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
            'LANGCHAIN_API_KEY': os.getenv('LANGCHAIN_API_KEY'),
            
            # Optional variables with defaults
            'LANGCHAIN_TRACING_V2': os.getenv('LANGCHAIN_TRACING_V2'),
            'LANGCHAIN_PROJECT': os.getenv('LANGCHAIN_PROJECT'),
            'LANGCHAIN_ENDPOINT': os.getenv('LANGCHAIN_ENDPOINT')
        }
        
        
        # Log successful loading (without exposing sensitive values)
        logger.info("All required environment variables loaded successfully")
        logger.debug("Loaded variables: " + ", ".join(f"{k}: {'*' * 8}" for k in env_vars.keys()))
        
        return env_vars
        
    except Exception as e:
        logger.error(f"Error loading environment variables: {str(e)}", exc_info=True)
        raise