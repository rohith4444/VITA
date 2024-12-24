from typing import List, Dict, Any
from src.agents.base_agent import BaseAgent
from src.utils.llm import get_llm
from configs.agent_config import SUPERVISING_AGENT_CONFIG
from src.prompts.routing_prompts import ROUTING_PROMPT_TEMPLATE

class SupervisingAgent(BaseAgent):
    def __init__(self, specialized_agents: List[BaseAgent]):
        super().__init__(SUPERVISING_AGENT_CONFIG)
        self.specialized_agents = specialized_agents
        self.llm = get_llm()
        
    async def route_query(self, query: str) -> BaseAgent:
        """Route the query to the most appropriate specialized agent"""
        # Create routing prompt with available agents
        agent_descriptions = [
            f"Agent: {agent.name}\nExpertise: {', '.join(agent.expertise)}\n"
            for agent in self.specialized_agents
        ]
        
        prompt = ROUTING_PROMPT_TEMPLATE.format(
            query=query,
            agents="\n".join(agent_descriptions)
        )
        
        # Get routing decision from LLM
        response = self.llm.invoke(prompt)
        selected_agent_name = response.content.strip()
        
        # Find the selected agent
        for agent in self.specialized_agents:
            if agent.name.lower() in selected_agent_name.lower():
                return agent
                
        # Default to the agent with highest confidence if no clear match
        return max(self.specialized_agents, 
                  key=lambda a: a.can_handle(query))
    
    async def process(self, query: str, context: Dict[str, Any] = None) -> str:
        """Process a query by routing it to the appropriate specialized agent"""
        # Route query to appropriate agent
        selected_agent = await self.route_query(query)
        
        # Process query with selected agent
        response = await selected_agent.process(query, context)
        
        return f"[{selected_agent.name}]: {response}"

    def can_handle(self, query: str) -> float:
        """Supervising agent can handle all queries"""
        return 1.0