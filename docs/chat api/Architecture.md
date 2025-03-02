# Chat API Module - Detailed Architecture Documentation

## Introduction

The Chat API module provides a RESTful interface for users to interact with the VITA platform's specialized AI agents (Project Manager, Solution Architect, Full Stack Developer, and QA/Test). This module bridges the gap between the existing agent system with its memory architecture and user-facing chat functionality.

## Overall Architecture

The Chat API follows a layered architecture pattern with clear separation of concerns:

1. **API Layer** - Routes that define endpoints and handle HTTP requests/responses
2. **Service Layer** - Business logic implementation and coordination
3. **Data Layer** - Split between SQLite (via SQLAlchemy) and MongoDB (via the existing memory system)
4. **Adapters** - Interfaces to connect with external systems (agents, file storage, memory system)
5. **Utilities** - Helper components for cross-cutting concerns

## Core Components

### Database Layer (`database.py`)

This module establishes connections to both storage systems:

- **SQLAlchemy Setup**: Configures the ORM engine, creates a session factory, and defines the Base class for models
- **MongoDB Connection**: Provides access to the existing memory system's MongoDB instance
- **Migration Support**: Integrates with Alembic for database schema versioning

```python
# Simplified structure
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from chat_api.config import settings

# SQLAlchemy setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB connection (via memory system)
def get_mongo_client():
    # Configuration from settings
    # Returns a configured MongoDB client
    pass
```

### Data Models

#### SQLAlchemy Models (`models/`)

These models define the database schema for the SQLite database:

- **User** (`user.py`): User accounts and authentication data
- **Session** (`session.py`): Chat sessions and their metadata
- **Message** (`message.py`): Chat messages with content and references
- **Artifact** (`artifact.py`): Files, code snippets, and other generated content

Each model defines the table structure, relationships, and any constraints:

```python
# Example SQLAlchemy model (simplified)
class MessageModel(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)
    type = Column(String, nullable=False, default="text")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=lambda: {})
    
    # Relationships
    session = relationship("SessionModel", back_populates="messages")
    user = relationship("UserModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message")
```

#### Pydantic Schemas (`schemas/`)

These schemas define the validation rules for API requests and responses:

- **User Schemas**: Registration, login, profile information
- **Session Schemas**: Creating and updating chat sessions
- **Message Schemas**: Sending and receiving chat messages
- **Artifact Schemas**: File uploads and content creation

```python
# Example Pydantic schema (simplified)
class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    type: MessageType = MessageType.TEXT
    files: List[str] = []
    parent_message_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
```

### Memory System Integration

#### Memory Adapter (`adapters/memory_adapter.py`)

This adapter serves as the bridge between the Chat API and the existing three-tier memory system:

- Connects to the existing `MemoryManager`
- Focuses primarily on the Long-term Memory tier for persistence
- Translates between Chat API data models and memory system formats
- Provides methods for storing and retrieving conversational context

```python
class MemoryAdapter:
    """
    Adapter for the existing memory system.
    Provides an interface to the three-tier memory architecture for the chat API.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def store_in_long_term(
        self, 
        agent_id: str, 
        content: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.7
    ) -> bool:
        """
        Store content in long-term memory for agent context.
        """
        try:
            result = await self.memory_manager.store(
                agent_id=agent_id,
                memory_type=MemoryType.LONG_TERM,
                content=content,
                metadata=metadata,
                importance=importance
            )
            return result
        except Exception as e:
            # Error handling
            return False
    
    # Additional methods for retrieval, etc.
```

#### Memory Service (`services/memory_service.py`)

This service coordinates memory operations and context building:

- Uses the Memory Adapter to interact with the memory system
- Manages the formatting and transformation of chat data for agent consumption
- Handles synchronization between SQLite and Long-term Memory
- Provides methods for retrieving comprehensive context for agents

```python
class MemoryService:
    """
    Service for managing chat memory and context.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter, context_builder: ContextBuilder):
        self.memory_adapter = memory_adapter
        self.context_builder = context_builder
    
    def add_user_message(self, session_id: UUID, message_content: str, message_id: UUID, 
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a user message to memory for agent context.
        """
        try:
            # Format for long-term memory
            content = {
                "message": message_content,
                "role": "user",
                "message_id": str(message_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in long-term memory
            return self.memory_adapter.store_in_long_term(
                agent_id=str(session_id),
                content=content,
                metadata=metadata
            )
        except Exception as e:
            # Error handling
            return False
    
    # Additional methods
```

#### Context Builder (`utils/context_builder.py`)

This utility constructs the context required by agents:

- Retrieves relevant conversation history from SQLite
- Fetches additional context from Long-term Memory
- Builds comprehensive context objects for specific agent types
- Formats the context according to each agent's requirements

```python
class ContextBuilder:
    """
    Utility for building agent context from multiple sources.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter):
        self.memory_adapter = memory_adapter
    
    async def build_context(
        self, 
        session_id: UUID, 
        message_history: List[Dict[str, Any]],
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for an agent.
        """
        try:
            # Get additional context from long-term memory
            long_term_context = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id)
            )
            
            # Combine with message history from SQLite
            context = {
                "conversation_history": message_history,
                "long_term_context": long_term_context,
                # Additional context elements
            }
            
            # Format for specific agent type
            return self.format_for_agent(context, agent_type)
        except Exception as e:
            # Error handling
            return {"conversation_history": message_history}
    
    # Helper methods for formatting
```

### Agent Integration

#### Agent Adapter (`adapters/agent_adapter.py`)

This adapter interfaces with the existing agent system:

- Creates and manages agent instances
- Routes user messages to the appropriate agent
- Formats responses for the Chat API
- Handles agent lifecycle management

```python
class AgentAdapter:
    """
    Adapter for the existing agent system.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self._active_agents = {}  # session_id -> agent instance
    
    async def create_agent(self, session_id: str, agent_type: str, name: Optional[str] = None) -> str:
        """
        Create a new agent instance for a session.
        """
        try:
            # Generate agent ID
            agent_id = f"{agent_type}_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create agent instance
            agent_class = self.AGENT_TYPES[agent_type]
            agent_instance = agent_class(
                agent_id=agent_id,
                name=name or agent_type.replace('_', ' ').title(),
                memory_manager=self.memory_manager
            )
            
            # Store in active agents
            self._active_agents[session_id] = agent_instance
            
            return agent_id
        except Exception as e:
            # Error handling
            raise ValueError(f"Failed to create agent: {str(e)}")
    
    async def run_agent(self, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an agent with the given input data.
        """
        try:
            agent = self._active_agents[session_id]
            result = await agent.run(input_data)
            return result
        except Exception as e:
            # Error handling
            raise ValueError(f"Failed to run agent: {str(e)}")
    
    # Additional methods
```

#### Agent Service (`services/agent_service.py`)

This service coordinates agent interactions:

- Uses the Agent Adapter to invoke agents
- Processes user messages
- Handles feedback mechanisms
- Manages tool execution requests

```python
class AgentService:
    """
    Service for interacting with the agent system.
    """
    
    def __init__(
        self, 
        agent_adapter: AgentAdapter, 
        memory_service: MemoryService,
        response_formatter: ResponseFormatter
    ):
        self.agent_adapter = agent_adapter
        self.memory_service = memory_service
        self.response_formatter = response_formatter
    
    async def process_message(
        self, 
        session_id: UUID, 
        message_content: str,
        system_prompt: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate an agent response.
        """
        try:
            # Build context
            context = self.memory_service.build_context(
                session_id=session_id,
                system_prompt=system_prompt,
                user_info=user_info,
                additional_context=additional_context
            )
            
            # Add the current message
            context["current_message"] = message_content
            
            # Call the agent
            agent_response = await self.agent_adapter.generate_response(context)
            
            # Format the response
            formatted_response = self.response_formatter.format_response(agent_response)
            
            return formatted_response
        except Exception as e:
            # Error handling
            raise Exception(f"Failed to process message: {str(e)}")
    
    # Additional methods
```

### File Handling

#### File Adapter (`adapters/file_adapter.py`)

This adapter manages file storage operations:

- Handles file uploads and downloads
- Generates unique filenames
- Provides consistent file access interface
- Can be extended for cloud storage options

```python
class FileAdapter:
    """
    Utility class to handle file operations for chat attachments.
    """
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self._ensure_directory_exists()
    
    def save_file(self, file_content: BinaryIO, original_filename: str) -> str:
        """
        Save a file to the file system with a unique name.
        """
        # Generate unique filename
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create full path
        file_path = self.base_path / unique_filename
        
        # Write file
        with open(file_path, "wb") as f:
            content = file_content.read()
            f.write(content)
        
        return unique_filename
    
    # Additional methods
```

#### File Service (`services/file_service.py`)

This service coordinates file operations:

- Uses the File Adapter for storage operations
- Manages file metadata in the database
- Creates associations between files and messages/artifacts
- Handles file deletion and cleanup

```python
class FileService:
    """
    Service for handling file operations.
    """
    
    def __init__(self, db_session: Session, file_adapter: FileAdapter):
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
        """
        try:
            # Determine file type if not provided
            if not file_type:
                file_type, _ = mimetypes.guess_type(filename)
                if not file_type:
                    file_type = "application/octet-stream"
            
            # Save the file
            stored_filename = self.file_adapter.save_file(file_content, filename)
            
            # Create metadata
            file_metadata = {
                "original_filename": filename,
                "stored_filename": stored_filename,
                "file_type": file_type,
                "file_size": os.path.getsize(self.file_adapter.get_file_path(stored_filename)),
                "upload_date": datetime.utcnow().isoformat()
            }
            metadata = {**(metadata or {}), **file_metadata}
            
            # Create artifact in database
            artifact = ArtifactModel(
                id=uuid4(),
                message_id=message_id,
                type="file",
                content=stored_filename,
                title=filename,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            
            self.db.add(artifact)
            self.db.commit()
            self.db.refresh(artifact)
            
            return artifact
        except Exception as e:
            # Error handling
            self.db.rollback()
            raise Exception(f"Failed to save file: {str(e)}")
    
    # Additional methods
```

### Authentication & Authorization

#### Auth Module (`auth/`)

This module handles user authentication and security:

- **JWT Handler**: Token generation, validation, and refresh
- **Security**: Password hashing and validation
- **Dependencies**: FastAPI dependency functions for route protection

```python
# Sample JWT handler
class JWTHandler:
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        # Token generation logic
        pass
    
    def verify_token(token: str):
        # Token validation logic
        pass

# Sample security functions
def get_password_hash(password: str) -> str:
    # Password hashing
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Password verification
    pass
```

#### Auth Service (`services/auth_service.py`)

This service handles user authentication logic:

- User registration and validation
- Login and token generation
- Password reset procedures
- Session management

```python
class AuthService:
    """
    Service for user authentication.
    """
    
    def __init__(self, db_session: Session, jwt_handler: JWTHandler):
        self.db = db_session
        self.jwt_handler = jwt_handler
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserModel]:
        """
        Authenticate a user by username and password.
        """
        try:
            # Find user
            user = self.db.query(UserModel).filter(UserModel.username == username).first()
            if not user:
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                return None
            
            return user
        except Exception as e:
            # Error handling
            return None
    
    def create_tokens(self, user_id: UUID) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user.
        """
        try:
            # Create access token
            access_token = self.jwt_handler.create_access_token(
                data={"sub": str(user_id)}
            )
            
            # Create refresh token
            refresh_token = self.jwt_handler.create_refresh_token(
                data={"sub": str(user_id)}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            # Error handling
            raise Exception(f"Failed to create tokens: {str(e)}")
    
    # Additional methods
```

### Routes and API Endpoints

The routes modules define the API endpoints using FastAPI:

- **Auth Routes**: User registration, login, token refresh
- **Session Routes**: Create, list, update, delete chat sessions
- **Message Routes**: Send and receive chat messages
- **File Routes**: Upload and download files
- **Agent Routes**: Execute tools and provide feedback

```python
# Example route
@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def create_message(
    session_id: UUID,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    message_service: MessageService = Depends(get_message_service),
    session_service: SessionService = Depends(get_session_service),
    agent_service: AgentService = Depends(get_agent_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new user message and generate an assistant response.
    """
    try:
        # Check session ownership
        session = session_service.get_session(session_id=session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create user message
        user_message = message_service.create_user_message(
            session_id=session_id,
            content=message_data.content,
            user_id=user_id,
            metadata=message_data.metadata
        )
        
        # Generate assistant response in background
        background_tasks.add_task(
            generate_assistant_response,
            session_id=session_id,
            user_message=user_message,
            message_service=message_service,
            agent_service=agent_service
        )
        
        return user_message
    except Exception as e:
        # Error handling
        raise HTTPException(status_code=500, detail=str(e))
```

## Memory Management Strategy (Hybrid Approach)

The Chat API uses a hybrid approach to memory management:

### Primary Storage (SQLite via SQLAlchemy)
All persistent data required for the chat functionality is stored in SQLite:
- User accounts and profiles
- Chat sessions and their metadata
- Messages and their content
- Artifacts and file references

This ensures reliable, structured storage with clear relationships between entities.

### Agent Context (MongoDB via Memory System)
For agent context and knowledge, the system uses the existing memory system's Long-term Memory tier:
- Stores formatted conversation content for agent context
- Maintains references to important artifacts and insights
- Provides the agents with necessary historical context

### Synchronization Mechanism
The system maintains consistency between these two storage systems:
1. When a message is created:
   - First stored in SQLite (primary source of truth)
   - Then relevant context is extracted and stored in Long-term Memory
   - Both operations are coordinated by the Memory Service

2. When context is needed:
   - Primary message data is retrieved from SQLite
   - Additional context is fetched from Long-term Memory
   - The Context Builder combines these into a comprehensive context object

3. Error handling:
   - If SQLite storage succeeds but Long-term Memory fails, the operation continues (degraded context, but chat functionality maintained)
   - If SQLite storage fails, the entire operation fails (essential data preservation)

## Context Building Process

The context building process is crucial for agent operation:

1. **Retrieve Messages from SQLite**:
   - Get recent conversation history
   - Include metadata, references, and relationships

2. **Enrich with Long-term Memory**:
   - Fetch relevant context from Long-term Memory
   - Include any insights or patterns identified by agents

3. **Structure Based on Agent Type**:
   - Format context differently depending on the target agent
   - Include agent-specific data elements

4. **Add Current Operation Context**:
   - Add details about the current operation
   - Include any user-provided context

5. **Format for Agent Consumption**:
   - Transform into the structure expected by the agent system
   - Ensure compatibility with the agent's input requirements

This process ensures that agents have the context they need while maintaining the separation between the Chat API's persistence needs and the agent system's memory architecture.

## Error Handling and Resilience

The system includes robust error handling:

- **Graceful Degradation**: If non-critical components fail, the system continues with reduced functionality
- **Transaction Management**: Database operations use transactions to ensure consistency
- **Error Logging**: Comprehensive logging throughout the system
- **User Feedback**: Clear error messages for client applications

## API Documentation

The API is documented using OpenAPI (Swagger):
- Available at the `/docs` endpoint
- Includes all routes, request/response models, and authentication requirements
- Provides examples for common operations

## Conclusion

The Chat API module provides a RESTful interface to the VITA platform's agent system, with a clean separation of concerns and a hybrid storage approach. By storing chat data in SQLite and leveraging the existing memory system for agent context, it achieves both reliable persistence for chat functionality and seamless integration with the agent system.