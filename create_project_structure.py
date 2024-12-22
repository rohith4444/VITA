import os

def create_project_structure(base_path):
    # Define the project structure
    project_structure = {
        "agents": [],
        "core": [],
        "supervising_agent": [],
        "tests": [],
        "utils": [],
        "venv": None,  # Virtual environment directory (placeholder, will not create actual files)
        "requirements.txt": "# Add your project dependencies here\n",
        "settings.py": """# Settings file\n\nimport os\n\n# Example API Key\nAPI_KEY = os.getenv('API_KEY')\n""",
        ".env": "# Add your environment variables here\n",
        "README.md": "# Project Title\n\nProject description goes here.\n",
        "main.py": """# Main entry point\n\ndef main():\n    print('Project Initialized')\n\nif __name__ == '__main__':\n    main()\n"""
    }

    # Create directories and files
    for name, content in project_structure.items():
        item_path = os.path.join(base_path, name)
        if isinstance(content, list):  # It's a directory
            os.makedirs(item_path, exist_ok=True)
        elif isinstance(content, str):  # It's a file
            with open(item_path, 'w') as f:
                f.write(content)
        elif content is None:  # Skip creating venv
            continue

    print(f"Project structure created successfully at: {base_path}")

if __name__ == "__main__":
    # Specify the base directory (current directory by default)
    base_directory = os.getcwd()
    project_root = os.path.join(base_directory, "project_root")
    os.makedirs(project_root, exist_ok=True)
    create_project_structure(project_root)
