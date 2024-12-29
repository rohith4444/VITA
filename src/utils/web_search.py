from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.docstore.document import Document
from typing import List
from src.utils.logger import setup_logger

class WebSearchTool:
    """Tool for performing web searches using Tavily API."""
    
    def __init__(self, max_results: int = 3, search_depth: str = 'advanced'):
        self.logger = setup_logger("WebSearchTool")
        self.logger.info("Initializing WebSearchTool")
        
        try:
            self.logger.debug(f"Setting up Tavily search with max_results={max_results}, "
                            f"search_depth={search_depth}")
            
            self.searcher = TavilySearchResults(
                max_results=max_results,
                search_depth=search_depth,
                max_tokens=10000
            )
            
            self.max_results = max_results
            self.search_depth = search_depth
            
            self.logger.info("WebSearchTool initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSearchTool: {str(e)}", exc_info=True)
            raise
    
    def search(self, query: str) -> List[Document]:
        """
        Perform web search and return results as Documents.
        
        Args:
            query: Search query string
            
        Returns:
            List of Document objects containing search results
        """
        self.logger.info(f"Performing web search for query: {query}")
        
        try:
            # Execute search
            self.logger.debug("Invoking Tavily search")
            results = self.searcher.invoke(query)
            
            # Log search statistics
            self.logger.debug(f"Received {len(results)} results from Tavily")
            
            # Convert to documents
            documents = []
            for i, result in enumerate(results, 1):
                content = result.get("content", "")
                self.logger.debug(f"Result {i}: {len(content)} characters")
                documents.append(Document(page_content=content))
            
            self.logger.info(f"Successfully processed {len(documents)} search results into documents")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error during web search: {str(e)}", exc_info=True)
            raise