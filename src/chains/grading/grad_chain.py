from src.chains.grading.grad_models import GradeDocuments
from src.prompts.grading_prompts import GRADING_PROMPT
from src.utils.llm import get_llm
from typing import List
from langchain.docstore.document import Document
from src.utils.logger import setup_logger

class DocumentGrader:
    """Grades documents for relevance to a query."""
    
    def __init__(self):
        self.logger = setup_logger("DocumentGrader")
        self.logger.info("Initializing DocumentGrader")
        
        try:
            self.logger.debug("Getting LLM instance")
            self.llm = get_llm()
            
            self.logger.debug("Creating structured grader")
            self.structured_grader = self.llm.with_structured_output(GradeDocuments)
            
            self.logger.debug("Building grading chain")
            self.chain = GRADING_PROMPT | self.structured_grader
            
            self.logger.info("DocumentGrader initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize DocumentGrader: {str(e)}", exc_info=True)
            raise
    
    def grade_document(self, question: str, document: Document) -> bool:
        """Grade a single document."""
        self.logger.debug(f"Grading document for question: {question}")
        try:
            # Truncate document content for logging
            doc_preview = document.page_content[:100] + "..." if len(document.page_content) > 100 else document.page_content
            self.logger.debug(f"Document content preview: {doc_preview}")
            
            result = self.chain.invoke({
                "question": question,
                "document": document.page_content
            })
            
            is_relevant = result.binary_score.lower() == "yes"
            self.logger.info(f"Document graded as: {'relevant' if is_relevant else 'not relevant'}")
            return is_relevant
            
        except Exception as e:
            self.logger.error(f"Error grading document: {str(e)}", exc_info=True)
            raise
    
    def filter_relevant_documents(self, question: str, documents: List[Document]) -> List[Document]:
        """Filter and return only relevant documents."""
        self.logger.info(f"Filtering {len(documents)} documents for relevance")
        try:
            relevant_docs = [doc for doc in documents if self.grade_document(question, doc)]
            self.logger.info(f"Found {len(relevant_docs)} relevant documents out of {len(documents)}")
            return relevant_docs
            
        except Exception as e:
            self.logger.error(f"Error filtering documents: {str(e)}", exc_info=True)
            raise