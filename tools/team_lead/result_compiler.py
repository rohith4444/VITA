from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime
import os
import shutil
import json
import copy
import uuid
from pathlib import Path
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.team_lead.result_compiler")

try:
    from agents.code_assembler.ca_agent import CodeAssemblerAgent
    from memory.memory_manager import MemoryManager
    HAS_CODE_ASSEMBLER = True
except ImportError:
    logger.warning("CodeAssemblerAgent not available, falling back to basic compilation")
    HAS_CODE_ASSEMBLER = False


class ComponentType(Enum):
    """Enum representing types of components that can be compiled."""
    CODE = "code"                    # Source code files
    DOCUMENTATION = "documentation"  # Documentation files
    CONFIG = "config"                # Configuration files
    RESOURCE = "resource"            # Resource files (images, data, etc.)
    TEST = "test"                    # Test files
    BUILD = "build"                  # Build scripts and files

class ProjectType(Enum):
    """Enum representing types of projects that can be compiled."""
    WEB_APP = "web_app"              # Web application
    MOBILE_APP = "mobile_app"        # Mobile application
    API = "api"                      # API service
    LIBRARY = "library"              # Library or package
    DESKTOP_APP = "desktop_app"      # Desktop application
    DATA_PIPELINE = "data_pipeline"  # Data processing pipeline
    GENERIC = "generic"              # Generic project type

class ValidationLevel(Enum):
    """Enum representing validation severity levels."""
    ERROR = "error"                  # Critical issue that must be fixed
    WARNING = "warning"              # Potential issue that should be reviewed
    INFO = "info"                    # Informational note

class Component:
    """Class representing a project component."""
    
    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        agent_id: str,
        content: Any,
        file_path: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.component_type = component_type if isinstance(component_type, ComponentType) else ComponentType(component_type)
        self.agent_id = agent_id
        self.content = content
        self.file_path = file_path
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.validation_status = None
        self.validation_messages = []
        
        logger.debug(f"Created component {self.id} of type {component_type.value} from agent {agent_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "component_type": self.component_type.value,
            "agent_id": self.agent_id,
            "content": self.content,
            "file_path": self.file_path,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "validation_status": self.validation_status,
            "validation_messages": self.validation_messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create a component instance from a dictionary."""
        component = cls(
            name=data["name"],
            component_type=ComponentType(data["component_type"]),
            agent_id=data["agent_id"],
            content=data["content"],
            file_path=data.get("file_path"),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {})
        )
        component.id = data.get("id", component.id)
        component.timestamp = data.get("timestamp", component.timestamp)
        component.validation_status = data.get("validation_status")
        component.validation_messages = data.get("validation_messages", [])
        return component

class ValidationMessage:
    """Class representing a validation message."""
    
    def __init__(
        self,
        level: ValidationLevel,
        message: str,
        component_id: Optional[str] = None,
        related_component_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.level = level if isinstance(level, ValidationLevel) else ValidationLevel(level)
        self.message = message
        self.component_id = component_id
        self.related_component_ids = related_component_ids or []
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        
        log_func = logger.error if level == ValidationLevel.ERROR else \
                   logger.warning if level == ValidationLevel.WARNING else \
                   logger.info
        
        log_func(f"Validation {level.value}: {message}" + 
                (f" for component {component_id}" if component_id else ""))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation message to dictionary for serialization."""
        return {
            "id": self.id,
            "level": self.level.value,
            "message": self.message,
            "component_id": self.component_id,
            "related_component_ids": self.related_component_ids,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class ProjectStructure:
    """Class representing a project structure template."""
    
    def __init__(
        self,
        project_type: ProjectType,
        root_dir: str,
        directories: Dict[str, List[str]],
        file_mappings: Dict[ComponentType, List[str]],
        required_files: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.project_type = project_type if isinstance(project_type, ProjectType) else ProjectType(project_type)
        self.root_dir = root_dir
        self.directories = directories  # e.g., {"src": ["components", "utils"], "docs": []}
        self.file_mappings = {
            k if isinstance(k, ComponentType) else ComponentType(k): v
            for k, v in file_mappings.items()
        }  # Maps component types to directory patterns
        self.required_files = required_files
        self.metadata = metadata or {}
        
        logger.info(f"Created project structure for {project_type.value} project")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project structure to dictionary for serialization."""
        return {
            "project_type": self.project_type.value,
            "root_dir": self.root_dir,
            "directories": self.directories,
            "file_mappings": {k.value: v for k, v in self.file_mappings.items()},
            "required_files": self.required_files,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectStructure':
        """Create a project structure instance from a dictionary."""
        return cls(
            project_type=ProjectType(data["project_type"]),
            root_dir=data["root_dir"],
            directories=data["directories"],
            file_mappings={ComponentType(k): v for k, v in data["file_mappings"].items()},
            required_files=data["required_files"],
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def get_default_structure(cls, project_type: ProjectType) -> 'ProjectStructure':
        """Get a default project structure for a given project type."""
        if project_type == ProjectType.WEB_APP:
            return cls(
                project_type=ProjectType.WEB_APP,
                root_dir="web_app",
                directories={
                    "src": ["components", "pages", "styles", "utils", "hooks"],
                    "public": ["images", "fonts"],
                    "docs": [],
                    "tests": ["unit", "integration"]
                },
                file_mappings={
                    ComponentType.CODE: ["src"],
                    ComponentType.DOCUMENTATION: ["docs", "."],
                    ComponentType.CONFIG: ["."],
                    ComponentType.RESOURCE: ["public"],
                    ComponentType.TEST: ["tests"]
                },
                required_files=[
                    "package.json",
                    "README.md",
                    "src/index.js"
                ]
            )
        elif project_type == ProjectType.API:
            return cls(
                project_type=ProjectType.API,
                root_dir="api_service",
                directories={
                    "src": ["controllers", "models", "routes", "middleware", "services", "utils"],
                    "config": [],
                    "docs": ["api"],
                    "tests": ["unit", "integration"]
                },
                file_mappings={
                    ComponentType.CODE: ["src"],
                    ComponentType.DOCUMENTATION: ["docs", "."],
                    ComponentType.CONFIG: ["config", "."],
                    ComponentType.RESOURCE: ["src/resources"],
                    ComponentType.TEST: ["tests"]
                },
                required_files=[
                    "package.json",
                    "README.md",
                    "src/index.js",
                    "config/default.json"
                ]
            )
        else:
            # Generic project structure
            return cls(
                project_type=ProjectType.GENERIC,
                root_dir="project",
                directories={
                    "src": [],
                    "docs": [],
                    "tests": [],
                    "resources": []
                },
                file_mappings={
                    ComponentType.CODE: ["src"],
                    ComponentType.DOCUMENTATION: ["docs", "."],
                    ComponentType.CONFIG: ["."],
                    ComponentType.RESOURCE: ["resources"],
                    ComponentType.TEST: ["tests"],
                    ComponentType.BUILD: ["."]
                },
                required_files=[
                    "README.md"
                ]
            )

class CompilationResult:
    """Class representing the result of a compilation process."""
    
    def __init__(
        self,
        project_name: str,
        project_type: ProjectType,
        output_dir: str,
        components: List[Component],
        validation_messages: List[ValidationMessage],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.project_name = project_name
        self.project_type = project_type if isinstance(project_type, ProjectType) else ProjectType(project_type)
        self.output_dir = output_dir
        self.components = components
        self.validation_messages = validation_messages
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.success = not any(msg.level == ValidationLevel.ERROR for msg in validation_messages)
        
        logger.info(f"Compilation result created for {project_name}: {'SUCCESS' if self.success else 'FAILURE'}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert compilation result to dictionary for serialization."""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "project_type": self.project_type.value,
            "output_dir": self.output_dir,
            "components": [c.to_dict() for c in self.components],
            "validation_messages": [m.to_dict() for m in self.validation_messages],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "success": self.success
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the compilation result."""
        error_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.ERROR)
        warning_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.WARNING)
        info_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.INFO)
        
        component_counts = {}
        for component in self.components:
            comp_type = component.component_type.value
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
        
        return {
            "project_name": self.project_name,
            "project_type": self.project_type.value,
            "output_dir": self.output_dir,
            "timestamp": self.timestamp,
            "success": self.success,
            "component_count": len(self.components),
            "component_types": component_counts,
            "validation_summary": {
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "has_errors": error_count > 0
            }
        }


class ProjectAssembly:
    """Class that manages the project assembly process."""
    
    def __init__(self, project_name: str, project_type: ProjectType, output_base_dir: str = "outputs"):
        self.project_name = project_name
        self.project_type = project_type if isinstance(project_type, ProjectType) else ProjectType(project_type)
        self.output_base_dir = output_base_dir
        self.components: Dict[str, Component] = {}  # Component ID to Component
        self.component_by_path: Dict[str, str] = {}  # File path to Component ID
        self.validation_messages: List[ValidationMessage] = []
        self.project_structure = ProjectStructure.get_default_structure(self.project_type)
        self.output_dir = os.path.join(
            output_base_dir, 
            f"{project_name.lower().replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info(f"Initialized project assembly for {project_name} of type {project_type.value}")
    
    @trace_method
    def register_component(
        self,
        name: str,
        component_type: ComponentType,
        agent_id: str,
        content: Any,
        file_path: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a component for the project.
        
        Args:
            name: Name of the component
            component_type: Type of component
            agent_id: ID of the agent that created the component
            content: Content of the component
            file_path: Optional file path for the component
            dependencies: Optional list of component IDs this component depends on
            metadata: Optional additional metadata
            
        Returns:
            str: Component ID
        """
        logger.info(f"Registering component {name} of type {component_type.value} from agent {agent_id}")
        
        # Create component
        component = Component(
            name=name,
            component_type=component_type,
            agent_id=agent_id,
            content=content,
            file_path=file_path,
            dependencies=dependencies,
            metadata=metadata
        )
        
        # Check for path conflicts
        if file_path and file_path in self.component_by_path:
            existing_id = self.component_by_path[file_path]
            existing_component = self.components[existing_id]
            
            # Create validation warning
            self.validation_messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Component path conflict: {file_path} already registered by agent {existing_component.agent_id}",
                    component_id=component.id,
                    related_component_ids=[existing_id],
                    metadata={"conflict_type": "path"}
                )
            )
            
            # Generate a unique path
            base_path, ext = os.path.splitext(file_path)
            new_path = f"{base_path}_from_{agent_id}{ext}"
            logger.warning(f"Path conflict detected. Changed {file_path} to {new_path}")
            component.file_path = new_path
            file_path = new_path
        
        # Store the component
        self.components[component.id] = component
        if file_path:
            self.component_by_path[file_path] = component.id
        
        # Validate the component
        self._validate_component(component)
        
        logger.info(f"Component {name} registered with ID {component.id}")
        return component.id
    
    def _validate_component(self, component: Component) -> None:
        """
        Validate a component.
        
        Args:
            component: Component to validate
        """
        # Check dependencies
        for dep_id in component.dependencies:
            if dep_id not in self.components:
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Dependency {dep_id} not found",
                        component_id=component.id,
                        metadata={"missing_dependency": dep_id}
                    )
                )
        
        # Check file path against project structure
        if component.file_path:
            valid_dirs = self.project_structure.file_mappings.get(component.component_type, [])
            
            # Check if file path matches any of the valid directories
            if not any(component.file_path.startswith(d) for d in valid_dirs):
                suggested_dir = valid_dirs[0] if valid_dirs else "."
                suggested_path = os.path.join(suggested_dir, os.path.basename(component.file_path))
                
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.INFO,
                        message=f"File path {component.file_path} may not follow project structure. Consider {suggested_path}",
                        component_id=component.id,
                        metadata={"suggested_path": suggested_path}
                    )
                )
    
    @trace_method
    def validate_all_components(self) -> List[ValidationMessage]:
        """
        Validate all registered components.
        
        Returns:
            List[ValidationMessage]: List of validation messages
        """
        logger.info("Validating all components")
        
        # Clear previous validation messages
        self.validation_messages = []
        
        # Validate each component individually
        for component in self.components.values():
            self._validate_component(component)
        
        # Validate project-level requirements
        self._validate_project_requirements()
        
        # Validate dependencies
        self._validate_dependencies()
        
        # Log validation summary
        error_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.ERROR)
        warning_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.WARNING)
        info_count = sum(1 for m in self.validation_messages if m.level == ValidationLevel.INFO)
        
        logger.info(f"Validation completed with {error_count} errors, {warning_count} warnings, and {info_count} info messages")
        return self.validation_messages
    
    def _validate_project_requirements(self) -> None:
        """Validate project-level requirements."""
        logger.debug("Validating project-level requirements")
        
        # Check required files
        for required_file in self.project_structure.required_files:
            if not any(comp.file_path == required_file for comp in self.components.values()):
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Required file {required_file} not found in project",
                        metadata={"required_file": required_file}
                    )
                )
        
        # Check component type coverage
        component_types = {comp.component_type for comp in self.components.values()}
        for comp_type in ComponentType:
            if comp_type not in component_types and comp_type != ComponentType.BUILD:
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.INFO,
                        message=f"No components of type {comp_type.value} found",
                        metadata={"missing_component_type": comp_type.value}
                    )
                )
    
    def _validate_dependencies(self) -> None:
        """Validate component dependencies."""
        logger.debug("Validating component dependencies")
        
        # Build dependency graph
        dependency_graph = {}
        for comp_id, component in self.components.items():
            dependency_graph[comp_id] = component.dependencies
        
        # Check for circular dependencies
        visited = set()
        temp_visited = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            if node in temp_visited:
                cycle_path = path + [node]
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Circular dependency detected: {' -> '.join(cycle_path)}",
                        component_id=node,
                        related_component_ids=cycle_path,
                        metadata={"cycle_path": cycle_path}
                    )
                )
                return True
            
            if node in visited:
                return False
            
            temp_visited.add(node)
            path.append(node)
            
            for dep in dependency_graph.get(node, []):
                if dep in dependency_graph and has_cycle(dep, path):
                    return True
            
            temp_visited.remove(node)
            path.pop()
            visited.add(node)
            return False
        
        for node in dependency_graph:
            if node not in visited:
                has_cycle(node, [])
    
    @trace_method
    def organize_components(self) -> Dict[str, str]:
        """
        Organize components into a project structure.
        
        Returns:
            Dict[str, str]: Mapping of component IDs to file paths
        """
        logger.info("Organizing components into project structure")
        
        # Create mapping of component IDs to file paths
        component_paths = {}
        
        # First pass: use explicit file paths
        for comp_id, component in self.components.items():
            if component.file_path:
                component_paths[comp_id] = component.file_path
        
        # Second pass: infer paths for components without explicit paths
        for comp_id, component in self.components.items():
            if comp_id not in component_paths:
                # Generate path based on component type and name
                comp_type = component.component_type
                valid_dirs = self.project_structure.file_mappings.get(comp_type, ["."])
                base_dir = valid_dirs[0] if valid_dirs else "."
                
                # Generate filename from name
                filename = component.name.lower().replace(" ", "_")
                if not filename.endswith(self._get_extension_for_type(comp_type)):
                    filename += self._get_extension_for_type(comp_type)
                
                file_path = os.path.join(base_dir, filename)
                
                # Check for path conflicts
                if file_path in {p for p in component_paths.values()}:
                    base_name, ext = os.path.splitext(filename)
                    filename = f"{base_name}_from_{component.agent_id}{ext}"
                    file_path = os.path.join(base_dir, filename)
                
                component_paths[comp_id] = file_path
                component.file_path = file_path
        
        logger.info(f"Organized {len(component_paths)} components")
        return component_paths
    
    def _get_extension_for_type(self, component_type: ComponentType) -> str:
        """Get default file extension for a component type."""
        extensions = {
            ComponentType.CODE: ".js",
            ComponentType.DOCUMENTATION: ".md",
            ComponentType.CONFIG: ".json",
            ComponentType.RESOURCE: ".txt",
            ComponentType.TEST: ".test.js",
            ComponentType.BUILD: ".sh"
        }
        return extensions.get(component_type, ".txt")
    
    @trace_method
    def generate_project(self) -> CompilationResult:
        """
        Generate the project files.
        
        Returns:
            CompilationResult: Result of the compilation process
        """
        logger.info(f"Generating project in {self.output_dir}")
        
        # Validate components
        self.validate_all_components()
        
        # Organize components
        self.organize_components()
        
        # Check if output directory exists, create if not
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            logger.debug(f"Created output directory: {self.output_dir}")
        
        # Create directory structure
        self._create_directory_structure()
        
        # Write component files
        files_written = self._write_component_files()
        
        # Create compilation result
        result = CompilationResult(
            project_name=self.project_name,
            project_type=self.project_type,
            output_dir=self.output_dir,
            components=list(self.components.values()),
            validation_messages=self.validation_messages,
            metadata={
                "files_written": files_written,
                "compilation_time": datetime.utcnow().isoformat()
            }
        )
        
        # Write compilation metadata
        self._write_compilation_metadata(result)
        
        logger.info(f"Project generation completed with {files_written} files written")
        return result
    
    def _create_directory_structure(self) -> None:
        """Create the project directory structure."""
        logger.debug("Creating directory structure")
        
        # Create base project directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create subdirectories
        for dir_name, subdirs in self.project_structure.directories.items():
            # Create main directory
            dir_path = os.path.join(self.output_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            
            # Create subdirectories
            for subdir in subdirs:
                subdir_path = os.path.join(dir_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
        
        logger.debug("Directory structure created")
    
    def _write_component_files(self) -> int:
        """
        Write component files to disk.
        
        Returns:
            int: Number of files written
        """
        logger.debug("Writing component files")
        
        files_written = 0
        
        for comp_id, component in self.components.items():
            if not component.file_path:
                logger.warning(f"Component {comp_id} has no file path, skipping")
                continue
            
            # Get absolute path
            abs_path = os.path.join(self.output_dir, component.file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            try:
                # Write file based on content type
                if isinstance(component.content, str):
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write(component.content)
                elif isinstance(component.content, (dict, list)):
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        json.dump(component.content, f, indent=2)
                elif isinstance(component.content, bytes):
                    with open(abs_path, 'wb') as f:
                        f.write(component.content)
                else:
                    # Try to convert to string
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write(str(component.content))
                
                files_written += 1
                logger.debug(f"Wrote file: {component.file_path}")
                
            except Exception as e:
                error_msg = f"Error writing component {comp_id} to {component.file_path}: {str(e)}"
                logger.error(error_msg)
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=error_msg,
                        component_id=comp_id
                    )
                )
        
        return files_written
    
    def _write_compilation_metadata(self, result: CompilationResult) -> None:
        """Write compilation metadata to disk."""
        logger.debug("Writing compilation metadata")
        
        metadata_path = os.path.join(self.output_dir, "compilation_metadata.json")
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.debug(f"Wrote compilation metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error writing compilation metadata: {str(e)}")
    
    @trace_method
    def remove_component(self, component_id: str) -> bool:
        """
        Remove a component from the project.
        
        Args:
            component_id: ID of the component to remove
            
        Returns:
            bool: True if component was removed, False otherwise
        """
        logger.info(f"Removing component {component_id}")
        
        if component_id not in self.components:
            logger.warning(f"Component {component_id} not found")
            return False
        
        component = self.components[component_id]
        
        # Remove from file path mapping
        if component.file_path and component.file_path in self.component_by_path:
            del self.component_by_path[component.file_path]
        
        # Remove component
        del self.components[component_id]
        
        # Remove from other components' dependencies
        for comp in self.components.values():
            if component_id in comp.dependencies:
                comp.dependencies.remove(component_id)
        
        logger.info(f"Component {component_id} removed")
        return True
    
    @trace_method
    def get_component(self, component_id: str) -> Optional[Component]:
        """
        Get a component by ID.
        
        Args:
            component_id: ID of the component to get
            
        Returns:
            Optional[Component]: Component if found, None otherwise
        """
        if component_id not in self.components:
            logger.warning(f"Component {component_id} not found")
            return None
        
        return self.components[component_id]
    
    @trace_method
    def get_components_by_type(self, component_type: ComponentType) -> List[Component]:
        """
        Get all components of a given type.
        
        Args:
            component_type: Type of components to get
            
        Returns:
            List[Component]: Components of the specified type
        """
        comp_type = component_type if isinstance(component_type, ComponentType) else ComponentType(component_type)
        
        components = [
            comp for comp in self.components.values()
            if comp.component_type == comp_type
        ]
        
        logger.debug(f"Found {len(components)} components of type {comp_type.value}")
        return components
    
    @trace_method
    def get_components_by_agent(self, agent_id: str) -> List[Component]:
        """
        Get all components created by a given agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List[Component]: Components created by the specified agent
        """
        components = [
            comp for comp in self.components.values()
            if comp.agent_id == agent_id
        ]
        
        logger.debug(f"Found {len(components)} components from agent {agent_id}")
        return components
    
    @trace_method
    def get_compilation_status(self) -> Dict[str, Any]:
        """
        Get the current status of the compilation process.
        
        Returns:
            Dict[str, Any]: Compilation status
        """
        logger.info("Retrieving compilation status")
        
        # Count components by type
        component_counts = {}
        for component in self.components.values():
            comp_type = component.component_type.value
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
        
        # Count validation messages by level
        validation_counts = {
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for message in self.validation_messages:
            level = message.level.value
            validation_counts[level] = validation_counts.get(level, 0) + 1
        
        # Check for required files
        missing_required = []
        for required_file in self.project_structure.required_files:
            if not any(comp.file_path == required_file for comp in self.components.values()):
                missing_required.append(required_file)
        
        return {
            "project_name": self.project_name,
            "project_type": self.project_type.value,
            "output_dir": self.output_dir,
            "component_count": len(self.components),
            "component_types": component_counts,
            "validation": validation_counts,
            "has_errors": validation_counts["error"] > 0,
            "missing_required_files": missing_required,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @trace_method
    def resolve_component_conflicts(self) -> List[Dict[str, Any]]:
        """
        Identify and resolve component conflicts.
        
        Returns:
            List[Dict[str, Any]]: List of resolved conflicts
        """
        logger.info("Resolving component conflicts")
        
        resolved_conflicts = []
        
        # Check for path conflicts
        path_conflicts = {}
        for comp_id, component in self.components.items():
            if not component.file_path:
                continue
                
            norm_path = os.path.normpath(component.file_path)
            if norm_path in path_conflicts:
                path_conflicts[norm_path].append(comp_id)
            else:
                path_conflicts[norm_path] = [comp_id]
        
        # Resolve path conflicts
        for path, conflict_ids in path_conflicts.items():
            if len(conflict_ids) <= 1:
                continue
                
            logger.warning(f"Path conflict detected for {path} among {conflict_ids}")
            
            # Keep the newest component with the original path
            conflict_components = [self.components[cid] for cid in conflict_ids]
            conflict_components.sort(key=lambda c: c.timestamp, reverse=True)
            
            # Original component keeps its path
            original_comp = conflict_components[0]
            
            # Rename other components
            for comp in conflict_components[1:]:
                base_dir = os.path.dirname(path)
                filename = os.path.basename(path)
                base_name, ext = os.path.splitext(filename)
                new_path = os.path.join(base_dir, f"{base_name}_from_{comp.agent_id}{ext}")
                
                # Update component path
                old_path = comp.file_path
                comp.file_path = new_path
                
                # Update path mapping
                if old_path in self.component_by_path:
                    del self.component_by_path[old_path]
                self.component_by_path[new_path] = comp.id
                
                # Record resolution
                resolved_conflicts.append({
                    "conflict_type": "path",
                    "original_path": old_path,
                    "new_path": new_path,
                    "component_id": comp.id,
                    "resolution": "renamed"
                })
                
                logger.info(f"Resolved path conflict for {comp.id}: {old_path} -> {new_path}")
        
        # Check for duplicate components (same name and type)
        name_type_conflicts = {}
        for comp_id, component in self.components.items():
            key = f"{component.name}_{component.component_type.value}"
            if key in name_type_conflicts:
                name_type_conflicts[key].append(comp_id)
            else:
                name_type_conflicts[key] = [comp_id]
        
        # Resolve name/type conflicts
        for key, conflict_ids in name_type_conflicts.items():
            if len(conflict_ids) <= 1:
                continue
                
            name, comp_type = key.rsplit('_', 1)
            logger.warning(f"Name/type conflict detected for {name} of type {comp_type} among {conflict_ids}")
            
            # Keep the newest component with the original path
            conflict_components = [self.components[cid] for cid in conflict_ids]
            conflict_components.sort(key=lambda c: c.timestamp, reverse=True)
            
            # Original component keeps its name
            original_comp = conflict_components[0]
            
            # Add agent ID to other components' names
            for comp in conflict_components[1:]:
                old_name = comp.name
                comp.name = f"{old_name} from {comp.agent_id}"
                
                # Record resolution
                resolved_conflicts.append({
                    "conflict_type": "name",
                    "original_name": old_name,
                    "new_name": comp.name,
                    "component_id": comp.id,
                    "resolution": "renamed"
                })
                
                logger.info(f"Resolved name conflict for {comp.id}: {old_name} -> {comp.name}")
        
        logger.info(f"Resolved {len(resolved_conflicts)} component conflicts")
        return resolved_conflicts

class ResultCompiler:
    """Main class for compiling and assembling results from multiple agents."""
    
    def __init__(self):
        self.assemblies = {}  # Dict[project_name, ProjectAssembly]
        self.completed_compilations = []  # List of CompilationResult
        
        logger.info("Initialized ResultCompiler")
    
    @trace_method
    def create_project(
        self, 
        project_name: str, 
        project_type: Union[ProjectType, str],
        output_base_dir: str = "outputs"
    ) -> str:
        """
        Create a new project assembly.
        
        Args:
            project_name: Name of the project
            project_type: Type of project
            output_base_dir: Base directory for output
            
        Returns:
            str: Project name
        """
        logger.info(f"Creating project {project_name} of type {project_type}")
        
        # Convert string to enum if needed
        if isinstance(project_type, str):
            try:
                project_type = ProjectType(project_type)
            except ValueError:
                logger.error(f"Invalid project type: {project_type}")
                project_type = ProjectType.GENERIC
        
        # Check if project already exists
        if project_name in self.assemblies:
            logger.warning(f"Project {project_name} already exists, creating new version")
            project_name = f"{project_name}_v{len([p for p in self.assemblies if p.startswith(project_name)])}"
        
        # Create assembly
        self.assemblies[project_name] = ProjectAssembly(
            project_name=project_name,
            project_type=project_type,
            output_base_dir=output_base_dir
        )
        
        logger.info(f"Created project {project_name}")
        return project_name
    
    @trace_method
    def add_component(
        self,
        project_name: str,
        name: str,
        component_type: Union[ComponentType, str],
        agent_id: str,
        content: Any,
        file_path: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a component to a project.
        
        Args:
            project_name: Name of the project
            name: Name of the component
            component_type: Type of component
            agent_id: ID of the agent that created the component
            content: Content of the component
            file_path: Optional file path for the component
            dependencies: Optional list of component IDs this component depends on
            metadata: Optional additional metadata
            
        Returns:
            Optional[str]: Component ID if added successfully, None otherwise
        """
        logger.info(f"Adding component {name} to project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        # Convert string to enum if needed
        if isinstance(component_type, str):
            try:
                component_type = ComponentType(component_type)
            except ValueError:
                logger.error(f"Invalid component type: {component_type}")
                return None
        
        # Add component to project
        assembly = self.assemblies[project_name]
        component_id = assembly.register_component(
            name=name,
            component_type=component_type,
            agent_id=agent_id,
            content=content,
            file_path=file_path,
            dependencies=dependencies,
            metadata=metadata
        )
        
        return component_id
    
    @trace_method
    def compile_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Compile a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Optional[Dict[str, Any]]: Compilation result summary if successful, None otherwise
        """
        logger.info(f"Compiling project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        assembly = self.assemblies[project_name]
        
        try:
            # Resolve conflicts
            assembly.resolve_component_conflicts()
            
            # Generate project
            result = assembly.generate_project()
            
            # Store compilation result
            self.completed_compilations.append(result)
            
            # Return summary
            summary = result.get_summary()
            logger.info(f"Project {project_name} compiled successfully: {summary['success']}")
            return summary
            
        except Exception as e:
            logger.error(f"Error compiling project {project_name}: {str(e)}", exc_info=True)
            return None
    
    @trace_method
    def get_project_status(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Optional[Dict[str, Any]]: Project status if found, None otherwise
        """
        logger.info(f"Getting status for project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        assembly = self.assemblies[project_name]
        return assembly.get_compilation_status()
    
    @trace_method
    def get_component_by_id(self, project_name: str, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a component by ID.
        
        Args:
            project_name: Name of the project
            component_id: ID of the component
            
        Returns:
            Optional[Dict[str, Any]]: Component if found, None otherwise
        """
        logger.info(f"Getting component {component_id} from project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        assembly = self.assemblies[project_name]
        component = assembly.get_component(component_id)
        
        if not component:
            logger.warning(f"Component {component_id} not found in project {project_name}")
            return None
        
        return component.to_dict()
    
    @trace_method
    def bulk_add_components(
        self,
        project_name: str,
        components: List[Dict[str, Any]],
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Add multiple components to a project at once.
        
        Args:
            project_name: Name of the project
            components: List of component definitions
            agent_id: ID of the agent adding the components
            
        Returns:
            Dict[str, Any]: Summary of added components
        """
        logger.info(f"Bulk adding {len(components)} components to project {project_name} from agent {agent_id}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return {"success": False, "error": f"Project {project_name} not found"}
        
        assembly = self.assemblies[project_name]
        
        successful = []
        failed = []
        
        for component_def in components:
            try:
                # Extract component data
                name = component_def.get("name")
                if not name:
                    failed.append({"error": "Missing component name", "definition": component_def})
                    continue
                
                component_type = component_def.get("component_type")
                if not component_type:
                    failed.append({"error": "Missing component type", "name": name})
                    continue
                
                content = component_def.get("content")
                if content is None:
                    failed.append({"error": "Missing component content", "name": name})
                    continue
                
                # Register component
                component_id = assembly.register_component(
                    name=name,
                    component_type=component_type,
                    agent_id=agent_id,
                    content=content,
                    file_path=component_def.get("file_path"),
                    dependencies=component_def.get("dependencies"),
                    metadata=component_def.get("metadata")
                )
                
                successful.append({
                    "name": name,
                    "component_id": component_id,
                    "component_type": component_type
                })
                
            except Exception as e:
                failed.append({
                    "error": str(e),
                    "name": component_def.get("name", "Unknown")
                })
        
        logger.info(f"Bulk add completed: {len(successful)} successful, {len(failed)} failed")
        
        return {
            "success": len(failed) == 0,
            "added_count": len(successful),
            "failed_count": len(failed),
            "successful": successful,
            "failed": failed
        }
    
    @trace_method
    def get_compilation_history(self) -> List[Dict[str, Any]]:
        """
        Get the compilation history.
        
        Returns:
            List[Dict[str, Any]]: List of compilation result summaries
        """
        logger.info("Getting compilation history")
        
        return [result.get_summary() for result in self.completed_compilations]


class ResultCompiler:
    """Main class for compiling and assembling results from multiple agents."""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize the result compiler.
        
        Args:
            memory_manager: Optional memory manager for Code Assembler integration
        """
        self.assemblies = {}  # Dict[project_name, ProjectAssembly]
        self.completed_compilations = []  # List of CompilationResult
        self.memory_manager = memory_manager  # For Code Assembler integration
        self.code_assembler_agent = None  # Will be initialized if needed
        
        logger.info("Initialized ResultCompiler")
    
    @trace_method
    def create_project(
        self, 
        project_name: str, 
        project_type: Union[ProjectType, str],
        output_base_dir: str = "outputs"
    ) -> str:
        """
        Create a new project assembly.
        
        Args:
            project_name: Name of the project
            project_type: Type of project
            output_base_dir: Base directory for output
            
        Returns:
            str: Project name
        """
        logger.info(f"Creating project {project_name} of type {project_type}")
        
        # Convert string to enum if needed
        if isinstance(project_type, str):
            try:
                project_type = ProjectType(project_type)
            except ValueError:
                logger.error(f"Invalid project type: {project_type}")
                project_type = ProjectType.GENERIC
        
        # Check if project already exists
        if project_name in self.assemblies:
            logger.warning(f"Project {project_name} already exists, creating new version")
            project_name = f"{project_name}_v{len([p for p in self.assemblies if p.startswith(project_name)])}"
        
        # Create assembly
        self.assemblies[project_name] = ProjectAssembly(
            project_name=project_name,
            project_type=project_type,
            output_base_dir=output_base_dir
        )
        
        logger.info(f"Created project {project_name}")
        return project_name
    
    @trace_method
    def add_component(
        self,
        project_name: str,
        name: str,
        component_type: Union[ComponentType, str],
        agent_id: str,
        content: Any,
        file_path: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a component to a project.
        
        Args:
            project_name: Name of the project
            name: Name of the component
            component_type: Type of component
            agent_id: ID of the agent that created the component
            content: Content of the component
            file_path: Optional file path for the component
            dependencies: Optional list of component IDs this component depends on
            metadata: Optional additional metadata
            
        Returns:
            Optional[str]: Component ID if added successfully, None otherwise
        """
        logger.info(f"Adding component {name} to project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        # Convert string to enum if needed
        if isinstance(component_type, str):
            try:
                component_type = ComponentType(component_type)
            except ValueError:
                logger.error(f"Invalid component type: {component_type}")
                return None
        
        # Add component to project
        assembly = self.assemblies[project_name]
        component_id = assembly.register_component(
            name=name,
            component_type=component_type,
            agent_id=agent_id,
            content=content,
            file_path=file_path,
            dependencies=dependencies,
            metadata=metadata
        )
        
        return component_id
    
    @trace_method
    async def compile_project(self, project_name: str, project_description: str = "") -> Optional[Dict[str, Any]]:
        """
        Compile a project using Code Assembler Agent if available.
        
        Args:
            project_name: Name of the project
            project_description: Description of the project for Code Assembler
            
        Returns:
            Optional[Dict[str, Any]]: Compilation result summary if successful, None otherwise
        """
        logger.info(f"Compiling project {project_name}")
        
        if project_name not in self.assemblies:
            logger.error(f"Project {project_name} not found")
            return None
        
        assembly = self.assemblies[project_name]
        
        try:
            # Check if we should use Code Assembler Agent
            if HAS_CODE_ASSEMBLER and self.memory_manager:
                logger.info("Using Code Assembler Agent for advanced compilation")
                result = await self.delegate_to_code_assembler(
                    project_name=project_name,
                    project_description=project_description,
                    project_type=assembly.project_type.value
                )
                if result:
                    logger.info(f"Code Assembler compilation successful: {result['success']}")
                    return result
                else:
                    logger.warning("Code Assembler compilation failed, falling back to basic compilation")
            
            # If Code Assembler not available or failed, use basic compilation
            logger.info("Using basic compilation")
            
            # Resolve conflicts
            assembly.resolve_component_conflicts()
            
            # Generate project
            result = assembly.generate_project()
            
            # Store compilation result
            self.completed_compilations.append(result)
            
            # Return summary
            summary = result.get_summary()
            logger.info(f"Project {project_name} compiled successfully: {summary['success']}")
            return summary
            
        except Exception as e:
            logger.error(f"Error compiling project {project_name}: {str(e)}", exc_info=True)
            return None
    
    @trace_method
    async def delegate_to_code_assembler(
        self,
        project_name: str,
        project_description: str,
        project_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Delegate compilation to Code Assembler Agent.
        
        Args:
            project_name: Name of the project
            project_description: Description of the project
            project_type: Type of project
            
        Returns:
            Optional[Dict[str, Any]]: Compilation result summary if successful, None otherwise
        """
        logger.info(f"Delegating compilation of {project_name} to Code Assembler Agent")
        
        try:
            # Initialize Code Assembler Agent if not already done
            if not self.code_assembler_agent and HAS_CODE_ASSEMBLER:
                logger.info("Initializing Code Assembler Agent")
                # Create a unique ID for the Code Assembler Agent
                code_assembler_id = f"code_assembler_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.code_assembler_agent = CodeAssemblerAgent(
                    agent_id=code_assembler_id,
                    name="Code Assembler",
                    memory_manager=self.memory_manager
                )
                logger.info(f"Code Assembler Agent initialized with ID: {code_assembler_id}")
            
            if not self.code_assembler_agent:
                logger.error("Failed to initialize Code Assembler Agent")
                return None
            
            # Get components from the current project assembly
            assembly = self.assemblies[project_name]
            components_dict = {}
            
            for comp_id, component in assembly.components.items():
                components_dict[comp_id] = {
                    "name": component.name,
                    "content": component.content,
                    "type": component.component_type.value,
                    "file_path": component.file_path,
                    "agent_id": component.agent_id,
                    "metadata": component.metadata
                }
            
            # Create input data for Code Assembler
            input_data = {
                "project_name": project_name,
                "project_type": project_type,
                "project_description": project_description,
                "components": components_dict
            }
            
            logger.info(f"Sending {len(components_dict)} components to Code Assembler Agent")
            
            # Invoke Code Assembler Agent
            result = await self.code_assembler_agent.run(input_data)
            
            # Process and store results
            assembly_result = await self.process_assembly_results(project_name, result)
            
            return assembly_result
            
        except Exception as e:
            logger.error(f"Error delegating to Code Assembler: {str(e)}", exc_info=True)
            return None
    
    @trace_method
    async def process_assembly_results(
        self,
        project_name: str,
        assembly_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process results returned from the Code Assembler Agent.
        
        Args:
            project_name: Name of the project
            assembly_result: Results from Code Assembler Agent
            
        Returns:
            Dict[str, Any]: Processed result summary
        """
        logger.info(f"Processing assembly results for project {project_name}")
        
        try:
            if not assembly_result:
                logger.warning("Empty assembly result received")
                return None
            
            # Extract important information from the assembly result
            compiled_project = assembly_result.get("compiled_project", {})
            output_location = assembly_result.get("output_location", "")
            
            # Update the assembly with the output location
            if project_name in self.assemblies and output_location:
                self.assemblies[project_name].output_dir = output_location
            
            # Create a summary of the assembly results
            summary = {
                "project_name": project_name,
                "success": True,
                "output_dir": output_location,
                "compilation_timestamp": datetime.utcnow().isoformat(),
                "component_count": len(self.assemblies[project_name].components),
                "assembled_by": "code_assembler_agent",
                "validation_summary": assembly_result.get("validation_results", {}).get("validation_summary", {})
            }
            
            # Store the result in completed compilations
            if "validation_results" in assembly_result:
                validation_messages = []
                for level, messages in assembly_result["validation_results"].get("issues_by_category", {}).items():
                    for message in messages:
                        validation_level = ValidationLevel.ERROR if message.get("level") == "error" else \
                                          ValidationLevel.WARNING if message.get("level") == "warning" else \
                                          ValidationLevel.INFO
                        validation_messages.append(
                            ValidationMessage(
                                level=validation_level,
                                message=message.get("message", ""),
                                metadata={"category": level}
                            )
                        )
                
                result = CompilationResult(
                    project_name=project_name,
                    project_type=self.assemblies[project_name].project_type,
                    output_dir=output_location,
                    components=list(self.assemblies[project_name].components.values()),
                    validation_messages=validation_messages,
                    metadata={"assembled_by": "code_assembler_agent"}
                )
                
                self.completed_compilations.append(result)
            
            logger.info(f"Successfully processed assembly results for {project_name}")
            return summary
            
        except Exception as e:
            logger.error(f"Error processing assembly results: {str(e)}", exc_info=True)
            return {
                "project_name": project_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }