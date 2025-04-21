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
from agents.qa_test.qat_agent import QATestAgent
from backend.config import config
from agents.core.monitoring.service import monitoring_service

# Initialize logger
logger = setup_logger("run_qa_test_agent")

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
async def run_qa_test_agent(
    input_data: Dict[str, Any], 
    programming_language: str = None,
    test_framework: str = None
) -> Dict[str, Any]:
    """
    Run the QA/Test Agent to generate tests for the provided code.
    
    Args:
        input_data: Input containing code, specifications, and description
        programming_language: Optional programming language preference
        test_framework: Optional testing framework preference
        
    Returns:
        Dict[str, Any]: Test results including test cases and test code
    """
    memory_manager = None
    qa_test_agent = None
    
    try:
        # Initialize Memory Manager
        memory_manager = await MemoryManager.create(config.database_url())
        logger.info("Memory Manager initialized")

        # Initialize QA/Test Agent
        agent_id = f"qa_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        qa_test_agent = QATestAgent(
            agent_id=agent_id,
            name="qa_test",
            memory_manager=memory_manager
        )
        logger.info(f"QA/Test Agent initialized with ID: {agent_id}")

        # Add language and framework preferences if provided
        if programming_language:
            input_data["programming_language"] = programming_language
            logger.info(f"Using specified programming language: {programming_language}")
            
        if test_framework:
            input_data["test_framework"] = test_framework
            logger.info(f"Using specified test framework: {test_framework}")

        async with qa_test_agent:
            # Run the agent
            result = await qa_test_agent.run(input_data)
            
            if not result:
                raise ValueError("QA/Test Agent execution produced no result")
                
            logger.info("QA/Test Agent execution completed")
            
            report = await qa_test_agent.generate_report()
            logger.info("Generated final report")

            return result

    except Exception as e:
        logger.error(f"Error running QA/Test Agent: {str(e)}", exc_info=True)
        raise
    
    finally:
        if qa_test_agent:
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

def save_test_files(result: Dict[str, Any], output_dir: str = "generated_tests"):
    """
    Save generated test files to the filesystem.
    
    Args:
        result: Result from QA/Test Agent
        output_dir: Directory to save test files
    """
    if "test_code" not in result or not result["test_code"]:
        logger.warning("No test code found in results")
        return
        
    # Create output directory if it doesn't exist
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    
    # Save each test file
    test_code = result["test_code"]
    file_count = 0
    
    for filename, content in test_code.items():
        file_path = out_path / filename
        
        # Ensure parent directories exist for the file
        file_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(content)
            
        file_count += 1
        logger.info(f"Saved test file: {file_path}")
        
    logger.info(f"Saved {file_count} test files to {out_path}")

@trace_method
async def main():
    try:
        # Setup signal handlers in a cross-platform way
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Run QA/Test Agent')
        parser.add_argument('--lang', '-l', help='Programming language')
        parser.add_argument('--framework', '-f', help='Testing framework')
        parser.add_argument('--output', '-o', default='generated_tests', help='Output directory for test files')
        args = parser.parse_args()

        # Sample input data
        sample_code = {
            "UserController": """
                class UserController {
                    constructor(userService) {
                        this.userService = userService;
                    }
                    
                    async getUser(id) {
                        return await this.userService.findById(id);
                    }
                    
                    async createUser(userData) {
                        return await this.userService.create(userData);
                    }
                    
                    async updateUser(id, userData) {
                        return await this.userService.update(id, userData);
                    }
                    
                    async deleteUser(id) {
                        return await this.userService.delete(id);
                    }
                }
            """,
            "UserService": """
                class UserService {
                    constructor(userRepository) {
                        this.userRepository = userRepository;
                    }
                    
                    async findById(id) {
                        return await this.userRepository.findById(id);
                    }
                    
                    async create(userData) {
                        // Validate user data
                        if (!userData.email || !userData.password) {
                            throw new Error('Email and password are required');
                        }
                        
                        return await this.userRepository.create(userData);
                    }
                    
                    async update(id, userData) {
                        return await this.userRepository.update(id, userData);
                    }
                    
                    async delete(id) {
                        return await this.userRepository.delete(id);
                    }
                }
            """,
            "UserRepository": """
                class UserRepository {
                    constructor(database) {
                        this.database = database;
                        this.collection = 'users';
                    }
                    
                    async findById(id) {
                        return await this.database.findOne(this.collection, { id });
                    }
                    
                    async create(userData) {
                        return await this.database.insert(this.collection, userData);
                    }
                    
                    async update(id, userData) {
                        return await this.database.update(this.collection, { id }, userData);
                    }
                    
                    async delete(id) {
                        return await this.database.delete(this.collection, { id });
                    }
                }
            """
        }
        
        sample_specifications = {
            "component_specifications": [
                {
                    "component": "UserController",
                    "purpose": "Handle HTTP requests for user operations",
                    "functionality": [
                        "Get user by ID",
                        "Create new user",
                        "Update user",
                        "Delete user"
                    ]
                },
                {
                    "component": "UserService",
                    "purpose": "Implement business logic for user operations",
                    "functionality": [
                        "User data validation",
                        "User operations"
                    ]
                },
                {
                    "component": "UserRepository",
                    "purpose": "Manage data access for user operations",
                    "functionality": [
                        "Database operations for user entity"
                    ]
                }
            ],
            "api_specifications": [
                {
                    "api_name": "User API",
                    "description": "REST API for user management",
                    "endpoints": [
                        {
                            "path": "/users/:id",
                            "method": "GET",
                            "description": "Get user by ID"
                        },
                        {
                            "path": "/users",
                            "method": "POST",
                            "description": "Create new user"
                        },
                        {
                            "path": "/users/:id",
                            "method": "PUT",
                            "description": "Update user"
                        },
                        {
                            "path": "/users/:id",
                            "method": "DELETE",
                            "description": "Delete user"
                        }
                    ]
                }
            ]
        }

        input_data = {
            "input": "User management module for a web application",
            "code": sample_code,
            "specifications": sample_specifications
        }

        # Run QA/Test Agent
        result = await run_qa_test_agent(
            input_data, 
            programming_language=args.lang,
            test_framework=args.framework
        )
        
        if result:
            print("\nQA/Test Agent Execution Completed Successfully")
            
            # Save test files
            save_test_files(result, args.output)
            
            # Print summary
            if "test_code" in result:
                print(f"\nGenerated {len(result['test_code'])} test files")
                print(f"Files saved to: {args.output}")
                
                # Print filenames
                print("\nGenerated test files:")
                for filename in result['test_code'].keys():
                    print(f"- {filename}")
            else:
                print("No test code was generated")
        else:
            print("No result received from QA/Test agent")
            
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