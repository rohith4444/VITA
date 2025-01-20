import os

def create_file(path):
    """Create an empty file if it doesn't exist."""
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass

def setup_frontend():
    """Create the frontend project structure while preserving existing files."""
    
    # Files to keep (already exist from create-next-app)
    existing_files = [
        '.gitignore',
        'README.md',
        'next-env.d.ts',
        'next.config.ts',
        'package.json',
        'package-lock.json',
        'postcss.config.mjs',
        'tailwind.config.ts',
        'tsconfig.json',
        'src/app/layout.tsx',
        'src/app/page.tsx',
        'src/app/globals.css',
        'public/next.svg',
        'public/vercel.svg'
    ]
    
    # New directories to create
    new_dirs = [
        'src/components/chat',
        'src/components/common',
        'src/components/ui',
        'src/hooks',
        'src/lib/api',
        'src/lib/utils',
        'src/types',
        'src/app/chat',
        'public/assets'
    ]
    
    # New files to create
    new_files = [
        # Chat components
        'src/components/chat/ChatContainer.tsx',
        'src/components/chat/ChatInput.tsx',
        'src/components/chat/ChatMessage.tsx',
        'src/components/chat/ChatWindow.tsx',
        'src/components/chat/AgentMessage.tsx',
        'src/components/chat/UserMessage.tsx',
        'src/components/chat/FileUpload.tsx',
        
        # Common components
        'src/components/common/Header.tsx',
        'src/components/common/Footer.tsx',
        
        # UI components
        'src/components/ui/button.tsx',
        'src/components/ui/card.tsx',
        'src/components/ui/dialog.tsx',
        'src/components/ui/input.tsx',
        
        # Hooks
        'src/hooks/useChat.ts',
        'src/hooks/useAgents.ts',
        'src/hooks/useFileUpload.ts',
        
        # API and utils
        'src/lib/api/agents.ts',
        'src/lib/api/chat.ts',
        'src/lib/api/types.ts',
        'src/lib/utils/constants.ts',
        'src/lib/utils/helpers.ts',
        
        # Types
        'src/types/index.ts',
        
        # Chat pages
        'src/app/chat/page.tsx',
        'src/app/chat/loading.tsx'
    ]
    
    print("Starting frontend structure setup...")
    
    # Create directories
    for dir_path in new_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except Exception as e:
            print(f"Error creating directory {dir_path}: {str(e)}")
        
    # Create new files
    for file_path in new_files:
        try:
            create_file(file_path)
            print(f"Created file: {file_path}")
        except Exception as e:
            print(f"Error creating file {file_path}: {str(e)}")
    
    print("\nFrontend structure created successfully!")
    print("\nExisting files preserved:")
    for file in existing_files:
        if os.path.exists(file):
            print(f"- {file}")

if __name__ == '__main__':
    setup_frontend()