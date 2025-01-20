from fastapi import APIRouter, HTTPException, Depends, Query
from src.api.models.chat import ChatRequest, ChatResponse, ErrorResponse, AgentResponse, CodeAnalysisRequest, CodeAnalysisResponse
from src.agents.python_agent import PythonAgent
from src.chat.session import ChatSession
from src.utils.logger import setup_logger
from typing import List, Optional

router = APIRouter()
logger = setup_logger("PythonRouter")

async def get_python_agent(session_id: str = None) -> PythonAgent:
    """Dependency to get Python agent instance"""
    try:
        session = ChatSession(None, session_id) if session_id else None
        return PythonAgent(session=session)
    except Exception as e:
        logger.error(f"Failed to initialize Python agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize agent")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_python_agent(
    request: ChatRequest,
    agent: PythonAgent = Depends(get_python_agent)
) -> ChatResponse:
    """
    Chat with Python Agent endpoint
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
                "domain": "python_programming"
            }
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Processing failed",
                code="PYTHON_AGENT_ERROR",
                details={"message": str(e)}
            ).model_dump()
        )

@router.get("/info", response_model=AgentResponse)
async def get_agent_info(
    agent: PythonAgent = Depends(get_python_agent)
):
    """Get Python Agent information"""
    return AgentResponse(
        name=agent.name,
        description=agent.description,
        expertise=agent.expertise,
        available=True
    )

@router.get("/capabilities")
async def get_capabilities(
    agent: PythonAgent = Depends(get_python_agent)
):
    """Get detailed capabilities of the Python Agent"""
    return {
        "programming_domains": [
            "algorithms",
            "data structures",
            "software design",
            "testing",
            "debugging"
        ],
        "tools": agent.tools,
        "specialties": [
            "code optimization",
            "best practices",
            "problem solving",
            "code review"
        ]
    }

@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(
    request: CodeAnalysisRequest,
    agent: PythonAgent = Depends(get_python_agent)
):
    """Analyze Python code for best practices and improvements"""
    try:
        analysis_request = f"Please analyze this Python code for best practices and potential improvements:\n\n{request.code}"
        analysis = await agent.process(analysis_request, request.context)
        
        return CodeAnalysisResponse(
            code=request.code,
            analysis=analysis,
            agent_name=agent.name,
            metadata={
                "expertise": agent.expertise,
                "type": "code_analysis"
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing code: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Analysis failed",
                code="PYTHON_AGENT_ERROR",
                details={"message": str(e)}
            ).model_dump()
        )

@router.post("/confidence")
async def check_confidence(
    query: str,
    agent: PythonAgent = Depends(get_python_agent)
):
    """Check Python Agent's confidence in handling a specific query"""
    confidence = agent.can_handle(query)
    return {
        "query": query,
        "confidence": confidence,
        "threshold": 0.5,
        "can_handle": confidence > 0.5,
        "expertise_matches": [
            expertise for expertise in agent.expertise
            if any(word.lower() in query.lower() for word in expertise.split())
        ]
    }