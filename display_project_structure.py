import os

def display_project_structure(base_path, indent=""):
    # Define hidden files/directories to exclude
    exclude_items = {".git", "vitaenv"}
    # List items excluding the specified ones
    items = [item for item in os.listdir(base_path) if item not in exclude_items]
    for index, item in enumerate(sorted(items)):
        item_path = os.path.join(base_path, item)
        # Add tree-like symbols for visual hierarchy
        is_last = index == len(items) - 1
        branch = "└── " if is_last else "├── "
        # Print the current item
        print(f"{indent}{branch}{item}")
        # If it's a directory, recursively display its contents
        if os.path.isdir(item_path):
            new_indent = indent + ("    " if is_last else "│   ")
            display_project_structure(item_path, new_indent)

if __name__ == "__main__":
    # Use the current working directory as the base path
    base_directory = os.getcwd()
    print(f"Project structure for: {base_directory} (excluding .git and venv)")
    display_project_structure(base_directory)
