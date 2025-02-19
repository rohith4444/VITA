import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.logging.log_server import serve_logging

def setup_logging_environment():
    """Setup the logging environment"""
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create empty __init__.py files if they don't exist
    core_init = project_root / "core" / "__init__.py"
    core_init.parent.mkdir(exist_ok=True)
    core_init.touch()
    
    logging_init = project_root / "core" / "logging" / "__init__.py"
    logging_init.parent.mkdir(exist_ok=True)
    logging_init.touch()

if __name__ == "__main__":
    # Setup the environment
    setup_logging_environment()
    
    # Print startup message
    print("====================================")
    print("Starting logging server...")
    print("Log files will be stored in: ./logs/")
    print("Press Ctrl+C to stop the server")
    print("====================================")
    
    # Start the logging server
    serve_logging()