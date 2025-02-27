import os
import sys
from pathlib import Path

# Get the project root directory
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
from agents.full_stack_developer.agent import FullStackDeveloperAgent
from agents.full_stack_developer.state_graph import create_initial_state
from backend.config import config
from agents.core.monitoring.service import monitoring_service

# Initialize logger
logger = setup_logger("run_fsd_agent")

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
async def run_full_stack_developer(task_specification: str) -> Dict[str, Any]:
    """
    Run the Full Stack Developer agent with the provided task specification.
    
    Args:
        task_specification: Description of the development task
        
    Returns:
        Dict[str, Any]: Results including code and documentation
    """
    memory_manager = None
    fsd_agent = None
    
    try:
        # Initialize Memory Manager
        memory_manager = await MemoryManager.create(config.database_url())
        logger.info("Memory Manager initialized")

        # Initialize Full Stack Developer Agent
        agent_id = f"fsd_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        fsd_agent = FullStackDeveloperAgent(
            agent_id=agent_id,
            name="Full Stack Developer",
            memory_manager=memory_manager
        )
        logger.info(f"Full Stack Developer Agent initialized with ID: {agent_id}")

        # Create initial state
        initial_state = create_initial_state(task_specification)
        logger.info("Created initial state")
        
        async with fsd_agent:
            # Run the agent
            result = await fsd_agent.run({"input": task_specification})
            
            if not result:
                raise ValueError("Full Stack Developer execution produced no result")
                
            logger.info("Full Stack Developer execution completed")
            
            report = await fsd_agent.generate_report()
            logger.info("Generated final report")

            return result

    except Exception as e:
        logger.error(f"Error running Full Stack Developer: {str(e)}", exc_info=True)
        raise
    
    finally:
        if fsd_agent:
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

def save_files_to_directory(files: Dict[str, str], directory: str) -> None:
    """
    Save files to the specified directory.
    
    Args:
        files: Dictionary mapping filenames to content
        directory: Directory to save files in
    """
    dir_path = Path(directory)
    dir_path.mkdir(exist_ok=True, parents=True)
    file_count = 0
    
    for filename, content in files.items():
        try:
            # Make sure filename doesn't try to navigate outside target directory
            safe_filename = Path(filename).name
            file_path = dir_path / safe_filename
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(exist_ok=True, parents=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            file_count += 1
            logger.info(f"Saved file: {file_path}")
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            
    logger.info(f"Saved {file_count} files to {dir_path}")

@trace_method
async def save_output(result: Dict[str, Any], output_dir: str = "generated_output") -> None:
    """
    Save the generated code and documentation to the filesystem.
    
    Args:
        result: Results from the Full Stack Developer Agent
        output_dir: Base directory for output
    """
    base_output_path = Path(output_dir)
    base_output_path.mkdir(exist_ok=True, parents=True)
    
    try:
        # Save code files
        if "generated_code" in result:
            code_base_dir = base_output_path / "code"
            
            # Process each component
            for component_name, files in result["generated_code"].items():
                component_dir = code_base_dir / component_name
                component_dir.mkdir(exist_ok=True, parents=True)
                
                # Convert paths to use component dir
                processed_files = {}
                for file_path, content in files.items():
                    # Create a safe path within the component directory
                    processed_files[file_path] = content
                
                # Save files
                save_files_to_directory(processed_files, component_dir)
                logger.info(f"Saved {len(files)} files for {component_name} component")
        
        # Save documentation
        if "documentation" in result:
            docs_dir = base_output_path / "docs"
            docs_dir.mkdir(exist_ok=True, parents=True)
            
            save_files_to_directory(result["documentation"], docs_dir)
            logger.info(f"Saved {len(result['documentation'])} documentation files")
        
        # Save full result as JSON for reference
        with open(base_output_path / "full_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"All outputs saved to {base_output_path}")
            
    except Exception as e:
        logger.error(f"Error saving outputs: {str(e)}", exc_info=True)
        raise

@trace_method
async def main():
    try:
        # Setup signal handlers in a cross-platform way
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Run Full Stack Developer Agent')
        parser.add_argument('--task', '-t', type=str, help='Task specification')
        parser.add_argument('--file', '-f', type=str, help='File containing task specification')
        parser.add_argument('--output', '-o', default='generated_output', help='Output directory')
        args = parser.parse_args()

        # Get task specification
        task_specification = None
        if args.task:
            task_specification = args.task
        elif args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                task_specification = f.read()
        else:
            # Default task if none provided
            task_specification = """
            Create a simple to-do list application with the following features:
            - Add new tasks with title, description, and due date
            - Mark tasks as complete
            - View all tasks and filter by status
            - Delete tasks
            - Store tasks in a database
            
            The application should have a clean and responsive user interface.
            """

        print("\nTask Specification:")
        print("==================")
        print(task_specification)
        print("==================\n")
        print("Starting Full Stack Developer Agent...\n")

        # Run Full Stack Developer Agent
        result = await run_full_stack_developer(task_specification)
        
        if result:
            print("\nFull Stack Developer Agent Execution Completed Successfully")
            
            # Save outputs to filesystem
            await save_output(result, args.output)
            
            # Print summary
            print("\nGeneration Summary:")
            print("==================")
            if "generated_code" in result:
                total_files = sum(len(files) for files in result["generated_code"].values())
                print(f"Generated {total_files} code files across {len(result['generated_code'])} components")
                
                # List components
                for component, files in result["generated_code"].items():
                    print(f"- {component}: {len(files)} files")
                    
            if "documentation" in result:
                print(f"\nGenerated {len(result['documentation'])} documentation files:")
                for doc_name in result["documentation"].keys():
                    print(f"- {doc_name}")
                    
            print(f"\nAll files saved to: {args.output}/")
        else:
            print("No result received from Full Stack Developer agent")
            
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