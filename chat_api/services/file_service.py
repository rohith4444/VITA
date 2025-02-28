from typing import Dict, Any, List, Optional, BinaryIO, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import mimetypes
import os

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from chat_api.adapters.file_adapter import FileAdapter
from chat_api.models.artifact import ArtifactModel
from core.logging.logger import setup_logger

logger = setup_logger(__name__)

class FileService:
    """
    Service for handling file operations.
    """
    
    def __init__(self, db_session: Session, file_adapter: FileAdapter):
        """
        Initialize the file service.
        
        Args:
            db_session: SQLAlchemy database session
            file_adapter: Adapter for file operations
        """
        self.db = db_session
        self.file_adapter = file_adapter
    
    def save_file(
        self, 
        session_id: UUID, 
        message_id: UUID, 
        file_content: BinaryIO, 
        filename: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArtifactModel:
        """
        Save a file and create an artifact record.
        
        Args:
            session_id: ID of the session
            message_id: ID of the message the file is attached to
            file_content: Content of the file
            filename: Original filename
            file_type: Optional MIME type of the file
            metadata: Optional metadata for the file
            
        Returns:
            The created artifact model
        """
        try:
            # Determine file type if not provided
            if not file_type:
                file_type, _ = mimetypes.guess_type(filename)
                if not file_type:
                    file_type = "application/octet-stream"
            
            # Save the file
            stored_filename = self.file_adapter.save_file(file_content, filename)
            
            # Create metadata if not provided
            if metadata is None:
                metadata = {}
            
            # Add file information to metadata
            file_metadata = {
                "original_filename": filename,
                "stored_filename": stored_filename,
                "file_type": file_type,
                "file_size": os.path.getsize(self.file_adapter.get_file_path(stored_filename)),
                "upload_date": datetime.utcnow().isoformat()
            }
            metadata = {**metadata, **file_metadata}
            
            # Create artifact in database
            artifact_id = uuid4()
            artifact = ArtifactModel(
                id=artifact_id,
                message_id=message_id,
                type="file",
                content=stored_filename,  # Store the filename as content
                title=filename,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            
            self.db.add(artifact)
            self.db.commit()
            self.db.refresh(artifact)
            
            logger.info(f"Saved file {stored_filename} as artifact {artifact_id} for message {message_id}")
            return artifact
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error saving file for message {message_id}: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
        except Exception as e:
            logger.error(f"Error saving file for message {message_id}: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
    
    def get_file(self, artifact_id: UUID) -> Tuple[bytes, str, str]:
        """
        Get a file by artifact ID.
        
        Args:
            artifact_id: ID of the artifact
            
        Returns:
            Tuple of (file content, filename, file type)
        """
        try:
            # Get the artifact
            artifact = self.db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
            if not artifact or artifact.type != "file":
                logger.warning(f"Attempted to get non-existent file artifact {artifact_id}")
                raise ValueError(f"File artifact {artifact_id} not found")
            
            # Get the stored filename
            stored_filename = artifact.content
            
            # Get the file content
            file_content = self.file_adapter.read_file(stored_filename)
            if file_content is None:
                logger.warning(f"File not found for artifact {artifact_id}: {stored_filename}")
                raise ValueError(f"File not found for artifact {artifact_id}")
            
            # Get the original filename and file type
            original_filename = artifact.title
            file_type = artifact.metadata.get("file_type", "application/octet-stream")
            
            logger.info(f"Retrieved file {stored_filename} for artifact {artifact_id}")
            return file_content, original_filename, file_type
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving file for artifact {artifact_id}: {str(e)}")
            raise Exception(f"Failed to retrieve file: {str(e)}")
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving file for artifact {artifact_id}: {str(e)}")
            raise Exception(f"Failed to retrieve file: {str(e)}")
    
    def delete_file(self, artifact_id: UUID) -> bool:
        """
        Delete a file by artifact ID.
        
        Args:
            artifact_id: ID of the artifact
            
        Returns:
            True if the file was deleted, False otherwise
        """
        try:
            # Get the artifact
            artifact = self.db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
            if not artifact or artifact.type != "file":
                logger.warning(f"Attempted to delete non-existent file artifact {artifact_id}")
                return False
            
            # Get the stored filename
            stored_filename = artifact.content
            
            # Delete the file
            if stored_filename:
                self.file_adapter.delete_file(stored_filename)
            
            # Delete the artifact
            self.db.delete(artifact)
            self.db.commit()
            
            logger.info(f"Deleted file {stored_filename} and artifact {artifact_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting file for artifact {artifact_id}: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting file for artifact {artifact_id}: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def get_files_for_message(self, message_id: UUID) -> List[ArtifactModel]:
        """
        Get all files for a message.
        
        Args:
            message_id: ID of the message
            
        Returns:
            List of file artifact models
        """
        try:
            # Get file artifacts for the message
            artifacts = self.db.query(ArtifactModel).filter(
                ArtifactModel.message_id == message_id,
                ArtifactModel.type == "file"
            ).all()
            
            logger.info(f"Retrieved {len(artifacts)} files for message {message_id}")
            return artifacts
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving files for message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve files: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving files for message {message_id}: {str(e)}")
            raise Exception(f"Failed to retrieve files: {str(e)}")