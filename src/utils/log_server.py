import logging
import logging.handlers
import socketserver
import struct
import pickle
import threading
import time
import os
from pathlib import Path
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Colored log formatter"""
    
    def __init__(self):
        super().__init__()
        # Color codes for different levels
        self.colors = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[37;41m', # White on Red
            'RESET': '\033[0m'        # Reset color
        }
        self.fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record):
        # Get color based on level
        color = self.colors.get(record.levelname, self.colors['RESET'])
        
        # Format the message
        formatted_msg = logging.Formatter(self.fmt).format(record)
        
        # Color the entire message and reset at the end
        return f"{color}{formatted_msg}{self.colors['RESET']}"

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for log records with duplicate detection"""
    
    def __init__(self, *args, **kwargs):
        self.loggers = {}
        self.message_cache = set()  # Cache for duplicate detection
        super().__init__(*args, **kwargs)

    def handle(self):
        while True:
            try:
                chunk = self.connection.recv(4)
                if len(chunk) < 4:
                    break
                slen = struct.unpack('>L', chunk)[0]
                chunk = self.connection.recv(slen)
                while len(chunk) < slen:
                    chunk = chunk + self.connection.recv(slen - len(chunk))
                obj = pickle.loads(chunk)
                record = logging.makeLogRecord(obj)
                self.handle_log_record(record)
            except Exception as e:
                print(f"Error handling log record: {e}")
                break

    def is_duplicate(self, record):
        """Check if a log record is a duplicate"""
        # Create a unique key for the message
        msg_key = f"{record.name}:{record.levelname}:{record.msg}:{record.created}"
        
        if msg_key in self.message_cache:
            return True
        
        # Add to cache
        self.message_cache.add(msg_key)
        
        # Keep cache size manageable
        if len(self.message_cache) > 1000:
            self.message_cache.clear()
            
        return False

    def handle_log_record(self, record):
        # Skip if it's a duplicate message
        if self.is_duplicate(record):
            return
            
        # Get or create logger
        if record.name not in self.loggers:
            logger = logging.getLogger(record.name)
            logger.handlers = []  # Remove existing handlers
            logger.propagate = False  # Prevent propagation
            
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter())
            logger.addHandler(console_handler)
            
            # File handler
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(
                log_dir / f"{record.name.replace('.', '_')}.log"
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
            self.loggers[record.name] = logger
        
        logger = self.loggers[record.name]
        logger.handle(record)

class LogServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def serve_logging(host='localhost', port=9020):
    """Start the logging server"""
    try:
        print('\033[0;32m' + f"Log server started on {host}:{port}" + '\033[0m')
        server = LogServer((host, port), LogRecordStreamHandler)
        server.serve_forever()
    except Exception as e:
        print('\033[0;31m' + f"Error starting log server: {e}" + '\033[0m')

if __name__ == '__main__':
    serve_logging()