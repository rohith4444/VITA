from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.docstore.document import Document

class BaseRetriever(ABC):
    """Abstract base class for retrievers."""
    
    def __init__(self, **kwargs):
        """Initialize retriever with any necessary configuration."""
        pass

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the retriever's knowledge base."""
        pass

    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve relevant documents based on a query."""
        pass

    @abstractmethod
    def update_documents(self, documents: List[Document]) -> None:
        """Update existing documents in the retriever's knowledge base."""
        pass

    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the retriever's knowledge base."""
        pass

    def similarity_score(self, query: str, document: Document) -> float:
        """Calculate similarity score between query and document."""
        raise NotImplementedError(
            "Similarity scoring not implemented for this retriever."
        )