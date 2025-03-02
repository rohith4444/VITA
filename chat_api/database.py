from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from core.logging.logger import setup_logger
from chat_api.config import settings

# Initialize logger
logger = setup_logger("chat_api.database")
logger.info("Initializing database connections")

# SQLite setup with SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency for routes
def get_db():
    """
    FastAPI dependency to provide a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize MongoDB connection through memory system
def get_memory_manager():
    """
    Get the memory manager instance for the MongoDB-based memory system.
    """
    from memory.memory_manager import MemoryManager
    from backend.config import config
    
    try:
        # Create memory manager with database URL from config
        memory_manager = MemoryManager.create(config.database_url())
        logger.info("Memory manager initialized successfully")
        return memory_manager
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {str(e)}", exc_info=True)
        raise

# Global memory manager instance (initialized in main.py)
memory_manager = None