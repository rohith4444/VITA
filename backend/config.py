import os
from dotenv import load_dotenv

# Load default environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Load specific environment files if available
ENV = os.getenv("ENV", "development")  # Default to "development"

if ENV == "development":
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env.development"), override=True)
elif ENV == "production":
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env.production"), override=True)

class Config:
    """Configuration settings for the backend"""

    # LLM Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # PostgreSQL Database Configuration
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    @staticmethod
    def database_url():
        """Returns the PostgreSQL connection URL"""
        return f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
