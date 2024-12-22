from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_directory_loader(file_type, directory_path):
    """Create a DirectoryLoader for a specific file type."""
    from langchain_community.document_loaders import PyMuPDFLoader

    loaders = {
        ".pdf": (PyMuPDFLoader, {}),
    }

    if file_type not in loaders:
        raise ValueError(f"Unsupported file type: {file_type}")

    loader_cls, loader_kwargs = loaders[file_type]
    return DirectoryLoader(
        path=directory_path,
        glob=f"**/*{file_type}",
        loader_cls=loader_cls,
        loader_kwargs=loader_kwargs,
        show_progress=True
    )

def initialize_vector_db(data_path: str, vector_db_path: str):
    """Load documents and initialize the vector database."""
    loader = create_directory_loader(".pdf", data_path)
    documents = loader.load()
    
    # Split documents into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)

    # Initialize and persist the vector database
    vectorstore = Chroma.from_documents(docs, embedding_function=OpenAIEmbeddings())
    vectorstore.persist(persist_directory=vector_db_path)
    print(f"Vector database initialized at {vector_db_path}")
