import asyncio
from datetime import datetime
from typing import Dict, Any
import json
from core.logging.logger import setup_logger
from memory.memory_manager import MemoryManager
from agents.core.project_manager.agent import ProjectManagerAgent
from backend.config import Config

# Initialize logger
logger = setup_logger("run_pm_agent")

async def run_project_manager(project_description: str) -> Dict[str, Any]:
    """
    Run the Project Manager Agent with the given project description.
    
    Args:
        project_description: Project requirements/description
        
    Returns:
        Dict[str, Any]: Final project plan
    """
    try:
        # Initialize Memory Manager
        memory_manager = await MemoryManager.create(Config.database_url())
        logger.info("Memory Manager initialized")

        # Initialize Project Manager Agent
        agent_id = f"pm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        pm_agent = ProjectManagerAgent(
            agent_id=agent_id,
            name="Project Manager",
            memory_manager=memory_manager
        )
        logger.info(f"Project Manager Agent initialized with ID: {agent_id}")

        # Run the agent
        initial_state = {"input": project_description, "status": "initialized"}
        logger.info("Starting Project Manager workflow")
        
        # Execute workflow
        result = await pm_agent.run(initial_state)
        
        # Log intermediate states from memory
        working_memory = await memory_manager.retrieve(
            agent_id=agent_id,
            memory_type="WORKING"
        )
        logger.debug(f"Working Memory State: {json.dumps(working_memory, indent=2)}")

        return result

    except Exception as e:
        logger.error(f"Error running Project Manager: {str(e)}", exc_info=True)
        raise

async def main():
    # Example project description
    project_description = """
    Create a web application for task management with the following features:
    - User authentication
    - Task creation and assignment
    - Project organization
    - Progress tracking
    - Team collaboration
    """

    try:
        result = await run_project_manager(project_description)
        print("\nFinal Project Plan:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())