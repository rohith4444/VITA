"""Test if environment and dependencies are set up correctly."""
import unittest
from src.utils.env_loader import load_env_variables
from src.utils.llm import get_llm
from src.utils.embeddings import get_openai_embeddings, get_hf_embeddings

class TestSetup(unittest.TestCase):
    def test_env_variables(self):
        """Test if environment variables are loaded correctly."""
        env_vars = load_env_variables()
        self.assertIsNotNone(env_vars['OPENAI_API_KEY'])
        self.assertIsNotNone(env_vars['HUGGINGFACEHUB_API_TOKEN'])
        self.assertIsNotNone(env_vars['TAVILY_API_KEY'])
    
    def test_llm_setup(self):
        """Test if LLM can be initialized."""
        llm = get_llm()
        self.assertIsNotNone(llm)
    
    def test_embeddings_setup(self):
        """Test if embeddings can be initialized."""
        openai_embeddings = get_openai_embeddings()
        hf_embeddings = get_hf_embeddings()
        self.assertIsNotNone(openai_embeddings)
        self.assertIsNotNone(hf_embeddings)

if __name__ == '__main__':
    unittest.main()