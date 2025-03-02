from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response, FileResponse

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.artifact_schemas import ArtifactResponse
from chat_api.services.file_service import FileService
from chat_api.services.session_service import SessionService
from chat_api.services.message_service import MessageService
from chat_api.adapters.file_adapter import FileAdapter
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.services.memory_service import MemoryService
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.response_formatter import format_success_response, raise_http_exception
from chat_api.auth.dependencies import get_current_user_id
from chat_api.config import settings
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.routes.file_routes")

# Create router
router = APIRouter(prefix="/files", tags=["files"])

# Dependency for FileService
def get_file_service(db: Session = Depends(get_db)) -> FileService:
    """FastAPI dependency for the file service."""
    file_adapter = FileAdapter()
    return FileService(db_session=db, file_adapter=file_adapter)

# Dependency for SessionService
def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """FastAPI dependency for the session service."""
    memory_adapter = MemoryAdapter()
    return SessionService(db_session=db, memory_adapter=memory_adapter)

# Dependency for MessageService
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    """FastAPI dependency for the message service."""
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder(memory_adapter)
    )
    file_adapter = FileAdapter()
    return MessageService(
        db_session=db,
        memory_service=memory_service,
        file_adapter=file_adapter
    )

@router.post("/sessions/{session_id}/messages/{message_id}/upload", response_model=ArtifactResponse)
async def upload_file(
    session_id: UUID,
    message_id: UUID,
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
    session_service: SessionService = Depends(get_session_service),
    message_service: MessageService = Depends(get_message_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Upload a file attachment for a message.
    
    Args:
        session_id: ID of the session
        message_id: ID of the message
        file: File to upload
        
    Returns:
        Artifact created for the file
    """
    try:
        # Check file size
        file_size_limit = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)  # Reset file position after checking size
        
        if file_size > file_size_limit:
            raise_http_exception(
                error_code="file_too_large",
                message=f"File size exceeds the maximum limit of {settings.MAX_FILE_SIZE_MB}MB",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise_http_exception(
                error_code="session_not_found",
                message=f"Session {session_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this session",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check message existence and ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise_http_exception(
                error_code="message_not_found",
                message=f"Message {message_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if message.session_id != session_id:
            raise_http_exception(
                error_code="message_not_in_session",
                message=f"Message {message_id} not found in session {session_id}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Only user messages can have file attachments
        if message.role != "user":
            raise_http_exception(
                error_code="invalid_operation",
                message="Files can only be attached to user messages",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file content type
        content_type = file.content_type or "application/octet-stream"
        if not is_valid_content_type(content_type):
            raise_http_exception(
                error_code="invalid_file_type",
                message="File type not allowed",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )
        
        # Save the file
        artifact = file_service.save_file(
            session_id=session_id,
            message_id=message_id,
            file_content=file.file,
            filename=file.filename,
            file_type=content_type
        )
        
        return artifact
        
    except ValueError as e:
        logger.error(f"Validation error for file upload: {str(e)}")
        raise_http_exception(
            error_code="validation_error",
            message=str(e),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file for message {message_id} in session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="file_upload_failed",
            message=f"Failed to upload file: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{artifact_id}")
async def download_file(
    artifact_id: UUID,
    file_service: FileService = Depends(get_file_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Download a file by artifact ID.
    
    Args:
        artifact_id: ID of the artifact
        
    Returns:
        File content with appropriate content type
    """
    try:
        # Check ownership of the artifact
        if not file_service.check_artifact_ownership(artifact_id=artifact_id, user_id=user_id):
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access this file",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get the file content, filename, and type
        file_content, filename, file_type = file_service.get_file(artifact_id=artifact_id)
        
        if not file_content:
            raise_http_exception(
                error_code="file_not_found",
                message=f"File for artifact {artifact_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Return the file as a response
        return Response(
            content=file_content,
            media_type=file_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"Error retrieving file: {str(e)}")
        raise_http_exception(
            error_code="file_not_found",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error downloading file for artifact {artifact_id}: {str(e)}")
        raise_http_exception(
            error_code="file_download_failed",
            message=f"Failed to download file: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    artifact_id: UUID,
    file_service: FileService = Depends(get_file_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a file by artifact ID.
    
    Args:
        artifact_id: ID of the artifact
        
    Returns:
        204 No Content on success
    """
    try:
        # Check ownership of the artifact
        if not file_service.check_artifact_ownership(artifact_id=artifact_id, user_id=user_id):
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to delete this file",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the file
        success = file_service.delete_file(artifact_id=artifact_id)
        
        if not success:
            raise_http_exception(
                error_code="file_not_found",
                message=f"File artifact {artifact_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting file for artifact {artifact_id}: {str(e)}")
        raise_http_exception(
            error_code="file_deletion_failed",
            message=f"Failed to delete file: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/messages/{message_id}", response_model=List[ArtifactResponse])
async def get_message_files(
    message_id: UUID,
    file_service: FileService = Depends(get_file_service),
    message_service: MessageService = Depends(get_message_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all files for a message.
    
    Args:
        message_id: ID of the message
        
    Returns:
        List of file artifacts
    """
    try:
        # Check message ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise_http_exception(
                error_code="message_not_found",
                message=f"Message {message_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check session ownership
        session = session_service.get_session(session_id=message.session_id)
        if session.user_id != user_id:
            raise_http_exception(
                error_code="permission_denied",
                message="Not authorized to access files for this message",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Get all files for the message
        files = file_service.get_files_for_message(message_id=message_id)
        
        return files
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving files for message {message_id}: {str(e)}")
        raise_http_exception(
            error_code="file_retrieval_failed",
            message=f"Failed to retrieve files: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Helper function to validate file content types
def is_valid_content_type(content_type: str) -> bool:
    """
    Validate that a file content type is allowed.
    
    Args:
        content_type: MIME type to validate
        
    Returns:
        bool: True if allowed, False otherwise
    """
    allowed_types = [
        # Documents
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "text/markdown",
        "application/json",
        "application/xml",
        
        # Images
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/svg+xml",
        "image/webp",
        
        # Archives
        "application/zip",
        "application/x-rar-compressed",
        "application/x-tar",
        "application/gzip",
        
        # Code
        "text/javascript",
        "text/css",
        "text/html",
        "application/x-python-code",
        "application/x-java-source",
    ]
    
    return content_type in allowed_types