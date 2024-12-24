# src/utils/web_search.py
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.docstore.document import Document
from typing import List

class WebSearchTool:
    def __init__(self, max_results: int = 3, search_depth: str = 'advanced'):
        self.searcher = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            max_tokens=10000
        )
    
    def search(self, query: str) -> List[Document]:
        results = self.searcher.invoke(query)
        return [Document(page_content=result["content"]) for result in results]