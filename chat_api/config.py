import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.config")
logger.info("Initializing chat API configuration")

# Load environment variables
load_dotenv()


class ChatAPISettings(BaseSettings):
    """
    Configuration settings for the chat API.
    Inherits from BaseSettings for automatic environment variable loading.
    """
    # API Settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    API_TITLE: str = "VITA Chat API"
    API_DESCRIPTION: str = "API for conversation-based interaction with VITA AI agents"
    
    # Server Settings
    HOST: str = os.getenv("CHAT_API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("CHAT_API_PORT", "8000"))
    DEBUG: bool = os.getenv("CHAT_API_DEBUG", "False").lower() == "true"
    
    # Session Settings
    SESSION_EXPIRY_HOURS: int = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
    MAX_MESSAGES_PER_SESSION: int = int(os.getenv("MAX_MESSAGES_PER_SESSION", "100"))
    
    # Memory Settings
    SHORT_TERM_MEMORY_TTL: int = int(os.getenv("SHORT_TERM_MEMORY_TTL", "3600"))  # 1 hour in seconds
    WORKING_MEMORY_TTL: int = int(os.getenv("WORKING_MEMORY_TTL", "86400"))  # 24 hours in seconds
    
    # Security Settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Token Settings
    TOKEN_ALGORITHM: str = os.getenv("TOKEN_ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    TOKEN_SECRET_KEY: str = os.getenv("TOKEN_SECRET_KEY", "development_secret_key")

    # Database configuration
    DATABASE_URL = "sqlite:///./vita.db"

    # API configuration
    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"

    # Chat configuration
    MAX_MESSAGES_PER_PAGE = 50
    MAX_MESSAGE_LENGTH = 2000  # Maximum length of a message in characters

    # Logging configuration
    LOG_LEVEL = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = ChatAPISettings()

logger.info(f"Chat API configuration loaded: API version {settings.API_VERSION}")
logger.debug(f"API will run on {settings.HOST}:{settings.PORT}")

# Validate critical settings
if settings.TOKEN_SECRET_KEY == "development_secret_key" and not settings.DEBUG:
    logger.warning("Using default development secret key in non-debug mode")

# Export settings instance
__all__ = ["settings"]