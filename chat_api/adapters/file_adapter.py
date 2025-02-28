# app/utils/file_adapter.py

import os
import uuid
from typing import BinaryIO, Optional
from pathlib import Path
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class FileAdapter:
    """
    Utility class to handle file operations for chat attachments.
    """
    
    def __init__(self, base_path: str = "uploads"):
        """
        Initialize the FileAdapter.
        
        Args:
            base_path: The base directory where files will be stored
        """
        self.base_path = Path(base_path)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the upload directory exists."""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"Ensured directory exists: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {self.base_path}: {str(e)}")
            raise Exception(f"Failed to create storage directory: {str(e)}")
    
    def save_file(self, file_content: BinaryIO, original_filename: str) -> str:
        """
        Save a file to the file system with a unique name.
        
        Args:
            file_content: The file content as a binary stream
            original_filename: The original name of the file
            
        Returns:
            The path to the saved file (relative to the base path)
        """
        # Generate a unique filename to avoid collisions
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create the full path
        file_path = self.base_path / unique_filename
        
        try:
            # Write the file
            with open(file_path, "wb") as f:
                content = file_content.read()
                f.write(content)
            
            logger.info(f"File saved successfully: {unique_filename} (original: {original_filename})")
            # Return the relative path from the base directory
            return unique_filename
        except Exception as e:
            logger.error(f"Failed to save file {original_filename}: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
    
    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path for a stored file.
        
        Args:
            filename: The filename (returned from save_file)
            
        Returns:
            The full path to the file
        """
        return self.base_path / filename
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from the file system.
        
        Args:
            filename: The filename to delete
            
        Returns:
            True if the file was deleted successfully, False otherwise
        """
        file_path = self.get_file_path(filename)
        try:
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"File deleted successfully: {filename}")
                return True
            logger.warning(f"Attempted to delete non-existent file: {filename}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {str(e)}")
            return False
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if the file exists, False otherwise
        """
        exists = self.get_file_path(filename).exists()
        if not exists:
            logger.debug(f"File does not exist: {filename}")
        return exists
    
    def read_file(self, filename: str) -> Optional[bytes]:
        """
        Read a file from the file system.
        
        Args:
            filename: The filename to read
            
        Returns:
            The file content as bytes, or None if the file doesn't exist
        """
        file_path = self.get_file_path(filename)
        if not file_path.exists():
            logger.warning(f"Attempted to read non-existent file: {filename}")
            return None
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                logger.info(f"File read successfully: {filename}")
                return content
        except Exception as e:
            logger.error(f"Failed to read file {filename}: {str(e)}")
            raise Exception(f"Failed to read file: {str(e)}")