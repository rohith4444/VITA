from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session
from memory.base import MemoryType

from chat_api.adapters.memory_adapter import MemoryAdapter
from chat_api.models.message import MessageModel
from chat_api.models.session import SessionModel
from chat_api.models.artifact import ArtifactModel
from core.logging.logger import setup_logger
from agents.core.monitoring.decorators import monitor_operation
from core.tracing.service import trace_class, trace_method

@trace_class
class MemorySynchronizer:
    """
    Synchronizes data between SQLAlchemy database and the Memory System.
    Ensures consistency between the primary source of truth (database) and
    the agent context in the memory system.
    """
    
    def __init__(self, memory_adapter: MemoryAdapter):
        """
        Initialize the memory synchronizer.
        
        Args:
            memory_adapter: Adapter for memory operations
        """
        self.memory_adapter = memory_adapter
        self.logger = setup_logger("chat_api.utils.memory_sync")
        self.logger.info("Initializing Memory Synchronizer")
    
    @trace_method
    @monitor_operation(operation_type="memory_full_sync")
    async def synchronize_session(self, session_id: UUID, db_session: Session) -> bool:
        """
        Synchronize all session data between database and memory system.
        
        Args:
            session_id: ID of the session to synchronize
            db_session: Database session for queries
            
        Returns:
            bool: Success status
        """
        self.logger.info(f"Starting full synchronization for session {session_id}")
        try:
            # Get session info from database
            session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                self.logger.error(f"Session {session_id} not found in database")
                return False
                
            # Synchronize session metadata
            await self._sync_session_metadata(session)
                
            # Get messages for session from database
            messages = db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(MessageModel.created_at).all()
            
            # Synchronize each message
            for message in messages:
                await self._sync_message(message, db_session)
                
            self.logger.info(f"Full synchronization completed for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during session synchronization for {session_id}: {str(e)}")
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_session_sync")
    async def _sync_session_metadata(self, session: SessionModel) -> bool:
        """
        Synchronize session metadata to the memory system.
        
        Args:
            session: Session model from database
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Synchronizing session metadata for {session.id}")
        try:
            # Format session data for memory
            session_data = {
                "session_id": str(session.id),
                "title": session.title,
                "status": session.status,
                "session_type": session.session_type,
                "primary_agent": session.primary_agent,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            
            # Store in Long-term Memory
            success = await self.memory_adapter.store_long_term(
                agent_id=str(session.id),
                content={"session_info": session_data},
                metadata={
                    "content_type": "session_info",
                    "sync_timestamp": datetime.utcnow().isoformat()
                },
                importance=0.9  # High importance for session metadata
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error synchronizing session metadata for {session.id}: {str(e)}")
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_message_sync")
    async def _sync_message(self, message: MessageModel, db_session: Session) -> bool:
        """
        Synchronize a message and its artifacts to the memory system.
        
        Args:
            message: Message model from database
            db_session: Database session for queries
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Synchronizing message {message.id} for session {message.session_id}")
        try:
            # Format message data
            message_data = {
                "message_id": str(message.id),
                "role": message.role,
                "content": message.content,
                "type": message.type,
                "created_at": message.created_at.isoformat()
            }
            
            # Get artifacts associated with this message
            artifacts = db_session.query(ArtifactModel).filter(
                ArtifactModel.message_id == message.id
            ).all()
            
            if artifacts:
                message_data["artifacts"] = [
                    {
                        "artifact_id": str(artifact.id),
                        "title": artifact.title,
                        "type": artifact.type
                    }
                    for artifact in artifacts
                ]
            
            # Store message in Long-term Memory
            message_success = await self.memory_adapter.store_long_term(
                agent_id=str(message.session_id),
                content={"message": message_data},
                metadata={
                    "message_id": str(message.id),
                    "content_type": "message",
                    "role": message.role,
                    "sync_timestamp": datetime.utcnow().isoformat()
                },
                importance=0.8 if message.role == "user" else 0.7  # Higher importance for user messages
            )
            
            # Synchronize each artifact separately
            artifact_results = []
            for artifact in artifacts:
                artifact_results.append(await self._sync_artifact(artifact, message.session_id))
            
            # Success if message and all artifacts synchronized
            return message_success and all(artifact_results)
            
        except Exception as e:
            self.logger.error(f"Error synchronizing message {message.id}: {str(e)}")
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_artifact_sync")
    async def _sync_artifact(self, artifact: ArtifactModel, session_id: UUID) -> bool:
        """
        Synchronize an artifact to the memory system.
        
        Args:
            artifact: Artifact model from database
            session_id: Session ID for the artifact
            
        Returns:
            bool: Success status
        """
        self.logger.debug(f"Synchronizing artifact {artifact.id} for message {artifact.message_id}")
        try:
            # Create a summary of the artifact content (truncated)
            content_preview = artifact.content[:200] + "..." if len(artifact.content) > 200 else artifact.content
            
            # Format artifact data
            artifact_data = {
                "artifact_id": str(artifact.id),
                "message_id": str(artifact.message_id),
                "type": artifact.type,
                "title": artifact.title,
                "language": artifact.language,
                "content_preview": content_preview,
                "created_at": artifact.created_at.isoformat(),
                "updated_at": artifact.updated_at.isoformat()
            }
            
            # Store in Long-term Memory
            success = await self.memory_adapter.store_long_term(
                agent_id=str(session_id),
                content={"artifact": artifact_data},
                metadata={
                    "artifact_id": str(artifact.id),
                    "message_id": str(artifact.message_id),
                    "content_type": "artifact",
                    "artifact_type": artifact.type,
                    "sync_timestamp": datetime.utcnow().isoformat()
                },
                importance=0.8  # Higher importance for artifacts
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error synchronizing artifact {artifact.id}: {str(e)}")
            return False
    
    @trace_method
    @monitor_operation(operation_type="memory_reconciliation")
    async def reconcile_data(self, session_id: UUID, db_session: Session) -> Dict[str, Any]:
        """
        Reconcile data between database and memory system to find discrepancies.
        
        Args:
            session_id: ID of the session to reconcile
            db_session: Database session for queries
            
        Returns:
            Dict[str, Any]: Report of reconciliation findings
        """
        self.logger.info(f"Starting data reconciliation for session {session_id}")
        try:
            # Initialize report
            report = {
                "session_id": str(session_id),
                "timestamp": datetime.utcnow().isoformat(),
                "db_message_count": 0,
                "memory_message_count": 0,
                "db_artifact_count": 0,
                "memory_artifact_count": 0,
                "discrepancies": [],
                "actions_taken": []
            }
            
            # Get database counts
            db_messages = db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).all()
            report["db_message_count"] = len(db_messages)
            
            db_artifacts = db_session.query(ArtifactModel).filter(
                ArtifactModel.message_id.in_([m.id for m in db_messages])
            ).all()
            report["db_artifact_count"] = len(db_artifacts)
            
            # Get memory counts
            memory_messages = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id),
                query={"metadata.content_type": "message"},
                limit=1000
            )
            report["memory_message_count"] = len(memory_messages)
            
            memory_artifacts = await self.memory_adapter.retrieve_long_term(
                agent_id=str(session_id),
                query={"metadata.content_type": "artifact"},
                limit=1000
            )
            report["memory_artifact_count"] = len(memory_artifacts)
            
            # Check for message discrepancies
            db_message_ids = {str(m.id) for m in db_messages}
            memory_message_ids = {
                m["content"].get("message", {}).get("message_id") 
                for m in memory_messages 
                if "message" in m["content"]
            }
            
            missing_in_memory = db_message_ids - memory_message_ids
            if missing_in_memory:
                report["discrepancies"].append({
                    "type": "missing_messages_in_memory",
                    "count": len(missing_in_memory),
                    "ids": list(missing_in_memory)
                })
                
                # Auto-repair by synchronizing missing messages
                for message_id in missing_in_memory:
                    message = next((m for m in db_messages if str(m.id) == message_id), None)
                    if message:
                        success = await self._sync_message(message, db_session)
                        if success:
                            report["actions_taken"].append(f"Synchronized missing message {message_id}")
            
            # Check for artifact discrepancies
            db_artifact_ids = {str(a.id) for a in db_artifacts}
            memory_artifact_ids = {
                a["content"].get("artifact", {}).get("artifact_id") 
                for a in memory_artifacts 
                if "artifact" in a["content"]
            }
            
            missing_in_memory = db_artifact_ids - memory_artifact_ids
            if missing_in_memory:
                report["discrepancies"].append({
                    "type": "missing_artifacts_in_memory",
                    "count": len(missing_in_memory),
                    "ids": list(missing_in_memory)
                })
                
                # Auto-repair by synchronizing missing artifacts
                for artifact_id in missing_in_memory:
                    artifact = next((a for a in db_artifacts if str(a.id) == artifact_id), None)
                    if artifact:
                        success = await self._sync_artifact(artifact, session_id)
                        if success:
                            report["actions_taken"].append(f"Synchronized missing artifact {artifact_id}")
            
            self.logger.info(f"Reconciliation completed for session {session_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error during data reconciliation for session {session_id}: {str(e)}")
            return {
                "session_id": str(session_id),
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    @trace_method
    @monitor_operation(operation_type="memory_sync_error_recovery")
    async def handle_sync_error(self, session_id: UUID, error_context: Dict[str, Any]) -> bool:
        """
        Handle synchronization errors with recovery attempts.
        
        Args:
            session_id: ID of the session with errors
            error_context: Context information about the error
            
        Returns:
            bool: Success status of recovery
        """
        self.logger.info(f"Handling sync error for session {session_id}")
        try:
            error_type = error_context.get("error_type")
            entity_id = error_context.get("entity_id")
            entity_type = error_context.get("entity_type")
            
            # Log error for tracking
            await self.memory_adapter.store_long_term(
                agent_id=str(session_id),
                content={
                    "sync_error": {
                        "error_type": error_type,
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "error_message": error_context.get("error_message"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                metadata={
                    "content_type": "sync_error",
                    "error_type": error_type,
                    "entity_id": entity_id,
                    "entity_type": entity_type
                },
                importance=0.6  # Lower importance for error logs
            )
            
            # Default recovery is to try again later - could be enhanced with
            # specific recovery strategies for different error types
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling sync error for session {session_id}: {str(e)}")
            return False