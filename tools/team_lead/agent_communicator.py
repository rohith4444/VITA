from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import uuid
import copy
import json
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger with moderate logging level
logger = setup_logger("tools.team_lead.agent_communicator")

class MessageType(Enum):
    """Enum representing the possible types of messages between agents."""
    INSTRUCTION = "instruction"   # Directing an agent to perform a task
    REQUEST = "request"           # Requesting information or action
    RESPONSE = "response"         # Responding to a request
    NOTIFICATION = "notification" # Informational update
    ERROR = "error"               # Error notification
    DELIVERABLE = "deliverable"   # Transferring a work product
    USER_FEEDBACK = "user_feedback"  # Feedback from user via Scrum Master
    APPROVAL_REQUEST = "approval_request"  # Request for user approval via Scrum Master
    MILESTONE_PRESENTATION = "milestone_presentation"  # Milestone data for user presentation
    USER_DECISION = "user_decision"  # Decision made by user via Scrum Master

class MessagePriority(Enum):
    """Enum representing the priority levels for messages."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    USER_INITIATED = "user_initiated"  # Special priority for user-initiated requests

class DeliverableType(Enum):
    """Enum representing the types of deliverables that can be transferred."""
    CODE = "code"                 # Source code files
    DOCUMENTATION = "documentation" # Documentation files
    DESIGN = "design"             # Design specifications
    TEST = "test"                 # Test cases or test code
    ANALYSIS = "analysis"         # Analysis reports or results
    USER_PRESENTATION = "user_presentation"  # Content prepared for user consumption

class AgentType(Enum):
    """Enum representing the types of agents in the system."""
    TEAM_LEAD = "team_lead"
    SOLUTION_ARCHITECT = "solution_architect"
    FULL_STACK_DEVELOPER = "full_stack_developer"
    QA_TEST = "qa_test"
    SCRUM_MASTER = "scrum_master"  # Added Scrum Master agent type
    PROJECT_MANAGER = "project_manager"
    CODE_ASSEMBLER = "code_assembler"

class UserFeedbackType(Enum):
    """Enum representing types of user feedback."""
    GENERAL = "general"           # General comments
    SUGGESTION = "suggestion"     # Suggested changes or improvements
    APPROVAL = "approval"         # User approval of deliverable
    REJECTION = "rejection"       # User rejection of deliverable
    QUESTION = "question"         # User question about deliverable
    CLARIFICATION = "clarification"  # User asking for clarification
    REQUIREMENT = "requirement"   # User adding/changing requirements

class Message:
    """Class representing a communication message between agents."""
    
    def __init__(
        self,
        source_agent_id: str,
        target_agent_id: str,
        content: Any,
        message_type: MessageType,
        reference_id: Optional[str] = None,
        task_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,  # Added user_id for user-related messages
        user_context: Optional[Dict[str, Any]] = None  # Added user context
    ):
        self.id = str(uuid.uuid4())
        self.source_agent_id = source_agent_id
        self.target_agent_id = target_agent_id
        self.content = content
        self.message_type = message_type if isinstance(message_type, MessageType) else MessageType(message_type)
        self.reference_id = reference_id
        self.task_id = task_id
        self.priority = priority if isinstance(priority, MessagePriority) else MessagePriority(priority)
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.status = "created"
        self.response_to = None
        self.user_id = user_id  # Store user ID for user-related messages
        self.user_context = user_context or {}  # Store user context data
        
        logger.debug(f"Created new message {self.id} from {source_agent_id} to {target_agent_id} of type {message_type.value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "reference_id": self.reference_id,
            "task_id": self.task_id,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "status": self.status,
            "response_to": self.response_to,
            "user_id": self.user_id,  # Include user ID in serialization
            "user_context": self.user_context  # Include user context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message instance from a dictionary."""
        message = cls(
            source_agent_id=data["source_agent_id"],
            target_agent_id=data["target_agent_id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            reference_id=data.get("reference_id"),
            task_id=data.get("task_id"),
            priority=MessagePriority(data.get("priority", "medium")),
            metadata=data.get("metadata", {}),
            user_id=data.get("user_id"),  # Extract user ID
            user_context=data.get("user_context", {})  # Extract user context
        )
        message.id = data.get("id", message.id)
        message.timestamp = data.get("timestamp", message.timestamp)
        message.status = data.get("status", message.status)
        message.response_to = data.get("response_to")
        return message
    
    def create_response(self, content: Any, metadata: Optional[Dict[str, Any]] = None) -> 'Message':
        """Create a response message to this message."""
        response = Message(
            source_agent_id=self.target_agent_id,
            target_agent_id=self.source_agent_id,
            content=content,
            message_type=MessageType.RESPONSE,
            reference_id=self.reference_id,
            task_id=self.task_id,
            priority=self.priority,
            metadata=metadata or {},
            user_id=self.user_id,  # Preserve user ID
            user_context=self.user_context  # Preserve user context
        )
        response.response_to = self.id
        logger.debug(f"Created response message {response.id} to message {self.id}")
        return response

class UserFeedback:
    """Class representing feedback from a user."""
    
    def __init__(
        self,
        user_id: str,
        content: Any,
        feedback_type: UserFeedbackType,
        target_id: Optional[str] = None,  # ID of target component/deliverable
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        requires_response: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.content = content
        self.feedback_type = feedback_type if isinstance(feedback_type, UserFeedbackType) else UserFeedbackType(feedback_type)
        self.target_id = target_id
        self.project_id = project_id
        self.task_id = task_id
        self.requires_response = requires_response
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.status = "created"
        
        logger.debug(f"Created user feedback {self.id} of type {feedback_type.value} from user {user_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user feedback to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "feedback_type": self.feedback_type.value,
            "target_id": self.target_id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "requires_response": self.requires_response,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserFeedback':
        """Create a user feedback instance from a dictionary."""
        feedback = cls(
            user_id=data["user_id"],
            content=data["content"],
            feedback_type=UserFeedbackType(data["feedback_type"]),
            target_id=data.get("target_id"),
            project_id=data.get("project_id"),
            task_id=data.get("task_id"),
            requires_response=data.get("requires_response", False),
            metadata=data.get("metadata", {})
        )
        feedback.id = data.get("id", feedback.id)
        feedback.timestamp = data.get("timestamp", feedback.timestamp)
        feedback.status = data.get("status", feedback.status)
        return feedback

class ApprovalRequest:
    """Class representing a request for user approval."""
    
    def __init__(
        self,
        title: str,
        description: str,
        requestor_agent_id: str,
        content: Any,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        deadline: Optional[str] = None,
        options: Optional[List[Dict[str, Any]]] = None,  # Possible decisions
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.requestor_agent_id = requestor_agent_id
        self.content = content
        self.project_id = project_id
        self.task_id = task_id
        self.deadline = deadline
        self.options = options or [
            {"id": "approve", "label": "Approve", "description": "Approve as is"},
            {"id": "reject", "label": "Reject", "description": "Reject and provide feedback"}
        ]
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.status = "pending"
        self.decision = None
        self.decision_timestamp = None
        self.decision_feedback = None
        
        logger.debug(f"Created approval request {self.id} from {requestor_agent_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert approval request to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requestor_agent_id": self.requestor_agent_id,
            "content": self.content,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "deadline": self.deadline,
            "options": self.options,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "status": self.status,
            "decision": self.decision,
            "decision_timestamp": self.decision_timestamp,
            "decision_feedback": self.decision_feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRequest':
        """Create an approval request instance from a dictionary."""
        request = cls(
            title=data["title"],
            description=data["description"],
            requestor_agent_id=data["requestor_agent_id"],
            content=data["content"],
            project_id=data.get("project_id"),
            task_id=data.get("task_id"),
            deadline=data.get("deadline"),
            options=data.get("options"),
            metadata=data.get("metadata", {})
        )
        request.id = data.get("id", request.id)
        request.timestamp = data.get("timestamp", request.timestamp)
        request.status = data.get("status", request.status)
        request.decision = data.get("decision")
        request.decision_timestamp = data.get("decision_timestamp")
        request.decision_feedback = data.get("decision_feedback")
        return request
    
    def record_decision(
        self,
        decision: str,
        feedback: Optional[Any] = None
    ) -> None:
        """Record a decision on this approval request."""
        self.decision = decision
        self.decision_timestamp = datetime.utcnow().isoformat()
        self.decision_feedback = feedback
        self.status = "decided"
        
        logger.debug(f"Recorded decision '{decision}' for approval request {self.id}")

class Deliverable:
    """Class representing a work product deliverable."""
    
    def __init__(
        self,
        content: Any,
        deliverable_type: DeliverableType,
        source_agent_id: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0",
        for_user_presentation: bool = False  # Added flag for user presentation
    ):
        self.id = str(uuid.uuid4())
        self.content = content
        self.deliverable_type = deliverable_type if isinstance(deliverable_type, DeliverableType) else DeliverableType(deliverable_type)
        self.source_agent_id = source_agent_id
        self.task_id = task_id
        self.metadata = metadata or {}
        self.version = version
        self.timestamp = datetime.utcnow().isoformat()
        self.for_user_presentation = for_user_presentation  # Flag for user-targeted content
        
        logger.info(f"Created deliverable {self.id} of type {deliverable_type.value} from agent {source_agent_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deliverable to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "deliverable_type": self.deliverable_type.value,
            "source_agent_id": self.source_agent_id,
            "task_id": self.task_id,
            "metadata": self.metadata,
            "version": self.version,
            "timestamp": self.timestamp,
            "for_user_presentation": self.for_user_presentation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deliverable':
        """Create a deliverable instance from a dictionary."""
        deliverable = cls(
            content=data["content"],
            deliverable_type=DeliverableType(data["deliverable_type"]),
            source_agent_id=data["source_agent_id"],
            task_id=data.get("task_id"),
            metadata=data.get("metadata", {}),
            version=data.get("version", "1.0"),
            for_user_presentation=data.get("for_user_presentation", False)
        )
        deliverable.id = data.get("id", deliverable.id)
        deliverable.timestamp = data.get("timestamp", deliverable.timestamp)
        return deliverable
    
    def update_version(self, new_content: Any, version: Optional[str] = None) -> 'Deliverable':
        """Create a new version of this deliverable with updated content."""
        # Determine new version
        if version:
            new_version = version
        else:
            try:
                major, minor = self.version.split('.')
                new_version = f"{major}.{int(minor) + 1}"
            except (ValueError, AttributeError):
                new_version = f"{self.version}.1"
        
        # Create new deliverable with updated content and version
        updated = Deliverable(
            content=new_content,
            deliverable_type=self.deliverable_type,
            source_agent_id=self.source_agent_id,
            task_id=self.task_id,
            metadata={**self.metadata, "previous_version": self.version},
            version=new_version,
            for_user_presentation=self.for_user_presentation
        )
        
        logger.info(f"Updated deliverable {self.id} to version {new_version}")
        return updated

class CommunicationChannel:
    """Class representing a communication channel between agents."""
    
    def __init__(self, source_agent_id: str, target_agent_id: str):
        self.id = f"{source_agent_id}_{target_agent_id}"
        self.source_agent_id = source_agent_id
        self.target_agent_id = target_agent_id
        self.message_queue = []
        self.message_history = []
        self.created_at = datetime.utcnow().isoformat()
        self.last_active = self.created_at
        
        logger.info(f"Created communication channel {self.id} between {source_agent_id} and {target_agent_id}")
    
    def add_message(self, message: Message) -> None:
        """Add a message to the channel queue."""
        if message.source_agent_id != self.source_agent_id or message.target_agent_id != self.target_agent_id:
            logger.warning(f"Message {message.id} source/target doesn't match channel {self.id}")
            return
        
        self.message_queue.append(message)
        message.status = "queued"
        self.last_active = datetime.utcnow().isoformat()
        logger.debug(f"Added message {message.id} to channel {self.id} queue")
    
    def get_next_message(self) -> Optional[Message]:
        """Get the next message from the queue."""
        if not self.message_queue:
            return None
        
        # Sort by priority and timestamp, with special handling for user-initiated messages
        self.message_queue.sort(
            key=lambda m: (
                # Make user-initiated messages highest priority
                -1 if m.priority == MessagePriority.USER_INITIATED else
                {"critical": 0, "high": 1, "medium": 2, "low": 3}[m.priority.value],
                m.timestamp
            )
        )
        
        message = self.message_queue.pop(0)
        message.status = "processing"
        self.last_active = datetime.utcnow().isoformat()
        logger.debug(f"Retrieved message {message.id} from channel {self.id} queue")
        return message
    
    def mark_delivered(self, message_id: str) -> bool:
        """Mark a message as delivered."""
        # Check if in queue
        for i, message in enumerate(self.message_queue):
            if message.id == message_id:
                message.status = "delivered"
                self.message_history.append(self.message_queue.pop(i))
                self.last_active = datetime.utcnow().isoformat()
                logger.info(f"Marked message {message_id} as delivered in channel {self.id}")
                return True
        
        # Check if in history
        for message in self.message_history:
            if message.id == message_id:
                message.status = "delivered"
                self.last_active = datetime.utcnow().isoformat()
                logger.info(f"Updated message {message_id} status to delivered in channel {self.id}")
                return True
        
        logger.warning(f"Message {message_id} not found in channel {self.id}")
        return False

class AgentCommunicator:
    """Main class for managing agent communications."""
    
    def __init__(self):
        self.channels = {}  # Dict[channel_id, CommunicationChannel]
        self.agents = set()  # Set of registered agent IDs
        self.deliverables = {}  # Dict[deliverable_id, Deliverable]
        self.agent_message_boxes = {}  # Dict[agent_id, List[Message]]
        self.message_status = {}  # Dict[message_id, Dict[status_info]]
        self.user_feedback = {}  # Dict[feedback_id, UserFeedback]  # Added for user feedback
        self.approval_requests = {}  # Dict[request_id, ApprovalRequest]  # Added for approval requests
        self.user_preferences = {}  # Dict[user_id, Dict[preference_data]]  # Added for user preferences
        
        logger.info("Initialized AgentCommunicator")
    
    @trace_method
    def register_agent(self, agent_id: str) -> None:
        """Register an agent with the communicator."""
        self.agents.add(agent_id)
        if agent_id not in self.agent_message_boxes:
            self.agent_message_boxes[agent_id] = []
        logger.info(f"Registered agent {agent_id} with communicator")
    
    @trace_method
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the communicator."""
        if agent_id in self.agents:
            self.agents.remove(agent_id)
            logger.info(f"Unregistered agent {agent_id} from communicator")
        else:
            logger.warning(f"Attempted to unregister unknown agent {agent_id}")
    
    @trace_method
    def send_message(
        self, 
        source_agent_id: str, 
        target_agent_id: str, 
        content: Any, 
        message_type: Union[MessageType, str] = MessageType.NOTIFICATION,
        reference_id: Optional[str] = None,
        task_id: Optional[str] = None,
        priority: Union[MessagePriority, str] = MessagePriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,  # Added user_id parameter
        user_context: Optional[Dict[str, Any]] = None  # Added user context
    ) -> Optional[str]:
        """
        Send a message from one agent to another.
        
        Args:
            source_agent_id: ID of the sending agent
            target_agent_id: ID of the receiving agent
            content: Message content
            message_type: Type of message
            reference_id: Optional reference ID (e.g., for a task or conversation)
            task_id: Optional task ID
            priority: Message priority
            metadata: Optional additional metadata
            user_id: ID of the user if message relates to user interaction
            user_context: Additional user context information
            
        Returns:
            Optional[str]: Message ID if sent successfully, None otherwise
        """
        logger.info(f"Sending message from {source_agent_id} to {target_agent_id} of type {message_type}")
        
        # Validate agents are registered
        if source_agent_id not in self.agents:
            logger.error(f"Cannot send message: Source agent {source_agent_id} not registered")
            return None
        
        if target_agent_id not in self.agents and target_agent_id != "broadcast":
            logger.error(f"Cannot send message: Target agent {target_agent_id} not registered")
            return None
        
        # Convert string types to enum if needed
        if isinstance(message_type, str):
            try:
                message_type = MessageType(message_type)
            except ValueError:
                logger.error(f"Invalid message type: {message_type}")
                return None
        
        if isinstance(priority, str):
            try:
                priority = MessagePriority(priority)
            except ValueError:
                logger.error(f"Invalid priority: {priority}")
                return None
        
        # Handle user-initiated messages (from Scrum Master)
        if source_agent_id == "scrum_master" and user_id:
            priority = MessagePriority.USER_INITIATED
        
        # Create message
        message = Message(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content=content,
            message_type=message_type,
            reference_id=reference_id,
            task_id=task_id,
            priority=priority,
            metadata=metadata or {},
            user_id=user_id,
            user_context=user_context
        )
        
        # Handle broadcast message
        if target_agent_id == "broadcast":
            logger.info(f"Broadcasting message {message.id} from {source_agent_id} to all agents")
            broadcast_count = 0
            
            for agent_id in self.agents:
                if agent_id != source_agent_id:  # Don't send to self
                    broadcast_message = copy.deepcopy(message)
                    broadcast_message.target_agent_id = agent_id
                    self._deliver_message(broadcast_message)
                    broadcast_count += 1
            
            logger.info(f"Broadcast message {message.id} delivered to {broadcast_count} agents")
            return message.id
        
        # Regular message delivery
        self._deliver_message(message)
        return message.id
    
    def _deliver_message(self, message: Message) -> None:
        """Internal method to deliver a message to its target."""
        # Get or create channel
        channel_id = f"{message.source_agent_id}_{message.target_agent_id}"
        if channel_id not in self.channels:
            self.channels[channel_id] = CommunicationChannel(
                source_agent_id=message.source_agent_id,
                target_agent_id=message.target_agent_id
            )
        
        # Add message to channel
        channel = self.channels[channel_id]
        channel.add_message(message)
        
        # Add to target agent's message box
        if message.target_agent_id in self.agent_message_boxes:
            self.agent_message_boxes[message.target_agent_id].append(message)
            logger.debug(f"Added message {message.id} to {message.target_agent_id}'s message box")
        
        # Track message status
        self.message_status[message.id] = {
            "status": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
            "channel_id": channel_id
        }
        
        logger.info(f"Delivered message {message.id} from {message.source_agent_id} to {message.target_agent_id}")
    
    @trace_method
    def get_messages(
        self, 
        agent_id: str, 
        message_type: Optional[Union[MessageType, str]] = None,
        max_messages: int = 10,
        include_user_messages_only: bool = False  # Added flag for user-related messages
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages for an agent.
        
        Args:
            agent_id: ID of the agent retrieving messages
            message_type: Optional filter by message type
            max_messages: Maximum number of messages to retrieve
            include_user_messages_only: Only include messages with user context
            
        Returns:
            List[Dict[str, Any]]: List of messages as dictionaries
        """
        logger.info(f"Retrieving messages for agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot retrieve messages: Agent {agent_id} not registered")
            return []
        
        # Filter messages
        if message_type:
            if isinstance(message_type, str):
                try:
                    message_type = MessageType(message_type)
                except ValueError:
                    logger.error(f"Invalid message type: {message_type}")
                    return []
            
            messages = [
                m.to_dict() for m in self.agent_message_boxes.get(agent_id, [])
                if m.message_type == message_type and (not include_user_messages_only or m.user_id is not None)
            ]
        else:
            messages = [
                m.to_dict() for m in self.agent_message_boxes.get(agent_id, [])
                if not include_user_messages_only or m.user_id is not None
            ]
        
        # Sort by priority and timestamp with special handling for user-initiated messages
        messages.sort(
            key=lambda m: (
                # Make user-initiated messages highest priority
                -1 if m["priority"] == MessagePriority.USER_INITIATED.value else
                {"critical": 0, "high": 1, "medium": 2, "low": 3}[m["priority"]],
                m["timestamp"]
            )
        )
        
        # Limit number of messages
        messages = messages[:max_messages]
        
        logger.info(f"Retrieved {len(messages)} messages for agent {agent_id}")
        return messages
    
    @trace_method
    def acknowledge_message(self, agent_id: str, message_id: str) -> bool:
        """
        Mark a message as acknowledged by the recipient.
        
        Args:
            agent_id: ID of the acknowledging agent
            message_id: ID of the message to acknowledge
            
        Returns:
            bool: True if message was acknowledged, False otherwise
        """
        logger.info(f"Acknowledging message {message_id} by agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot acknowledge message: Agent {agent_id} not registered")
            return False
        
        # Find the message
        message = None
        for m in self.agent_message_boxes.get(agent_id, []):
            if m.id == message_id:
                message = m
                break
        
        if not message:
            logger.warning(f"Message {message_id} not found in {agent_id}'s message box")
            return False
        
        # Update message status
        message.status = "acknowledged"
        
        # Update tracking
        if message_id in self.message_status:
            self.message_status[message_id]["status"] = "acknowledged"
            self.message_status[message_id]["acknowledged_at"] = datetime.utcnow().isoformat()
            self.message_status[message_id]["acknowledged_by"] = agent_id
        
        logger.info(f"Message {message_id} acknowledged by {agent_id}")
        return True
    
    @trace_method
    async def transfer_deliverable(
        self, 
        source_agent_id: str, 
        target_agent_id: str,
        content: Any,
        deliverable_type: Union[DeliverableType, str],
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        for_user_presentation: bool = False,  # New parameter
        user_id: Optional[str] = None         # New parameter for user context
    ) -> Optional[str]:
        """
        Transfer a deliverable from one agent to another.
        Enhanced to support user-targeted deliverables.
        
        Args:
            source_agent_id: ID of the sending agent
            target_agent_id: ID of the receiving agent
            content: Deliverable content
            deliverable_type: Type of deliverable
            task_id: Optional task ID
            metadata: Optional additional metadata
            message: Optional accompanying message
            for_user_presentation: Whether this is for user presentation
            user_id: Optional user ID if this is related to a specific user
            
        Returns:
            Optional[str]: Deliverable ID if transferred successfully, None otherwise
        """
        logger.info(f"Transferring {deliverable_type} deliverable from {source_agent_id} to {target_agent_id}")
        
        # Validate inputs
        if source_agent_id not in self.agents:
            logger.error(f"Cannot transfer deliverable: Source agent {source_agent_id} not registered")
            return None
        
        if target_agent_id not in self.agents:
            logger.error(f"Cannot transfer deliverable: Target agent {target_agent_id} not registered")
            return None
        
        # Convert string type to enum if needed
        if isinstance(deliverable_type, str):
            try:
                deliverable_type = DeliverableType(deliverable_type)
            except ValueError:
                logger.error(f"Invalid deliverable type: {deliverable_type}")
                return None
        
        # Create deliverable
        deliverable = Deliverable(
            content=content,
            deliverable_type=deliverable_type,
            source_agent_id=source_agent_id,
            task_id=task_id,
            metadata=metadata or {},
            for_user_presentation=for_user_presentation
        )
        
        # Store deliverable
        self.deliverables[deliverable.id] = deliverable
        
        # Determine message type and priority based on target and purpose
        message_type = MessageType.DELIVERABLE
        message_priority = MessagePriority.HIGH
        
        # If this is going to Scrum Master and is for user, adjust accordingly
        if target_agent_id == "scrum_master" and for_user_presentation:
            message_type = MessageType.MILESTONE_PRESENTATION
            message_priority = MessagePriority.HIGH
        
        # Create message to carry the deliverable
        message_content = {
            "deliverable_id": deliverable.id,
            "deliverable_type": deliverable.deliverable_type.value,
            "message": message or f"Transferring {deliverable_type.value} deliverable",
            "for_user_presentation": for_user_presentation
        }
        
        # Add user context if provided
        message_metadata = {"deliverable_id": deliverable.id}
        if user_id:
            message_metadata["user_id"] = user_id
        
        # Send the message
        message_id = self.send_message(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content=message_content,
            message_type=message_type,
            task_id=task_id,
            priority=message_priority,
            metadata=message_metadata,
            user_id=user_id
        )
        
        if not message_id:
            logger.error(f"Failed to send message with deliverable {deliverable.id}")
            # Remove deliverable if message failed
            if deliverable.id in self.deliverables:
                del self.deliverables[deliverable.id]
            return None
        
        logger.info(f"Successfully transferred deliverable {deliverable.id} with message {message_id}")
        return deliverable.id

    @trace_method
    def submit_user_feedback(
        self,
        user_id: str,
        content: Any,
        feedback_type: Union[UserFeedbackType, str],
        target_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        requires_response: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Submit user feedback through the Scrum Master agent.
        
        Args:
            user_id: ID of the user submitting feedback
            content: Feedback content
            feedback_type: Type of feedback
            target_id: Optional ID of target component/deliverable
            project_id: Optional project ID
            task_id: Optional task ID
            requires_response: Whether a response is required
            metadata: Optional additional metadata
            
        Returns:
            Optional[str]: Feedback ID if submitted successfully, None otherwise
        """
        logger.info(f"Submitting {feedback_type} user feedback from user {user_id}")
        
        # Ensure Scrum Master is registered
        if "scrum_master" not in self.agents:
            logger.error("Cannot submit feedback: Scrum Master agent not registered")
            return None
        
        # Convert string type to enum if needed
        if isinstance(feedback_type, str):
            try:
                feedback_type = UserFeedbackType(feedback_type)
            except ValueError:
                logger.error(f"Invalid feedback type: {feedback_type}")
                return None
        
        # Create feedback object
        feedback = UserFeedback(
            user_id=user_id,
            content=content,
            feedback_type=feedback_type,
            target_id=target_id,
            project_id=project_id,
            task_id=task_id,
            requires_response=requires_response,
            metadata=metadata
        )
        
        # Store feedback
        self.user_feedback[feedback.id] = feedback
        
        # Send message to Scrum Master
        message_content = {
            "feedback_id": feedback.id,
            "feedback_type": feedback.feedback_type.value,
            "content": content,
            "target_id": target_id,
            "requires_response": requires_response
        }
        
        message_id = self.send_message(
            source_agent_id="user", # Special case for user messages
            target_agent_id="scrum_master",
            content=message_content,
            message_type=MessageType.USER_FEEDBACK,
            task_id=task_id,
            priority=MessagePriority.USER_INITIATED,
            metadata={"project_id": project_id} if project_id else None,
            user_id=user_id
        )
        
        if not message_id:
            logger.error(f"Failed to send message with feedback {feedback.id}")
            # Remove feedback if message failed
            if feedback.id in self.user_feedback:
                del self.user_feedback[feedback.id]
            return None
        
        logger.info(f"Successfully submitted user feedback {feedback.id} with message {message_id}")
        return feedback.id

    @trace_method
    def submit_approval_request(
        self,
        title: str,
        description: str,
        requestor_agent_id: str,
        content: Any,
        user_id: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        deadline: Optional[str] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Submit a request for user approval via the Scrum Master.
        
        Args:
            title: Title of the approval request
            description: Detailed description
            requestor_agent_id: ID of the requesting agent
            content: Content to approve
            user_id: ID of the user to request approval from
            project_id: Optional project ID
            task_id: Optional task ID
            deadline: Optional deadline for approval
            options: Optional custom approval options
            metadata: Optional additional metadata
            
        Returns:
            Optional[str]: Request ID if submitted successfully, None otherwise
        """
        logger.info(f"Submitting approval request from {requestor_agent_id} to user {user_id}")
        
        # Ensure Scrum Master is registered
        if "scrum_master" not in self.agents:
            logger.error("Cannot submit approval request: Scrum Master agent not registered")
            return None
        
        # Ensure requestor is registered
        if requestor_agent_id not in self.agents:
            logger.error(f"Cannot submit approval request: Requestor agent {requestor_agent_id} not registered")
            return None
        
        # Create approval request
        approval_request = ApprovalRequest(
            title=title,
            description=description,
            requestor_agent_id=requestor_agent_id,
            content=content,
            project_id=project_id,
            task_id=task_id,
            deadline=deadline,
            options=options,
            metadata=metadata
        )
        
        # Store approval request
        self.approval_requests[approval_request.id] = approval_request
        
        # Send message to Scrum Master
        message_content = {
            "approval_request_id": approval_request.id,
            "title": title,
            "description": description,
            "content": content,
            "deadline": deadline,
            "options": options
        }
        
        message_id = self.send_message(
            source_agent_id=requestor_agent_id,
            target_agent_id="scrum_master",
            content=message_content,
            message_type=MessageType.APPROVAL_REQUEST,
            task_id=task_id,
            priority=MessagePriority.HIGH,
            metadata={"project_id": project_id} if project_id else None,
            user_id=user_id
        )
        
        if not message_id:
            logger.error(f"Failed to send message with approval request {approval_request.id}")
            # Remove approval request if message failed
            if approval_request.id in self.approval_requests:
                del self.approval_requests[approval_request.id]
            return None
        
        logger.info(f"Successfully submitted approval request {approval_request.id} with message {message_id}")
        return approval_request.id

    @trace_method
    def record_user_decision(
        self,
        user_id: str,
        approval_request_id: str,
        decision: str,
        feedback: Optional[Any] = None
    ) -> bool:
        """
        Record a user's decision on an approval request.
        
        Args:
            user_id: ID of the user making the decision
            approval_request_id: ID of the approval request
            decision: Decision string (e.g., "approve", "reject")
            feedback: Optional feedback with the decision
            
        Returns:
            bool: Success status
        """
        logger.info(f"Recording user decision from user {user_id} for request {approval_request_id}")
        
        # Check if approval request exists
        if approval_request_id not in self.approval_requests:
            logger.error(f"Cannot record decision: Approval request {approval_request_id} not found")
            return False
        
        # Get approval request
        approval_request = self.approval_requests[approval_request_id]
        
        # Record decision
        approval_request.record_decision(decision, feedback)
        
        # Notify requestor
        message_content = {
            "approval_request_id": approval_request_id,
            "decision": decision,
            "feedback": feedback,
            "decision_timestamp": approval_request.decision_timestamp
        }
        
        message_id = self.send_message(
            source_agent_id="scrum_master",
            target_agent_id=approval_request.requestor_agent_id,
            content=message_content,
            message_type=MessageType.USER_DECISION,
            task_id=approval_request.task_id,
            priority=MessagePriority.HIGH,
            metadata={"project_id": approval_request.project_id} if approval_request.project_id else None,
            user_id=user_id
        )
        
        if not message_id:
            logger.error(f"Failed to send notification about decision on request {approval_request_id}")
            return False
        
        logger.info(f"Successfully recorded user decision for request {approval_request_id}")
        return True

    @trace_method
    def get_user_feedback(
        self,
        feedback_id: Optional[str] = None,
        user_id: Optional[str] = None,
        feedback_type: Optional[Union[UserFeedbackType, str]] = None,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user feedback.
        
        Args:
            feedback_id: Optional specific feedback ID
            user_id: Optional filter by user ID
            feedback_type: Optional filter by feedback type
            project_id: Optional filter by project ID
            limit: Maximum number of feedback items to return
            
        Returns:
            List[Dict[str, Any]]: List of matching feedback items
        """
        logger.info("Retrieving user feedback")
        
        # Convert string type to enum if needed
        if isinstance(feedback_type, str):
            try:
                feedback_type = UserFeedbackType(feedback_type)
            except ValueError:
                logger.warning(f"Invalid feedback type: {feedback_type}")
                feedback_type = None
        
        # Get specific feedback if ID provided
        if feedback_id:
            if feedback_id in self.user_feedback:
                return [self.user_feedback[feedback_id].to_dict()]
            return []
        
        # Filter feedback based on criteria
        filtered_feedback = []
        for fb in self.user_feedback.values():
            # Apply filters
            if user_id and fb.user_id != user_id:
                continue
            if feedback_type and fb.feedback_type != feedback_type:
                continue
            if project_id and fb.project_id != project_id:
                continue
            
            filtered_feedback.append(fb.to_dict())
        
        # Sort by timestamp (newest first) and limit
        filtered_feedback.sort(key=lambda f: f.get("timestamp", ""), reverse=True)
        filtered_feedback = filtered_feedback[:limit]
        
        logger.info(f"Retrieved {len(filtered_feedback)} feedback items")
        return filtered_feedback

    @trace_method
    def get_approval_requests(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        requestor_agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve approval requests.
        
        Args:
            request_id: Optional specific request ID
            user_id: Optional filter by user ID
            requestor_agent_id: Optional filter by requestor agent ID
            project_id: Optional filter by project ID
            status: Optional filter by status
            limit: Maximum number of requests to return
            
        Returns:
            List[Dict[str, Any]]: List of matching approval requests
        """
        logger.info("Retrieving approval requests")
        
        # Get specific request if ID provided
        if request_id:
            if request_id in self.approval_requests:
                return [self.approval_requests[request_id].to_dict()]
            return []
        
        # Filter requests based on criteria
        filtered_requests = []
        for req in self.approval_requests.values():
            # Apply filters
            if requestor_agent_id and req.requestor_agent_id != requestor_agent_id:
                continue
            if project_id and req.project_id != project_id:
                continue
            if status and req.status != status:
                continue
            # User ID is stored in metadata, check if it matches
            if user_id and req.metadata.get("user_id") != user_id:
                continue
            
            filtered_requests.append(req.to_dict())
        
        # Sort by timestamp (newest first) and limit
        filtered_requests.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        filtered_requests = filtered_requests[:limit]
        
        logger.info(f"Retrieved {len(filtered_requests)} approval requests")
        return filtered_requests

    @trace_method
    def store_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a user preference.
        
        Args:
            user_id: ID of the user
            preference_type: Type of preference
            preference_value: Value of the preference
            metadata: Optional additional metadata
            
        Returns:
            bool: Success status
        """
        logger.info(f"Storing {preference_type} preference for user {user_id}")
        
        # Initialize user preferences if needed
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        # Store preference
        self.user_preferences[user_id][preference_type] = {
            "value": preference_value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        logger.info(f"Successfully stored {preference_type} preference for user {user_id}")
        return True

    @trace_method
    def get_user_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve user preferences.
        
        Args:
            user_id: ID of the user
            preference_type: Optional specific preference type
            
        Returns:
            Dict[str, Any]: User preferences
        """
        logger.info(f"Retrieving preferences for user {user_id}")
        
        # Check if user exists
        if user_id not in self.user_preferences:
            logger.warning(f"No preferences found for user {user_id}")
            return {}
        
        # Get specific preference if type provided
        if preference_type:
            if preference_type in self.user_preferences[user_id]:
                return {preference_type: self.user_preferences[user_id][preference_type]}
            return {}
        
        # Return all preferences
        return self.user_preferences[user_id]

    @trace_method
    def get_communication_stats_with_user_data(
        self,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get communication statistics with user interaction data.
        
        Args:
            agent_id: Optional agent ID to get stats for
            user_id: Optional user ID to filter by
            
        Returns:
            Dict[str, Any]: Communication statistics
        """
        logger.info("Retrieving communication statistics with user data")
        
        # Get base stats
        stats = self.get_communication_stats(agent_id)
        
        # Add user-specific information
        if user_id:
            # Count user feedback
            user_feedback_count = sum(1 for fb in self.user_feedback.values() 
                                if fb.user_id == user_id)
            
            # Count user approval requests
            user_approval_count = sum(1 for req in self.approval_requests.values() 
                                if req.metadata.get("user_id") == user_id)
            
            # Add user stats
            stats["user_interaction"] = {
                "user_id": user_id,
                "feedback_count": user_feedback_count,
                "approval_request_count": user_approval_count,
                "has_preferences": user_id in self.user_preferences
            }
        else:
            # Add overall user stats
            stats["user_interaction"] = {
                "feedback_count": len(self.user_feedback),
                "approval_request_count": len(self.approval_requests),
                "unique_users": len(set(fb.user_id for fb in self.user_feedback.values()))
            }
        
        return stats