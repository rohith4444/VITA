from typing import Dict, List, Any, Optional, Set, Tuple
import os
import shutil
import json
from pathlib import Path
from enum import Enum
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.code_assembler.file_organizer")

class ComponentType(Enum):
    """Enum representing types of components that can be organized."""
    FRONTEND = "frontend"       # Frontend code (UI, components, etc.)
    BACKEND = "backend"         # Backend code (API, services, etc.)
    DATABASE = "database"       # Database scripts and models
    CONFIG = "config"           # Configuration files
    DOCUMENTATION = "documentation"  # Documentation files
    STATIC = "static"           # Static assets (images, styles, etc.)
    TEST = "test"               # Test files
    BUILD = "build"             # Build scripts and configuration
    UNKNOWN = "unknown"         # Unknown file types

class FileType(Enum):
    """Enum representing file types based on extension."""
    JAVASCRIPT = "javascript"   # .js, .jsx, .ts, .tsx
    PYTHON = "python"           # .py
    HTML = "html"               # .html, .htm
    CSS = "css"                 # .css, .scss, .sass
    JSON = "json"               # .json
    YAML = "yaml"               # .yml, .yaml
    MARKDOWN = "markdown"       # .md
    SQL = "sql"                 # .sql
    DOCKER = "docker"           # Dockerfile
    SHELL = "shell"             # .sh, .bash
    TEXT = "text"               # .txt
    UNKNOWN = "unknown"         # Unknown extensions

class ProjectType(Enum):
    """Enum representing types of projects."""
    WEB_APP = "web_app"             # Web application
    BACKEND_API = "backend_api"     # Backend API service
    FRONTEND_APP = "frontend_app"   # Frontend application
    FULL_STACK = "full_stack"       # Full stack application
    LIBRARY = "library"             # Library or package
    CLI = "cli"                     # Command-line interface application
    STATIC_SITE = "static_site"     # Static website
    UNKNOWN = "unknown"             # Unknown project type

class DirectoryStructure:
    """Class representing a project directory structure template."""
    
    def __init__(
        self,
        project_type: ProjectType,
        root_dir: str,
        directories: Dict[str, List[str]],
        mappings: Dict[ComponentType, List[str]]
    ):
        """
        Initialize a directory structure.
        
        Args:
            project_type: Type of the project
            root_dir: Root directory name
            directories: Dictionary mapping directory names to subdirectories
            mappings: Dictionary mapping component types to directory paths
        """
        self.project_type = project_type
        self.root_dir = root_dir
        self.directories = directories
        self.mappings = mappings
        
    @classmethod
    def get_structure_template(cls, project_type: ProjectType) -> 'DirectoryStructure':
        """
        Get a predefined structure template for a project type.
        
        Args:
            project_type: Type of the project
            
        Returns:
            DirectoryStructure: Template for the specified project type
        """
        if project_type == ProjectType.WEB_APP:
            return cls(
                project_type=ProjectType.WEB_APP,
                root_dir="web_app",
                directories={
                    "src": ["components", "pages", "utils", "hooks", "contexts", "styles", "assets"],
                    "public": ["images", "fonts"],
                    "api": ["routes", "controllers", "models", "middleware", "utils"],
                    "docs": ["api", "guides"],
                    "tests": ["unit", "integration", "e2e"],
                    "config": []
                },
                mappings={
                    ComponentType.FRONTEND: ["src", "public"],
                    ComponentType.BACKEND: ["api"],
                    ComponentType.DATABASE: ["api/models"],
                    ComponentType.CONFIG: ["config"],
                    ComponentType.DOCUMENTATION: ["docs"],
                    ComponentType.STATIC: ["public"],
                    ComponentType.TEST: ["tests"],
                    ComponentType.BUILD: ["."]
                }
            )
        elif project_type == ProjectType.BACKEND_API:
            return cls(
                project_type=ProjectType.BACKEND_API,
                root_dir="api_service",
                directories={
                    "src": ["routes", "controllers", "models", "middleware", "services", "utils"],
                    "config": ["env"],
                    "docs": ["api"],
                    "tests": ["unit", "integration"]
                },
                mappings={
                    ComponentType.BACKEND: ["src"],
                    ComponentType.DATABASE: ["src/models"],
                    ComponentType.CONFIG: ["config"],
                    ComponentType.DOCUMENTATION: ["docs"],
                    ComponentType.TEST: ["tests"],
                    ComponentType.BUILD: ["."]
                }
            )
        # Add more project types as needed
        else:
            # Default directory structure for unknown project types
            return cls(
                project_type=ProjectType.UNKNOWN,
                root_dir="project",
                directories={
                    "src": [],
                    "docs": [],
                    "tests": [],
                    "config": []
                },
                mappings={
                    ComponentType.FRONTEND: ["src"],
                    ComponentType.BACKEND: ["src"],
                    ComponentType.DATABASE: ["src"],
                    ComponentType.CONFIG: ["config"],
                    ComponentType.DOCUMENTATION: ["docs"],
                    ComponentType.STATIC: ["src/assets"],
                    ComponentType.TEST: ["tests"],
                    ComponentType.BUILD: ["."]
                }
            )

class Component:
    """Class representing a code component to be organized."""
    
    def __init__(
        self,
        name: str,
        content: str,
        component_type: ComponentType,
        file_type: Optional[FileType] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a code component.
        
        Args:
            name: Name of the component
            content: Content of the component
            component_type: Type of the component
            file_type: Type of the file
            file_path: Original file path (if available)
            metadata: Additional metadata
        """
        self.name = name
        self.content = content
        self.component_type = component_type
        self.file_type = file_type or self._determine_file_type(name)
        self.file_path = file_path
        self.metadata = metadata or {}
        self.target_path = None  # Will be set during organization
        
    def _determine_file_type(self, name: str) -> FileType:
        """
        Determine file type based on file name.
        
        Args:
            name: Name of the file
            
        Returns:
            FileType: Determined file type
        """
        if not name:
            return FileType.UNKNOWN
            
        extension = name.split(".")[-1].lower() if "." in name else ""
        
        if extension in ["js", "jsx", "ts", "tsx"]:
            return FileType.JAVASCRIPT
        elif extension == "py":
            return FileType.PYTHON
        elif extension in ["html", "htm"]:
            return FileType.HTML
        elif extension in ["css", "scss", "sass"]:
            return FileType.CSS
        elif extension == "json":
            return FileType.JSON
        elif extension in ["yml", "yaml"]:
            return FileType.YAML
        elif extension == "md":
            return FileType.MARKDOWN
        elif extension == "sql":
            return FileType.SQL
        elif extension in ["sh", "bash"]:
            return FileType.SHELL
        elif extension == "txt":
            return FileType.TEXT
        elif name == "Dockerfile":
            return FileType.DOCKER
        else:
            return FileType.UNKNOWN

class FileOrganizer:
    """Main class for organizing files into a project structure."""
    
    def __init__(self, project_type: ProjectType = ProjectType.UNKNOWN, output_dir: str = "output"):
        """
        Initialize the file organizer.
        
        Args:
            project_type: Type of the project
            output_dir: Base output directory
        """
        self.project_type = project_type
        self.output_dir = output_dir
        self.structure = DirectoryStructure.get_structure_template(project_type)
        self.components: List[Component] = []
        self.file_paths: Dict[str, str] = {}  # Maps component names to file paths
        
        # Create unique project directory name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.project_dir = os.path.join(
            output_dir, 
            f"{self.structure.root_dir}_{timestamp}"
        )
        
        logger.info(f"Initialized FileOrganizer for {project_type.value} project")

    @trace_method
    def add_component(self, component: Component) -> None:
        """
        Add a component to be organized.
        
        Args:
            component: Component to add
        """
        self.components.append(component)
        logger.debug(f"Added component: {component.name} ({component.component_type.value})")

    @trace_method
    def organize_files(self) -> str:
        """
        Organize all added components into a project structure.
        
        Returns:
            str: Path to the organized project directory
        """
        logger.info(f"Starting file organization for {len(self.components)} components")
        
        try:
            # Create project directory structure
            self.create_directory_structure()
            
            # Determine file placement for each component
            for component in self.components:
                target_path = self.determine_file_placement(component)
                component.target_path = target_path
                
                # Check for conflicts
                if target_path in self.file_paths.values():
                    target_path = self.handle_file_conflict(component, target_path)
                    component.target_path = target_path
                
                self.file_paths[component.name] = target_path
            
            # Write files
            self.write_files()
            
            # Generate project metadata
            self.create_project_metadata()
            
            logger.info(f"File organization completed. Project directory: {self.project_dir}")
            return self.project_dir
            
        except Exception as e:
            logger.error(f"Error during file organization: {str(e)}", exc_info=True)
            raise

    @trace_method
    def create_directory_structure(self) -> None:
        """Create the directory structure for the project."""
        logger.info(f"Creating directory structure at {self.project_dir}")
        
        try:
            # Create project directory
            os.makedirs(self.project_dir, exist_ok=True)
            
            # Create subdirectories
            for dir_name, subdirs in self.structure.directories.items():
                # Create main directory
                dir_path = os.path.join(self.project_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                
                # Create subdirectories
                for subdir in subdirs:
                    subdir_path = os.path.join(dir_path, subdir)
                    os.makedirs(subdir_path, exist_ok=True)
            
            logger.debug("Directory structure created successfully")
            
        except Exception as e:
            logger.error(f"Error creating directory structure: {str(e)}", exc_info=True)
            raise

    @trace_method
    def determine_file_placement(self, component: Component) -> str:
        """
        Determine the appropriate file path for a component.
        
        Args:
            component: Component to place
            
        Returns:
            str: Target file path for the component
        """
        logger.debug(f"Determining file placement for {component.name}")
        
        # If component already has a file path, use it as a starting point
        if component.file_path:
            # Check if the path fits within our structure
            for base_dir in self.structure.mappings.get(component.component_type, ["src"]):
                if component.file_path.startswith(base_dir):
                    return os.path.join(self.project_dir, component.file_path)
        
        # Get potential directories for this component type
        base_dirs = self.structure.mappings.get(component.component_type, ["src"])
        if not base_dirs:
            base_dirs = ["src"]  # Default to src if no mapping is found
            
        # Choose the most appropriate directory based on component name and type
        base_dir = base_dirs[0]  # Default to first option
        
        # Adjust based on component specifics
        if component.component_type == ComponentType.TEST:
            if "test" in component.name.lower() or "spec" in component.name.lower():
                if component.file_type == FileType.JAVASCRIPT:
                    base_dir = "tests/unit" if "unit" in component.name.lower() else "tests"
                elif component.file_type == FileType.PYTHON:
                    base_dir = "tests/unit" if "unit" in component.name.lower() else "tests"
        elif component.component_type == ComponentType.DOCUMENTATION:
            if component.file_type == FileType.MARKDOWN:
                base_dir = "docs"
                if "api" in component.name.lower():
                    base_dir = "docs/api"
                elif "guide" in component.name.lower():
                    base_dir = "docs/guides"
        elif component.component_type == ComponentType.FRONTEND:
            if "component" in component.name.lower():
                base_dir = "src/components"
            elif "page" in component.name.lower():
                base_dir = "src/pages"
            elif "hook" in component.name.lower():
                base_dir = "src/hooks"
            elif "context" in component.name.lower():
                base_dir = "src/contexts"
            elif "style" in component.name.lower() or component.file_type == FileType.CSS:
                base_dir = "src/styles"
        elif component.component_type == ComponentType.BACKEND:
            if "route" in component.name.lower():
                base_dir = "api/routes" if self.project_type == ProjectType.WEB_APP else "src/routes"
            elif "controller" in component.name.lower():
                base_dir = "api/controllers" if self.project_type == ProjectType.WEB_APP else "src/controllers"
            elif "model" in component.name.lower():
                base_dir = "api/models" if self.project_type == ProjectType.WEB_APP else "src/models"
            elif "middleware" in component.name.lower():
                base_dir = "api/middleware" if self.project_type == ProjectType.WEB_APP else "src/middleware"
            elif "service" in component.name.lower():
                base_dir = "api/services" if self.project_type == ProjectType.WEB_APP else "src/services"
            elif "util" in component.name.lower():
                base_dir = "api/utils" if self.project_type == ProjectType.WEB_APP else "src/utils"
        
        # Ensure the file has an appropriate extension
        file_name = component.name
        if "." not in file_name:
            # Add default extension based on file type
            if component.file_type == FileType.JAVASCRIPT:
                file_name += ".js"
            elif component.file_type == FileType.PYTHON:
                file_name += ".py"
            elif component.file_type == FileType.HTML:
                file_name += ".html"
            elif component.file_type == FileType.CSS:
                file_name += ".css"
            elif component.file_type == FileType.MARKDOWN:
                file_name += ".md"
            elif component.file_type == FileType.YAML:
                file_name += ".yml"
            elif component.file_type == FileType.JSON:
                file_name += ".json"
        
        # Construct full path
        target_path = os.path.join(self.project_dir, base_dir, file_name)
        logger.debug(f"Determined path for {component.name}: {target_path}")
        
        return target_path

    @trace_method
    def handle_file_conflict(self, component: Component, target_path: str) -> str:
        """
        Handle file conflicts by generating alternative paths.
        
        Args:
            component: Component with conflicting path
            target_path: Original target path
            
        Returns:
            str: New non-conflicting target path
        """
        logger.warning(f"File conflict detected for path: {target_path}")
        
        # Get directory and filename
        dir_name = os.path.dirname(target_path)
        file_name = os.path.basename(target_path)
        
        # Split filename and extension
        if "." in file_name:
            base_name, extension = file_name.rsplit(".", 1)
            extension = "." + extension
        else:
            base_name = file_name
            extension = ""
        
        # Generate new unique filename
        counter = 1
        while True:
            new_file_name = f"{base_name}_{counter}{extension}"
            new_path = os.path.join(dir_name, new_file_name)
            
            if new_path not in self.file_paths.values():
                logger.debug(f"Resolved conflict for {component.name}: {new_path}")
                return new_path
                
            counter += 1

    @trace_method
    def write_files(self) -> None:
        """Write all components to their target paths."""
        logger.info("Writing files to target paths")
        
        for component in self.components:
            if not component.target_path:
                logger.warning(f"No target path for component {component.name}, skipping")
                continue
                
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(component.target_path), exist_ok=True)
                
                # Write file
                with open(component.target_path, "w", encoding="utf-8") as f:
                    f.write(component.content)
                    
                logger.debug(f"Written file: {component.target_path}")
                
            except Exception as e:
                logger.error(f"Error writing file {component.target_path}: {str(e)}", exc_info=True)

    @trace_method
    def create_project_metadata(self) -> None:
        """Create project metadata file with information about the organization."""
        logger.info("Creating project metadata")
        
        try:
            metadata = {
                "project_type": self.project_type.value,
                "created_at": datetime.now().isoformat(),
                "component_count": len(self.components),
                "component_types": {},
                "file_structure": {}
            }
            
            # Count components by type
            for component in self.components:
                comp_type = component.component_type.value
                if comp_type not in metadata["component_types"]:
                    metadata["component_types"][comp_type] = 0
                metadata["component_types"][comp_type] += 1
            
            # Generate file structure
            structure = {}
            for component in self.components:
                if component.target_path:
                    rel_path = os.path.relpath(component.target_path, self.project_dir)
                    structure[rel_path] = {
                        "name": component.name,
                        "type": component.component_type.value,
                        "file_type": component.file_type.value
                    }
            
            metadata["file_structure"] = structure
            
            # Write metadata file
            metadata_path = os.path.join(self.project_dir, "project_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
                
            logger.debug(f"Created project metadata file: {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error creating project metadata: {str(e)}", exc_info=True)

# Example usage
if __name__ == "__main__":
    # Create a file organizer for a web application
    organizer = FileOrganizer(project_type=ProjectType.WEB_APP, output_dir="./output")
    
    # Add some sample components
    frontend_component = Component(
        name="App.jsx",
        content="""import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Hello World</h1>
      </header>
    </div>
  );
}

export default App;
""",
        component_type=ComponentType.FRONTEND,
        file_type=FileType.JAVASCRIPT
    )
    
    backend_component = Component(
        name="userController.js",
        content="""const User = require('../models/user');

exports.getUsers = async (req, res) => {
  try {
    const users = await User.find();
    res.json(users);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
""",
        component_type=ComponentType.BACKEND,
        file_type=FileType.JAVASCRIPT
    )
    
    # Add components to organizer
    organizer.add_component(frontend_component)
    organizer.add_component(backend_component)
    
    # Organize files
    project_dir = organizer.organize_files()
    print(f"Project organized at: {project_dir}")