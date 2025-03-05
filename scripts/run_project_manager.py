import os
import sys
from pathlib import Path

# Get the project root directory (parent of scripts folder)
project_root = Path(__file__).parent.parent
backend_dir = project_root / 'backend'

# Add both project root and backend to Python path
sys.path.extend([str(project_root), str(backend_dir)])

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import signal
from core.logging.logger import setup_logger
from core.tracing.service import trace_method, tracing_service
from memory.memory_manager import MemoryManager
from agents.project_manager.pm_agent import ProjectManagerAgent
from agents.project_manager.pm_state_graph import create_initial_state
from backend.config import config
from agents.core.monitoring.service import monitoring_service

# Initialize logger
logger = setup_logger("run_pm_agent")

# Shared flag for shutdown
shutdown_event = asyncio.Event()

async def cleanup(signal_received=None):
    """Cleanup function to be called on shutdown."""
    if signal_received:
        logger.info(f'Received signal: {signal_received}')
    logger.info('Starting cleanup process...')
    
    try:
        await monitoring_service.cleanup()
        logger.info('Monitoring service cleanup completed')
    except Exception as e:
        logger.error(f"Error cleaning up monitoring service: {str(e)}", exc_info=True)

def signal_handler(signum, frame):
    """Signal handler that works on both Windows and Unix."""
    logger.info(f'Signal received: {signum}')
    # Set the event
    if asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().create_task(cleanup(signum))
    shutdown_event.set()

@trace_method
async def run_project_manager(project_description: str) -> Dict[str, Any]:
    memory_manager = None
    pm_agent = None
    
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
        
        async with pm_agent:
            # Run the agent
            result = await pm_agent.run(initial_state)
            
            if not result:
                raise ValueError("Project Manager execution produced no result")
                
            logger.info("Project Manager execution completed")
            
            report = await pm_agent.generate_report()
            logger.info("Generated final report")

            return result

    except Exception as e:
        logger.error(f"Error running Project Manager: {str(e)}", exc_info=True)
        raise
    
    finally:
        if pm_agent:
            try:
                await cleanup()
            except Exception as e:
                logger.error(f"Error during monitoring cleanup: {str(e)}", exc_info=True)
                
        if memory_manager:
            try:
                await memory_manager.cleanup()
                logger.info("Memory manager cleanup completed")
            except Exception as e:
                logger.error(f"Error during memory cleanup: {str(e)}", exc_info=True)

@trace_method
async def main():
    try:
        # Setup signal handlers in a cross-platform way
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

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
        await cleanup()
    finally:
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process terminated with error: {str(e)}", exc_info=True)