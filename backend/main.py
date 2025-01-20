# main.py
import asyncio
from src.chat.session import ChatSession
from src.utils.logger import setup_logger
from src.utils.env_loader import load_env_variables
from src.agents.python_agent import PythonAgent
from src.agents.mechatronic_agent import MechatronicAgent
from src.agents.supervising_agent import SupervisingAgent

logger = setup_logger("main")

async def initialize_chat_system():
    """Initialize the chat system"""
    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_env_variables()
        
        # Create chat session first
        logger.info("Creating chat session...")
        chat_session = ChatSession(None)  # Temporarily pass None
        
        # Initialize agents with session
        logger.info("Initializing specialized agents...")
        python_agent = PythonAgent(session=chat_session)
        mechatronic_agent = MechatronicAgent(session=chat_session)
        
        # Initialize supervising agent
        logger.info("Initializing supervising agent...")
        supervising_agent = SupervisingAgent(
            [python_agent, mechatronic_agent],
            session=chat_session
        )
        
        # Set supervising agent in chat session
        chat_session.agent = supervising_agent
        
        return chat_session
        
    except Exception as e:
        logger.error(f"Failed to initialize chat system: {str(e)}", exc_info=True)
        return None
    
async def main():
    try:
        # Initialize chat system
        chat_session = await initialize_chat_system()
        if not chat_session:
            logger.error("Failed to initialize chat system. Exiting...")
            return

        logger.info("Chat system initialized successfully")
        print("\nMulti-Agent Chat System")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                # Get user input
                user_message = input("\nYou: ").strip()
                if not user_message:
                    continue
                    
                if user_message.lower() == 'exit':
                    logger.info("User requested exit")
                    break
                
                # Process message
                print("\nProcessing...")
                response = await chat_session.process_message(user_message)
                print(f"\nAssistant: {response}")
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                print("\nAn error occurred. Please try again.")
                
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
    finally:
        logger.info("Shutting down chat system")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")