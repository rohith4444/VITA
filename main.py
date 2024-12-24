# main.py
import asyncio
from src.agents.python_agent import PythonAgent
from src.agents.mechatronic_agent import MechatronicAgent
from src.agents.supervising_agent import SupervisingAgent

async def main():
    # Initialize specialized agents
    python_agent = PythonAgent()
    mechatronic_agent = MechatronicAgent()
    supervising_agent = SupervisingAgent([python_agent, mechatronic_agent])
    
    print("Multi-Agent System")
    print("Type 'exit' to quit\n")
    
    while True:
        query = input("\nQuestion: ")
        if query.lower() == 'exit':
            break
            
        print("\nProcessing...")
        response = await supervising_agent.process(query)
        print(f"\nAnswer: {response}")

if __name__ == "__main__":
    asyncio.run(main())