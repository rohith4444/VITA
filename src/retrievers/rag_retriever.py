from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter

from src.retrievers.base_retriever import BaseRetriever
from src.utils.embeddings import get_openai_embeddings
from src.utils.llm import get_llm

class RAGRetriever(BaseRetriever):
    """RAG (Retrieval Augmented Generation) retriever implementation."""
    
    def __init__(
        self,
        embedding_model=None,
        persist_directory: Optional[str] = None,
        collection_name: str = "rag_collection",
        search_type: str = "similarity",
        k: int = 3
    ):
        super().__init__()
        
        # Initialize embedding model
        self.embedding_model = embedding_model or get_openai_embeddings()
        
        # Initialize vector store
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model,
            collection_name=collection_name
        )
        
        # Initialize retriever settings
        self.search_type = search_type
        self.k = k
        
        # Initialize the base retriever
        self.base_retriever = self.vector_store.as_retriever(
            search_type=self.search_type,
            search_kwargs={"k": self.k}
        )
        
        # Initialize LLM for document filtering
        self.llm = get_llm()
        self.filter_chain = LLMChainFilter.from_llm(self.llm)
        
        # Create contextual compression retriever
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.filter_chain,
            base_retriever=self.base_retriever
        )

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        self.vector_store.add_documents(documents)
        if self.vector_store.persist_directory:
            self.vector_store.persist()

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve relevant documents using the compression retriever."""
        k = kwargs.get('k', self.k)
        documents = self.compression_retriever.get_relevant_documents(
            query,
            kwargs.get('search_kwargs', {"k": k})
        )
        return documents

    def update_documents(self, documents: List[Document]) -> None:
        """Update documents in the vector store."""
        # For Chroma, we need to delete and re-add documents
        doc_ids = [doc.metadata.get('id') for doc in documents]
        self.delete_documents(doc_ids)
        self.add_documents(documents)

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store."""
        self.vector_store.delete(document_ids)
        if self.vector_store.persist_directory:
            self.vector_store.persist()

    def similarity_score(self, query: str, document: Document) -> float:
        """Calculate similarity score between query and document."""
        query_embedding = self.embedding_model.embed_query(query)
        doc_embedding = self.embedding_model.embed_documents([document.page_content])[0]
        
        return self.vector_store.similarity_search_with_score(
            query,
            k=1,
            filter={"id": document.metadata.get('id')}
        )[0][1]