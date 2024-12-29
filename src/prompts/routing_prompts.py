from src.utils.logger import setup_logger

logger = setup_logger("RoutingPrompts")

logger.debug("Initializing routing prompt template")

ROUTING_PROMPT_TEMPLATE = """You are a supervising agent responsible for routing queries to specialized agents. Based on the query and available agents, determine which agent would be best suited to handle the request.

Query: {query}

Available Agents:
{agents}

Respond with only the name of the most appropriate agent to handle this query."""

logger.info("Routing prompt template initialized successfully")