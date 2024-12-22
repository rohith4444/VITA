from langchain.llms import OpenAI
from supervising_agent.supervisor import SupervisingAgent

if __name__ == "__main__":
    llm = OpenAI(model_name="gpt-4", api_key="your-api-key")
    supervising_agent = SupervisingAgent(llm=llm)

    while True:
        query = input("> ")
        if query.lower() in ["exit", "quit"]:
            break
        response = supervising_agent.route_query(query)
        print(response)
