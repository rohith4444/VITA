from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Body

from sqlalchemy.orm import Session

from chat_api.database import get_db
from chat_api.services.agent_service import AgentService
from chat_api.services.session_service import SessionService
from chat_api.adapters.agent_adapter import AgentAdapter
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.response_formatter import ResponseFormatter, format_success_response, raise_http_exception
from chat_api.auth.dependencies import get_current_user_id
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("chat_api.routes.agent_routes")

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])

# Dependency for AgentService
def get_agent_service() -> AgentService:
    """FastAPI dependency for the agent service."""
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder(memory_adapter)
    )
    agent_adapter = AgentAdapter(memory_adapter.memory_manager)
    return AgentService(
        agent_adapter=agent_adapter,
        memory_service=memory_service,
        response_formatter=ResponseFormatter()
    )

# Dependency for SessionService
def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """FastAPI dependency for the session service."""
    memory_adapter = MemoryAdapter()
    return SessionService(db_session=db, memory_adapter=memory_adapter)

@router.post("/feedback/{session_id}/{message_id}")
async def submit_feedback(
    session_id: UUID,
    message_id: UUID,
    feedback: Dict[str, Any] = Body(...),
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Submit feedback for an agent response.
    
    Args:
        session_id: ID of the session
        message_id: ID of the message
        feedback: Feedback data
        
    Returns:
        Status of the feedback submission
    """
    try:
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
        
        # Process feedback
        result = await agent_service.process_feedback(
            session_id=session_id,
            message_id=message_id,
            feedback=feedback
        )
        
        return format_success_response({
            "status": "success",
            "message": "Feedback recorded successfully",
            "message_id": str(message_id),
            "feedback_type": feedback.get("type", "general"),
            "result": result
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing feedback for message {message_id} in session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="feedback_processing_failed",
            message=f"Failed to process feedback: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/tools/{session_id}")
async def execute_tool(
    session_id: UUID,
    tool_request: Dict[str, Any] = Body(...),
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Execute an agent tool.
    
    Args:
        session_id: ID of the session
        tool_request: Tool request data containing name and parameters
        
    Returns:
        Tool execution results
    """
    try:
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
        
        # Extract tool name and parameters
        tool_name = tool_request.get("name")
        tool_params = tool_request.get("params", {})
        
        if not tool_name:
            raise_http_exception(
                error_code="invalid_request",
                message="Tool name is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute the tool
        result = await agent_service.execute_tool(
            session_id=session_id,
            tool_name=tool_name,
            tool_params=tool_params
        )
        
        return format_success_response({
            "status": "success",
            "tool_name": tool_name,
            "result": result
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing tool in session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="tool_execution_failed",
            message=f"Failed to execute tool: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/report/{session_id}")
async def generate_report(
    session_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Generate a comprehensive report for a session.
    
    Args:
        session_id: ID of the session
        
    Returns:
        Generated report
    """
    try:
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
        
        # Generate report
        report = await agent_service.generate_report(session_id=session_id)
        
        return format_success_response({
            "status": "success",
            "session_id": str(session_id),
            "report": report
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating report for session {session_id}: {str(e)}")
        raise_http_exception(
            error_code="report_generation_failed",
            message=f"Failed to generate report: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/types")
async def get_agent_types(
    agent_service: AgentService = Depends(get_agent_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a list of available agent types with descriptions.
    
    Returns:
        Dictionary of agent types and descriptions
    """
    try:
        agent_types = await agent_service.get_agent_types()
        
        return format_success_response({
            "status": "success",
            "agent_types": agent_types
        })
        
    except Exception as e:
        logger.error(f"Error retrieving agent types: {str(e)}")
        raise_http_exception(
            error_code="agent_types_retrieval_failed",
            message=f"Failed to retrieve agent types: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Missing import
from chat_api.services.memory_service import MemoryService