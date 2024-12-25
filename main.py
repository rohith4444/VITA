import asyncio
from typing import Optional
from src.agents.python_agent import PythonAgent
from src.agents.mechatronic_agent import MechatronicAgent
from src.agents.supervising_agent import SupervisingAgent
from src.utils.logger import setup_logger
from src.utils.env_loader import load_env_variables

logger = setup_logger("main")

async def initialize_agents() -> Optional[SupervisingAgent]:
    """Initialize the agent system"""
    try:
        logger.info("Initializing specialized agents...")
        python_agent = PythonAgent()
        mechatronic_agent = MechatronicAgent()
        
        logger.info("Initializing supervising agent...")
        supervising_agent = SupervisingAgent([python_agent, mechatronic_agent])
        
        return supervising_agent
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}", exc_info=True)
        return None

async def process_query(agent: SupervisingAgent, query: str) -> Optional[str]:
    """Process a single query"""
    try:
        logger.info(f"Processing query: {query}")
        response = await agent.process(query)
        logger.info("Query processed successfully")
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return "I apologize, but I encountered an error processing your query. Please try again."

async def main():
    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_env_variables()
        
        # Initialize the agent system
        supervising_agent = await initialize_agents()
        if not supervising_agent:
            logger.error("Failed to initialize the agent system. Exiting...")
            return

        logger.info("Multi-Agent System initialized successfully")
        print("\nMulti-Agent System")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                query = input("\nQuestion: ").strip()
                if not query:
                    continue
                    
                if query.lower() == 'exit':
                    logger.info("User requested exit")
                    break
                
                print("\nProcessing...")
                response = await process_query(supervising_agent, query)
                if response:
                    print(f"\nAnswer: {response}")
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
                print("\nAn unexpected error occurred. Please try again.")
                
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
    finally:
        logger.info("Shutting down Multi-Agent System")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")