from typing import Optional, Any
from langchain_chroma import Chroma
from langchain.retrievers import MultiQueryRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter, CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from src.retrievers.retrieval_strategies import RetrievalStrategy
from src.utils.llm import get_llm
from src.utils.logger import setup_logger

class RetrievalFactory:
    """Factory for creating different types of retrievers."""
    
    def __init__(self, vector_store: Chroma):
        self.logger = setup_logger("RetrievalFactory")
        self.logger.info("Initializing RetrievalFactory")
        
        try:
            self.vector_store = vector_store
            self.logger.debug("Getting LLM instance")
            self.llm = get_llm()
            self.logger.info("RetrievalFactory initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing RetrievalFactory: {str(e)}", exc_info=True)
            raise
    
    def create_retriever(self, 
                        strategy: RetrievalStrategy,
                        k: int = 3,
                        reranker_model: str = "BAAI/bge-reranker-large",
                        **kwargs) -> Any:
        """Create a retriever based on the specified strategy."""
        self.logger.info(f"Creating retriever with strategy: {strategy.value}")
        self.logger.debug(f"Parameters: k={k}, reranker_model={reranker_model}")
        
        try:
            # Base similarity retriever
            self.logger.debug("Creating base similarity retriever")
            base_retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
            
            if strategy == RetrievalStrategy.BASIC:
                self.logger.info("Using basic similarity retriever")
                return base_retriever
                
            elif strategy == RetrievalStrategy.COMPRESSION:
                self.logger.debug("Creating compression retriever")
                filter_chain = LLMChainFilter.from_llm(llm=self.llm)
                retriever = ContextualCompressionRetriever(
                    base_compressor=filter_chain,
                    base_retriever=base_retriever
                )
                self.logger.info("Compression retriever created successfully")
                return retriever
                
            elif strategy == RetrievalStrategy.MULTI_QUERY:
                self.logger.debug("Creating multi-query retriever")
                retriever = MultiQueryRetriever.from_llm(
                    retriever=base_retriever,
                    llm=self.llm
                )
                self.logger.info("Multi-query retriever created successfully")
                return retriever
                
            elif strategy == RetrievalStrategy.CHAINED:
                self.logger.debug("Creating chained retriever")
                
                # First level: Compression retriever
                self.logger.debug("Setting up compression layer")
                filter_chain = LLMChainFilter.from_llm(llm=self.llm)
                compression_retriever = ContextualCompressionRetriever(
                    base_compressor=filter_chain,
                    base_retriever=base_retriever
                )
                
                # Second level: Reranker
                self.logger.debug(f"Setting up reranker with model: {reranker_model}")
                reranker = HuggingFaceCrossEncoder(model_name=reranker_model)
                reranker_compressor = CrossEncoderReranker(model=reranker, top_n=k)
                
                # Final chained retriever
                retriever = ContextualCompressionRetriever(
                    base_compressor=reranker_compressor,
                    base_retriever=compression_retriever
                )
                self.logger.info("Chained retriever created successfully")
                return retriever
            
            else:
                error_msg = f"Unknown retrieval strategy: {strategy}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            self.logger.error(f"Error creating retriever: {str(e)}", exc_info=True)
            raise