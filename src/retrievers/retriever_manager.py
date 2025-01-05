import os
from typing import Dict, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.retrievers.retrieval_factory import RetrievalFactory
from src.retrievers.retrieval_strategies import RetrievalStrategy
from src.utils.logger import setup_logger

class RetrieverManager:
    """Manages retriever instances and their lifecycle."""
    
    _instances: Dict = {}  # Cache for retriever instances
    _logger = setup_logger("RetrieverManager")
    
    @classmethod
    def get_retriever(cls, agent_name: str):
        """Get or create a retriever for an agent."""
        if agent_name not in cls._instances:
            cls._logger.info(f"Creating new retriever for {agent_name}")
            try:
                 # Get project root directory
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
                # Use absolute paths
                vector_store_path = os.path.join(root_dir, "vector_stores", agent_name.lower())
                
                collection_name = f"{agent_name.replace(' ', '_').lower()}_collection"

                # Connect to vector store
                vector_store = Chroma(
                    persist_directory=vector_store_path,
                    collection_name=collection_name,
                    embedding_function=OpenAIEmbeddings(model='text-embedding-3-small')
                )
                    # Create retriever
                factory = RetrievalFactory(vector_store)
                retriever = factory.create_retriever(
                    strategy=RetrievalStrategy.CHAINED,
                    k=3
                )
                
                cls._instances[agent_name] = retriever
                cls._logger.info(f"Retriever created successfully for {agent_name}")
                
            except Exception as e:
                cls._logger.error(f"Failed to create retriever for {agent_name}: {str(e)}")
                raise
                
        return cls._instances[agent_name]