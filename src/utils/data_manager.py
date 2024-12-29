import os
from typing import Dict, List, Optional
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.utils.logger import setup_logger

class AgentDataManager:
    """Manages data loading and vector store operations for agents."""
    
    def __init__(self, agent_name: str, base_dir: str = "VITA"):
        self.logger = setup_logger(f"DataManager.{agent_name}")
        self.logger.info(f"Initializing AgentDataManager for {agent_name}")
        
        try:
            self.agent_name = agent_name
            
            # Set up paths
            self.data_dir = os.path.join(base_dir, "data", f"{agent_name}/docs")
            self.vector_store_dir = os.path.join(base_dir, "vector_stores", agent_name)
            self.logger.debug(f"Data directory: {self.data_dir}")
            self.logger.debug(f"Vector store directory: {self.vector_store_dir}")
            
            # Initialize embedding model
            self.logger.debug("Initializing OpenAI embedding model")
            self.embedding_model = OpenAIEmbeddings(model='text-embedding-3-small')
            
            # Set up document loaders
            self.logger.debug("Setting up document loaders")
            self.loaders = {
                '.pdf': (PyMuPDFLoader, {}),
                # Add more loaders as needed
            }
            
            # Initialize text splitter
            self.logger.debug("Initializing text splitter")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=300
            )
            
            # Initialize vector store
            self.vector_store = None
            self.logger.info("AgentDataManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing AgentDataManager: {str(e)}", exc_info=True)
            raise
    
    def load_and_process_documents(self) -> List[Document]:
        """Load and process documents from the agent's data directory."""
        self.logger.info("Loading and processing documents")
        documents = []
        
        try:
            # Load documents for each supported file type
            for file_type, (loader_cls, loader_kwargs) in self.loaders.items():
                self.logger.debug(f"Loading {file_type} documents")
                loader = DirectoryLoader(
                    path=self.data_dir,
                    glob=f"**/*{file_type}",
                    loader_cls=loader_cls,
                    loader_kwargs=loader_kwargs,
                    show_progress=True
                )
                try:
                    docs = loader.load()
                    self.logger.debug(f"Loaded {len(docs)} {file_type} documents")
                    documents.extend(docs)
                except Exception as e:
                    self.logger.error(f"Error loading {file_type} documents: {str(e)}", exc_info=True)
            
            # Split documents into chunks
            self.logger.debug(f"Splitting {len(documents)} documents into chunks")
            chunked_docs = self.text_splitter.split_documents(documents)
            self.logger.info(f"Successfully processed {len(chunked_docs)} document chunks")
            return chunked_docs
            
        except Exception as e:
            self.logger.error(f"Error in document processing: {str(e)}", exc_info=True)
            raise
    
    def create_or_load_vector_store(self, force_reload: bool = False) -> Chroma:
        """Create or load the vector store for the agent."""
        self.logger.info(f"Creating/loading vector store (force_reload={force_reload})")
        
        try:
            # Check if vector store already exists
            if os.path.exists(self.vector_store_dir) and not force_reload:
                self.logger.info(f"Loading existing vector store for {self.agent_name}")
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_dir,
                    collection_name=f"{self.agent_name}_collection",
                    embedding_function=self.embedding_model
                )
            else:
                self.logger.info(f"Creating new vector store for {self.agent_name}")
                # Load and process documents
                documents = self.load_and_process_documents()
                
                # Create vector store
                self.logger.debug("Initializing Chroma with processed documents")
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    collection_name=f"{self.agent_name}_collection",
                    embedding=self.embedding_model,
                    collection_metadata={"hnsw:space": "cosine"},
                    persist_directory=self.vector_store_dir
                )
            
            self.logger.info("Vector store operation completed successfully")
            return self.vector_store
            
        except Exception as e:
            self.logger.error(f"Error in vector store operation: {str(e)}", exc_info=True)
            raise
    
    def get_vector_store(self) -> Optional[Chroma]:
        """Get the current vector store instance."""
        self.logger.debug("Getting vector store instance")
        try:
            if self.vector_store is None:
                self.logger.debug("No existing vector store, creating new one")
                self.create_or_load_vector_store()
            return self.vector_store
        except Exception as e:
            self.logger.error(f"Error getting vector store: {str(e)}", exc_info=True)
            raise