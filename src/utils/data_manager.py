# src/utils/data_manager.py
import os
from typing import Dict, List, Optional
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class AgentDataManager:
    """Manages data loading and vector store operations for agents."""
    
    def __init__(self, agent_name: str, base_dir: str = "VITA"):
        self.agent_name = agent_name
        
        # Set up paths
        self.data_dir = os.path.join(base_dir, "data", f"{agent_name}/docs")
        self.vector_store_dir = os.path.join(base_dir, "vector_stores", agent_name)
        
        # Initialize embedding model
        self.embedding_model = OpenAIEmbeddings(model='text-embedding-3-small')
        
        # Set up document loaders
        self.loaders = {
            '.pdf': (PyMuPDFLoader, {}),
            # Add more loaders as needed
        }
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300
        )
        
        # Initialize vector store
        self.vector_store = None
    
    def load_and_process_documents(self) -> List[Document]:
        """Load and process documents from the agent's data directory."""
        documents = []
        
        # Load documents for each supported file type
        for file_type, (loader_cls, loader_kwargs) in self.loaders.items():
            loader = DirectoryLoader(
                path=self.data_dir,
                glob=f"**/*{file_type}",
                loader_cls=loader_cls,
                loader_kwargs=loader_kwargs,
                show_progress=True
            )
            try:
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {file_type} documents: {e}")
        
        # Split documents into chunks
        chunked_docs = self.text_splitter.split_documents(documents)
        return chunked_docs
    
    def create_or_load_vector_store(self, force_reload: bool = False) -> Chroma:
        """Create or load the vector store for the agent."""
        # Check if vector store already exists
        if os.path.exists(self.vector_store_dir) and not force_reload:
            print(f"Loading existing vector store for {self.agent_name}")
            self.vector_store = Chroma(
                persist_directory=self.vector_store_dir,
                collection_name=f"{self.agent_name}_collection",
                embedding_function=self.embedding_model
            )
        else:
            print(f"Creating new vector store for {self.agent_name}")
            # Load and process documents
            documents = self.load_and_process_documents()
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=documents,
                collection_name=f"{self.agent_name}_collection",
                embedding=self.embedding_model,
                collection_metadata={"hnsw:space": "cosine"},
                persist_directory=self.vector_store_dir
            )
        
        return self.vector_store
    
    def get_vector_store(self) -> Optional[Chroma]:
        """Get the current vector store instance."""
        if self.vector_store is None:
            self.create_or_load_vector_store()
        return self.vector_store