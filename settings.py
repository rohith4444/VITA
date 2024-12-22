import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Paths
MECHATRONIC_DB_PATH = "data/vector_db/mechatronics"
PYTHON_DB_PATH = "data/vector_db/python"

# Logging
LOG_LEVEL = "DEBUG"
