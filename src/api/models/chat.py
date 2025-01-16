from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class ChatRequest(BaseModel):
    """Request model for chat endpoints"""
    message: str = Field(..., description="The message to be processed")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation tracking")
    context: Optional[Dict] = Field(default={}, description="Additional context for the message")

class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    message: str = Field(..., description="The agent's response")
    agent_name: str = Field(..., description="Name of the responding agent")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict] = Field(default={}, description="Additional response metadata")

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict] = Field(default={}, description="Additional error details")

class AgentResponse(BaseModel):
    """Model for agent information"""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    expertise: List[str] = Field(..., description="Areas of expertise")
    available: bool = Field(..., description="Agent availability status")

class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    code: str = Field(..., description="Python code to analyze")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict] = Field(default={}, description="Additional context")

class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis"""
    code: str = Field(..., description="Original code")
    analysis: str = Field(..., description="Analysis result")
    agent_name: str = Field(..., description="Agent name")
    metadata: Optional[Dict] = Field(default={}, description="Additional metadata")