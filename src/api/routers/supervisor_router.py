from fastapi import APIRouter, HTTPException, Depends
from src.api.models.chat import ChatRequest, ChatResponse, ErrorResponse, AgentResponse
from src.agents.supervising_agent import SupervisingAgent
from src.agents.python_agent import PythonAgent
from src.agents.mechatronic_agent import MechatronicAgent
from src.chat.session import ChatSession
from src.utils.logger import setup_logger
from typing import List

router = APIRouter()
logger = setup_logger("SupervisorRouter")

async def get_supervising_agent(session_id: str = None) -> SupervisingAgent:
    """Dependency to get Supervising agent instance with all specialized agents"""
    try:
        session = ChatSession(None, session_id) if session_id else None
        
        # Initialize specialized agents
        python_agent = PythonAgent(session=session)
        mechatronic_agent = MechatronicAgent(session=session)
        
        # Create supervising agent with specialized agents
        return SupervisingAgent(
            specialized_agents=[python_agent, mechatronic_agent],
            session=session
        )
    except Exception as e:
        logger.error(f"Failed to initialize Supervising agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize supervising agent")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_supervisor(
    request: ChatRequest,
    agent: SupervisingAgent = Depends(get_supervising_agent)
) -> ChatResponse:
    """
    Chat with Supervising Agent endpoint - automatically routes to the most appropriate agent
    """
    try:
        logger.info(f"Processing chat request with session ID: {request.session_id}")
        response = await agent.process(request.message, request.context)
        
        # Extract agent name from response format [Agent Name]: Response
        agent_name = response.split(']:')[0].strip('[') if ']' in response else "Supervisor"
        message = response.split(']:')[1].strip() if ']' in response else response
        
        return ChatResponse(
            message=message,
            agent_name=agent_name,
            session_id=request.session_id,
            metadata={
                "routed": True,
                "original_query": request.message
            }
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Processing failed",
                code="SUPERVISOR_ERROR",
                details={"message": str(e)}
            ).dict()
        )

@router.get("/agents", response_model=List[AgentResponse])
async def list_available_agents(
    agent: SupervisingAgent = Depends(get_supervising_agent)
):
    """Get information about all available agents"""
    return [
        AgentResponse(
            name=specialized_agent.name,
            description=specialized_agent.description,
            expertise=specialized_agent.expertise,
            available=True
        )
        for specialized_agent in agent.specialized_agents
    ]

@router.get("/route-analysis")
async def analyze_routing(
    query: str,
    agent: SupervisingAgent = Depends(get_supervising_agent)
):
    """Analyze how a query would be routed without executing it"""
    try:
        selected_agent = await agent.route_query(query)
        confidence_scores = {
            agent.name: agent.can_handle(query)
            for agent in agent.specialized_agents
        }
        
        return {
            "selected_agent": selected_agent.name,
            "confidence_scores": confidence_scores,
            "query": query
        }
    except Exception as e:
        logger.error(f"Error analyzing routing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze query routing"
        )