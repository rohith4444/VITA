# Chat API Usage Guide

This guide provides practical instructions for using the Chat API to interact with specialized AI agents (Project Manager, Solution Architect, Full Stack Developer, and QA/Test).

## Getting Started

### 1. Server Setup

Start the API server:

```bash
python main.py
```

By default, the server runs on `http://localhost:8000`, but this can be configured in the `.env` file.

### 2. API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These provide a complete reference for all endpoints, request/response schemas, and authentication requirements.

## Authentication Flow

### 1. Register a User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "johnsmith",
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johnsmith",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00"
}
```

### 2. Log In and Get Access Token

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=johnsmith&password=SecurePassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use the Access Token

For all subsequent requests, include the access token in the Authorization header:

```http
GET /api/v1/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Working with Chat Sessions

### 1. Create a New Chat Session

```http
POST /api/v1/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "My Project Discussion",
  "session_type": "developer",
  "primary_agent": "solution_architect",
  "settings": {
    "preferred_language": "en",
    "temperature": 0.5,
    "verbose_mode": true
  },
  "metadata": {
    "project_id": "12345",
    "topic": "API Design"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2023-01-01T00:00:00",
  "data": {
    "session_id": "987e6543-e21b-43d3-b654-426614174000",
    "title": "My Project Discussion",
    "status": "active",
    "session_type": "developer",
    "primary_agent": "solution_architect",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "message_count": 0,
    "settings": {
      "preferred_language": "en",
      "temperature": 0.5,
      "verbose_mode": true
    },
    "metadata": {
      "project_id": "12345",
      "topic": "API Design"
    }
  },
  "error": null
}
```

### 2. List All Sessions

```http
GET /api/v1/sessions?skip=0&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "items": [
    {
      "session_id": "987e6543-e21b-43d3-b654-426614174000",
      "title": "My Project Discussion",
      "status": "active",
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "message_count": 0
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

### 3. Get Session Details

```http
GET /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Update a Session

```http
PUT /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "Updated Project Discussion",
  "primary_agent": "full_stack_developer"
}
```

### 5. Archive a Session

```http
POST /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000/archive
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 6. Delete a Session

```http
DELETE /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Chat Conversation Flow

### 1. Send a Message

```http
POST /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "I need to design a REST API for a task management system.",
  "role": "user",
  "type": "text",
  "metadata": {
    "source": "web_client",
    "client_id": "browser123"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2023-01-01T00:01:00",
  "data": {
    "message_id": "123e4567-e89b-12d3-a456-426614174000",
    "session_id": "987e6543-e21b-43d3-b654-426614174000",
    "created_at": "2023-01-01T00:01:00",
    "role": "user",
    "type": "text",
    "content": "I need to design a REST API for a task management system.",
    "files": [],
    "artifacts": [],
    "metadata": {
      "source": "web_client",
      "client_id": "browser123"
    }
  },
  "error": null
}
```

The agent response will be generated asynchronously. To retrieve it, you need to fetch messages.

### 2. Get Messages in a Session

```http
GET /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000/messages?skip=0&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2023-01-01T00:02:00",
  "data": {
    "messages": [
      {
        "message_id": "123e4567-e89b-12d3-a456-426614174000",
        "session_id": "987e6543-e21b-43d3-b654-426614174000",
        "created_at": "2023-01-01T00:01:00",
        "role": "user",
        "type": "text",
        "content": "I need to design a REST API for a task management system.",
        "files": [],
        "artifacts": [],
        "metadata": {
          "source": "web_client",
          "client_id": "browser123"
        }
      },
      {
        "message_id": "234e5678-e89b-12d3-a456-426614174000",
        "session_id": "987e6543-e21b-43d3-b654-426614174000",
        "created_at": "2023-01-01T00:01:30",
        "role": "assistant",
        "type": "text",
        "content": "I'd be happy to help you design a REST API for a task management system. Let's start by identifying the key resources and operations we'll need...",
        "files": [],
        "artifacts": [
          {
            "artifact_id": "345e6789-e89b-12d3-a456-426614174000",
            "title": "Task Management API Design",
            "type": "application/vnd.ant.code",
            "created_at": "2023-01-01T00:01:30",
            "content_preview": "# Task Management API\n\n## Resources\n\n- Users\n- Tasks\n- Projects\n..."
          }
        ],
        "metadata": {
          "agent_type": "solution_architect",
          "confidence": 0.95,
          "processing_time": 1.2
        }
      }
    ],
    "total": 2
  },
  "error": null
}
```

### 3. Get a Specific Message

```http
GET /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000/messages/234e5678-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Delete a Message

```http
DELETE /api/v1/sessions/987e6543-e21b-43d3-b654-426614174000/messages/234e5678-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Working with Artifacts

### 1. View Artifact Content

Get the full content of an artifact:

```http
GET /api/v1/artifacts/345e6789-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Update an Artifact

```http
PUT /api/v1/artifacts/345e6789-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "Updated Task Management API Design",
  "content": "# Revised Task Management API\n\n## Resources\n\n- Users\n- Tasks\n- Projects\n- Tags\n..."
}
```

## File Handling

### 1. Upload a File to a Message

```http
POST /api/v1/files/sessions/987e6543-e21b-43d3-b654-426614174000/messages/123e4567-e89b-12d3-a456-426614174000/upload
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data

file=@/path/to/requirements.pdf
```

**Response:**
```json
{
  "artifact_id": "456f7890-e89b-12d3-a456-426614174000",
  "session_id": "987e6543-e21b-43d3-b654-426614174000",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2023-01-01T00:05:00",
  "updated_at": "2023-01-01T00:05:00",
  "type": "file",
  "title": "requirements.pdf",
  "content_preview": null,
  "metadata": {
    "original_filename": "requirements.pdf",
    "file_type": "application/pdf",
    "file_size": 52428
  }
}
```

### 2. Download a File

```http
GET /api/v1/files/456f7890-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

This will return the file content with appropriate content type and disposition headers.

### 3. Get Files for a Message

```http
GET /api/v1/files/messages/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Delete a File

```http
DELETE /api/v1/files/456f7890-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Agent-Specific Operations

### 1. Get Available Agent Types

```http
GET /api/v1/agent/types
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "agent_types": {
      "project_manager": "Manages project planning and coordination",
      "solution_architect": "Designs system architecture and technical specifications",
      "full_stack_developer": "Implements frontend and backend components",
      "qa_test": "Creates test plans and validates implementation"
    }
  }
}
```

### 2. Execute an Agent Tool

```http
POST /api/v1/agent/tools/987e6543-e21b-43d3-b654-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "generate_task_breakdown",
  "params": {
    "project_name": "Task Management API",
    "deadline": "2023-12-31",
    "complexity": "medium"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "tool_name": "generate_task_breakdown",
  "result": {
    "tasks": [
      {
        "id": "T1",
        "name": "Define API Requirements",
        "estimated_hours": 8,
        "dependencies": []
      },
      {
        "id": "T2",
        "name": "Design Database Schema",
        "estimated_hours": 10,
        "dependencies": ["T1"]
      },
      ...
    ],
    "total_estimated_hours": 120,
    "critical_path": ["T1", "T2", "T5", "T8", "T12"]
  }
}
```

### 3. Provide Feedback on Agent Response

```http
POST /api/v1/agent/feedback/987e6543-e21b-43d3-b654-426614174000/234e5678-e89b-12d3-a456-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "type": "rating",
  "value": 4,
  "comment": "Good response but missed some edge cases."
}
```

### 4. Generate a Report

```http
GET /api/v1/agent/report/987e6543-e21b-43d3-b654-426614174000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "session_id": "987e6543-e21b-43d3-b654-426614174000",
  "report": {
    "title": "Project Report: Task Management API",
    "generated_at": "2023-01-02T12:00:00",
    "summary": "This report summarizes the design and implementation plan for the Task Management API...",
    "requirements": [...],
    "architecture": [...],
    "implementation_plan": [...],
    "artifacts": [...]
  }
}
```

## Error Handling

All endpoints return standardized error responses when issues occur:

```json
{
  "status": "error",
  "timestamp": "2023-01-01T00:00:00",
  "data": null,
  "error": {
    "code": "not_found",
    "message": "Session not found",
    "details": {
      "session_id": "987e6543-e21b-43d3-b654-426614174000"
    }
  }
}
```

Common error codes include:
- `validation_error`: Invalid input data
- `not_found`: Requested resource not found
- `permission_denied`: Not authorized to access resource
- `session_limit_exceeded`: Reached maximum message limit
- `tool_execution_failed`: Agent tool execution error

## Websocket Connection (Optional)

For real-time updates, you can connect to the websocket endpoint:

```
ws://localhost:8000/api/v1/ws/sessions/987e6543-e21b-43d3-b654-426614174000
```

Include the token in the connection query parameters:
```
?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Messages received through the websocket will follow this format:

```json
{
  "event": "message_created",
  "data": {
    "message_id": "234e5678-e89b-12d3-a456-426614174000",
    "session_id": "987e6543-e21b-43d3-b654-426614174000",
    "role": "assistant",
    "content": "...",
    "created_at": "2023-01-01T00:01:30"
  }
}
```

## Client SDK Examples

### JavaScript/TypeScript

```typescript
import axios from 'axios';

// Configure API client
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000
});

// Set authentication token
function setAuthToken(token) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// Login
async function login(username, password) {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await apiClient.post('/auth/token', formData);
  const { access_token } = response.data;
  
  setAuthToken(access_token);
  return access_token;
}

// Create a session
async function createSession(title, agentType) {
  const response = await apiClient.post('/sessions', {
    title,
    primary_agent: agentType
  });
  
  return response.data.data;
}

// Send a message
async function sendMessage(sessionId, content) {
  const response = await apiClient.post(`/sessions/${sessionId}/messages`, {
    content,
    role: 'user',
    type: 'text'
  });
  
  return response.data.data;
}

// Get all messages for a session
async function getMessages(sessionId) {
  const response = await apiClient.get(`/sessions/${sessionId}/messages`);
  return response.data.data.messages;
}

// Example usage
async function chatWithAgent() {
  // Login
  await login('johnsmith', 'SecurePassword123');
  
  // Create session
  const session = await createSession('API Design Discussion', 'solution_architect');
  
  // Send a message
  await sendMessage(session.session_id, 'I need to design a REST API for a task management system.');
  
  // Wait a moment for the agent to respond
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  // Get messages including the agent's response
  const messages = await getMessages(session.session_id);
  console.log(messages);
}

chatWithAgent().catch(console.error);
```

### Python

```python
import requests
import time

class ChatAPIClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login(self, username, password):
        response = self.session.post(
            f"{self.base_url}/auth/token",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        token_data = response.json()
        self.session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        return token_data
    
    def create_session(self, title, agent_type="solution_architect"):
        response = self.session.post(
            f"{self.base_url}/sessions",
            json={"title": title, "primary_agent": agent_type}
        )
        response.raise_for_status()
        return response.json()["data"]
    
    def send_message(self, session_id, content):
        response = self.session.post(
            f"{self.base_url}/sessions/{session_id}/messages",
            json={"content": content, "role": "user", "type": "text"}
        )
        response.raise_for_status()
        return response.json()["data"]
    
    def get_messages(self, session_id):
        response = self.session.get(
            f"{self.base_url}/sessions/{session_id}/messages"
        )
        response.raise_for_status()
        return response.json()["data"]["messages"]

# Example usage
client = ChatAPIClient()
client.login("johnsmith", "SecurePassword123")

# Create a session
session = client.create_session("API Design Chat", "solution_architect")
session_id = session["session_id"]

# Send a message
client.send_message(session_id, "I need to design a REST API for a task management system.")

# Wait for agent response
time.sleep(3)

# Get all messages
messages = client.get_messages(session_id)
for msg in messages:
    print(f"[{msg['role']}] {msg['content'][:100]}...")
    if msg['artifacts']:
        print(f"  Artifacts: {len(msg['artifacts'])}")
```

## Recommended Workflow

For a typical project, here's a recommended workflow:

1. **Project Setup**: Create a session with the Project Manager agent to define project scope and requirements.

2. **Architecture Design**: Create a session with the Solution Architect agent to design the system architecture.

3. **Implementation**: Create a session with the Full Stack Developer agent to implement components based on the architecture.

4. **Testing**: Create a session with the QA/Test agent to develop test plans and validate the implementation.

5. **Cross-agent Collaboration**: Reference artifacts from previous sessions when starting a new session with a different agent type.

This workflow leverages the specialized capabilities of each agent type while maintaining continuity throughout the project lifecycle.