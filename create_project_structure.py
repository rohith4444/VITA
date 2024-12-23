import os

def create_file(path):
    """Create an empty file."""
    # Get the directory name of the path
    dirname = os.path.dirname(path)
    
    # Only create directory if there is a directory path
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    # Create the file
    with open(path, 'w') as f:
        pass

def setup_project():
    """Create the project structure inside current directory."""
    
    # Root level files
    root_files = [
        '.env.example',
        '.gitignore',
        'README.md',
        'requirements.txt',
        'setup.py'
    ]
    
    for file in root_files:
        if not os.path.exists(file):  # Only create if doesn't exist
            create_file(file)
    
    # Create directory structure with __init__.py files
    dirs = [
        'configs',
        'src',
        'src/agents',
        'src/prompts',
        'src/retrievers',
        'src/utils',
        'src/chains',
        'tests',
        'tests/test_agents',
        'tests/test_retrievers',
        'tests/test_chains'
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        init_file = os.path.join(dir_path, '__init__.py')
        if not os.path.exists(init_file):  # Only create if doesn't exist
            create_file(init_file)
    
    # Create configuration files
    config_files = [
        'configs/agent_config.py',
        'configs/model_config.py'
    ]
    
    for file in config_files:
        if not os.path.exists(file):  # Only create if doesn't exist
            create_file(file)
    
    # Create component files
    component_files = [
        'src/agents/base_agent.py',
        'src/agents/supervising_agent.py',
        'src/agents/mechatronic_agent.py',
        'src/agents/python_agent.py',
        'src/prompts/grading_prompts.py',
        'src/prompts/routing_prompts.py',
        'src/prompts/agent_prompts.py',
        'src/retrievers/base_retriever.py',
        'src/retrievers/rag_retriever.py',
        'src/utils/document_processor.py',
        'src/utils/embeddings.py',
        'src/utils/llm.py',
        'src/chains/grading_chain.py',
        'src/chains/rag_chain.py'
    ]
    
    for file in component_files:
        if not os.path.exists(file):  # Only create if doesn't exist
            create_file(file)
            
    print("Project structure created successfully!")

if __name__ == '__main__':
    setup_project()