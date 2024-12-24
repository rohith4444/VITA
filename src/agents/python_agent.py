from src.agents.base_agent import BaseAgent
from configs.agent_config import PYTHON_AGENT_CONFIG

class PythonAgent(BaseAgent):
    def __init__(self):
        super().__init__(PYTHON_AGENT_CONFIG)
    
    async def process(self, query: str, context: dict = None) -> str:
        return await self.answer_question(query)
    
    def can_handle(self, query: str) -> float:
        expertise_words = set(word.lower() for expertise in self.expertise for word in expertise.split())
        query_words = set(query.lower().split())
        return len(expertise_words.intersection(query_words)) / len(query_words)