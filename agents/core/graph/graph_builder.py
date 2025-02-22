from langgraph.graph import StateGraph
from typing import Any, Set, List, Tuple, Callable
from core.logging.logger import setup_logger

logger = setup_logger("core.graph.builder")

class WorkflowGraphBuilder:
    """Helper class to capture graph structure before compilation."""
    
    def __init__(self, state_type):
        """
        Initialize the graph builder.
        
        Args:
            state_type: The type definition for the graph state
        """
        self.graph = StateGraph(state_type)
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str]] = []
        logger.debug(f"Initialized WorkflowGraphBuilder with state type: {state_type.__name__}")
        
    def add_node(self, name: str, func: Callable, **kwargs) -> None:
        """
        Add node and track it.
        
        Args:
            name: Name of the node
            func: Function to execute at this node
            **kwargs: Additional arguments for the node
        """
        self.graph.add_node(name, func, **kwargs)
        self.nodes.add(name)
        logger.debug(f"Added node: {name}")
        
    def add_edge(self, start: str, end: str, **kwargs) -> None:
        """
        Add edge and track it.
        
        Args:
            start: Starting node name
            end: Ending node name
            **kwargs: Additional arguments for the edge
        """
        self.graph.add_edge(start, end, **kwargs)
        self.edges.append((start, end))
        logger.debug(f"Added edge: {start} -> {end}")
        
    def set_entry_point(self, node: str) -> None:
        """
        Set the entry point.
        
        Args:
            node: Name of the entry point node
        """
        self.graph.set_entry_point(node)
        logger.debug(f"Set entry point to: {node}")
        
    def compile(self) -> StateGraph:
        """
        Return compiled graph.
        
        Returns:
            StateGraph: The compiled graph ready for execution
        """
        logger.info("Compiling graph")
        return self.graph.compile()