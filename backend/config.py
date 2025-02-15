import os
from typing import Optional
from dotenv import load_dotenv
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("config")
logger.info("Initializing configuration")

# Load default environment variables
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
    logger.debug(f"Loaded default environment from {env_file}")
else:
    logger.warning("Default .env file not found")

# Load specific environment files if available
ENV = os.getenv("ENV", "development")
logger.info(f"Current environment: {ENV}")

try:
    if ENV == "development":
        env_path = os.path.join(os.path.dirname(__file__), ".env.development")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            logger.debug("Loaded development environment variables")
        else:
            logger.warning(".env.development file not found")
            
    elif ENV == "production":
        env_path = os.path.join(os.path.dirname(__file__), ".env.production")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            logger.debug("Loaded production environment variables")
        else:
            logger.warning(".env.production file not found")
    else:
        logger.warning(f"Unknown environment: {ENV}")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}", exc_info=True)
    raise

class Config:
    """
    Configuration settings for the backend.
    Manages environment variables and provides validation.
    """

    def __init__(self):
        self.logger = setup_logger("config.Config")
        self.logger.info("Initializing Config class")

    # LLM Configuration
    @property
    def OPENAI_API_KEY(self) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY is required")
        return api_key

    # PostgreSQL Database Configuration
    @property
    def POSTGRES_DB(self) -> str:
        db = os.getenv("POSTGRES_DB")
        if not db:
            self.logger.error("POSTGRES_DB not found in environment")
            raise ValueError("POSTGRES_DB is required")
        return db

    @property
    def POSTGRES_USER(self) -> str:
        user = os.getenv("POSTGRES_USER")
        if not user:
            self.logger.error("POSTGRES_USER not found in environment")
            raise ValueError("POSTGRES_USER is required")
        return user

    @property
    def POSTGRES_PASSWORD(self) -> str:
        password = os.getenv("POSTGRES_PASSWORD")
        if not password:
            self.logger.error("POSTGRES_PASSWORD not found in environment")
            raise ValueError("POSTGRES_PASSWORD is required")
        return password

    @property
    def POSTGRES_HOST(self) -> str:
        host = os.getenv("POSTGRES_HOST")
        if not host:
            self.logger.error("POSTGRES_HOST not found in environment")
            raise ValueError("POSTGRES_HOST is required")
        return host

    @property
    def POSTGRES_PORT(self) -> str:
        port = os.getenv("POSTGRES_PORT")
        if not port:
            self.logger.error("POSTGRES_PORT not found in environment")
            raise ValueError("POSTGRES_PORT is required")
        return port

    def database_url(self) -> str:
        """
        Returns the PostgreSQL connection URL.
        
        Returns:
            str: Formatted database URL
            
        Raises:
            ValueError: If any required database configuration is missing
        """
        try:
            url = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            self.logger.debug("Generated database URL successfully")
            return url
        except Exception as e:
            self.logger.error(f"Failed to generate database URL: {str(e)}", exc_info=True)
            raise

    def validate_config(self) -> bool:
        """
        Validates all configuration settings.
        
        Returns:
            bool: True if all settings are valid
            
        Raises:
            ValueError: If any required configuration is missing
        """
        try:
            self.logger.info("Validating configuration")
            
            # Validate OpenAI configuration
            _ = self.OPENAI_API_KEY
            
            # Validate database configuration
            _ = self.database_url()
            
            self.logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}", exc_info=True)
            raise

# Create singleton instance
config = Config()
try:
    config.validate_config()
    logger.info("Configuration initialized successfully")
except Exception as e:
    logger.error("Failed to initialize configuration", exc_info=True)
    raise