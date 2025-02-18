import os
import sys
from pathlib import Path

# Get the project root directory (parent of scripts folder)
project_root = Path(__file__).parent.parent
backend_dir = project_root / 'backend'

# Add both project root and backend to Python path
sys.path.extend([str(project_root), str(backend_dir)])

import os
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from core.logging.logger import setup_logger
from memory.memory_manager import MemoryManager
from agents.project_manager.agent import ProjectManagerAgent
from agents.project_manager.state_graph import create_initial_state
from backend.config import config

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
    memory_manager = None
    
    try:
        # Initialize Memory Manager
        memory_manager = await MemoryManager.create(config.database_url())
        logger.info("Memory Manager initialized")

        # Initialize Project Manager Agent
        agent_id = f"pm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        pm_agent = ProjectManagerAgent(
            agent_id=agent_id,
            name="Project Manager",
            memory_manager=memory_manager
        )
        logger.info(f"Project Manager Agent initialized with ID: {agent_id}")

        # Create initial state
        initial_state = create_initial_state(project_description)
        logger.info("Created initial state")
        logger.debug(f"Initial state: {initial_state}")

        # Run the agent
        logger.info("Starting Project Manager workflow")
        result = await pm_agent.run(initial_state)
        
        # Verify result
        if not result:
            raise ValueError("Project Manager execution produced no result")
            
        logger.info("Project Manager execution completed")
        logger.debug(f"Execution result: {result}")
        
        # Generate final report
        report = await pm_agent.generate_report()
        logger.info("Generated final report")
        logger.debug(f"Final report: {report}")

        return result

    except Exception as e:
        logger.error(f"Error running Project Manager: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        if memory_manager:
            try:
                await memory_manager.cleanup()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")

async def main():
    try:
        project_description = """
        Create a web application for task management with the following features:
        - User authentication
        - Task creation and assignment
        - Project organization
        - Progress tracking
        - Team collaboration
        """

        result = await run_project_manager(project_description)
        
        if result:
            print("\nFinal Project Plan:")
            try:
                print(json.dumps(result, indent=2))
            except TypeError as e:
                logger.error(f"Error serializing result: {str(e)}")
                print("Raw result:", result)
        else:
            print("No result received from project manager")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error("Main execution failed", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())