from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response, FileResponse

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.schemas.artifact import ArtifactResponse
from chat_api.services.file_service import FileService
from chat_api.services.session_service import SessionService
from chat_api.services.message_service import MessageService
from chat_api.adapters.file_adapter import FileAdapter
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.core.auth import get_current_user_id
from chat_api.core.logging import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(tags=["files"])

# Dependency for FileService
def get_file_service(db: Session = Depends(get_db)) -> FileService:
    file_adapter = FileAdapter()
    return FileService(db_session=db, file_adapter=file_adapter)

# Dependency for SessionService
def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    memory_adapter = MemoryAdapter()
    return SessionService(db_session=db, memory_adapter=memory_adapter)

# Dependency for MessageService
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    from chat_api.utils.context_builder import ContextBuilder
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder()
    )
    file_adapter = FileAdapter()
    return MessageService(
        db_session=db,
        memory_service=memory_service,
        file_adapter=file_adapter
    )

@router.post("/sessions/{session_id}/messages/{message_id}/files", response_model=ArtifactResponse)
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
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Check message existence and ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
        
        if message.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found in session {session_id}"
            )
        
        # Only user messages can have file attachments
        if message.role != "user":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Files can only be attached to user messages"
            )
        
        # Check user ownership of the message
        if message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this message"
            )
        
        # Save the file
        artifact = file_service.save_file(
            session_id=session_id,
            message_id=message_id,
            file_content=file.file,
            filename=file.filename,
            file_type=file.content_type
        )
        
        return artifact
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file for message {message_id} in session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/files/{artifact_id}")
async def download_file(
    artifact_id: UUID,
    file_service: FileService = Depends(get_file_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Download a file by artifact ID.
    """
    try:
        # Get the file content, filename, and type
        file_content, filename, file_type = file_service.get_file(artifact_id=artifact_id)
        
        # Return the file as a response
        return Response(
            content=file_content,
            media_type=file_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error downloading file for artifact {artifact_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.delete("/files/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    artifact_id: UUID,
    file_service: FileService = Depends(get_file_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a file by artifact ID.
    """
    try:
        # Delete the file
        success = file_service.delete_file(artifact_id=artifact_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File artifact {artifact_id} not found"
            )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting file for artifact {artifact_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.get("/messages/{message_id}/files", response_model=List[ArtifactResponse])
async def get_message_files(
    message_id: UUID,
    file_service: FileService = Depends(get_file_service),
    message_service: MessageService = Depends(get_message_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all files for a message.
    """
    try:
        # Check message ownership
        message = message_service.get_message(message_id=message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
        
        # Get all files for the message
        files = file_service.get_files_for_message(message_id=message_id)
        
        return files
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving files for message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve files: {str(e)}"
        )