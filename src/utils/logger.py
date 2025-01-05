import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Set up logger with both socket and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Socket handler for remote logging
    socket_handler = logging.handlers.SocketHandler('localhost', 9020)
    logger.addHandler(socket_handler)

    # Only add console handler for user-facing messages in main
    if name == "main":
        console_fmt = "%(message)s"  # Simplified format for user messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(console_fmt))
        console_handler.addFilter(lambda record: not record.msg.startswith(("DEBUG:", "INFO:")))
        logger.addHandler(console_handler)

    return logger

# Create a default logger for the application
app_logger = setup_logger("multi_agent_system")