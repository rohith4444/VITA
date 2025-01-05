from typing import Optional
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.utils.logger import setup_logger

class ChatSession:
    """Manages an individual chat session with memory"""
    
    def __init__(self, supervising_agent, session_id: str = "default"):
        self.logger = setup_logger(f"ChatSession_{session_id}")
        self.logger.info(f"Initializing chat session: {session_id}")
        
        try:
            self.session_id = session_id
            self.agent = supervising_agent
            
            # Initialize memory
            self.logger.debug("Setting up conversation memory")
            self.memory = ConversationBufferMemory(
                return_messages=True,
                memory_key="history"
            )

            
            # Create prompt template
            self.prompt = ChatPromptTemplate.from_messages([
            ("system", "When answering follow-up questions, explicitly reference information from previous responses."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}")
            ])

            # Add meta-conversation keywords
            self.meta_conversation_keywords = [
                "previous question",
                "earlier question",
                "last question",
                "what did i ask",
                "what was my question"
            ]

            self.logger.info("Chat session initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chat session: {str(e)}", exc_info=True)
            raise

    def get_chat_history(self, query):
        """Get conversation history from memory"""
        return self.memory.load_memory_variables({"query": query})["history"]

    async def process_message(self, message: str) -> str:
        """Process a message and maintain conversation history"""
        self.logger.info(f"Processing message in session {self.session_id}")
        self.logger.debug(f"Received message: {message}")
        
        try:
            # Check if this is a meta-conversation question
            if self._is_meta_question(message.lower()):
                history = self.get_chat_history({"query": message})
                if history:
                    for msg in reversed(history):
                        if msg.type == 'human':
                            return f"Your previous question was: '{msg.content}'"
                return "This is your first question in our conversation."
            
            # Normal message processing
            query = {"query": message}
            response = await self.agent.process(message)
            
            # Save context
            self.memory.save_context(
                query,
                {"output": response}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your message."

    def _is_meta_question(self, message: str) -> bool:
        """Check if message is asking about conversation history"""
        return any(keyword in message.lower() for keyword in self.meta_conversation_keywords)
    
    def clear_history(self):
        """Clear the conversation history"""
        self.logger.info(f"Clearing conversation history for session {self.session_id}")
        try:
            self.memory.clear()
            self.logger.debug("Conversation history cleared successfully")
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {str(e)}", exc_info=True)
            raise