# src/chains/qa/chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from src.utils.llm import get_llm
from typing import List
from langchain.docstore.document import Document

class QAChain:
    def __init__(self):
        self.llm = get_llm()
        self.chain = self._build_chain()
    
    def _build_chain(self):
        prompt = ChatPromptTemplate.from_template(
            """You are an assistant for question-answering tasks.
            Use the following pieces of retrieved context to answer the question.
            If no context is present or if you don't know the answer, just say that you don't know the answer.
            Do not make up the answer unless it is there in the provided context.
            Give a detailed answer and to the point answer with regard to the question.

            Question: {question}

            Context: {context}

            Answer:"""
        )
        
        return (
            {
                "context": (itemgetter("context") | RunnableLambda(self._format_docs)),
                "question": itemgetter("question")
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)
    
    def invoke(self, question: str, context: List[Document]) -> str:
        return self.chain.invoke({
            "context": context,
            "question": question
        })