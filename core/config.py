import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# API keys and other configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Paths to document directories
MECHATRONIC_DOCS_PATH = "data/mechatronics"
PYTHON_DOCS_PATH = "data/python"
