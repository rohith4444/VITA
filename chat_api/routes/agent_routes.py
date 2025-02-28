from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Body

from chat_api.services.agent_service import AgentService
from chat_api.services.session_service import SessionService
from chat_api.services.memory_service import MemoryService
from chat_api.adapters.agent_adapter import AgentAdapter
from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.utils.context_builder import ContextBuilder
from chat_api.utils.response_formatter import ResponseFormatter
from chat_api.core.auth import get_current_user_id
from chat_api.database import get_db
from chat_api.core.logging import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])

# Dependency for AgentService
def get_agent_service() -> AgentService:
    memory_adapter = MemoryAdapter()
    memory_service = MemoryService(
        memory_adapter=memory_adapter,
        context_builder=ContextBuilder()
    )
    return AgentService(
        agent_adapter=AgentAdapter(),
        memory_service=memory_service,
        response_formatter=ResponseFormatter()
    )

# Dependency for SessionService
def get_session_service(db = Depends(get_db)) -> SessionService:
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
        
        # Process feedback
        result = await agent_service.process_feedback(
            session_id=session_id,
            message_id=message_id,
            feedback=feedback
        )
        
        return {"status": "success", "result": result}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing feedback for message {message_id} in session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
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
        
        # Extract tool name and parameters
        tool_name = tool_request.get("name")
        tool_params = tool_request.get("params", {})
        
        if not tool_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tool name is required"
            )
        
        # Execute the tool
        result = await agent_service.execute_tool(
            session_id=session_id,
            tool_name=tool_name,
            tool_params=tool_params
        )
        
        return {"status": "success", "result": result}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing tool in session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool: {str(e)}"
        )