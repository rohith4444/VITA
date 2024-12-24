# scripts/init_vector_stores.py
import os
from src.utils.data_manager import AgentDataManager

def initialize_agent_vector_stores(base_dir: str = "VITA"):
    """Initialize vector stores for all agents."""
    # List of agents
    agents = ["mechatronic_agent", "python_agent"]
    
    for agent_name in agents:
        print(f"\nInitializing vector store for {agent_name}...")
        
        # Initialize data manager
        data_manager = AgentDataManager(agent_name, base_dir)
        
        # Create or update vector store
        data_manager.create_or_load_vector_store(force_reload=True)
        
        print(f"Vector store initialized for {agent_name}")

if __name__ == "__main__":
    initialize_agent_vector_stores()