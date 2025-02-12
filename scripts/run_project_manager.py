# scripts/run_project_manager.py

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.project_manager.agent import ProjectManagerAgent
from core.logging.logger import setup_logger

async def handle_new_project(project_requirements):
    # Create logger for this runner
    logger = setup_logger("project_manager.runner")
    logger.info("Starting new project setup")
    
    try:
        # 1. Create Project Manager Agent
        pm_agent = ProjectManagerAgent("PM-001", "Project Manager")
        logger.info("Project Manager Agent created")

        # 2. Process project input
        logger.info("Processing project input")
        result = await pm_agent.process_input(project_requirements)
        logger.info("Initial processing complete")

        # 3. LLM analyzes requirements
        logger.info("Starting requirements analysis")
        analysis = await pm_agent._analyze_requirements(project_requirements)
        logger.info("Requirements analysis complete")
        if analysis.get('understood_requirements'):
            logger.info(f"Key requirements: {analysis['understood_requirements'][:2]}")

        # 4. Generate project plan
        logger.info("Generating project plan")
        plan = await pm_agent._generate_project_plan(analysis)
        logger.info(f"Project plan generated with {len(plan.get('phases', []))} phases")

        # 5. Break down tasks
        logger.info("Breaking down tasks")
        tasks = await pm_agent.task_service.generate_detailed_tasks(
            plan.get("features", [])
        )
        total_tasks = sum(len(phase['tasks']) for phase in tasks.values())
        logger.info(f"Task breakdown complete with {total_tasks} total tasks")

        # 6. Create timeline
        logger.info("Creating project timeline")
        timeline = await pm_agent.timeline_service.create_timeline(
            tasks,
            datetime.now()
        )
        duration = timeline['end_date'] - timeline['start_date']
        logger.info(f"Timeline created. Project duration: {duration.days} days")

        # 7. Monitor and report
        logger.info("Generating final progress and report")
        progress = await pm_agent.monitor_progress()
        report = await pm_agent.generate_report()
        logger.info("Final report generation complete")

        return {
            "analysis": analysis,
            "plan": plan,
            "timeline": timeline,
            "report": report
        }

    except Exception as e:
        logger.error(f"Error during project setup: {str(e)}")
        raise

async def main():
    logger = setup_logger("main")
    
    # Sample project requirements
    requirements = {
        "features": ["user_auth", "task_management"],
        "timeline": "2 months",
        "constraints": ["budget_limited"]
    }

    logger.info("=== Starting Project Manager Example ===")
    logger.info(f"Project Features: {requirements['features']}")
    logger.info(f"Timeline: {requirements['timeline']}")
    logger.info(f"Constraints: {requirements['constraints']}")

    try:
        result = await handle_new_project(requirements)
        
        logger.info("=== Project Summary ===")
        logger.info(f"Start Date: {result['timeline']['start_date']}")
        logger.info(f"End Date: {result['timeline']['end_date']}")
        logger.info(f"Critical Path Tasks: {len(result['timeline']['critical_path'])}")
        logger.info("Project setup completed successfully! ✨")
        
    except Exception as e:
        logger.error(f"Project setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())