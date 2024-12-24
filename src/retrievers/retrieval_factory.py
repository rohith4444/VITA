# src/retrievers/retrieval_factory.py
from typing import Optional
from langchain_chroma import Chroma
from langchain.retrievers import MultiQueryRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter, CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from src.retrievers.retrieval_strategies import RetrievalStrategy
from src.utils.llm import get_llm

class RetrievalFactory:
    """Factory for creating different types of retrievers."""
    
    def __init__(self, vector_store: Chroma):
        self.vector_store = vector_store
        self.llm = get_llm()
    
    def create_retriever(self, 
                        strategy: RetrievalStrategy,
                        k: int = 3,
                        reranker_model: str = "BAAI/bge-reranker-large",
                        **kwargs) -> any:
        """
        Create a retriever based on the specified strategy.
        
        Args:
            strategy: The retrieval strategy to use
            k: Number of documents to retrieve
            reranker_model: Model name for reranker (used in CHAINED strategy)
            **kwargs: Additional arguments for specific retrievers
        """
        # Base similarity retriever
        base_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        if strategy == RetrievalStrategy.BASIC:
            return base_retriever
            
        elif strategy == RetrievalStrategy.COMPRESSION:
            filter_chain = LLMChainFilter.from_llm(llm=self.llm)
            return ContextualCompressionRetriever(
                base_compressor=filter_chain,
                base_retriever=base_retriever
            )
            
        elif strategy == RetrievalStrategy.MULTI_QUERY:
            return MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm
            )
            
        elif strategy == RetrievalStrategy.CHAINED:
            # First level: Compression retriever
            filter_chain = LLMChainFilter.from_llm(llm=self.llm)
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=filter_chain,
                base_retriever=base_retriever
            )
            
            # Second level: Reranker
            reranker = HuggingFaceCrossEncoder(model_name=reranker_model)
            reranker_compressor = CrossEncoderReranker(model=reranker, top_n=k)
            
            # Final chained retriever
            return ContextualCompressionRetriever(
                base_compressor=reranker_compressor,
                base_retriever=compression_retriever
            )
        
        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")