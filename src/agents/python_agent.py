from src.agents.base_agent import BaseAgent
from configs.agent_config import PYTHON_AGENT_CONFIG
from src.utils.logger import setup_logger

class PythonAgent(BaseAgent):
    def __init__(self, session=None):
        self.logger = setup_logger("PythonAgent")
        self.logger.info("Initializing Python Agent")
        try:
            super().__init__(PYTHON_AGENT_CONFIG, session=session)
            self.logger.info("Python Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Python Agent: {str(e)}", exc_info=True)
            raise
    
    async def process(self, query: str, context: dict = None) -> str:
        self.logger.info(f"Processing query: {query}")
        try:
            response = await self.answer_question(query)
            self.logger.debug(f"Generated response length: {len(response)}")
            return response
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise
    
    def can_handle(self, query: str) -> float:
        self.logger.debug(f"Calculating handling confidence for query: {query}")
        try:
            expertise_words = set(word.lower() for expertise in self.expertise 
                                for word in expertise.split())
            query_words = set(query.lower().split())
            confidence = len(expertise_words.intersection(query_words)) / len(query_words)
            
            self.logger.info(f"Calculated confidence score: {confidence:.2f}")
            return confidence
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {str(e)}", exc_info=True)
            return 0.0