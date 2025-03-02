# Chat API Endpoints

Here's a comprehensive list of all the API endpoints available in the Chat API:

## Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/token` - Log in and obtain access tokens
- `GET /api/v1/auth/me` - Get current user information
- `PUT /api/v1/auth/me` - Update current user information

## Sessions
- `POST /api/v1/sessions` - Create a new chat session
- `GET /api/v1/sessions` - List all sessions for the current user
- `GET /api/v1/sessions/{session_id}` - Get details of a specific session
- `PUT /api/v1/sessions/{session_id}` - Update a session
- `DELETE /api/v1/sessions/{session_id}` - Delete a session
- `POST /api/v1/sessions/{session_id}/archive` - Archive a session

## Messages
- `POST /api/v1/sessions/{session_id}/messages` - Send a new message
- `GET /api/v1/sessions/{session_id}/messages` - Get all messages in a session
- `GET /api/v1/sessions/{session_id}/messages/{message_id}` - Get a specific message
- `DELETE /api/v1/sessions/{session_id}/messages/{message_id}` - Delete a message
- `POST /api/v1/sessions/{session_id}/messages/{message_id}/feedback` - Add feedback to a message

## Files
- `POST /api/v1/files/sessions/{session_id}/messages/{message_id}/upload` - Upload a file attachment
- `GET /api/v1/files/{artifact_id}` - Download a file by artifact ID
- `DELETE /api/v1/files/{artifact_id}` - Delete a file by artifact ID
- `GET /api/v1/files/messages/{message_id}` - Get all files for a message

## Artifacts
- `GET /api/v1/artifacts/{artifact_id}` - Get artifact content
- `PUT /api/v1/artifacts/{artifact_id}` - Update an artifact

## Agent Operations
- `POST /api/v1/agent/feedback/{session_id}/{message_id}` - Submit feedback for an agent response
- `POST /api/v1/agent/tools/{session_id}` - Execute an agent tool
- `GET /api/v1/agent/report/{session_id}` - Generate a report for a session
- `GET /api/v1/agent/types` - Get a list of available agent types

## Utility Endpoints
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

These endpoints provide a complete set of features for interacting with specialized AI agents through a chat interface, managing sessions, messages, files, and leveraging agent-specific capabilities.