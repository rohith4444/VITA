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

class MessagePriority(Enum):
    """Enum representing the priority levels for messages."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DeliverableType(Enum):
    """Enum representing the types of deliverables that can be transferred."""
    CODE = "code"                 # Source code files
    DOCUMENTATION = "documentation" # Documentation files
    DESIGN = "design"             # Design specifications
    TEST = "test"                 # Test cases or test code
    ANALYSIS = "analysis"         # Analysis reports or results

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
        metadata: Optional[Dict[str, Any]] = None
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
            "response_to": self.response_to
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
            metadata=data.get("metadata", {})
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
            metadata=metadata or {}
        )
        response.response_to = self.id
        logger.debug(f"Created response message {response.id} to message {self.id}")
        return response

class Deliverable:
    """Class representing a work product deliverable."""
    
    def __init__(
        self,
        content: Any,
        deliverable_type: DeliverableType,
        source_agent_id: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0"
    ):
        self.id = str(uuid.uuid4())
        self.content = content
        self.deliverable_type = deliverable_type if isinstance(deliverable_type, DeliverableType) else DeliverableType(deliverable_type)
        self.source_agent_id = source_agent_id
        self.task_id = task_id
        self.metadata = metadata or {}
        self.version = version
        self.timestamp = datetime.utcnow().isoformat()
        
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
            "timestamp": self.timestamp
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
            version=data.get("version", "1.0")
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
            version=new_version
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
        
        # Sort by priority and timestamp
        self.message_queue.sort(
            key=lambda m: (
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
        metadata: Optional[Dict[str, Any]] = None
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
        
        # Create message
        message = Message(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content=content,
            message_type=message_type,
            reference_id=reference_id,
            task_id=task_id,
            priority=priority,
            metadata=metadata or {}
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
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages for an agent.
        
        Args:
            agent_id: ID of the agent retrieving messages
            message_type: Optional filter by message type
            max_messages: Maximum number of messages to retrieve
            
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
                if m.message_type == message_type
            ]
        else:
            messages = [m.to_dict() for m in self.agent_message_boxes.get(agent_id, [])]
        
        # Sort by priority and timestamp
        messages.sort(
            key=lambda m: (
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
        
        logger.info(f"Message {message_id} acknowledged by {agent_id}")
        return True
    
    @trace_method
    def transfer_deliverable(
        self, 
        source_agent_id: str, 
        target_agent_id: str,
        content: Any,
        deliverable_type: Union[DeliverableType, str],
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Optional[str]:
        """
        Transfer a deliverable from one agent to another.
        
        Args:
            source_agent_id: ID of the sending agent
            target_agent_id: ID of the receiving agent
            content: Deliverable content
            deliverable_type: Type of deliverable
            task_id: Optional task ID
            metadata: Optional additional metadata
            message: Optional accompanying message
            
        Returns:
            Optional[str]: Deliverable ID if transferred successfully, None otherwise
        """
        logger.info(f"Transferring {deliverable_type} deliverable from {source_agent_id} to {target_agent_id}")
        
        # Validate agents are registered
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
            metadata=metadata or {}
        )
        
        # Store deliverable
        self.deliverables[deliverable.id] = deliverable
        
        # Create message to carry the deliverable
        message_content = {
            "deliverable_id": deliverable.id,
            "deliverable_type": deliverable.deliverable_type.value,
            "message": message or f"Transferring {deliverable_type.value} deliverable"
        }
        
        # Send the message
        message_id = self.send_message(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content=message_content,
            message_type=MessageType.DELIVERABLE,
            task_id=task_id,
            priority=MessagePriority.HIGH,
            metadata={"deliverable_id": deliverable.id}
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
    def get_deliverable(self, deliverable_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a deliverable by ID.
        
        Args:
            deliverable_id: ID of the deliverable to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Deliverable as a dictionary if found, None otherwise
        """
        logger.info(f"Retrieving deliverable {deliverable_id}")
        
        if deliverable_id not in self.deliverables:
            logger.warning(f"Deliverable {deliverable_id} not found")
            return None
        
        deliverable = self.deliverables[deliverable_id]
        logger.info(f"Retrieved deliverable {deliverable_id} created by {deliverable.source_agent_id}")
        return deliverable.to_dict()
    
    @trace_method
    def update_deliverable(
        self, 
        deliverable_id: str, 
        agent_id: str,
        new_content: Any,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Update an existing deliverable with new content.
        
        Args:
            deliverable_id: ID of the deliverable to update
            agent_id: ID of the agent making the update
            new_content: New deliverable content
            metadata_updates: Optional updates to metadata
            
        Returns:
            Optional[str]: New deliverable ID if updated successfully, None otherwise
        """
        logger.info(f"Updating deliverable {deliverable_id} by agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot update deliverable: Agent {agent_id} not registered")
            return None
        
        if deliverable_id not in self.deliverables:
            logger.warning(f"Deliverable {deliverable_id} not found for update")
            return None
        
        original = self.deliverables[deliverable_id]
        
        # Check if agent is allowed to update
        if original.source_agent_id != agent_id:
            logger.warning(f"Agent {agent_id} not authorized to update deliverable {deliverable_id}")
            return None
        
        # Update metadata if provided
        if metadata_updates:
            updated_metadata = {**original.metadata, **metadata_updates}
        else:
            updated_metadata = original.metadata
        
        # Create updated deliverable
        updated = original.update_version(new_content=new_content)
        updated.metadata = updated_metadata
        
        # Store updated deliverable
        self.deliverables[updated.id] = updated
        
        logger.info(f"Deliverable {deliverable_id} updated to {updated.id} by {agent_id}")
        return updated.id
    
    @trace_method
    def request_status_update(
        self, 
        source_agent_id: str, 
        target_agent_id: str,
        task_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Request a status update from another agent.
        
        Args:
            source_agent_id: ID of the requesting agent
            target_agent_id: ID of the agent to request from
            task_id: Optional task ID to get status for
            
        Returns:
            Optional[str]: Message ID if request sent successfully, None otherwise
        """
        logger.info(f"Requesting status update from {target_agent_id} by {source_agent_id}")
        
        content = {
            "request_type": "status_update",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = self.send_message(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            content=content,
            message_type=MessageType.REQUEST,
            task_id=task_id,
            priority=MessagePriority.HIGH,
            metadata={"request_type": "status_update"}
        )
        
        if message_id:
            logger.info(f"Status update request sent as message {message_id}")
        else:
            logger.error("Failed to send status update request")
            
        return message_id
    
    @trace_method
    def broadcast_notification(
        self, 
        source_agent_id: str, 
        content: Any,
        priority: Union[MessagePriority, str] = MessagePriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Broadcast a notification to all agents.
        
        Args:
            source_agent_id: ID of the sending agent
            content: Notification content
            priority: Message priority
            metadata: Optional additional metadata
            
        Returns:
            Optional[str]: Message ID if broadcast successfully, None otherwise
        """
        logger.info(f"Broadcasting notification from {source_agent_id}")
        
        return self.send_message(
            source_agent_id=source_agent_id,
            target_agent_id="broadcast",
            content=content,
            message_type=MessageType.NOTIFICATION,
            priority=priority,
            metadata=metadata
        )
    
    @trace_method
    def get_communication_history(
        self, 
        agent_id: str, 
        other_agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        message_type: Optional[Union[MessageType, str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve communication history for an agent.
        
        Args:
            agent_id: ID of the agent
            other_agent_id: Optional ID of the other agent in the communication
            task_id: Optional task ID to filter by
            message_type: Optional message type to filter by
            start_time: Optional start time for filtering (ISO format)
            end_time: Optional end time for filtering (ISO format)
            limit: Maximum number of messages to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of messages as dictionaries
        """
        logger.info(f"Retrieving communication history for agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot retrieve history: Agent {agent_id} not registered")
            return []
        
        # Collect all messages to or from this agent
        all_messages = []
        for messages in self.agent_message_boxes.values():
            for message in messages:
                if message.source_agent_id == agent_id or message.target_agent_id == agent_id:
                    all_messages.append(message)
        
        # Apply filters
        filtered_messages = []
        for message in all_messages:
            # Filter by other agent
            if other_agent_id and message.source_agent_id != other_agent_id and message.target_agent_id != other_agent_id:
                continue
                
            # Filter by task ID
            if task_id and message.task_id != task_id:
                continue
                
            # Filter by message type
            if message_type:
                if isinstance(message_type, str):
                    if message.message_type.value != message_type:
                        continue
                elif message.message_type != message_type:
                    continue
            
            # Filter by time range
            if start_time:
                if message.timestamp < start_time:
                    continue
                    
            if end_time:
                if message.timestamp > end_time:
                    continue
            
            filtered_messages.append(message)
        
        # Sort by timestamp (newest first)
        filtered_messages.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Limit number of messages
        filtered_messages = filtered_messages[:limit]
        
        # Convert to dictionaries
        result = [message.to_dict() for message in filtered_messages]
        
        logger.info(f"Retrieved {len(result)} messages in communication history for agent {agent_id}")
        return result
    
    @trace_method
    def check_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a message.
        
        Args:
            message_id: ID of the message to check
            
        Returns:
            Optional[Dict[str, Any]]: Status information if message found, None otherwise
        """
        logger.info(f"Checking status of message {message_id}")
        
        if message_id not in self.message_status:
            logger.warning(f"Message {message_id} not found in status tracking")
            return None
        
        status_info = self.message_status[message_id]
        logger.debug(f"Message {message_id} status: {status_info['status']}")
        return status_info
    
    @trace_method
    def retry_failed_message(self, message_id: str) -> bool:
        """
        Retry sending a failed message.
        
        Args:
            message_id: ID of the failed message to retry
            
        Returns:
            bool: True if message was retried, False otherwise
        """
        logger.info(f"Attempting to retry message {message_id}")
        
        # Find the message
        message = None
        for agent_id, messages in self.agent_message_boxes.items():
            for m in messages:
                if m.id == message_id:
                    message = m
                    break
            if message:
                break
        
        if not message:
            logger.warning(f"Message {message_id} not found for retry")
            return False
        
        # Check if the message failed
        if message.status != "failed":
            logger.warning(f"Cannot retry message {message_id} with status {message.status}")
            return False
        
        # Reset message status
        message.status = "retry"
        
        # Attempt delivery again
        self._deliver_message(message)
        
        logger.info(f"Message {message_id} retry attempted")
        return True
    
    @trace_method
    def clear_agent_messages(self, agent_id: str) -> int:
        """
        Clear all messages for an agent.
        
        Args:
            agent_id: ID of the agent to clear messages for
            
        Returns:
            int: Number of messages cleared
        """
        logger.info(f"Clearing messages for agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot clear messages: Agent {agent_id} not registered")
            return 0
        
        if agent_id not in self.agent_message_boxes:
            logger.warning(f"No message box found for agent {agent_id}")
            return 0
        
        message_count = len(self.agent_message_boxes[agent_id])
        self.agent_message_boxes[agent_id] = []
        
        logger.info(f"Cleared {message_count} messages for agent {agent_id}")
        return message_count
    
    @trace_method
    def get_pending_deliverables(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all pending deliverables for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List[Dict[str, Any]]: List of pending deliverables
        """
        logger.info(f"Retrieving pending deliverables for agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.error(f"Cannot retrieve deliverables: Agent {agent_id} not registered")
            return []
        
        # Find all deliverable messages for this agent
        pending_deliverables = []
        
        for message in self.agent_message_boxes.get(agent_id, []):
            if message.message_type == MessageType.DELIVERABLE and message.status != "acknowledged":
                # Get the deliverable ID from the message
                deliverable_id = None
                
                if isinstance(message.content, dict) and "deliverable_id" in message.content:
                    deliverable_id = message.content["deliverable_id"]
                elif message.metadata and "deliverable_id" in message.metadata:
                    deliverable_id = message.metadata["deliverable_id"]
                
                if deliverable_id and deliverable_id in self.deliverables:
                    pending_deliverables.append({
                        "message_id": message.id,
                        "deliverable": self.deliverables[deliverable_id].to_dict(),
                        "timestamp": message.timestamp,
                        "source_agent_id": message.source_agent_id
                    })
        
        logger.info(f"Found {len(pending_deliverables)} pending deliverables for agent {agent_id}")
        return pending_deliverables
    
    @trace_method
    def get_communication_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Args:
            agent_id: Optional agent ID to get stats for
            
        Returns:
            Dict[str, Any]: Communication statistics
        """
        logger.info("Retrieving communication statistics")
        
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(self.agents),
            "total_messages": sum(len(msgs) for msgs in self.agent_message_boxes.values()),
            "total_deliverables": len(self.deliverables),
            "message_types": {},
            "deliverable_types": {},
            "agent_activity": {}
        }
        
        # Count message types
        for agent_messages in self.agent_message_boxes.values():
            for message in agent_messages:
                msg_type = message.message_type.value
                stats["message_types"][msg_type] = stats["message_types"].get(msg_type, 0) + 1
        
        # Count deliverable types
        for deliverable in self.deliverables.values():
            del_type = deliverable.deliverable_type.value
            stats["deliverable_types"][del_type] = stats["deliverable_types"].get(del_type, 0) + 1
        
        # Count agent activity
        for agent in self.agents:
            sent_count = 0
            received_count = 0
            
            for agent_messages in self.agent_message_boxes.values():
                for message in agent_messages:
                    if message.source_agent_id == agent:
                        sent_count += 1
                    if message.target_agent_id == agent:
                        received_count += 1
            
            stats["agent_activity"][agent] = {
                "sent": sent_count,
                "received": received_count,
                "total": sent_count + received_count
            }
        
        # Filter for specific agent if requested
        if agent_id:
            if agent_id in self.agents:
                filtered_stats = {
                    "timestamp": stats["timestamp"],
                    "agent_id": agent_id,
                    "sent_messages": stats["agent_activity"].get(agent_id, {}).get("sent", 0),
                    "received_messages": stats["agent_activity"].get(agent_id, {}).get("received", 0),
                    "total_messages": stats["agent_activity"].get(agent_id, {}).get("total", 0),
                    "message_types": {},
                    "deliverables_created": sum(1 for d in self.deliverables.values() if d.source_agent_id == agent_id)
                }
                
                # Count message types for this agent
                for agent_messages in self.agent_message_boxes.values():
                    for message in agent_messages:
                        if message.source_agent_id == agent_id or message.target_agent_id == agent_id:
                            msg_type = message.message_type.value
                            filtered_stats["message_types"][msg_type] = filtered_stats["message_types"].get(msg_type, 0) + 1
                
                stats = filtered_stats
                logger.info(f"Retrieved communication stats for agent {agent_id}")
            else:
                logger.warning(f"Agent {agent_id} not found for stats")
        else:
            logger.info("Retrieved overall communication stats")
        
        return stats

# Example usage
if __name__ == "__main__":
    # Create communicator
    communicator = AgentCommunicator()
    
    # Register some agents
    communicator.register_agent("solution_architect")
    communicator.register_agent("full_stack_developer")
    communicator.register_agent("qa_test")
    communicator.register_agent("team_lead")
    
    # Send a message
    message_id = communicator.send_message(
        source_agent_id="team_lead",
        target_agent_id="solution_architect",
        content="Please design the system architecture",
        message_type=MessageType.INSTRUCTION,
        task_id="task_1"
    )
    
    print(f"Sent message: {message_id}")
    
    # Get messages for an agent
    messages = communicator.get_messages("solution_architect")
    print(f"Retrieved {len(messages)} messages")
    
    # Transfer a deliverable
    deliverable_id = communicator.transfer_deliverable(
        source_agent_id="solution_architect",
        target_agent_id="full_stack_developer",
        content={"architecture": "Microservices", "components": ["api", "db", "auth"]},
        deliverable_type=DeliverableType.DESIGN,
        task_id="task_1"
    )
    
    print(f"Transferred deliverable: {deliverable_id}")
    
    # Check communication stats
    stats = communicator.get_communication_stats()
    print(f"Total messages: {stats['total_messages']}")
    print(f"Total deliverables: {stats['total_deliverables']}")