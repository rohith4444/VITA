from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_openai_embeddings(model="text-embedding-3-small"):
    """Get OpenAI embeddings model."""
    return OpenAIEmbeddings(model=model)

def get_hf_embeddings(model_name="mixedbread-ai/mxbai-embed-large-v1"):
    """Get HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(
        model_name=model_name,
    )