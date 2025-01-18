from typing import List, Dict, Any
from src.agents.base_agent import BaseAgent
from src.utils.llm import get_llm
from configs.agent_config import SUPERVISING_AGENT_CONFIG
from src.prompts.routing_prompts import ROUTING_PROMPT_TEMPLATE
from src.utils.monitoring import monitor_agent
from src.utils.logger import setup_logger

class SupervisingAgent(BaseAgent):
    """Agent responsible for routing queries to specialized agents."""
    
    def __init__(self, specialized_agents: List[BaseAgent], session=None):
        self.logger = setup_logger("SupervisingAgent")
        self.logger.info("Initializing SupervisingAgent")
        
        try:
            super().__init__(SUPERVISING_AGENT_CONFIG, session=session)
            
            self.logger.debug("Setting up specialized agents")
            self.specialized_agents = specialized_agents
            for agent in specialized_agents:
                self.logger.debug(f"Registered agent: {agent.name}")
                
            self.logger.debug("Getting LLM instance")
            self.llm = get_llm()
            
            self.logger.info(f"SupervisingAgent initialized with {len(specialized_agents)} agents")
        except Exception as e:
            self.logger.error(f"Failed to initialize SupervisingAgent: {str(e)}", exc_info=True)
            raise

    @monitor_agent    
    async def route_query(self, query: str) -> BaseAgent:
        """Route the query to the most appropriate specialized agent."""
        self.logger.info(f"Routing query: {query}")
        
        try:
            # Create routing prompt
            self.logger.debug("Building agent descriptions for routing")
            agent_descriptions = [
                f"Agent: {agent.name}\nExpertise: {', '.join(agent.expertise)}\n"
                for agent in self.specialized_agents
            ]
            
            prompt = ROUTING_PROMPT_TEMPLATE.format(
                query=query,
                agents="\n".join(agent_descriptions)
            )
            
            # Get routing decision from LLM
            self.logger.debug("Requesting routing decision from LLM")
            response = self.llm.invoke(prompt)
            selected_agent_name = response.content.strip()
            self.logger.debug(f"LLM suggested agent: {selected_agent_name}")
            
            # Find the selected agent
            for agent in self.specialized_agents:
                if agent.name.lower() in selected_agent_name.lower():
                    self.logger.info(f"Selected agent: {agent.name}")
                    return agent
            
            # Default to confidence scoring if no match found
            self.logger.warning("No exact agent match found, using confidence scoring")
            selected_agent = max(self.specialized_agents, 
                               key=lambda a: a.can_handle(query))
            self.logger.info(f"Selected agent by confidence: {selected_agent.name}")
            return selected_agent
            
        except Exception as e:
            self.logger.error(f"Error routing query: {str(e)}", exc_info=True)
            raise
    
    @monitor_agent
    async def process(self, query: str, context: Dict[str, Any] = None) -> str:
        """Process a query by routing it to the appropriate specialized agent."""
        self.logger.info(f"Processing query: {query}")
        
        try:
            # Route query
            selected_agent = await self.route_query(query)
            
            # Process with selected agent
            self.logger.debug(f"Delegating to {selected_agent.name}")
            response = await selected_agent.process(query, context)
            
            formatted_response = f"[{selected_agent.name}]: {response}"
            self.logger.info("Query processed successfully")
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise

    def can_handle(self, query: str) -> float:
        """Supervising agent can handle all queries."""
        return 1.0