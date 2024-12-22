from agents.base_agent import BaseAgent
from langchain.llms import OpenAI

class PythonAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Python Coder",
            vector_db_path="path_to_python_db",
            llm=OpenAI(model_name="gpt-4")
        )
