# src/agents/graph/state.py
from typing import List, TypedDict
from langchain.docstore.document import Document

class AgentGraphState(TypedDict):
    question: str 
    generation: str
    web_search_needed: str
    documents: List[Document]
    agent_name: str

# src/agents/graph/nodes.py
from src.agents.graph.state import AgentGraphState
from src.utils.web_search import WebSearchTool
from src.chains.rephrasing.chain import QueryRephraser
from src.chains.qa.chain import QAChain
from src.chains.grading.chain import DocumentGrader

class AgentNodes:
    def __init__(self, agent):
        self.agent = agent
        self.web_search = WebSearchTool()
        self.rephraser = QueryRephraser()
        self.qa_chain = QAChain()
        self.grader = DocumentGrader()

    def retrieve(self, state: AgentGraphState):
        docs = self.agent.retriever.get_relevant_documents(state["question"])
        return {"documents": docs, "question": state["question"]}

    def grade_documents(self, state: AgentGraphState):
        filtered_docs = []
        web_search_needed = "Yes"
        
        for doc in state["documents"]:
            if self.grader.grade_document(state["question"], doc):
                filtered_docs.append(doc)
                web_search_needed = "No"
                
        return {
            "documents": filtered_docs,
            "question": state["question"],
            "web_search_needed": web_search_needed
        }

    def rewrite_query(self, state: AgentGraphState):
        better_question = self.rephraser.rephrase(state["question"])
        return {"documents": state["documents"], "question": better_question}

    def web_search(self, state: AgentGraphState):
        web_docs = self.web_search.search(state["question"])
        all_docs = state["documents"] + web_docs
        return {"documents": all_docs, "question": state["question"]}

    def generate_answer(self, state: AgentGraphState):
        answer = self.qa_chain.invoke(state["question"], state["documents"])
        return {
            "documents": state["documents"],
            "question": state["question"],
            "generation": answer
        }

    def decide_to_generate(self, state: AgentGraphState):
        return "rewrite_query" if state["web_search_needed"] == "Yes" else "generate_answer"