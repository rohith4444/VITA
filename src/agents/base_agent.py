# src/agents/base_agent.py
from langgraph.graph import END, StateGraph
from src.agents.graph.state import AgentGraphState
from src.agents.graph.nodes import AgentNodes

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        # ... existing initialization ...
        self.nodes = AgentNodes(self)
        self.graph = self._build_graph()
        
    def _build_graph(self):
        graph = StateGraph(AgentGraphState)
        
        # Add nodes
        graph.add_node("retrieve", self.nodes.retrieve)
        graph.add_node("grade_documents", self.nodes.grade_documents)
        graph.add_node("rewrite_query", self.nodes.rewrite_query)
        graph.add_node("web_search", self.nodes.web_search)
        graph.add_node("generate_answer", self.nodes.generate_answer)
        
        # Build edges
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
        
        return graph.compile()

    async def answer_question(self, query: str) -> str:
        result = self.graph.invoke({
            "question": query,
            "documents": [],
            "generation": "",
            "web_search_needed": "No",
            "agent_name": self.name
        })
        return result["generation"]