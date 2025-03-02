# Chat API Endpoints Reference

This document provides a comprehensive reference of all endpoints available in the Chat API, organized by functional area.

## Base URL

All endpoints are prefixed with the API version:

```
/api/v1
```

## Authentication Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/auth/register` | Register a new user | `{ username, email, password }` | User object |
| `POST` | `/auth/token` | Log in and obtain access tokens | Form data: `username`, `password` | `{ access_token, refresh_token, token_type }` |
| `GET` | `/auth/me` | Get current user information | - | User object |
| `PUT` | `/auth/me` | Update current user information | `{ username?, email?, password? }` | Updated user object |

## Session Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/sessions` | Create a new chat session | `{ title?, session_type?, primary_agent?, settings?, metadata? }` | Session object |
| `GET` | `/sessions` | List all sessions for the current user | Query params: `skip`, `limit` | List of session objects |
| `GET` | `/sessions/{session_id}` | Get details of a specific session | - | Session object |
| `PUT` | `/sessions/{session_id}` | Update a session | `{ title?, status?, primary_agent?, settings?, metadata? }` | Updated session object |
| `DELETE` | `/sessions/{session_id}` | Delete a session | - | No content |
| `POST` | `/sessions/{session_id}/archive` | Archive a session | - | Updated session object |

## Message Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/sessions/{session_id}/messages` | Send a new message | `{ content, role?, type?, files?, parent_message_id?, metadata? }` | Message object |
| `GET` | `/sessions/{session_id}/messages` | Get all messages in a session | Query params: `skip`, `limit` | List of message objects |
| `GET` | `/sessions/{session_id}/messages/{message_id}` | Get a specific message | - | Message object |
| `DELETE` | `/sessions/{session_id}/messages/{message_id}` | Delete a message | - | No content |
| `POST` | `/sessions/{session_id}/messages/{message_id}/feedback` | Add feedback to a message | `{ type, value?, comment? }` | Feedback status |

## File Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/files/sessions/{session_id}/messages/{message_id}/upload` | Upload a file attachment | Form data: `file` | Artifact object |
| `GET` | `/files/{artifact_id}` | Download a file by artifact ID | - | File content |
| `DELETE` | `/files/{artifact_id}` | Delete a file by artifact ID | - | No content |
| `GET` | `/files/messages/{message_id}` | Get all files for a message | - | List of artifact objects |

## Artifact Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/artifacts/{artifact_id}` | Get artifact content | - | Artifact object with full content |
| `PUT` | `/artifacts/{artifact_id}` | Update an artifact | `{ title?, content?, language?, metadata? }` | Updated artifact object |

## Agent Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/agent/feedback/{session_id}/{message_id}` | Submit feedback for an agent response | `{ type, value?, comment? }` | Feedback status |
| `POST` | `/agent/tools/{session_id}` | Execute an agent tool | `{ name, params }` | Tool execution result |
| `GET` | `/agent/report/{session_id}` | Generate a report for a session | - | Generated report |
| `GET` | `/agent/types` | Get a list of available agent types | - | Map of agent types to descriptions |

## Utility Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/` | Root endpoint with API information | - | API info |
| `GET` | `/health` | Health check endpoint | - | Status |
| `GET` | `/docs` | Swagger UI documentation | - | Interactive docs UI |
| `GET` | `/redoc` | ReDoc documentation | - | Alternative docs UI |

## Common Parameters

### Query Parameters

- `skip`: Number of items to skip (pagination)
- `limit`: Maximum number of items to return (pagination)

### Path Parameters

- `session_id`: UUID of the chat session
- `message_id`: UUID of the message
- `artifact_id`: UUID of the artifact or file

## Authentication

All endpoints (except authentication endpoints and documentation) require an `Authorization` header with a valid JWT token:

```
Authorization: Bearer {your_access_token}
```

## Error Responses

All endpoints return standardized error responses with the following structure:

```json
{
  "status": "error",
  "timestamp": "2023-01-01T00:00:00",
  "data": null,
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

## Common Error Codes

| Error Code | Description |
|------------|-------------|
| `validation_error` | Invalid input data |
| `not_found` | Requested resource not found |
| `permission_denied` | Not authorized to access resource |
| `session_limit_exceeded` | Reached maximum message limit |
| `tool_execution_failed` | Agent tool execution error |
| `file_too_large` | Uploaded file exceeds maximum size |
| `invalid_file_type` | Unsupported file type |

## Data Types

### Session Status

- `active`: Active session
- `inactive`: Inactive session
- `archived`: Archived session
- `error`: Session in error state

### Session Types

- `standard`: Standard chat session
- `developer`: Developer-focused session
- `research`: Research-focused session

### Agent Types

- `project_manager`: Project planning and coordination
- `solution_architect`: System architecture and technical specifications
- `full_stack_developer`: Frontend and backend implementation
- `qa_test`: Test planning and validation

### Message Roles

- `user`: User message
- `assistant`: AI assistant message
- `system`: System message

### Message Types

- `text`: Text message
- `file`: File message
- `artifact`: Artifact message
- `error`: Error message
- `notification`: Notification message

### Artifact Types

- `application/vnd.ant.code`: Code snippet
- `text/markdown`: Markdown document
- `text/html`: HTML content
- `image/svg+xml`: SVG image
- `application/vnd.ant.mermaid`: Mermaid diagram
- `application/vnd.ant.react`: React component