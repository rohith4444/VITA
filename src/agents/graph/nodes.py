from src.agents.graph.state import AgentGraphState
from src.utils.web_search import WebSearchTool
from src.chains.rephrasing.rphr_chain import QueryRephraser
from src.chains.qa.qa_chain import QAChain
from src.chains.grading.grad_chain import DocumentGrader
from src.retrievers.retriever_manager import RetrieverManager
from src.utils.logger import setup_logger

class AgentNodes:
    """Handles all processing nodes in the agent's workflow graph."""
    
    def __init__(self, agent):
        self.logger = setup_logger(f"AgentNodes.{agent.name}")
        self.logger.info(f"Initializing AgentNodes for {agent.name}")
        
        try:
            self.agent = agent
            # Initialize tools with logging
            self.logger.debug("Initializing WebSearchTool")
            self.web_search = WebSearchTool()
            
            self.logger.debug("Initializing QueryRephraser")
            self.rephraser = QueryRephraser()
            
            self.logger.debug("Initializing QAChain")
            self.qa_chain = QAChain()
            
            self.logger.debug("Initializing DocumentGrader")
            self.grader = DocumentGrader()
            
            self.logger.info("Successfully initialized all tools")
        except Exception as e:
            self.logger.error(f"Error initializing AgentNodes: {str(e)}", exc_info=True)
            raise

    def retrieve(self, state: AgentGraphState) -> dict:
        """Retrieve relevant documents for the query."""
        self.logger.info(f"Starting document retrieval for query: {state['question']}")
        try:
            retriever = RetrieverManager.get_retriever(self.agent.name)
            docs = retriever.get_relevant_documents(state["question"])
            self.logger.debug(f"Retrieved {len(docs)} documents")
            
            for i, doc in enumerate(docs):
                self.logger.debug(f"Document {i+1} length: {len(doc.page_content)} chars")
            
            return {"documents": docs, "question": state["question"]}
            
        except Exception as e:
            self.logger.error(f"Error in document retrieval: {str(e)}", exc_info=True)
            raise

    def grade_documents(self, state: AgentGraphState) -> dict:
        """Grade retrieved documents for relevance."""
        self.logger.info("Starting document grading")
        filtered_docs = []
        web_search_needed = "Yes"
        
        try:
            for i, doc in enumerate(state["documents"]):
                self.logger.debug(f"Grading document {i+1}")
                if self.grader.grade_document(state["question"], doc):
                    filtered_docs.append(doc)
                    web_search_needed = "No"
                    self.logger.debug(f"Document {i+1} passed grading")
                else:
                    self.logger.debug(f"Document {i+1} failed grading")
            
            self.logger.info(f"Grading complete. {len(filtered_docs)} relevant documents found")
            return {
                "documents": filtered_docs,
                "question": state["question"],
                "web_search_needed": web_search_needed
            }
        except Exception as e:
            self.logger.error(f"Error in document grading: {str(e)}", exc_info=True)
            raise

    def rewrite_query(self, state: AgentGraphState) -> dict:
        """Rewrite query for web search."""
        self.logger.info(f"Rewriting query: {state['question']}")
        try:
            better_question = self.rephraser.rephrase(state["question"])
            self.logger.debug(f"Rewritten query: {better_question}")
            return {"documents": state["documents"], "question": better_question}
        except Exception as e:
            self.logger.error(f"Error in query rewriting: {str(e)}", exc_info=True)
            raise

    def web_search(self, state: AgentGraphState) -> dict:
        """Perform web search with rewritten query."""
        self.logger.info(f"Starting web search with query: {state['question']}")
        try:
            web_docs = self.web_search.search(state["question"])
            self.logger.debug(f"Found {len(web_docs)} documents from web search")
            
            all_docs = state["documents"] + web_docs
            self.logger.info(f"Combined document count: {len(all_docs)}")
            
            return {"documents": all_docs, "question": state["question"]}
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}", exc_info=True)
            raise

    def generate_answer(self, state: AgentGraphState) -> dict:
        """Generate answer using QA chain."""
        self.logger.info("Starting answer generation")
        try:
            self.logger.debug(f"Using {len(state['documents'])} documents for answer generation")
            answer = self.qa_chain.invoke(state["question"], state["documents"])
            
            self.logger.debug(f"Generated answer length: {len(answer)}")
            self.logger.info("Answer generation complete")
            
            return {
                "documents": state["documents"],
                "question": state["question"],
                "generation": answer
            }
        except Exception as e:
            self.logger.error(f"Error in answer generation: {str(e)}", exc_info=True)
            raise

    def decide_to_generate(self, state: AgentGraphState) -> str:
        """Decide whether to generate answer or search web."""
        decision = "rewrite_query" if state["web_search_needed"] == "Yes" else "generate_answer"
        self.logger.info(f"Decision made: {decision}")
        return decision