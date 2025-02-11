from fastapi import APIRouter, HTTPException, Depends
from src.api.models.chat import ChatRequest, ChatResponse, ErrorResponse, AgentResponse
from src.agents.mechatronic_agent import MechatronicAgent
from src.chat.session import ChatSession
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("MechatronicRouter")

async def get_mechatronic_agent(session_id: str = None) -> MechatronicAgent:
    """Dependency to get Mechatronic agent instance"""
    try:
        session = ChatSession(None, session_id) if session_id else None
        return MechatronicAgent(session=session)
    except Exception as e:
        logger.error(f"Failed to initialize Mechatronic agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize agent")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_mechatronic_agent(
    request: ChatRequest,
    agent: MechatronicAgent = Depends(get_mechatronic_agent)
) -> ChatResponse:
    """
    Chat with Mechatronic Agent endpoint
    """
    try:
        logger.info(f"Processing chat request with session ID: {request.session_id}")
        response = await agent.process(request.message, request.context)
        
        return ChatResponse(
            message=response,
            agent_name=agent.name,
            session_id=request.session_id,
            metadata={
                "expertise": agent.expertise,
                "domain": "mechatronics"
            }
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Processing failed",
                code="MECHATRONIC_AGENT_ERROR",
                details={"message": str(e)}
            ).model_dump()
        )

@router.get("/info", response_model=AgentResponse)
async def get_agent_info(
    agent: MechatronicAgent = Depends(get_mechatronic_agent)
):
    """Get Mechatronic Agent information"""
    return AgentResponse(
        name=agent.name,
        description=agent.description,
        expertise=agent.expertise,
        available=True
    )

@router.get("/capabilities")
async def get_capabilities(
    agent: MechatronicAgent = Depends(get_mechatronic_agent)
):
    """Get detailed capabilities of the Mechatronic Agent"""
    return {
        "domains": [
            "robotics",
            "electronics",
            "mechanical systems",
            "control systems"
        ],
        "tools": agent.tools,
        "specialties": [
            "hardware design",
            "system integration",
            "automation",
            "sensor systems"
        ]
    }