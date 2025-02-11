from langchain_core.prompts import ChatPromptTemplate
from src.utils.logger import setup_logger

logger = setup_logger("GradingPrompts")

logger.debug("Initializing grading system prompt")
GRADING_SYSTEM_PROMPT = """You are an expert grader assessing relevance of a retrieved document to a user question.
Follow these instructions for grading:
- If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.
- Your grade should be either 'yes' or 'no' to indicate whether the document is relevant to the question or not."""

logger.debug("Creating grading prompt template")
GRADING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", GRADING_SYSTEM_PROMPT),
    ("human", """Retrieved document:
{document}

User question:
{question}"""),
])

logger.info("Grading prompts initialized successfully")