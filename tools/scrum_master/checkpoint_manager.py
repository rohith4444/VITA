from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import uuid
import json
import copy
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.scrum_master.checkpoint_manager")

class CheckpointStatus(Enum):
    """Enum representing the possible states of a checkpoint."""
    PENDING = "pending"         # Awaiting user review
    APPROVED = "approved"       # User has approved the checkpoint
    REJECTED = "rejected"       # User has rejected the checkpoint
    FEEDBACK_PENDING = "feedback_pending"  # Feedback being processed
    REVISION_NEEDED = "revision_needed"    # Changes required
    COMPLETED = "completed"     # Checkpoint process complete

class CheckpointType(Enum):
    """Enum representing the types of checkpoints."""
    MILESTONE = "milestone"     # Major project milestone
    DELIVERABLE = "deliverable" # Specific project deliverable
    APPROVAL_GATE = "approval_gate"  # Formal approval required
    FEEDBACK = "feedback"       # Feedback collection point
    DECISION_POINT = "decision_point"  # User decision required

@trace_method
def create_checkpoint(
    checkpoint_id: Optional[str] = None,
    checkpoint_type: Union[CheckpointType, str] = CheckpointType.MILESTONE,
    title: str = "",
    description: str = "",
    project_id: Optional[str] = None,
    milestone_id: Optional[str] = None,
    requires_approval: bool = True,
    approval_deadline: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new checkpoint for user approval.
    
    Args:
        checkpoint_id: Optional ID for the checkpoint (generated if not provided)
        checkpoint_type: Type of checkpoint
        title: Title of the checkpoint
        description: Detailed description
        project_id: Associated project ID
        milestone_id: Associated milestone ID
        requires_approval: Whether explicit approval is required
        approval_deadline: Optional deadline for approval
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Newly created checkpoint
    """
    logger.info(f"Creating new {checkpoint_type} checkpoint: {title}")
    
    try:
        # Generate ID if not provided
        if not checkpoint_id:
            checkpoint_id = f"checkpoint_{str(uuid.uuid4())[:8]}"
        
        # Convert string checkpoint type to enum if needed
        if isinstance(checkpoint_type, str):
            try:
                checkpoint_type = CheckpointType(checkpoint_type)
            except ValueError:
                logger.warning(f"Invalid checkpoint type: {checkpoint_type}, defaulting to MILESTONE")
                checkpoint_type = CheckpointType.MILESTONE
        
        # Create the checkpoint
        checkpoint = {
            "id": checkpoint_id,
            "type": checkpoint_type.value,
            "title": title,
            "description": description,
            "project_id": project_id,
            "milestone_id": milestone_id,
            "requires_approval": requires_approval,
            "approval_deadline": approval_deadline,
            "status": CheckpointStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "feedback": [],
            "approval_history": [],
            "metadata": metadata or {}
        }
        
        logger.info(f"Created checkpoint {checkpoint_id}")
        return checkpoint
        
    except Exception as e:
        logger.error(f"Error creating checkpoint: {str(e)}", exc_info=True)
        # Return a minimal valid checkpoint
        return {
            "id": checkpoint_id or f"checkpoint_{str(uuid.uuid4())[:8]}",
            "type": CheckpointType.MILESTONE.value,
            "title": title or "Error checkpoint",
            "description": f"Error creating checkpoint: {str(e)}",
            "status": CheckpointStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "feedback": [],
            "approval_history": [],
            "metadata": metadata or {}
        }

@trace_method
def track_checkpoint_status(
    checkpoint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update and track the status of a checkpoint.
    
    Args:
        checkpoint: The checkpoint to track
        
    Returns:
        Dict[str, Any]: Updated checkpoint with status information
    """
    logger.info(f"Tracking status for checkpoint {checkpoint.get('id', 'unknown')}")
    
    try:
        # Make a copy to avoid modifying the original
        updated_checkpoint = copy.deepcopy(checkpoint)
        
        # Check if there's a deadline
        deadline = updated_checkpoint.get("approval_deadline")
        if deadline:
            try:
                deadline_date = datetime.fromisoformat(deadline)
                if datetime.utcnow() > deadline_date and updated_checkpoint.get("status") == CheckpointStatus.PENDING.value:
                    logger.warning(f"Checkpoint {updated_checkpoint.get('id')} has passed its deadline")
                    updated_checkpoint["metadata"] = updated_checkpoint.get("metadata", {})
                    updated_checkpoint["metadata"]["deadline_passed"] = True
            except (ValueError, TypeError):
                logger.warning(f"Invalid deadline format for checkpoint {updated_checkpoint.get('id')}")
        
        # Check feedback requirements
        if updated_checkpoint.get("status") == CheckpointStatus.REJECTED.value:
            if not updated_checkpoint.get("feedback"):
                logger.warning(f"Checkpoint {updated_checkpoint.get('id')} was rejected but has no feedback")
                updated_checkpoint["metadata"] = updated_checkpoint.get("metadata", {})
                updated_checkpoint["metadata"]["missing_feedback"] = True
        
        # Update timestamp
        updated_checkpoint["updated_at"] = datetime.utcnow().isoformat()
        
        return updated_checkpoint
        
    except Exception as e:
        logger.error(f"Error tracking checkpoint status: {str(e)}", exc_info=True)
        checkpoint["updated_at"] = datetime.utcnow().isoformat()
        checkpoint["metadata"] = checkpoint.get("metadata", {})
        checkpoint["metadata"]["tracking_error"] = str(e)
        return checkpoint

@trace_method
def process_user_approval(
    checkpoint: Dict[str, Any],
    user_id: str,
    approval_notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process user approval of a checkpoint.
    
    Args:
        checkpoint: The checkpoint being approved
        user_id: ID of the approving user
        approval_notes: Optional notes from the user
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Updated checkpoint with approval information
    """
    logger.info(f"Processing approval for checkpoint {checkpoint.get('id', 'unknown')} by user {user_id}")
    
    try:
        # Make a copy to avoid modifying the original
        updated_checkpoint = copy.deepcopy(checkpoint)
        
        # Create approval entry
        approval_entry = {
            "user_id": user_id,
            "action": "approved",
            "timestamp": datetime.utcnow().isoformat(),
            "notes": approval_notes,
            "metadata": metadata or {}
        }
        
        # Add to approval history
        updated_checkpoint.setdefault("approval_history", []).append(approval_entry)
        
        # Update status
        updated_checkpoint["status"] = CheckpointStatus.APPROVED.value
        updated_checkpoint["updated_at"] = datetime.utcnow().isoformat()
        
        # Add approval info to metadata
        updated_checkpoint.setdefault("metadata", {})
        updated_checkpoint["metadata"]["approved_by"] = user_id
        updated_checkpoint["metadata"]["approved_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Checkpoint {updated_checkpoint.get('id')} approved by user {user_id}")
        return updated_checkpoint
        
    except Exception as e:
        logger.error(f"Error processing approval: {str(e)}", exc_info=True)
        checkpoint["metadata"] = checkpoint.get("metadata", {})
        checkpoint["metadata"]["approval_error"] = str(e)
        return checkpoint

@trace_method
def process_user_rejection(
    checkpoint: Dict[str, Any],
    user_id: str,
    rejection_reason: str,
    feedback: Optional[List[Dict[str, Any]]] = None,
    requires_revision: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process user rejection of a checkpoint.
    
    Args:
        checkpoint: The checkpoint being rejected
        user_id: ID of the rejecting user
        rejection_reason: Primary reason for rejection
        feedback: Optional structured feedback items
        requires_revision: Whether revision is required
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Updated checkpoint with rejection information
    """
    logger.info(f"Processing rejection for checkpoint {checkpoint.get('id', 'unknown')} by user {user_id}")
    
    try:
        # Make a copy to avoid modifying the original
        updated_checkpoint = copy.deepcopy(checkpoint)
        
        # Create rejection entry
        rejection_entry = {
            "user_id": user_id,
            "action": "rejected",
            "reason": rejection_reason,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_revision": requires_revision,
            "metadata": metadata or {}
        }
        
        # Add to approval history
        updated_checkpoint.setdefault("approval_history", []).append(rejection_entry)
        
        # Update status based on whether revision is required
        if requires_revision:
            updated_checkpoint["status"] = CheckpointStatus.REVISION_NEEDED.value
        else:
            updated_checkpoint["status"] = CheckpointStatus.REJECTED.value
            
        updated_checkpoint["updated_at"] = datetime.utcnow().isoformat()
        
        # Add feedback if provided
        if feedback:
            # Add timestamp to each feedback item
            timestamped_feedback = []
            for item in feedback:
                feedback_item = copy.deepcopy(item)
                feedback_item["timestamp"] = feedback_item.get("timestamp", datetime.utcnow().isoformat())
                feedback_item["user_id"] = feedback_item.get("user_id", user_id)
                timestamped_feedback.append(feedback_item)
                
            # Add to existing feedback
            updated_checkpoint.setdefault("feedback", []).extend(timestamped_feedback)
        else:
            # Create a simple feedback entry from the rejection reason
            feedback_item = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "content": rejection_reason,
                "type": "rejection_reason"
            }
            updated_checkpoint.setdefault("feedback", []).append(feedback_item)
        
        # Add rejection info to metadata
        updated_checkpoint.setdefault("metadata", {})
        updated_checkpoint["metadata"]["rejected_by"] = user_id
        updated_checkpoint["metadata"]["rejected_at"] = datetime.utcnow().isoformat()
        updated_checkpoint["metadata"]["requires_revision"] = requires_revision
        
        logger.info(f"Checkpoint {updated_checkpoint.get('id')} rejected by user {user_id}")
        return updated_checkpoint
        
    except Exception as e:
        logger.error(f"Error processing rejection: {str(e)}", exc_info=True)
        checkpoint["metadata"] = checkpoint.get("metadata", {})
        checkpoint["metadata"]["rejection_error"] = str(e)
        return checkpoint

@trace_method
def add_user_feedback(
    checkpoint: Dict[str, Any],
    user_id: str,
    feedback_content: str,
    feedback_type: str = "general",
    component_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add user feedback to a checkpoint.
    
    Args:
        checkpoint: The checkpoint to add feedback to
        user_id: ID of the user providing feedback
        feedback_content: Content of the feedback
        feedback_type: Type of feedback (general, suggestion, issue, etc.)
        component_id: Optional specific component the feedback relates to
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Updated checkpoint with feedback added
    """
    logger.info(f"Adding {feedback_type} feedback to checkpoint {checkpoint.get('id', 'unknown')}")
    
    try:
        # Make a copy to avoid modifying the original
        updated_checkpoint = copy.deepcopy(checkpoint)
        
        # Create feedback entry
        feedback_entry = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "content": feedback_content,
            "type": feedback_type,
            "metadata": metadata or {}
        }
        
        if component_id:
            feedback_entry["component_id"] = component_id
        
        # Add to feedback list
        updated_checkpoint.setdefault("feedback", []).append(feedback_entry)
        
        # Update timestamp
        updated_checkpoint["updated_at"] = datetime.utcnow().isoformat()
        
        # Update status if pending and feedback was added
        if updated_checkpoint.get("status") == CheckpointStatus.PENDING.value:
            updated_checkpoint["status"] = CheckpointStatus.FEEDBACK_PENDING.value
        
        logger.info(f"Added feedback to checkpoint {updated_checkpoint.get('id')}")
        return updated_checkpoint
        
    except Exception as e:
        logger.error(f"Error adding feedback: {str(e)}", exc_info=True)
        checkpoint["metadata"] = checkpoint.get("metadata", {})
        checkpoint["metadata"]["feedback_error"] = str(e)
        return checkpoint

@trace_method
def get_pending_checkpoints(
    checkpoints: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filter and retrieve pending checkpoints that need user action.
    
    Args:
        checkpoints: List of all checkpoints
        
    Returns:
        List[Dict[str, Any]]: List of pending checkpoints
    """
    logger.info("Retrieving pending checkpoints")
    
    try:
        # Filter checkpoints that need user action
        pending_statuses = [
            CheckpointStatus.PENDING.value,
            CheckpointStatus.FEEDBACK_PENDING.value
        ]
        
        pending = [
            checkpoint for checkpoint in checkpoints
            if checkpoint.get("status") in pending_statuses
        ]
        
        # Sort by creation date (oldest first)
        pending.sort(key=lambda c: c.get("created_at", ""))
        
        logger.info(f"Found {len(pending)} pending checkpoints")
        return pending
        
    except Exception as e:
        logger.error(f"Error retrieving pending checkpoints: {str(e)}", exc_info=True)
        return []

@trace_method
def get_checkpoint_approval_status(
    checkpoint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get a summary of the checkpoint's approval status.
    
    Args:
        checkpoint: The checkpoint to analyze
        
    Returns:
        Dict[str, Any]: Approval status summary
    """
    logger.info(f"Getting approval status for checkpoint {checkpoint.get('id', 'unknown')}")
    
    try:
        checkpoint_id = checkpoint.get("id", "unknown")
        status = checkpoint.get("status", CheckpointStatus.PENDING.value)
        
        # Build status summary
        status_summary = {
            "checkpoint_id": checkpoint_id,
            "current_status": status,
            "requires_approval": checkpoint.get("requires_approval", True),
            "created_at": checkpoint.get("created_at"),
            "updated_at": checkpoint.get("updated_at"),
            "has_feedback": len(checkpoint.get("feedback", [])) > 0,
            "feedback_count": len(checkpoint.get("feedback", [])),
            "approval_history": len(checkpoint.get("approval_history", [])),
            "has_deadline": checkpoint.get("approval_deadline") is not None,
            "past_deadline": False,
            "deadline": checkpoint.get("approval_deadline")
        }
        
        # Check if past deadline
        if checkpoint.get("approval_deadline"):
            try:
                deadline_date = datetime.fromisoformat(checkpoint.get("approval_deadline"))
                status_summary["past_deadline"] = datetime.utcnow() > deadline_date
            except (ValueError, TypeError):
                pass
        
        # Check approval history
        approval_history = checkpoint.get("approval_history", [])
        if approval_history:
            most_recent = approval_history[-1]
            status_summary["last_action"] = most_recent.get("action")
            status_summary["last_action_by"] = most_recent.get("user_id")
            status_summary["last_action_time"] = most_recent.get("timestamp")
        
        # Get decision needed flag
        status_summary["needs_user_decision"] = status in [
            CheckpointStatus.PENDING.value,
            CheckpointStatus.FEEDBACK_PENDING.value
        ]
        
        # Get revision flag
        status_summary["needs_revision"] = status == CheckpointStatus.REVISION_NEEDED.value
        
        logger.info(f"Retrieved approval status for checkpoint {checkpoint_id}")
        return status_summary
        
    except Exception as e:
        logger.error(f"Error getting approval status: {str(e)}", exc_info=True)
        return {
            "checkpoint_id": checkpoint.get("id", "unknown"),
            "current_status": checkpoint.get("status", CheckpointStatus.PENDING.value),
            "error": str(e)
        }

@trace_method
def notify_team_lead(
    checkpoint: Dict[str, Any],
    notification_type: str,
    agent_id: str = "scrum_master",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a notification for the Team Lead about checkpoint events.
    
    Args:
        checkpoint: The checkpoint related to the notification
        notification_type: Type of notification (approval, rejection, feedback)
        agent_id: ID of the notifying agent (usually scrum_master)
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Notification data structure
    """
    logger.info(f"Creating {notification_type} notification for Team Lead about checkpoint {checkpoint.get('id', 'unknown')}")
    
    try:
        checkpoint_id = checkpoint.get("id", "unknown")
        
        # Create notification structure
        notification = {
            "id": f"notification_{str(uuid.uuid4())[:8]}",
            "source_agent_id": agent_id,
            "target_agent_id": "team_lead",
            "timestamp": datetime.utcnow().isoformat(),
            "notification_type": notification_type,
            "checkpoint_id": checkpoint_id,
            "checkpoint_type": checkpoint.get("type"),
            "checkpoint_title": checkpoint.get("title"),
            "checkpoint_status": checkpoint.get("status"),
            "project_id": checkpoint.get("project_id"),
            "milestone_id": checkpoint.get("milestone_id"),
            "requires_action": notification_type in ["rejection", "revision_needed", "feedback"],
            "metadata": metadata or {}
        }
        
        # Add specific details based on notification type
        if notification_type == "approval":
            # Find approval details
            approval_history = checkpoint.get("approval_history", [])
            if approval_history:
                most_recent = approval_history[-1]
                notification["approved_by"] = most_recent.get("user_id")
                notification["approval_notes"] = most_recent.get("notes")
                notification["approval_time"] = most_recent.get("timestamp")
        
        elif notification_type in ["rejection", "revision_needed"]:
            # Find rejection details
            approval_history = checkpoint.get("approval_history", [])
            if approval_history:
                most_recent = approval_history[-1]
                notification["rejected_by"] = most_recent.get("user_id")
                notification["rejection_reason"] = most_recent.get("reason")
                notification["rejection_time"] = most_recent.get("timestamp")
            
            # Add feedback
            notification["feedback"] = checkpoint.get("feedback", [])
            
        elif notification_type == "feedback":
            # Add feedback
            notification["feedback"] = checkpoint.get("feedback", [])
            
        logger.info(f"Created {notification_type} notification for Team Lead")
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}", exc_info=True)
        return {
            "id": f"notification_{str(uuid.uuid4())[:8]}",
            "source_agent_id": agent_id,
            "target_agent_id": "team_lead",
            "timestamp": datetime.utcnow().isoformat(),
            "notification_type": "error",
            "checkpoint_id": checkpoint.get("id", "unknown"),
            "error": str(e)
        }

@trace_method
def generate_checkpoint_report(
    checkpoints: List[Dict[str, Any]],
    report_type: str = "summary"
) -> Dict[str, Any]:
    """
    Generate a report about checkpoint statuses.
    
    Args:
        checkpoints: List of checkpoints to include in the report
        report_type: Type of report (summary, detailed)
        
    Returns:
        Dict[str, Any]: Generated report
    """
    logger.info(f"Generating {report_type} checkpoint report")
    
    try:
        # Count checkpoints by status
        status_counts = {}
        for checkpoint in checkpoints:
            status = checkpoint.get("status", CheckpointStatus.PENDING.value)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count checkpoints by type
        type_counts = {}
        for checkpoint in checkpoints:
            checkpoint_type = checkpoint.get("type", CheckpointType.MILESTONE.value)
            type_counts[checkpoint_type] = type_counts.get(checkpoint_type, 0) + 1
        
        # Build report
        report = {
            "report_id": f"checkpoint_report_{str(uuid.uuid4())[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "report_type": report_type,
            "total_checkpoints": len(checkpoints),
            "status_breakdown": status_counts,
            "type_breakdown": type_counts,
            "pending_count": status_counts.get(CheckpointStatus.PENDING.value, 0) + 
                            status_counts.get(CheckpointStatus.FEEDBACK_PENDING.value, 0),
            "approved_count": status_counts.get(CheckpointStatus.APPROVED.value, 0),
            "rejected_count": status_counts.get(CheckpointStatus.REJECTED.value, 0) +
                            status_counts.get(CheckpointStatus.REVISION_NEEDED.value, 0)
        }
        
        # Add detailed information for detailed report
        if report_type == "detailed":
            report["checkpoints"] = []
            
            for checkpoint in checkpoints:
                checkpoint_summary = {
                    "id": checkpoint.get("id"),
                    "title": checkpoint.get("title"),
                    "type": checkpoint.get("type"),
                    "status": checkpoint.get("status"),
                    "created_at": checkpoint.get("created_at"),
                    "updated_at": checkpoint.get("updated_at"),
                    "feedback_count": len(checkpoint.get("feedback", [])),
                    "approval_history_count": len(checkpoint.get("approval_history", []))
                }
                
                report["checkpoints"].append(checkpoint_summary)
        
        logger.info(f"Generated {report_type} report with {len(checkpoints)} checkpoints")
        return report
        
    except Exception as e:
        logger.error(f"Error generating checkpoint report: {str(e)}", exc_info=True)
        return {
            "report_id": f"checkpoint_report_{str(uuid.uuid4())[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "report_type": "error",
            "error": str(e)
        }

@trace_method
def complete_checkpoint(
    checkpoint: Dict[str, Any],
    final_status: CheckpointStatus = CheckpointStatus.COMPLETED,
    completion_notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Mark a checkpoint as complete, regardless of its current status.
    
    Args:
        checkpoint: The checkpoint to complete
        final_status: Final status for the checkpoint
        completion_notes: Optional notes about completion
        metadata: Additional metadata
        
    Returns:
        Dict[str, Any]: Updated checkpoint marked as complete
    """
    logger.info(f"Completing checkpoint {checkpoint.get('id', 'unknown')}")
    
    try:
        # Make a copy to avoid modifying the original
        updated_checkpoint = copy.deepcopy(checkpoint)
        
        # Create completion entry
        completion_entry = {
            "action": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "notes": completion_notes,
            "final_status": final_status.value,
            "metadata": metadata or {}
        }
        
        # Add to approval history
        updated_checkpoint.setdefault("approval_history", []).append(completion_entry)
        
        # Update status and timestamps
        updated_checkpoint["status"] = final_status.value
        updated_checkpoint["updated_at"] = datetime.utcnow().isoformat()
        updated_checkpoint.setdefault("metadata", {})["completed_at"] = datetime.utcnow().isoformat()
        
        # Add completion info to metadata
        if completion_notes:
            updated_checkpoint["metadata"]["completion_notes"] = completion_notes
        
        logger.info(f"Checkpoint {updated_checkpoint.get('id')} marked as complete")
        return updated_checkpoint
        
    except Exception as e:
        logger.error(f"Error completing checkpoint: {str(e)}", exc_info=True)
        checkpoint["metadata"] = checkpoint.get("metadata", {})
        checkpoint["metadata"]["completion_error"] = str(e)
        return checkpoint