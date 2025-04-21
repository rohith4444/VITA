#!/usr/bin/env python
"""
Script to visualize agent workflow graphs.
Uses mocking to avoid database initialization while still leveraging existing agent code.
"""

import os
import sys
from pathlib import Path
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add the project root to the path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create output directory
output_dir = Path("./docs/visualizations")
output_dir.mkdir(exist_ok=True, parents=True)

# Create a mock for the MemoryManager
class MockMemoryManager:
    """Mock memory manager that doesn't require a database connection."""
    
    @classmethod
    async def create(cls, db_url):
        """Mock create method."""
        return cls()
    
    async def store(self, *args, **kwargs):
        """Mock store method."""
        return True, "mock_memory_id"
    
    async def retrieve(self, *args, **kwargs):
        """Mock retrieve method."""
        return []
    
    async def cleanup(self):
        """Mock cleanup method."""
        pass

async def visualize_agents():
    """Create and visualize Team Lead and Scrum Master agents."""
    try:
        # Temporarily patch the import system
        import sys
        from unittest.mock import patch
        
        # Now import the agent classes with patched dependencies
        with patch.dict('sys.modules', {'memory.memory_manager': MagicMock()}):
            with patch('memory.memory_manager.MemoryManager', MockMemoryManager):
                # Import agent classes only after patching
                from agents.project_manager.pm_agent import ProjectManagerAgent
                from agents.team_lead.tl_agent import TeamLeadAgent
                from agents.scrum_master.sm_agent import ScrumMasterAgent
                
                # Create a mock memory manager
                memory_manager = await MockMemoryManager.create(db_url="mock://db")
                
                print("Initializing Team Lead Agent...")
                # Initialize Project Manager Agent
                project_manager = ProjectManagerAgent(
                    agent_id="project_manager_viz",
                    name="Project Manager",
                    memory_manager=memory_manager
                )

                # Get the graph builder directly without building the graph
                pm_builder = project_manager._get_graph_builder()

                # Save the graph visualization
                pm_graph = pm_builder.compile()
                pm_bytes = pm_graph.get_graph().draw_png()
                output_path = output_dir / "project_manager_workflow.png"
                with open(output_path, "wb") as f:
                    f.write(pm_bytes)
                print(f"Successfully saved Project Manager graph to {output_path}")
                
                # Initialize Team Lead Agent
                team_lead = TeamLeadAgent(
                    agent_id="team_lead_viz",
                    name="Team Lead",
                    memory_manager=memory_manager
                )
                
                # Get the graph builder directly without building the graph
                tl_builder = team_lead._get_graph_builder()
                
                # Save the graph visualization
                tl_graph = tl_builder.compile()
                tl_bytes = tl_graph.get_graph().draw_png()
                output_path = output_dir / "team_lead_workflow.png"
                with open(output_path, "wb") as f:
                    f.write(tl_bytes)
                print(f"Successfully saved Team Lead graph to {output_path}")
                
                print("Initializing Scrum Master Agent...")
                # Initialize Scrum Master Agent
                scrum_master = ScrumMasterAgent(
                    agent_id="scrum_master_viz",
                    name="Scrum Master",
                    memory_manager=memory_manager
                )
                
                # Get the graph builder
                sm_builder = scrum_master._get_graph_builder()
                
                # Save the graph visualization
                sm_graph = sm_builder.compile()
                sm_bytes = sm_graph.get_graph().draw_png()
                output_path = output_dir / "scrum_master_workflow.png"
                with open(output_path, "wb") as f:
                    f.write(sm_bytes)
                print(f"Successfully saved Scrum Master graph to {output_path}")
                
                print("Visualizations completed successfully!")
        
    except Exception as e:
        print(f"Error during visualization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(visualize_agents())