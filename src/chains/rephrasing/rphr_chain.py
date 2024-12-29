from langchain_core.output_parsers import StrOutputParser
from src.utils.llm import get_llm
from src.prompts.query_rephrasing_prompt import REPHRASE_PROMPT
from src.utils.logger import setup_logger

class QueryRephraser:
    """Rephrases queries to optimize them for web search."""
    
    def __init__(self):
        self.logger = setup_logger("QueryRephraser")
        self.logger.info("Initializing QueryRephraser")
        
        try:
            self.logger.debug("Getting LLM instance")
            self.llm = get_llm()
            
            self.logger.debug("Building rephrasing chain")
            self.chain = self._build_chain()
            
            self.logger.info("QueryRephraser initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize QueryRephraser: {str(e)}", exc_info=True)
            raise
    
    def _build_chain(self):
        """Build the rephrasing chain."""
        self.logger.debug("Creating chain with prompt and string output parser")
        try:
            chain = REPHRASE_PROMPT | self.llm | StrOutputParser()
            self.logger.debug("Chain built successfully")
            return chain
        except Exception as e:
            self.logger.error(f"Error building chain: {str(e)}", exc_info=True)
            raise
    
    def rephrase(self, question: str) -> str:
        """Rephrase a question for better web search results."""
        self.logger.info(f"Rephrasing question: {question}")
        try:
            rephrased = self.chain.invoke({"question": question})
            self.logger.debug(f"Original: '{question}' -> Rephrased: '{rephrased}'")
            
            # Basic validation of output
            if not rephrased or not isinstance(rephrased, str):
                raise ValueError("Invalid rephrasing output")
                
            self.logger.info("Question rephrased successfully")
            return rephrased
            
        except Exception as e:
            self.logger.error(f"Error rephrasing question: {str(e)}", exc_info=True)
            raise