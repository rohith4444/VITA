from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document

class DocumentProcessor:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Define loaders for different file types
        self.loaders = {
            '.pdf': (PyMuPDFLoader, {}),
            # Add more loaders as needed
        }

    def load_directory(self, directory_path: str, file_type: str = '.pdf') -> List[Document]:
        """Load all documents of a specific type from a directory."""
        if file_type not in self.loaders:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        loader_cls, loader_kwargs = self.loaders[file_type]
        loader = DirectoryLoader(
            path=directory_path,
            glob=f"**/*{file_type}",
            loader_cls=loader_cls,
            loader_kwargs=loader_kwargs,
            show_progress=True
        )
        return loader.load()

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks."""
        return self.text_splitter.split_documents(documents)

    def process_documents(self, directory_path: str, file_type: str = '.pdf') -> List[Document]:
        """Load and process documents from a directory."""
        # Load documents
        documents = self.load_directory(directory_path, file_type)
        
        # Split into chunks
        chunked_documents = self.split_documents(documents)
        
        return chunked_documents