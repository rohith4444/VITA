# src/chains/grading/chain.py
from src.chains.grading.grad_models import GradeDocuments
from src.chains.grading.prompts import GRADING_PROMPT
from src.utils.llm import get_llm
from typing import List
from langchain.docstore.document import Document

class DocumentGrader:
    def __init__(self):
        self.llm = get_llm()
        self.structured_grader = self.llm.with_structured_output(GradeDocuments)
        self.chain = GRADING_PROMPT | self.structured_grader
    
    def grade_document(self, question: str, document: Document) -> bool:
        """Grade a single document."""
        result = self.chain.invoke({
            "question": question,
            "document": document.page_content
        })
        return result.binary_score.lower() == "yes"
    
    def filter_relevant_documents(self, question: str, documents: List[Document]) -> List[Document]:
        """Filter and return only relevant documents."""
        return [doc for doc in documents if self.grade_document(question, doc)]