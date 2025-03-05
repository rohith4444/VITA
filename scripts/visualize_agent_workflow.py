import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import asyncio
from datetime import datetime
from typing import Dict, Any, Set, List, Tuple
import networkx as nx
import matplotlib.pyplot as plt

# Import agents
from agents.solution_architect.sa_agent import SolutionArchitectAgent
from memory.memory_manager import MemoryManager
from backend.config import config
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger("workflow_visualizer")


def create_visualization(nodes: Set[str], edges: List[Tuple[str, str]], agent_name: str) -> None:
    """
    Create a visual representation of an agent's workflow graph using networkx.
    
    Args:
        nodes: Set of node names
        edges: List of edge tuples (source, target)
        agent_name: Name of the agent for the visualization title
    """
    logger.info(f"Creating visualization for {agent_name}")

    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes and edges
    for node_name in nodes:
        graph.add_node(node_name)

    for start, end in edges:
        graph.add_edge(start, end)

    # Define layout
    pos = nx.spring_layout(graph)  # You can experiment with different layouts

    # Draw nodes
    plt.figure(figsize=(10, 6))
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=3000)
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, arrowstyle="->", arrowsize=15)
    
    # Draw labels
    nx.draw_networkx_labels(graph, pos, font_size=10, font_family="Arial")

    # Title
    plt.title(f"{agent_name} Workflow")
    plt.axis("off")

    # Save the visualization
    output_dir = Path("workflow_diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{agent_name.lower().replace(' ', '_')}.png"
    plt.savefig(output_path, format="png")
    logger.info(f"Saved visualization to {output_path}")
    plt.show()


async def visualize_agent_workflow(agent_class, agent_name: str):
    """
    Create and display a visualization of an agent's workflow.
    
    Args:
        agent_class: The agent class to visualize
        agent_name: Name of the agent
    """
    logger.info(f"Starting visualization process for {agent_name}")

    try:
        # Initialize memory manager
        memory_manager = await MemoryManager.create(config.database_url())
        logger.debug("Memory manager initialized")

        # Initialize agent
        agent_id = f"viz_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        agent = agent_class(
            agent_id=agent_id,
            name=agent_name,
            memory_manager=memory_manager
        )
        logger.debug(f"Agent initialized with ID: {agent_id}")

        # Get the graph builder from the agent
        builder = agent._get_graph_builder()
        logger.debug("Retrieved graph builder")

        # Create visualization
        create_visualization(builder.nodes, builder.edges, agent_name)

        # Cleanup
        await memory_manager.cleanup()
        logger.debug("Memory manager cleanup completed")

    except Exception as e:
        logger.error(f"Error visualizing workflow: {str(e)}", exc_info=True)
        raise


async def main():
    """
    Visualize workflows for all available agents.
    """
    logger.info("Starting workflow visualization process")

    try:
        # List of agents to visualize with their display names
        agents = [
            (SolutionArchitectAgent, "Solution Architect"),
        ]

        # Visualize each agent's workflow
        for agent_class, agent_name in agents:
            logger.info(f"Processing {agent_name} workflow")
            try:
                await visualize_agent_workflow(agent_class, agent_name)
                logger.info(f"Successfully visualized {agent_name} workflow")
            except Exception as e:
                logger.error(f"Failed to visualize {agent_name} workflow: {str(e)}")
                continue

        logger.info("Workflow visualization completed for all agents")

    except Exception as e:
        logger.error(f"Error in main visualization process: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Visualization process interrupted by user")
    except Exception as e:
        logger.error(f"Process terminated with error: {str(e)}", exc_info=True)
