# src/chains/rephrasing/chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.llm import get_llm

class QueryRephraser:
    def __init__(self):
        self.llm = get_llm()
        self.chain = self._build_chain()
    
    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Act as a question re-writer and perform the following task:
                      - Convert the following input question to a better version that is optimized for web search.
                      - When re-writing, look at the input question and try to reason about the underlying semantic intent / meaning."""),
            ("human", """Here is the initial question: {question}
                      Formulate an improved question.""")
        ])
        
        return prompt | self.llm | StrOutputParser()
    
    def rephrase(self, question: str) -> str:
        return self.chain.invoke({"question": question})