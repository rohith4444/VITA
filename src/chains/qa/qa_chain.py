from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from src.utils.llm import get_llm
from typing import List, Optional
from langchain.docstore.document import Document
from src.prompts.agent_prompts import (
    BASE_QA_PROMPT, 
    MECHATRONIC_QA_PROMPT, 
    PYTHON_QA_PROMPT
)
from src.utils.logger import setup_logger

class QAChain:
    """Chain for question answering with different agent specializations."""
    
    def __init__(self):
        self.logger = setup_logger("QAChain")
        self.logger.info("Initializing QAChain")
        
        try:
            self.logger.debug("Getting LLM instance")
            self.llm = get_llm()
            
            # Initialize different prompt chains
            self.logger.debug("Building specialized chains")
            self.chains = {
                "base": self._build_chain(BASE_QA_PROMPT),
                "python": self._build_chain(PYTHON_QA_PROMPT),
                "mechatronic": self._build_chain(MECHATRONIC_QA_PROMPT)
            }
            
            self.logger.info("QAChain initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize QAChain: {str(e)}", exc_info=True)
            raise
    
    def _build_chain(self, prompt_template):
        """Build a chain with specific prompt template."""
        self.logger.debug(f"Building chain with template: {prompt_template}")
        try:
            return (
                {
                    "context": (itemgetter("context") | RunnableLambda(self._format_docs)),
                    "question": itemgetter("question")
                }
                | prompt_template
                | self.llm
                | StrOutputParser()
            )
        except Exception as e:
            self.logger.error(f"Error building chain: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        """Format documents into a single string."""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def invoke(self, question: str, context: List[Document], agent_type: str = "base") -> str:
        """
        Invoke the QA chain with optional agent specialization.
        
        Args:
            question: The question to answer
            context: List of context documents
            agent_type: Type of agent ("base", "python", or "mechatronic")
        """
        self.logger.info(f"Processing question with {agent_type} agent")
        self.logger.debug(f"Question: {question}")
        self.logger.debug(f"Context documents: {len(context)}")
        
        try:
            # Validate agent type
            if agent_type not in self.chains:
                self.logger.warning(f"Unknown agent type: {agent_type}, falling back to base")
                agent_type = "base"
            
            # Get appropriate chain
            chain = self.chains[agent_type]
            
            # Process query
            self.logger.debug("Invoking QA chain")
            result = chain.invoke({
                "context": context,
                "question": question
            })
            
            self.logger.debug(f"Generated answer length: {len(result)}")
            self.logger.info("Successfully generated answer")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in QA chain: {str(e)}", exc_info=True)
            raise