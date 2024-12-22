from langchain.llms import OpenAI
from agents.mechatronic_agent import MechatronicAgent
from agents.python_agent import PythonAgent

classification_prompt = """
You are a supervising AI managing two agents:
1. Mechatronic Engineer: Specializes in hardware and engineering-related queries.
2. Python Coder: Specializes in software, coding, and programming-related queries.

Analyze the following user query and decide which agent should handle it. Respond with only the agent's name.

Query: "{query}"
"""

class SupervisingAgent:
    def __init__(self, llm: OpenAI):
        self.llm = llm
        self.agents = {
            "Mechatronic Engineer": MechatronicAgent(),
            "Python Coder": PythonAgent()
        }

    def classify_query(self, query: str) -> str:
        """Use the LLM to classify the query and return the agent's name."""
        prompt = classification_prompt.format(query=query)
        response = self.llm(prompt)
        return response.strip()

    def route_query(self, query: str) -> str:
        """Route the query to the appropriate agent based on classification."""
        agent_name = self.classify_query(query)
        agent = self.agents.get(agent_name)
        if agent:
            return agent.process_query(query)
        else:
            return f"Sorry, I couldn't determine the right agent for your query."
