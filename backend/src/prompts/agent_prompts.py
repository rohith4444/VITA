from langchain_core.prompts import ChatPromptTemplate
from src.utils.logger import setup_logger

logger = setup_logger("QAPrompts")

logger.debug("Initializing QA prompts")

BASE_QA_TEMPLATE = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context and conversation history to answer the question.
If referencing previous conversation, be explicit about it.
If no context is present or if you don't know the answer, just say that you don't know.

Previous conversation:
{history}

Context: {context}

Question: {question}

Answer:"""

MECHATRONIC_QA_TEMPLATE = """You are an expert mechatronic engineer with deep knowledge of hardware design, robotics, electronics, and mechanical systems.

Previous conversation:
{history}

Context: {context}

Question: {question}

Provide a detailed response drawing from your expertise, the given context, and previous conversation where relevant."""

PYTHON_QA_TEMPLATE = """You are an expert Python programmer with deep knowledge of software development, algorithms, and best practices.

Previous conversation:
{history}

Context: {context}

Question: {question}

Provide a detailed response with code examples where appropriate, drawing from your expertise, the given context, and previous conversation where relevant."""

logger.debug("Creating prompt templates")

BASE_QA_PROMPT = ChatPromptTemplate.from_template(BASE_QA_TEMPLATE)
MECHATRONIC_QA_PROMPT = ChatPromptTemplate.from_template(MECHATRONIC_QA_TEMPLATE)
PYTHON_QA_PROMPT = ChatPromptTemplate.from_template(PYTHON_QA_TEMPLATE)

logger.info("QA prompts initialized successfully")