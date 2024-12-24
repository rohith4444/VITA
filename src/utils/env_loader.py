"""Environment loading utilities."""
from dotenv import load_dotenv
import os

def load_env_variables():
    """Load environment variables from .env file."""
    # Load .env file
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'HUGGINGFACEHUB_API_TOKEN',
        'TAVILY_API_KEY'
    ]
    
    # Check if all required variables are present
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please ensure these are set in your .env file."
        )

    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'HUGGINGFACEHUB_API_TOKEN': os.getenv('HUGGINGFACEHUB_API_TOKEN'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY')
    }