from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from src.utils.llm import get_llm
from typing import List, Optional, Any
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
                    "question": itemgetter("question"),
                    "history": itemgetter("history")  # Just get history, no default
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
    
    def _format_history(self, history: List) -> str:
        """Format conversation history into a string."""
        if not history:
            return "No previous conversation."
            
        try:
            # If history items are ChatMessage objects
            if hasattr(history[0], 'type'):
                return "\n".join([f"{msg.type}: {msg.content}" for msg in history])
            # If history items are strings
            elif isinstance(history[0], str):
                return "\n".join(history)
            # If history is already formatted
            else:
                self.logger.warning(f"Unexpected history format: {type(history[0])}")
                return str(history)
                
        except Exception as e:
            self.logger.error(f"Error formatting history: {str(e)}")
            return "Error retrieving conversation history."
    
    def invoke(self, question: str, context: List[Document], agent_type: str = "base", history: List = None) -> str:
        self.logger.info(f"Processing question with {agent_type} agent")
        self.logger.debug(f"Question: {question}")
        self.logger.debug(f"Context documents: {len(context)}")
        self.logger.debug(f"History messages: {len(history) if history else 0}")
        
        try:
            # First map the agent type to chain keys
            agent_type = {
                "mechatronic_engineer": "mechatronic",
                "python_coder": "python"
            }.get(agent_type, "base")
            
            # Then check if this mapped type exists in chains
            if agent_type not in self.chains:
                self.logger.warning(f"Unknown agent type: {agent_type}, falling back to base")
                agent_type = "base"
            
            chain = self.chains[agent_type]
            prompt = BASE_QA_PROMPT  # Default prompt
            
            # Get the appropriate prompt
            if agent_type == "python":
                prompt = PYTHON_QA_PROMPT
            elif agent_type == "mechatronic":
                prompt = MECHATRONIC_QA_PROMPT
                
            formatted_context = self._format_docs(context)
            formatted_history = self._format_history(history)
            
            # Format and log the complete prompt
            self.logger.debug("Complete prompt being sent to LLM:")
            self.logger.debug("-" * 50)
            formatted_messages = prompt.format_messages(
                context=formatted_context,
                question=question,
                history=formatted_history
            )
            self.logger.debug("\n".join(str(m) for m in formatted_messages))
            self.logger.debug("-" * 50)
            
            # Invoke chain
            self.logger.debug("Invoking QA chain")
            result = chain.invoke({
                "context": context,
                "question": question,
                "history": formatted_history
            })
            
            self.logger.debug(f"Generated answer length: {len(result)}")
            self.logger.info("Successfully generated answer")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in QA chain: {str(e)}", exc_info=True)
            raise