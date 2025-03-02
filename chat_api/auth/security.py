from passlib.context import CryptContext
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.auth.security")

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    hashed = pwd_context.hash(password)
    logger.debug("Password hashed successfully")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    result = pwd_context.verify(plain_password, hashed_password)
    if not result:
        logger.debug("Password verification failed")
    return result