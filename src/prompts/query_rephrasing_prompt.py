from langchain_core.prompts import ChatPromptTemplate
from src.utils.logger import setup_logger

logger = setup_logger("RephrasingPrompts")

logger.debug("Initializing rephrasing system prompt")
REPHRASE_SYSTEM_PROMPT = """Act as a question re-writer and perform the following task:
                      - Convert the following input question to a better version that is optimized for web search.
                      - When re-writing, look at the input question and try to reason about the underlying semantic intent / meaning."""

logger.debug("Creating rephrasing prompt template")
REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", REPHRASE_SYSTEM_PROMPT),
    ("human", """Here is the initial question: {question}
              Formulate an improved question.""")
])

logger.info("Rephrasing prompts initialized successfully")