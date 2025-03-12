from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import re
import uuid
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.scrum_master.feedback_processor")

class FeedbackCategory(Enum):
    """Enum representing the categories of user feedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    USABILITY = "usability"
    CLARIFICATION = "clarification"
    GENERAL = "general"
    TECHNICAL = "technical"
    REQUIREMENT_CHANGE = "requirement_change"

class FeedbackPriority(Enum):
    """Enum representing the priority levels for feedback."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeedbackSentiment(Enum):
    """Enum representing the sentiment of user feedback."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"

class ImplementationStatus(Enum):
    """Enum representing the implementation status of feedback."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WONT_IMPLEMENT = "wont_implement"
    NEEDS_CLARIFICATION = "needs_clarification"

class RoutingDestination(Enum):
    """Enum representing the possible routing destinations for feedback."""
    TEAM_LEAD = "team_lead"
    SOLUTION_ARCHITECT = "solution_architect"
    FULL_STACK_DEVELOPER = "full_stack_developer"
    QA_TEST = "qa_test"
    PROJECT_MANAGER = "project_manager"
    MULTIPLE = "multiple_agents"  # For feedback that needs to be routed to multiple agents

class FeedbackItem:
    """Class representing a structured feedback item."""
    
    def __init__(
        self,
        user_id: str,
        content: str,
        feedback_id: Optional[str] = None,
        category: Optional[FeedbackCategory] = None,
        priority: Optional[FeedbackPriority] = None,
        sentiment: Optional[FeedbackSentiment] = None,
        project_id: Optional[str] = None,
        component_id: Optional[str] = None,
        task_id: Optional[str] = None,
        requires_response: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = feedback_id or str(uuid.uuid4())
        self.user_id = user_id
        self.content = content
        self.category = category or FeedbackCategory.GENERAL
        self.priority = priority or FeedbackPriority.MEDIUM
        self.sentiment = sentiment or FeedbackSentiment.NEUTRAL
        self.project_id = project_id
        self.component_id = component_id
        self.task_id = task_id
        self.requires_response = requires_response
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.actionable_items = []
        self.routing_destination = None
        self.implementation_status = ImplementationStatus.NOT_STARTED
        self.responses = []
        
        logger.debug(f"Created feedback item {self.id} from user {user_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback item to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "category": self.category.value,
            "priority": self.priority.value,
            "sentiment": self.sentiment.value,
            "project_id": self.project_id,
            "component_id": self.component_id,
            "task_id": self.task_id,
            "requires_response": self.requires_response,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "actionable_items": self.actionable_items,
            "routing_destination": self.routing_destination.value if self.routing_destination else None,
            "implementation_status": self.implementation_status.value,
            "responses": self.responses
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackItem':
        """Create a feedback item instance from a dictionary."""
        feedback = cls(
            user_id=data["user_id"],
            content=data["content"],
            feedback_id=data.get("id"),
            category=FeedbackCategory(data["category"]) if "category" in data else None,
            priority=FeedbackPriority(data["priority"]) if "priority" in data else None,
            sentiment=FeedbackSentiment(data["sentiment"]) if "sentiment" in data else None,
            project_id=data.get("project_id"),
            component_id=data.get("component_id"),
            task_id=data.get("task_id"),
            requires_response=data.get("requires_response", False),
            metadata=data.get("metadata", {})
        )
        feedback.timestamp = data.get("timestamp", feedback.timestamp)
        feedback.actionable_items = data.get("actionable_items", [])
        
        if "routing_destination" in data and data["routing_destination"]:
            feedback.routing_destination = RoutingDestination(data["routing_destination"])
            
        if "implementation_status" in data:
            feedback.implementation_status = ImplementationStatus(data["implementation_status"])
            
        feedback.responses = data.get("responses", [])
        return feedback

@trace_method
def categorize_feedback(
    feedback_content: str, 
    project_context: Optional[Dict[str, Any]] = None
) -> FeedbackCategory:
    """
    Analyze feedback content to determine its category.
    
    Args:
        feedback_content: The raw user feedback text
        project_context: Optional context about the project
        
    Returns:
        FeedbackCategory: The determined feedback category
    """
    logger.info("Categorizing feedback")
    
    # Convert to lowercase for pattern matching
    content_lower = feedback_content.lower()
    
    # Pattern matching for common feedback types
    bug_patterns = [
        r"bug", r"error", r"issue", r"problem", r"doesn't work", r"doesn't function", 
        r"broken", r"crash", r"exception", r"fail"
    ]
    
    feature_patterns = [
        r"feature request", r"new feature", r"add .*?ability", r"would like to.*?be able to", 
        r"could you add", r"missing feature", r"implement", r"should have"
    ]
    
    improvement_patterns = [
        r"improve", r"enhance", r"better if", r"would be nice", r"optimization", 
        r"performance", r"speed up", r"more efficient"
    ]
    
    usability_patterns = [
        r"confusing", r"difficult to use", r"intuitive", r"user experience", r"ux", 
        r"interface", r"ui", r"layout", r"design", r"easier to"
    ]
    
    clarification_patterns = [
        r"explain", r"clarify", r"understand", r"what does", r"how do", r"what is", 
        r"how can", r"unclear", r"confused"
    ]
    
    technical_patterns = [
        r"technical", r"code", r"algorithm", r"implementation", r"architecture", 
        r"database", r"api", r"function"
    ]
    
    requirement_patterns = [
        r"requirement", r"change scope", r"change specification", r"spec change", 
        r"update requirement", r"new requirement"
    ]
    
    # Check patterns for each category
    if any(re.search(pattern, content_lower) for pattern in bug_patterns):
        logger.debug("Categorized as BUG_REPORT")
        return FeedbackCategory.BUG_REPORT
    
    if any(re.search(pattern, content_lower) for pattern in feature_patterns):
        logger.debug("Categorized as FEATURE_REQUEST")
        return FeedbackCategory.FEATURE_REQUEST
    
    if any(re.search(pattern, content_lower) for pattern in improvement_patterns):
        logger.debug("Categorized as IMPROVEMENT")
        return FeedbackCategory.IMPROVEMENT
    
    if any(re.search(pattern, content_lower) for pattern in usability_patterns):
        logger.debug("Categorized as USABILITY")
        return FeedbackCategory.USABILITY
    
    if any(re.search(pattern, content_lower) for pattern in clarification_patterns):
        logger.debug("Categorized as CLARIFICATION")
        return FeedbackCategory.CLARIFICATION
    
    if any(re.search(pattern, content_lower) for pattern in technical_patterns):
        logger.debug("Categorized as TECHNICAL")
        return FeedbackCategory.TECHNICAL
    
    if any(re.search(pattern, content_lower) for pattern in requirement_patterns):
        logger.debug("Categorized as REQUIREMENT_CHANGE")
        return FeedbackCategory.REQUIREMENT_CHANGE
    
    logger.debug("Categorized as GENERAL (default)")
    return FeedbackCategory.GENERAL

@trace_method
def analyze_sentiment(feedback_content: str) -> FeedbackSentiment:
    """
    Analyze the sentiment expressed in feedback content.
    
    Args:
        feedback_content: The raw user feedback text
        
    Returns:
        FeedbackSentiment: The determined sentiment
    """
    logger.info("Analyzing feedback sentiment")
    
    # Convert to lowercase for pattern matching
    content_lower = feedback_content.lower()
    
    # Pattern matching for sentiment
    positive_patterns = [
        r"good", r"great", r"excellent", r"awesome", r"love", r"like", r"appreciate",
        r"thank", r"helpful", r"wonderful", r"fantastic", r"perfect", r"happy"
    ]
    
    negative_patterns = [
        r"bad", r"terrible", r"awful", r"hate", r"dislike", r"disappoint", r"frustrat",
        r"annoying", r"confusing", r"difficult", r"problem", r"issue", r"bug", r"error",
        r"fail", r"poor", r"horrible", r"unhappy", r"broken"
    ]
    
    # Count sentiment indicators
    positive_count = sum(1 for pattern in positive_patterns if re.search(pattern, content_lower))
    negative_count = sum(1 for pattern in negative_patterns if re.search(pattern, content_lower))
    
    # Determine sentiment based on counts
    if positive_count > 0 and negative_count > 0:
        if positive_count > negative_count * 2:
            logger.debug("Sentiment: POSITIVE (mostly positive with some negative)")
            return FeedbackSentiment.POSITIVE
        elif negative_count > positive_count * 2:
            logger.debug("Sentiment: NEGATIVE (mostly negative with some positive)")
            return FeedbackSentiment.NEGATIVE
        else:
            logger.debug("Sentiment: MIXED (balanced positive and negative)")
            return FeedbackSentiment.MIXED
    elif positive_count > 0:
        logger.debug("Sentiment: POSITIVE")
        return FeedbackSentiment.POSITIVE
    elif negative_count > 0:
        logger.debug("Sentiment: NEGATIVE")
        return FeedbackSentiment.NEGATIVE
    else:
        logger.debug("Sentiment: NEUTRAL (no strong sentiment detected)")
        return FeedbackSentiment.NEUTRAL

@trace_method
def prioritize_feedback(
    feedback: FeedbackItem,
    user_context: Optional[Dict[str, Any]] = None
) -> FeedbackPriority:
    """
    Determine the priority level of feedback.
    
    Args:
        feedback: The feedback item to prioritize
        user_context: Optional context about the user (e.g., role, preferences)
        
    Returns:
        FeedbackPriority: The determined priority level
    """
    logger.info(f"Prioritizing feedback item {feedback.id}")
    
    # Define base scores for each category
    category_weights = {
        FeedbackCategory.BUG_REPORT: 3,  # Bugs are generally higher priority
        FeedbackCategory.FEATURE_REQUEST: 2,
        FeedbackCategory.IMPROVEMENT: 2,
        FeedbackCategory.USABILITY: 2,
        FeedbackCategory.CLARIFICATION: 1,
        FeedbackCategory.GENERAL: 1,
        FeedbackCategory.TECHNICAL: 2,
        FeedbackCategory.REQUIREMENT_CHANGE: 3  # Requirement changes are important
    }
    
    # Start with base score from category
    base_score = category_weights.get(feedback.category, 1)
    
    # Adjustments based on content
    content_lower = feedback.content.lower()
    
    # Priority indicators in the content
    if any(term in content_lower for term in ["urgent", "immediately", "critical", "blocker", "blocking", "asap"]):
        base_score += 2
    elif any(term in content_lower for term in ["important", "high priority", "significant"]):
        base_score += 1
    elif any(term in content_lower for term in ["minor", "low priority", "not urgent", "when you can"]):
        base_score -= 1
    
    # Adjust for user context if available
    if user_context:
        # VIP users or stakeholders might get higher priority
        user_role = user_context.get("role", "").lower()
        if user_role in ["stakeholder", "manager", "executive", "vip"]:
            base_score += 1
        
        # Consider user's historical feedback quality
        feedback_quality = user_context.get("feedback_quality", 0.5)  # Default to medium
        if feedback_quality > 0.8:  # High-quality feedback provider
            base_score += 1
    
    # Convert score to priority level
    if base_score >= 4:
        priority = FeedbackPriority.CRITICAL
    elif base_score == 3:
        priority = FeedbackPriority.HIGH
    elif base_score == 2:
        priority = FeedbackPriority.MEDIUM
    else:
        priority = FeedbackPriority.LOW
    
    logger.debug(f"Assigned priority {priority.value} to feedback {feedback.id}")
    return priority

@trace_method
def extract_actionable_items(feedback_content: str) -> List[str]:
    """
    Extract specific actionable items from feedback content.
    
    Args:
        feedback_content: The raw user feedback text
        
    Returns:
        List[str]: List of actionable items extracted from the feedback
    """
    logger.info("Extracting actionable items from feedback")
    
    actionable_items = []
    
    # Look for common actionable item patterns
    patterns = [
        r"(?:please|can you|should|need to|must|would like to) (.*?)[\.|\?]",  # Requests
        r"(?:add|change|update|remove|fix|implement) (.*?)[\.|\?]",  # Direct actions
        r"it would be (?:better|nice|good|great|helpful) (?:if|to) (.*?)[\.|\?]",  # Suggestions
        r"(?:consider|think about) (.*?)[\.|\?]",  # Considerations
    ]
    
    # Apply each pattern
    for pattern in patterns:
        matches = re.finditer(pattern, feedback_content, re.IGNORECASE)
        for match in matches:
            item = match.group(1).strip()
            if item and len(item) > 3:  # Avoid very short items
                actionable_items.append(item)
    
    # If no patterns matched, look for sentences with action verbs
    if not actionable_items:
        sentences = re.split(r'[.!?]', feedback_content)
        action_verbs = ["add", "change", "update", "remove", "fix", "implement", 
                        "improve", "create", "revise", "modify", "enhance"]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(verb in sentence.lower() for verb in action_verbs) and len(sentence) > 10:
                actionable_items.append(sentence)
    
    # Deduplicate and clean
    unique_items = []
    for item in actionable_items:
        normalized = item.lower().strip()
        if normalized and not any(normalized in existing.lower() for existing in unique_items):
            unique_items.append(item)
    
    logger.debug(f"Extracted {len(unique_items)} actionable items")
    return unique_items

@trace_method
def determine_routing(
    feedback: FeedbackItem, 
    project_context: Optional[Dict[str, Any]] = None
) -> RoutingDestination:
    """
    Determine which agent(s) should handle the feedback.
    
    Args:
        feedback: The feedback item to route
        project_context: Optional context about the project structure
        
    Returns:
        RoutingDestination: The determined routing destination
    """
    logger.info(f"Determining routing for feedback {feedback.id}")
    
    # Initial routing based on feedback category
    category_routing = {
        FeedbackCategory.BUG_REPORT: RoutingDestination.QA_TEST,
        FeedbackCategory.FEATURE_REQUEST: RoutingDestination.SOLUTION_ARCHITECT,
        FeedbackCategory.IMPROVEMENT: RoutingDestination.FULL_STACK_DEVELOPER,
        FeedbackCategory.USABILITY: RoutingDestination.SOLUTION_ARCHITECT,
        FeedbackCategory.CLARIFICATION: RoutingDestination.TEAM_LEAD,
        FeedbackCategory.GENERAL: RoutingDestination.TEAM_LEAD,
        FeedbackCategory.TECHNICAL: RoutingDestination.FULL_STACK_DEVELOPER,
        FeedbackCategory.REQUIREMENT_CHANGE: RoutingDestination.PROJECT_MANAGER
    }
    
    routing = category_routing.get(feedback.category, RoutingDestination.TEAM_LEAD)
    
    # Refine based on content analysis
    content_lower = feedback.content.lower()
    
    # Check for specific technical terms
    if any(term in content_lower for term in ["architecture", "design pattern", "system design", "component design"]):
        routing = RoutingDestination.SOLUTION_ARCHITECT
    elif any(term in content_lower for term in ["test", "qa", "testing", "quality", "validation"]):
        routing = RoutingDestination.QA_TEST
    elif any(term in content_lower for term in ["code", "implementation", "function", "method", "programming"]):
        routing = RoutingDestination.FULL_STACK_DEVELOPER
    elif any(term in content_lower for term in ["schedule", "timeline", "plan", "resource", "scope"]):
        routing = RoutingDestination.PROJECT_MANAGER
    
    # Check for mentions of multiple concerns or agents
    multiple_concerns = False
    concern_count = 0
    
    if any(term in content_lower for term in ["architecture", "design", "structure"]):
        concern_count += 1
    if any(term in content_lower for term in ["code", "implementation", "function"]):
        concern_count += 1
    if any(term in content_lower for term in ["test", "quality", "bug"]):
        concern_count += 1
    if any(term in content_lower for term in ["schedule", "timeline", "requirement"]):
        concern_count += 1
    
    if concern_count >= 2:
        multiple_concerns = True
    
    # If multiple concerns or critical priority, route to Team Lead
    if multiple_concerns or feedback.priority == FeedbackPriority.CRITICAL:
        routing = RoutingDestination.TEAM_LEAD
    
    # Component-specific routing override if context provided
    if project_context and feedback.component_id:
        component_info = project_context.get("components", {}).get(feedback.component_id, {})
        primary_owner = component_info.get("primary_owner")
        
        if primary_owner:
            try:
                routing = RoutingDestination(primary_owner)
            except ValueError:
                # If not a valid routing destination, keep the previously determined one
                pass
    
    logger.debug(f"Routing feedback {feedback.id} to {routing.value}")
    return routing

@trace_method
def translate_feedback_for_technical_team(
    feedback: FeedbackItem,
    target_agent: RoutingDestination
) -> Dict[str, Any]:
    """
    Format user feedback for consumption by technical team members.
    
    Args:
        feedback: The feedback item to translate
        target_agent: The agent this feedback is being translated for
        
    Returns:
        Dict[str, Any]: Structured feedback ready for technical consumption
    """
    logger.info(f"Translating feedback {feedback.id} for {target_agent.value}")
    
    # Start with base structure
    translated = {
        "feedback_id": feedback.id,
        "timestamp": feedback.timestamp,
        "category": feedback.category.value,
        "priority": feedback.priority.value,
        "content": feedback.content,
        "actionable_items": feedback.actionable_items or extract_actionable_items(feedback.content),
        "requires_response": feedback.requires_response,
        "metadata": feedback.metadata.copy()
    }
    
    # Add project context if available
    if feedback.project_id:
        translated["project_id"] = feedback.project_id
    if feedback.component_id:
        translated["component_id"] = feedback.component_id
    if feedback.task_id:
        translated["task_id"] = feedback.task_id
    
    # Customize based on target agent
    if target_agent == RoutingDestination.SOLUTION_ARCHITECT:
        # Emphasize design and architectural implications
        translated["technical_focus"] = "architecture_implications"
        translated["design_considerations"] = True
        
    elif target_agent == RoutingDestination.FULL_STACK_DEVELOPER:
        # Emphasize implementation details
        translated["technical_focus"] = "implementation_details"
        translated["code_level_impact"] = True
        
    elif target_agent == RoutingDestination.QA_TEST:
        # Emphasize quality and testing implications
        translated["technical_focus"] = "testing_implications"
        translated["quality_impact"] = True
        
    elif target_agent == RoutingDestination.PROJECT_MANAGER:
        # Emphasize timeline and resource implications
        translated["technical_focus"] = "project_management_implications"
        translated["timeline_impact"] = True
        
    elif target_agent == RoutingDestination.TEAM_LEAD:
        # Provide coordination context
        translated["technical_focus"] = "coordination_context"
        translated["cross_functional_impact"] = True
    
    logger.debug(f"Translated feedback {feedback.id} for {target_agent.value}")
    return translated

@trace_method
def process_feedback(
    user_id: str, 
    content: str, 
    project_id: Optional[str] = None,
    component_id: Optional[str] = None,
    task_id: Optional[str] = None,
    requires_response: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    user_context: Optional[Dict[str, Any]] = None,
    project_context: Optional[Dict[str, Any]] = None
) -> FeedbackItem:
    """
    Process raw user feedback to create a structured feedback item.
    
    Args:
        user_id: ID of the user providing feedback
        content: Raw feedback content
        project_id: Optional project identifier
        component_id: Optional component identifier
        task_id: Optional task identifier
        requires_response: Whether a response is required
        metadata: Optional additional metadata
        user_context: Optional context about the user
        project_context: Optional context about the project
        
    Returns:
        FeedbackItem: Processed feedback item
    """
    logger.info(f"Processing feedback from user {user_id}")
    
    # Create feedback item with basic information
    feedback = FeedbackItem(
        user_id=user_id,
        content=content,
        project_id=project_id,
        component_id=component_id,
        task_id=task_id,
        requires_response=requires_response,
        metadata=metadata or {}
    )
    
    # Analyze and categorize
    feedback.category = categorize_feedback(content, project_context)
    feedback.sentiment = analyze_sentiment(content)
    feedback.priority = prioritize_feedback(feedback, user_context)
    
    # Extract actionable items
    feedback.actionable_items = extract_actionable_items(content)
    
    # Determine routing
    feedback.routing_destination = determine_routing(feedback, project_context)
    
    logger.info(f"Feedback processing complete for item {feedback.id}")
    return feedback

@trace_method
def track_feedback_status(
    feedback_id: str,
    feedback_items: Dict[str, FeedbackItem],
    new_status: Union[ImplementationStatus, str],
    update_notes: Optional[str] = None
) -> Tuple[bool, Optional[FeedbackItem]]:
    """
    Update the implementation status of a feedback item.
    
    Args:
        feedback_id: ID of the feedback item
        feedback_items: Dictionary of feedback items
        new_status: New implementation status
        update_notes: Optional notes about the update
        
    Returns:
        Tuple[bool, Optional[FeedbackItem]]: Success status and updated feedback item
    """
    logger.info(f"Updating status for feedback {feedback_id} to {new_status}")
    
    # Check if feedback exists
    if feedback_id not in feedback_items:
        logger.error(f"Feedback {feedback_id} not found")
        return False, None
    
    # Get feedback item
    feedback = feedback_items[feedback_id]
    
    # Convert string status to enum if needed
    if isinstance(new_status, str):
        try:
            new_status = ImplementationStatus(new_status)
        except ValueError:
            logger.error(f"Invalid status: {new_status}")
            return False, None
    
    # Update status
    feedback.implementation_status = new_status
    
    # Add update to metadata
    if "status_updates" not in feedback.metadata:
        feedback.metadata["status_updates"] = []
    
    update = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": new_status.value,
        "notes": update_notes
    }
    
    feedback.metadata["status_updates"].append(update)
    
    logger.info(f"Updated feedback {feedback_id} status to {new_status.value}")
    return True, feedback

@trace_method
def add_response_to_feedback(
    feedback_id: str,
    feedback_items: Dict[str, FeedbackItem],
    agent_id: str,
    response_content: str,
    response_metadata: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[FeedbackItem]]:
    """
    Add a response to a feedback item.
    
    Args:
        feedback_id: ID of the feedback item
        feedback_items: Dictionary of feedback items
        agent_id: ID of the agent providing the response
        response_content: Content of the response
        response_metadata: Optional metadata about the response
        
    Returns:
        Tuple[bool, Optional[FeedbackItem]]: Success status and updated feedback item
    """
    logger.info(f"Adding response to feedback {feedback_id} from agent {agent_id}")
    
    # Check if feedback exists
    if feedback_id not in feedback_items:
        logger.error(f"Feedback {feedback_id} not found")
        return False, None
    
    # Get feedback item
    feedback = feedback_items[feedback_id]
    
    # Create response
    response = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "content": response_content,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": response_metadata or {}
    }
    
    # Add response
    feedback.responses.append(response)
    
    logger.info(f"Added response {response['id']} to feedback {feedback_id}")
    return True, feedback

@trace_method
def filter_feedback(
    feedback_items: Dict[str, FeedbackItem],
    filters: Dict[str, Any]
) -> List[FeedbackItem]:
    """
    Filter feedback items based on criteria.
    
    Args:
        feedback_items: Dictionary of feedback items
        filters: Dictionary of filter criteria
        
    Returns:
        List[FeedbackItem]: Filtered feedback items
    """
    logger.info(f"Filtering feedback with criteria: {filters}")
    
    filtered_items = []
    
    for feedback in feedback_items.values():
        include = True
        
        # Apply filters
        for key, value in filters.items():
            if key == "user_id" and feedback.user_id != value:
                include = False
                break
                
            if key == "project_id" and feedback.project_id != value:
                include = False
                break
                
            if key == "component_id" and feedback.component_id != value:
                include = False
                break
                
            if key == "task_id" and feedback.task_id != value:
                include = False
                break
                
            if key == "category" and feedback.category != value and feedback.category.value != value:
                include = False
                break
                
            if key == "priority" and feedback.priority != value and feedback.priority.value != value:
                include = False
                break
                
            if key == "sentiment" and feedback.sentiment != value and feedback.sentiment.value != value:
                include = False
                break
                
            if key == "implementation_status" and feedback.implementation_status != value and feedback.implementation_status.value != value:
                include = False
                break
                
            if key == "routing_destination" and feedback.routing_destination != value and (feedback.routing_destination and feedback.routing_destination.value != value):
                include = False
                break
                
            if key == "has_responses" and bool(feedback.responses) != value:
                include = False
                break
        
        if include:
            filtered_items.append(feedback)
    
    logger.info(f"Found {len(filtered_items)} feedback items matching filters")
    return filtered_items

@trace_method
def generate_feedback_summary(
    feedback_items: List[FeedbackItem]
) -> Dict[str, Any]:
    """
    Generate a summary of feedback items.
    
    Args:
        feedback_items: List of feedback items to summarize
        
    Returns:
        Dict[str, Any]: Feedback summary
    """
    logger.info(f"Generating summary for {len(feedback_items)} feedback items")
    
    summary = {
        "total_count": len(feedback_items),
        "categories": {},
        "priorities": {},
        "sentiments": {},
        "statuses": {},
        "routing": {},
        "response_stats": {
            "with_responses": 0,
            "awaiting_response": 0
        },
        "users": set(),
        "projects": set(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Process each feedback item
    for feedback in feedback_items:
        # Count by category
        category = feedback.category.value
        summary["categories"][category] = summary["categories"].get(category, 0) + 1
        
        # Count by priority
        priority = feedback.priority.value
        summary["priorities"][priority] = summary["priorities"].get(priority, 0) + 1
        
        # Count by sentiment
        sentiment = feedback.sentiment.value
        summary["sentiments"][sentiment] = summary["sentiments"].get(sentiment, 0) + 1
        
        # Count by status
        status = feedback.implementation_status.value
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
        
        # Count by routing
        if feedback.routing_destination:
            routing = feedback.routing_destination.value
            summary["routing"][routing] = summary["routing"].get(routing, 0) + 1
        
        # Count response stats
        if feedback.responses:
            summary["response_stats"]["with_responses"] += 1
        elif feedback.requires_response:
            summary["response_stats"]["awaiting_response"] += 1
        
        # Add user and project
        if feedback.user_id:
            summary["users"].add(feedback.user_id)
        if feedback.project_id:
            summary["projects"].add(feedback.project_id)
    
    # Convert sets to lists for serialization
    summary["users"] = list(summary["users"])
    summary["projects"] = list(summary["projects"])
    
    # Add time-based analysis
    if feedback_items:
        # Sort by timestamp
        sorted_items = sorted(feedback_items, key=lambda x: x.timestamp)
        summary["earliest_feedback"] = sorted_items[0].timestamp
        summary["latest_feedback"] = sorted_items[-1].timestamp
        
        # Recent feedback count (last 24 hours)
        recent_cutoff = (datetime.utcnow() - datetime.timedelta(days=1)).isoformat()
        summary["recent_feedback_count"] = sum(1 for f in feedback_items if f.timestamp >= recent_cutoff)
    
    logger.info(f"Generated feedback summary with {summary['total_count']} items")
    return summary

@trace_method
def prepare_feedback_for_user(
    feedback: FeedbackItem,
    responses: Optional[List[Dict[str, Any]]] = None,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format feedback and responses for presentation to the user.
    
    Args:
        feedback: The feedback item to format
        responses: Optional list of responses to include
        user_preferences: Optional user preferences for formatting
        
    Returns:
        Dict[str, Any]: User-friendly presentation of feedback and responses
    """
    logger.info(f"Preparing feedback {feedback.id} for user presentation")
    
    # Default presentation
    presentation = {
        "feedback_id": feedback.id,
        "original_content": feedback.content,
        "timestamp": feedback.timestamp,
        "status": feedback.implementation_status.value,
        "responses": responses or feedback.responses,
        "has_updates": bool(feedback.metadata.get("status_updates", [])),
        "action_taken": False
    }
    
    # Check if any action has been taken
    if feedback.implementation_status != ImplementationStatus.NOT_STARTED:
        presentation["action_taken"] = True
    
    # Get latest status update if available
    status_updates = feedback.metadata.get("status_updates", [])
    if status_updates:
        latest_update = status_updates[-1]
        presentation["latest_update"] = {
            "timestamp": latest_update.get("timestamp"),
            "status": latest_update.get("status"),
            "notes": latest_update.get("notes")
        }
    
    # Customize based on user preferences
    if user_preferences:
        # Detail level
        detail_level = user_preferences.get("detail_level", "medium")
        
        if detail_level == "minimal":
            # Remove details for minimal view
            if "latest_update" in presentation:
                presentation["latest_update"] = {"status": presentation["latest_update"]["status"]}
            presentation.pop("has_updates", None)
            
            # Summarize responses
            if presentation["responses"]:
                presentation["response_count"] = len(presentation["responses"])
                presentation["latest_response"] = presentation["responses"][-1]
                presentation.pop("responses")
                
        elif detail_level == "detailed":
            # Add more details for detailed view
            presentation["category"] = feedback.category.value
            presentation["priority"] = feedback.priority.value
            presentation["actionable_items"] = feedback.actionable_items
            
            # Add all status updates
            if status_updates:
                presentation["all_status_updates"] = status_updates
    
    logger.debug(f"Prepared feedback {feedback.id} for user presentation")
    return presentation

@trace_method
def analyze_feedback_trends(
    feedback_items: List[FeedbackItem],
    timeframe: Optional[int] = 30  # days
) -> Dict[str, Any]:
    """
    Analyze trends in feedback over time.
    
    Args:
        feedback_items: List of feedback items to analyze
        timeframe: Optional timeframe in days (default: 30)
        
    Returns:
        Dict[str, Any]: Trend analysis results
    """
    logger.info(f"Analyzing feedback trends over {timeframe} days")
    
    # Calculate cutoff date
    cutoff_date = (datetime.utcnow() - datetime.timedelta(days=timeframe)).isoformat()
    
    # Filter recent feedback
    recent_feedback = [f for f in feedback_items if f.timestamp >= cutoff_date]
    
    # Group by day
    feedback_by_day = {}
    for feedback in recent_feedback:
        day = feedback.timestamp.split('T')[0]  # Extract date part
        if day not in feedback_by_day:
            feedback_by_day[day] = []
        feedback_by_day[day].append(feedback)
    
    # Prepare daily counts
    daily_counts = []
    for day, items in sorted(feedback_by_day.items()):
        daily_counts.append({
            "date": day,
            "count": len(items),
            "positive": sum(1 for f in items if f.sentiment == FeedbackSentiment.POSITIVE),
            "negative": sum(1 for f in items if f.sentiment == FeedbackSentiment.NEGATIVE),
            "neutral": sum(1 for f in items if f.sentiment == FeedbackSentiment.NEUTRAL),
            "by_category": {
                cat.value: sum(1 for f in items if f.category == cat)
                for cat in FeedbackCategory
            }
        })
    
    # Calculate trend indicators
    trends = {
        "total_feedback": len(recent_feedback),
        "daily_average": len(recent_feedback) / timeframe if timeframe > 0 else 0,
        "sentiment_trend": {},
        "category_trend": {},
        "daily_counts": daily_counts
    }
    
    # Sentiment trends
    sentiment_counts = {
        FeedbackSentiment.POSITIVE.value: sum(1 for f in recent_feedback if f.sentiment == FeedbackSentiment.POSITIVE),
        FeedbackSentiment.NEGATIVE.value: sum(1 for f in recent_feedback if f.sentiment == FeedbackSentiment.NEGATIVE),
        FeedbackSentiment.NEUTRAL.value: sum(1 for f in recent_feedback if f.sentiment == FeedbackSentiment.NEUTRAL),
        FeedbackSentiment.MIXED.value: sum(1 for f in recent_feedback if f.sentiment == FeedbackSentiment.MIXED)
    }
    
    total = len(recent_feedback)
    if total > 0:
        for sentiment, count in sentiment_counts.items():
            trends["sentiment_trend"][sentiment] = count / total
    
    # Category trends
    category_counts = {
        cat.value: sum(1 for f in recent_feedback if f.category == cat)
        for cat in FeedbackCategory
    }
    
    if total > 0:
        for category, count in category_counts.items():
            trends["category_trend"][category] = count / total
    
    # Identify top issues based on negative feedback
    negative_feedback = [f for f in recent_feedback if f.sentiment == FeedbackSentiment.NEGATIVE]
    if negative_feedback:
        # Extract common words and phrases
        common_terms = {}
        for feedback in negative_feedback:
            # Simple tokenization - can be improved
            words = feedback.content.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_terms[word] = common_terms.get(word, 0) + 1
        
        # Get top terms
        top_terms = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:10]
        trends["top_issue_terms"] = [{"term": term, "count": count} for term, count in top_terms]
    
    logger.info(f"Analyzed trends for {len(recent_feedback)} feedback items")
    return trends

@trace_method
def extract_feature_requests(
    feedback_items: List[FeedbackItem]
) -> List[Dict[str, Any]]:
    """
    Extract feature requests from feedback items.
    
    Args:
        feedback_items: List of feedback items to analyze
        
    Returns:
        List[Dict[str, Any]]: Extracted feature requests
    """
    logger.info("Extracting feature requests from feedback")
    
    feature_requests = []
    
    # Filter for feature request category
    request_feedback = [f for f in feedback_items if f.category == FeedbackCategory.FEATURE_REQUEST]
    
    for feedback in request_feedback:
        # Extract the feature request from actionable items
        if feedback.actionable_items:
            for item in feedback.actionable_items:
                # Skip items that are too short
                if len(item) < 10:
                    continue
                    
                feature_requests.append({
                    "feedback_id": feedback.id,
                    "user_id": feedback.user_id,
                    "feature_description": item,
                    "timestamp": feedback.timestamp,
                    "priority": feedback.priority.value,
                    "status": feedback.implementation_status.value,
                    "project_id": feedback.project_id,
                    "component_id": feedback.component_id
                })
        else:
            # If no actionable items, use the whole feedback content
            feature_requests.append({
                "feedback_id": feedback.id,
                "user_id": feedback.user_id,
                "feature_description": feedback.content,
                "timestamp": feedback.timestamp,
                "priority": feedback.priority.value,
                "status": feedback.implementation_status.value,
                "project_id": feedback.project_id,
                "component_id": feedback.component_id
            })
    
    logger.info(f"Extracted {len(feature_requests)} feature requests")
    return feature_requests

@trace_method
def extract_bug_reports(
    feedback_items: List[FeedbackItem]
) -> List[Dict[str, Any]]:
    """
    Extract bug reports from feedback items.
    
    Args:
        feedback_items: List of feedback items to analyze
        
    Returns:
        List[Dict[str, Any]]: Extracted bug reports
    """
    logger.info("Extracting bug reports from feedback")
    
    bug_reports = []
    
    # Filter for bug report category
    bug_feedback = [f for f in feedback_items if f.category == FeedbackCategory.BUG_REPORT]
    
    for feedback in bug_feedback:
        # Extract information about the bug
        description = feedback.content
        
        # Try to extract steps to reproduce from actionable items
        steps_to_reproduce = []
        expected_result = None
        actual_result = None
        
        if feedback.actionable_items:
            for item in feedback.actionable_items:
                if "steps" in item.lower() or "reproduce" in item.lower():
                    steps_to_reproduce.append(item)
                elif "expected" in item.lower():
                    expected_result = item
                elif "actual" in item.lower():
                    actual_result = item
        
        bug_reports.append({
            "feedback_id": feedback.id,
            "user_id": feedback.user_id,
            "bug_description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "expected_result": expected_result,
            "actual_result": actual_result,
            "timestamp": feedback.timestamp,
            "priority": feedback.priority.value,
            "status": feedback.implementation_status.value,
            "project_id": feedback.project_id,
            "component_id": feedback.component_id
        })
    
    logger.info(f"Extracted {len(bug_reports)} bug reports")
    return bug_reports