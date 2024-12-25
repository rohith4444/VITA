from typing import List, TypedDict
from langchain.docstore.document import Document

class AgentGraphState(TypedDict):
    question: str 
    generation: str
    web_search_needed: str
    documents: List[Document]
    agent_name: str
