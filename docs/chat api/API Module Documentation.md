# Chat API Module Documentation

This document provides an overview of the Chat API module, its components, and their functionality.

## Starting Point

### main.py
Main application entry point that initializes the FastAPI app, registers routes, and configures middleware.

**Methods and Functions:**
- `validation_exception_handler(request, exc)` - Handles validation errors
- `http_exception_handler(request, exc)` - Handles HTTP exceptions
- `general_exception_handler(request, exc)` - Handles general exceptions
- `root()` - Root endpoint
- `health_check()` - Health check endpoint

### config.py
Configuration settings for the Chat API module, loaded from environment variables.

**Classes:**
- `ChatAPISettings` - Configuration class with settings for API, server, sessions, memory, security and database

## Database

### database.py
Establishes connections to both storage systems (SQLite via SQLAlchemy and MongoDB via memory system).

**Functions:**
- `get_db()` - FastAPI dependency to provide a database session
- `get_memory_manager()` - Get the memory manager instance for the MongoDB-based memory system

## Adapters
Interfaces to connect with external systems.

### adapters/agent_adapter.py
Interface between the Chat API and the agent system.

**Classes:**
- `AgentAdapter` - Adapter for the existing agent system

**Methods:**
- `create_agent(session_id, agent_type, name)` - Create a new agent instance
- `run_agent(session_id, input_data)` - Run an agent with input data
- `generate_response(context)` - Generate a response from the appropriate agent
- `generate_title(first_message)` - Generate a title based on first message
- `process_feedback(context)` - Process user feedback on a response
- `execute_tool(context)` - Execute a tool via the agent
- `generate_report(session_id)` - Generate a comprehensive report
- `get_agent_instance(session_id)` - Get the active agent instance
- `get_agent_types()` - Get available agent types with descriptions
- `cleanup_agent(session_id)` - Clean up resources for an agent
- `cleanup_all_agents()` - Clean up resources for all active agents

### adapters/file_adapter.py
Handles file storage operations.

**Classes:**
- `FileAdapter` - Utility class for file operations

**Methods:**
- `_ensure_directory_exists()` - Ensure the upload directory exists
- `save_file(file_content, original_filename)` - Save a file with a unique name
- `get_file_path(filename)` - Get the full path for a stored file
- `delete_file(filename)` - Delete a file from the file system
- `file_exists(filename)` - Check if a file exists
- `read_file(filename)` - Read a file from the file system

### adapters/memory_adapter.py
Connection to the existing memory system with focus on Long-term Memory.

**Classes:**
- `MemoryAdapter` - Adapter for the existing memory system

**Methods:**
- `store_short_term(agent_id, content, metadata)` - Store content in short-term memory
- `store_working(agent_id, content, metadata)` - Store content in working memory
- `store_long_term(agent_id, content, metadata, importance)` - Store content in long-term memory
- `retrieve_short_term(agent_id, query)` - Retrieve content from short-term memory
- `retrieve_working(agent_id, query)` - Retrieve content from working memory
- `retrieve_long_term(agent_id, query, sort_by, limit)` - Retrieve content from long-term memory
- `search_long_term(agent_id, keywords, content_type, limit)` - Search long-term memory
- `update_long_term(agent_id, memory_id, update_data, importance)` - Update a memory entry
- `initialize_session_memory(session_id, agent_id)` - Initialize memory for a new session
- `cleanup()` - Clean up memory resources
- `_format_memory_entry(entry)` - Format a MemoryEntry as a dictionary

## Authentication
Components related to user authentication and authorization.

### auth/dependencies.py
FastAPI dependencies for authentication.

**Functions:**
- `get_current_user(token, db)` - Get the authenticated user from token
- `get_current_user_id(current_user)` - Get just the current user's ID
- `get_current_admin_user(current_user)` - Verify the current user is an admin

### auth/jwt_handler.py
JWT token generation and validation.

**Functions:**
- `create_access_token(data, expires_delta)` - Create a JWT access token
- `create_refresh_token(data)` - Create a JWT refresh token with longer expiration
- `verify_token(token)` - Verify a JWT token and extract its payload

### auth/security.py
Password hashing and verification.

**Functions:**
- `get_password_hash(password)` - Hash a password for storage
- `verify_password(plain_password, hashed_password)` - Verify a password against a hash

## Migrations
Database migration files.

### migrations/env.py
Alembic environment configuration for database migrations.

**Functions:**
- `run_migrations_offline()` - Run migrations in 'offline' mode
- `run_migrations_online()` - Run migrations in 'online' mode

## Models
SQLAlchemy models defining the database schema.

### models/artifact.py
SQLAlchemy model for artifacts (generated content like code, diagrams).

**Classes:**
- `ArtifactModel` - SQLAlchemy model for artifacts

### models/message.py
SQLAlchemy model for chat messages.

**Classes:**
- `MessageModel` - SQLAlchemy model for messages

### models/response.py
Pydantic models for API responses.

**Classes:**
- `ResponseStatus` - Enum for API response statuses
- `ErrorDetail` - Model for detailed error information
- `APIResponse` - Base model for all API responses
- `SessionResponse` - Response model for session operations
- `MessageResponse` - Response model for message operations
- `MessageListResponse` - Response model for listing multiple messages
- `ErrorResponse` - Response model for error situations

### models/session.py
SQLAlchemy model for chat sessions.

**Classes:**
- `SessionModel` - SQLAlchemy model for chat sessions

### models/user.py
SQLAlchemy model for users.

**Classes:**
- `UserModel` - SQLAlchemy model for users

## Routes
API endpoints definitions.

### routes/agent_routes.py
Routes for agent-specific operations.

**Functions:**
- `get_agent_service()` - FastAPI dependency for the agent service
- `get_session_service(db)` - FastAPI dependency for the session service
- `submit_feedback(session_id, message_id, feedback, agent_service, session_service, user_id)` - Submit feedback for an agent response
- `execute_tool(session_id, tool_request, agent_service, session_service, user_id)` - Execute an agent tool
- `generate_report(session_id, agent_service, session_service, user_id)` - Generate a comprehensive report
- `get_agent_types(agent_service, user_id)` - Get a list of available agent types

### routes/auth_routes.py
Routes for authentication operations.

**Functions:**
- `get_auth_service(db)` - FastAPI dependency for the auth service
- `register_user(user_data, auth_service)` - Register a new user
- `login_for_access_token(form_data, auth_service)` - Authenticate user and provide access token
- `read_users_me(current_user)` - Get current authenticated user
- `update_user_me(user_data, current_user_id, auth_service)` - Update current user's information

### routes/file_routes.py
Routes for file operations.

**Functions:**
- `get_file_service(db)` - FastAPI dependency for the file service
- `get_session_service(db)` - FastAPI dependency for the session service
- `get_message_service(db)` - FastAPI dependency for the message service
- `upload_file(session_id, message_id, file, file_service, session_service, message_service, user_id)` - Upload a file attachment
- `download_file(artifact_id, file_service, user_id)` - Download a file by artifact ID
- `delete_file(artifact_id, file_service, user_id)` - Delete a file by artifact ID
- `get_message_files(message_id, file_service, message_service, user_id)` - Get all files for a message
- `is_valid_content_type(content_type)` - Validate that a file content type is allowed

### routes/message_routes.py
Routes for chat message operations.

**Functions:**
- `get_message_service(db)` - FastAPI dependency for the message service
- `get_session_service(db)` - FastAPI dependency for the session service
- `get_agent_service()` - FastAPI dependency for the agent service
- `get_messages(session_id, skip, limit, message_service, session_service, user_id)` - Get all messages for a session
- `create_message(session_id, message_data, background_tasks, message_service, session_service, agent_service, user_id)` - Create a new user message
- `get_message(session_id, message_id, message_service, session_service, user_id)` - Get a specific message
- `delete_message(session_id, message_id, message_service, session_service, user_id)` - Delete a message
- `add_message_feedback(session_id, message_id, feedback_data, message_service, session_service, agent_service, user_id)` - Add feedback to a message
- `generate_assistant_response(session_id, user_message, message_service, agent_service)` - Background task for generating assistant response
- `update_session_title(session_id, message_content, session_service, agent_service)` - Background task for updating session title

### routes/session_routes.py
Routes for session management.

**Functions:**
- `get_session_service(db)` - FastAPI dependency for the session service
- `create_session(session_data, service, user_id)` - Create a new chat session
- `get_user_sessions(skip, limit, service, user_id)` - Get all sessions for the current user
- `get_session(session_id, service, user_id)` - Get a specific session
- `update_session(session_id, session_data, service, user_id)` - Update a session
- `delete_session(session_id, service, user_id)` - Delete a session
- `archive_session(session_id, service, user_id)` - Archive a session

## Schemas
Pydantic models for request/response validation.

### schemas/artifact_schemas.py
Schemas for artifacts data.

**Classes:**
- `ArtifactType` - Enum for possible artifact types
- `Artifact` - Model representing an artifact
- `ArtifactCreate` - Model for creating a new artifact
- `ArtifactUpdate` - Model for updating an existing artifact
- `ArtifactResponse` - Model for artifact responses

### schemas/message_schemas.py
Schemas for chat messages.

**Classes:**
- `MessageRole` - Enum for possible message roles
- `MessageType` - Enum for possible message types
- `FileReference` - Model for file references within messages
- `ArtifactReference` - Model for artifact references within messages
- `Message` - Model representing a chat message
- `MessageCreate` - Model for creating a new message
- `ResponseCreate` - Model for creating an assistant response

### schemas/response_schemas.py
Schemas for API responses.

**Classes:**
- `ResponseStatus` - Enum for API response statuses
- `ErrorDetail` - Model for detailed error information
- `APIResponse` - Base model for all API responses
- `SessionResponse` - Response model for session operations
- `MessageResponse` - Response model for message operations
- `MessageListResponse` - Response model for listing multiple messages
- `ErrorResponse` - Response model for error situations

### schemas/session_schemas.py
Schemas for chat sessions.

**Classes:**
- `SessionStatus` - Enum for possible session statuses
- `SessionType` - Enum for possible session types
- `AgentType` - Enum for available agent types
- `UserSettings` - Model for user-specific settings within a session
- `Session` - Model representing a chat session
- `SessionCreate` - Model for creating a new session
- `SessionUpdate` - Model for session updates

### schemas/user_schemas.py
Schemas for user data.

**Classes:**
- `UserBase` - Base user schema with common attributes
- `UserCreate` - Schema for creating a new user
- `UserUpdate` - Schema for updating user information
- `UserInDB` - Schema for user information from database
- `UserResponse` - Schema for user response to clients
- `Token` - Schema for authentication token
- `TokenData` - Schema for token payload

## Services
Business logic implementation.

### services/agent_service.py
Service for interacting with the agent system.

**Classes:**
- `AgentService` - Service for agent operations

**Methods:**
- `process_message(session_id, message_content, system_prompt, user_info, additional_context)` - Process a user message
- `generate_title(session_id, first_message)` - Generate a title for a chat session
- `process_feedback(session_id, message_id, feedback)` - Process user feedback
- `execute_tool(session_id, tool_name, tool_params)` - Execute a tool via the agent
- `get_agent_types()` - Get available agent types
- `generate_report(session_id)` - Generate a comprehensive report
- `cleanup_session_agents(session_id)` - Clean up agent resources

### services/auth_service.py
Service for user authentication operations.

**Classes:**
- `AuthService` - Service for user authentication

**Methods:**
- `get_user_by_username(username)` - Get a user by username
- `get_user_by_email(email)` - Get a user by email
- `create_user(username, email, password)` - Create a new user
- `authenticate_user(username, password)` - Authenticate a user
- `create_tokens(user_id)` - Create access and refresh tokens
- `update_user(user_id, username, email, password)` - Update user information

### services/file_service.py
Service for handling file operations.

**Classes:**
- `FileService` - Service for file operations

**Methods:**
- `save_file(session_id, message_id, file_content, filename, file_type, metadata)` - Save a file and create an artifact
- `get_file(artifact_id)` - Get a file by artifact ID
- `delete_file(artifact_id)` - Delete a file by artifact ID
- `get_files_for_message(message_id)` - Get all files for a message

### services/memory_service.py
Service for managing chat memory and context.

**Classes:**
- `MemoryService` - Service for memory operations

**Methods:**
- `add_user_message(session_id, message_content, message_id, metadata)` - Add a user message to memory
- `add_assistant_response(session_id, response_content, response_id, metadata, artifacts)` - Add an assistant response
- `add_artifact(session_id, message_id, artifact_id, artifact_type, title, summary, metadata)` - Add an artifact
- `build_context(session_id, system_prompt, user_info, additional_context)` - Build a context object
- `synchronize_session(session_id)` - Synchronize database records with Long-term Memory
- `clear_session_memory(session_id)` - Clear all memory for a session

### services/message_service.py
Service for managing chat messages with dual storage.

**Classes:**
- `MessageService` - Service for message operations

**Methods:**
- `create_user_message(session_id, content, user_id, metadata)` - Create a new user message
- `create_assistant_response(session_id, content, metadata, artifacts)` - Create a new assistant response
- `get_message(message_id)` - Get a message by ID
- `get_session_messages(session_id, limit, offset)` - Get messages for a session
- `get_artifacts_for_message(message_id)` - Get artifacts for a message
- `delete_message(message_id)` - Delete a message and its artifacts
- `add_message_feedback(message_id, feedback_type, feedback_content, user_id)` - Add feedback to a message

### services/session_service.py
Service for managing chat sessions.

**Classes:**
- `SessionService` - Service for session operations

**Methods:**
- `create_session(user_id, title, session_type, primary_agent, settings, metadata)` - Create a new chat session
- `get_session(session_id)` - Get a session by ID
- `get_user_sessions(user_id, status, limit, offset, include_message_count)` - Get user sessions
- `update_session(session_id, title, status, primary_agent, settings, metadata)` - Update a session
- `delete_session(session_id)` - Delete a session
- `archive_session(session_id)` - Archive a session
- `validate_session_limits(session_id)` - Validate session has not exceeded limits
- `synchronize_session_memory(session_id)` - Synchronize session data between database and memory

## Utilities
Helper components for cross-cutting concerns.

### utils/context_builder.py
Utility for building conversation context from memory for AI agents.

**Classes:**
- `ContextBuilder` - Utility for building agent context

**Methods:**
- `build_context(session_id, message_id, time_window, max_messages, system_prompt, user_info, additional_context)` - Build context
- `_get_conversation_from_db(session_id, time_window, max_messages)` - Get conversation from database
- `_get_conversation_from_memory(session_id, time_window, max_messages)` - Get conversation from memory
- `_get_session_info(session_id)` - Get session information
- `_get_working_state(session_id)` - Get current working state
- `_get_long_term_context(session_id)` - Extract relevant long-term context
- `format_for_agent(context, agent_type)` - Format context for a specific agent type
- `_format_conversation_for_agent(conversation_history)` - Format conversation as text
- `_format_for_project_manager(context)` - Format context for Project Manager
- `_format_for_solution_architect(context)` - Format context for Solution Architect
- `_format_for_developer(context)` - Format context for Developer
- `_format_for_qa_test(context)` - Format context for QA/Test agent

### utils/memory_sync.py
Synchronizes data between SQLAlchemy database and the Memory System.

**Classes:**
- `MemorySynchronizer` - Synchronizer for database and memory system

**Methods:**
- `synchronize_session(session_id, db_session)` - Synchronize all session data
- `_sync_session_metadata(session)` - Synchronize session metadata
- `_sync_message(message, db_session)` - Synchronize a message and its artifacts
- `_sync_artifact(artifact, session_id)` - Synchronize an artifact
- `reconcile_data(session_id, db_session)` - Reconcile data to find discrepancies
- `handle_sync_error(session_id, error_context)` - Handle synchronization errors

### utils/response_formatter.py
Utilities for formatting API responses.

**Functions:**
- `format_session_response(session)` - Format a session object into a response
- `format_message_response(message)` - Format a message object into a response
- `format_message_list_response(messages, total)` - Format a list of messages
- `format_error_response(error_code, message, status_code, details)` - Format an error response
- `format_success_response(data)` - Format a generic success response
- `raise_http_exception(error_code, message, status_code, details)` - Raise an HTTP exception
- `handle_exception(exception, error_code, status_code)` - Handle an exception and format response

### utils/validators.py
Validation utilities for input data.

**Functions:**
- `validate_session_id(session_id)` - Validate a session ID format
- `validate_message_id(message_id)` - Validate a message ID format
- `validate_agent_type(agent_type)` - Validate that an agent type is supported
- `validate_session_status(status)` - Validate that a session status is valid
- `validate_message_role(role)` - Validate that a message role is valid
- `validate_message_type(message_type)` - Validate that a message type is valid
- `validate_message_content(content, message_type)` - Validate message content
- `validate_session_limit(session_message_count)` - Validate session has not exceeded limits
- `validate_metadata(metadata)` - Validate metadata structure and content
- `_is_json_serializable(value)` - Check if a value is JSON serializable