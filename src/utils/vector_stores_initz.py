import os
from src.utils.data_manager import AgentDataManager
from src.utils.logger import setup_logger

logger = setup_logger("VectorStoresInit")

def initialize_agent_vector_stores(base_dir: str = "VITA"):
    """Initialize vector stores for all agents."""
    logger.info(f"Starting vector store initialization in directory: {base_dir}")
    
    try:
        # List of agents
        agents = ["mechatronic_agent", "python_agent"]
        logger.debug(f"Initializing vector stores for agents: {agents}")
        
        for agent_name in agents:
            logger.info(f"Processing agent: {agent_name}")
            
            try:
                # Initialize data manager
                logger.debug(f"Creating data manager for {agent_name}")
                data_manager = AgentDataManager(agent_name, base_dir)
                
                # Create or update vector store
                logger.debug(f"Creating/updating vector store for {agent_name}")
                data_manager.create_or_load_vector_store(force_reload=True)
                
                logger.info(f"Vector store initialized successfully for {agent_name}")
                
            except Exception as e:
                logger.error(f"Error initializing vector store for {agent_name}: {str(e)}", 
                           exc_info=True)
                logger.warning(f"Continuing with next agent")
                continue
        
        logger.info("Vector store initialization completed for all agents")
        
    except Exception as e:
        logger.error(f"Critical error in vector store initialization: {str(e)}", 
                    exc_info=True)
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting vector stores initialization script")
        initialize_agent_vector_stores()
        logger.info("Script completed successfully")
    except Exception as e:
        logger.critical(f"Script failed: {str(e)}", exc_info=True)
        raise