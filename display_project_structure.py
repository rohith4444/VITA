import os

def display_structure(startpath, exclude_dirs=None, exclude_files=None):
    """
    Display the project structure in a tree-like format.
    Uses ASCII characters for Windows compatibility.
    """
    if exclude_dirs is None:
        exclude_dirs = [
            '__pycache__', 
            '.git', 
            '.venv', 
            'venv', 
            'node_modules', 
            '.next',  
            'backend_v1'  # Added backend_v1 to exclude list
        ]
    if exclude_files is None:
        exclude_files = ['.pyc', '.pyo', '.pyd', '.DS_Store']
        
    def should_exclude(name, is_dir=True):
        if is_dir:
            return any(excluded in name for excluded in exclude_dirs)
        return any(name.endswith(excluded) for excluded in exclude_files)

    print("\nProject Structure:")
    print("================")
    
    for root, dirs, files in os.walk(startpath):
        # Calculate the current level
        level = root.replace(startpath, '').count(os.sep)
        indent = '|   ' * (level - 1) + '+-- ' if level > 0 else ''
        
        # Print the current directory
        rel_path = os.path.relpath(root, startpath)
        if rel_path != '.':
            print(f'{indent}{os.path.basename(root)}/')
        
        # Filter and sort directories
        dirs[:] = sorted([d for d in dirs if not should_exclude(d, True)])
        
        # Filter and sort files
        files = sorted([f for f in files if not should_exclude(f, False)])
        
        # Print files
        for i, file in enumerate(files):
            if level == 0:
                print(f'+-- {file}')
            else:
                is_last = (i == len(files) - 1) and not dirs
                file_indent = '|   ' * (level - 1) + ('`-- ' if is_last else '+-- ')
                print(f'{file_indent}{file}')

def main():
    # Get the current directory
    current_dir = os.getcwd()
    display_structure(current_dir)

if __name__ == "__main__":
    main()