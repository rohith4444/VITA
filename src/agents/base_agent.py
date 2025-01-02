from abc import ABC
from typing import List
from langgraph.graph import END, StateGraph
from configs.agent_config import AgentConfig  
from src.agents.graph.state import AgentGraphState
from src.agents.graph.nodes import AgentNodes
from src.utils.logger import setup_logger

class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, config: AgentConfig):
        self.logger = setup_logger(f"agent.{config.name}")
        self.logger.info(f"Initializing {config.name} agent")
        
        try:
            self.name = config.name
            self.description = config.description
            self.expertise = config.expertise
            self.tools = config.tools
            
            # Initialize components
            self.logger.debug("Initializing agent nodes")
            self.nodes = AgentNodes(self)
            
            self.logger.debug("Building agent processing graph")
            self.graph = self._build_graph()
            
            self.logger.info(f"{self.name} agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {config.name} agent: {str(e)}", exc_info=True)
            raise
        
    def _build_graph(self) -> StateGraph:
        """Build the processing graph for this agent."""
        self.logger.debug("Building state graph")
        try:
            graph = StateGraph(AgentGraphState)
            
            # Add nodes
            self.logger.debug("Adding graph nodes")
            graph.add_node("retrieve", self.nodes.retrieve)
            graph.add_node("grade_documents", self.nodes.grade_documents)
            graph.add_node("rewrite_query", self.nodes.rewrite_query)
            graph.add_node("web_search", self.nodes.web_search)
            graph.add_node("generate_answer", self.nodes.generate_answer)
            
            # Build edges
            self.logger.debug("Building graph edges")
            graph.set_entry_point("retrieve")
            graph.add_edge("retrieve", "grade_documents")
            
            graph.add_conditional_edges(
                "grade_documents",
                self.nodes.decide_to_generate,
                {
                    "rewrite_query": "rewrite_query",
                    "generate_answer": "generate_answer"
                }
            )
            
            graph.add_edge("rewrite_query", "web_search")
            graph.add_edge("web_search", "generate_answer")
            graph.add_edge("generate_answer", END)
            
            self.logger.debug("Graph compilation starting")
            compiled_graph = graph.compile()
            self.logger.debug("Graph compilation completed")
            
            return compiled_graph
            
        except Exception as e:
            self.logger.error("Failed to build graph", exc_info=True)
            raise
    
    async def answer_question(self, query: str) -> str:
        """Process a query through the agent's graph."""
        self.logger.info(f"Processing query: {query}")
        try:
            result = self.graph.invoke({
                "question": query,
                "documents": [],
                "generation": "",
                "web_search_needed": "No",
                "agent_name": self.name
            })
            
            self.logger.info("Query processed successfully")
            return result["generation"]
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise

    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the given query."""
        try:
            expertise_words = set(word.lower() for expertise in self.expertise 
                                for word in expertise.split())
            query_words = set(query.lower().split())
            confidence = len(expertise_words.intersection(query_words)) / len(query_words)
            
            self.logger.debug(f"Query handling confidence: {confidence}")
            return confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating handling confidence: {str(e)}", exc_info=True)
            return 0.0