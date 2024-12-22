from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI

class BaseAgent:
    def __init__(self, name: str, vector_db_path: str, llm: OpenAI):
        self.name = name
        self.vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=OpenAIEmbeddings())
        self.llm = llm

    def process_query(self, query: str) -> str:
        """Process the query using the RAG flow."""
        # Step 1: Retrieve relevant documents
        context_docs = self.retrieve_context(query)
        
        # Step 2: Generate response
        if context_docs:
            response = self.generate_response(query, context_docs)
        else:
            response = self.fallback_search(query)

        return response

    def retrieve_context(self, query: str):
        """Retrieve documents from the vector store."""
        return self.vectorstore.similarity_search(query, k=5)

    def generate_response(self, query: str, context_docs):
        """Generate a response using the retrieved documents."""
        context = "\n".join([doc.page_content for doc in context_docs])
        prompt = f"Given the query: '{query}' and the context: '{context}', generate a detailed answer."
        return self.llm(prompt)

    def fallback_search(self, query: str):
        """Fallback mechanism to handle queries with no relevant documents."""
        prompt = f"Rephrase the query '{query}' for a broader search."
        return self.llm(prompt)
