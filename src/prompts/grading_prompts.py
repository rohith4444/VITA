# src/chains/grading/prompts.py
from langchain_core.prompts import ChatPromptTemplate

GRADING_SYSTEM_PROMPT = """You are an expert grader assessing relevance of a retrieved document to a user question.
Follow these instructions for grading:
- If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.
- Your grade should be either 'yes' or 'no' to indicate whether the document is relevant to the question or not."""

GRADING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", GRADING_SYSTEM_PROMPT),
    ("human", """Retrieved document:
{document}

User question:
{question}"""),
])