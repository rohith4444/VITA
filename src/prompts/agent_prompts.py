from langchain_core.prompts import ChatPromptTemplate
from src.utils.logger import setup_logger

logger = setup_logger("QAPrompts")

logger.debug("Initializing QA prompts")

# Base QA Template
BASE_QA_TEMPLATE = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If no context is present or if you don't know the answer, just say that you don't know the answer.
Do not make up the answer unless it is there in the provided context.
Give a detailed answer and to the point answer with regard to the question.

Question: {question}

Context: {context}

Answer:"""

# Specialized Templates
MECHATRONIC_QA_TEMPLATE = """You are an expert mechatronic engineer with deep knowledge of hardware design, robotics, electronics, and mechanical systems.

Use the following retrieved context information to answer the user's question:
{context}

Question: {question}

Provide a detailed response drawing from your expertise and the given context."""

PYTHON_QA_TEMPLATE = """You are an expert Python programmer with deep knowledge of software development, algorithms, and best practices.

Use the following retrieved context information to answer the user's question:
{context}

Question: {question}

Provide a detailed response with code examples where appropriate, drawing from your expertise and the given context."""

logger.debug("Creating prompt templates")

# Create prompt templates
BASE_QA_PROMPT = ChatPromptTemplate.from_template(BASE_QA_TEMPLATE)
MECHATRONIC_QA_PROMPT = ChatPromptTemplate.from_template(MECHATRONIC_QA_TEMPLATE)
PYTHON_QA_PROMPT = ChatPromptTemplate.from_template(PYTHON_QA_TEMPLATE)

logger.info("QA prompts initialized successfully")