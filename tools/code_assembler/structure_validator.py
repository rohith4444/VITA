from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import os
import json
import yaml
import re
from pathlib import Path
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.code_assembler.structure_validator")

class ValidationLevel(Enum):
    """Enum representing validation severity levels."""
    ERROR = "error"         # Critical issue that must be fixed
    WARNING = "warning"     # Potential issue that should be reviewed
    INFO = "info"           # Informational note

class ValidationMessage:
    """Class representing a validation message or issue."""
    
    def __init__(
        self,
        level: ValidationLevel,
        message: str,
        file_path: Optional[str] = None,
        component_id: Optional[str] = None,
        recommendation: Optional[str] = None
    ):
        """
        Initialize a validation message.
        
        Args:
            level: Severity level of the validation message
            message: Description of the validation issue
            file_path: Path to the file with the issue (if applicable)
            component_id: ID of the component with the issue (if applicable)
            recommendation: Suggested fix for the issue
        """
        self.level = level
        self.message = message
        self.file_path = file_path
        self.component_id = component_id
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation message to dictionary for serialization."""
        return {
            "level": self.level.value,
            "message": self.message,
            "file_path": self.file_path,
            "component_id": self.component_id,
            "recommendation": self.recommendation
        }
    
    def __str__(self) -> str:
        """String representation of the validation message."""
        path_info = f" in {self.file_path}" if self.file_path else ""
        comp_info = f" (component: {self.component_id})" if self.component_id else ""
        rec_info = f" - {self.recommendation}" if self.recommendation else ""
        return f"[{self.level.value.upper()}]{path_info}{comp_info}: {self.message}{rec_info}"

class ProjectType(Enum):
    """Enum representing types of projects that can be validated."""
    WEB_APP = "web_app"                 # Web application
    BACKEND_API = "backend_api"         # Backend API service
    FRONTEND_APP = "frontend_app"       # Frontend application
    FULL_STACK = "full_stack"           # Full stack application
    LIBRARY = "library"                 # Library or package
    CLI = "cli"                         # Command-line interface application
    STATIC_SITE = "static_site"         # Static website
    UNKNOWN = "unknown"                 # Unknown project type

class StructureValidator:
    """Class for validating project structure."""
    
    def __init__(self, project_dir: str, project_type: ProjectType = ProjectType.UNKNOWN):
        """
        Initialize a structure validator.
        
        Args:
            project_dir: Path to the project directory
            project_type: Type of the project
        """
        self.project_dir = project_dir
        self.project_type = project_type
        self.validation_messages: List[ValidationMessage] = []
        self.essential_files = self._get_essential_files()
        self.expected_structure = self._get_expected_structure()
        
        logger.info(f"Initialized StructureValidator for {project_type.value} project at {project_dir}")
    
    def _get_essential_files(self) -> Dict[str, str]:
        """
        Get essential files for the project type.
        
        Returns:
            Dict[str, str]: Dictionary mapping essential files to their descriptions
        """
        # Common essential files for all project types
        essential_files = {
            "README.md": "Project documentation"
        }
        
        # Add project-type-specific essential files
        if self.project_type == ProjectType.WEB_APP or self.project_type == ProjectType.FRONTEND_APP:
            essential_files.update({
                "package.json": "Node.js package configuration",
                ".gitignore": "Git ignore file",
                "index.html": "Main HTML entry point",
            })
        elif self.project_type == ProjectType.BACKEND_API:
            essential_files.update({
                "package.json": "Node.js package configuration" if self._is_node_project() else None,
                "requirements.txt": "Python dependencies" if self._is_python_project() else None,
                ".gitignore": "Git ignore file",
            })
        elif self.project_type == ProjectType.FULL_STACK:
            essential_files.update({
                "package.json": "Node.js package configuration",
                ".gitignore": "Git ignore file",
                "docker-compose.yml": "Docker Compose configuration for services"
            })
        
        # Remove None values (for conditional entries)
        return {k: v for k, v in essential_files.items() if v is not None}
    
    def _is_node_project(self) -> bool:
        """Check if the project appears to be a Node.js project."""
        return os.path.exists(os.path.join(self.project_dir, "package.json"))
    
    def _is_python_project(self) -> bool:
        """Check if the project appears to be a Python project."""
        return (os.path.exists(os.path.join(self.project_dir, "requirements.txt")) or 
                os.path.exists(os.path.join(self.project_dir, "setup.py")))
    
    def _get_expected_structure(self) -> Dict[str, List[str]]:
        """
        Get expected directory structure for the project type.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping directories to subdirectories
        """
        # Default structure
        structure = {
            ".": ["README.md", ".gitignore"]
        }
        
        # Add project-type-specific structure
        if self.project_type == ProjectType.WEB_APP:
            structure.update({
                "src": ["components", "pages", "assets", "styles"],
                "public": [],
                "tests": []
            })
        elif self.project_type == ProjectType.BACKEND_API:
            if self._is_node_project():
                structure.update({
                    "src": ["routes", "controllers", "models", "middleware", "services"],
                    "tests": []
                })
            elif self._is_python_project():
                structure.update({
                    "app": ["routes", "models", "services"],
                    "tests": []
                })
        elif self.project_type == ProjectType.FULL_STACK:
            structure.update({
                "frontend": ["src", "public"],
                "backend": ["src"],
                "docs": []
            })
        
        return structure
    
    @trace_method
    def validate(self) -> List[ValidationMessage]:
        """
        Validate the project structure.
        
        Returns:
            List[ValidationMessage]: List of validation messages
        """
        logger.info(f"Starting validation of project structure in {self.project_dir}")
        
        try:
            # Reset validation messages
            self.validation_messages = []
            
            # Run validation checks
            self._validate_essential_files()
            self._validate_directory_structure()
            self._validate_file_placement()
            self._validate_config_files()
            
            # Sort messages by level (errors first, then warnings, then info)
            self.validation_messages.sort(
                key=lambda msg: {"error": 0, "warning": 1, "info": 2}[msg.level.value]
            )
            
            logger.info(f"Validation completed with {len(self.validation_messages)} messages")
            return self.validation_messages
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}", exc_info=True)
            self.validation_messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message=f"Validation failed with error: {str(e)}",
                    recommendation="Check the logs for details"
                )
            )
            return self.validation_messages
    
    @trace_method
    def _validate_essential_files(self) -> None:
        """Check if essential files exist in the project."""
        logger.debug("Validating essential files")
        
        for file_name, description in self.essential_files.items():
            file_path = os.path.join(self.project_dir, file_name)
            
            if not os.path.exists(file_path):
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Missing essential file: {file_name}",
                        file_path=file_path,
                        recommendation=f"Create {file_name} ({description})"
                    )
                )
            elif os.path.getsize(file_path) == 0:
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Essential file is empty: {file_name}",
                        file_path=file_path,
                        recommendation=f"Add content to {file_name} ({description})"
                    )
                )
    
    @trace_method
    def _validate_directory_structure(self) -> None:
        """Check if the project has the expected directory structure."""
        logger.debug("Validating directory structure")
        
        for directory, expected_contents in self.expected_structure.items():
            if directory == ".":
                dir_path = self.project_dir
            else:
                dir_path = os.path.join(self.project_dir, directory)
            
            # Check if the directory exists
            if not os.path.exists(dir_path):
                if directory == ".":
                    continue  # Skip validation of root directory itself
                
                self.validation_messages.append(
                    ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Missing directory: {directory}",
                        recommendation=f"Create directory '{directory}'"
                    )
                )
                continue
            
            # Check for expected subdirectories/files
            for expected in expected_contents:
                expected_path = os.path.join(dir_path, expected)
                if not os.path.exists(expected_path):
                    level = ValidationLevel.WARNING
                    # For files that are not marked as essential, use INFO level
                    if os.path.splitext(expected)[1] and expected not in self.essential_files:
                        level = ValidationLevel.INFO
                    
                    self.validation_messages.append(
                        ValidationMessage(
                            level=level,
                            message=f"Missing expected item: {expected} in {directory}",
                            recommendation=f"Create {expected} in {directory} directory"
                        )
                    )
    
    @trace_method
    def _validate_file_placement(self) -> None:
        """Check if files are placed in appropriate directories."""
        logger.debug("Validating file placement")
        
        # Define patterns for file types
        patterns = {
            "component": (r"^.*Component\.(js|jsx|ts|tsx)$", "src/components"),
            "page": (r"^.*Page\.(js|jsx|ts|tsx)$", "src/pages"),
            "style": (r"^.*\.(css|scss|sass)$", "src/styles"),
            "model": (r"^.*Model\.(js|ts|py)$", "src/models" if self.project_type == ProjectType.BACKEND_API else "backend/src/models"),
            "controller": (r"^.*Controller\.(js|ts|py)$", "src/controllers" if self.project_type == ProjectType.BACKEND_API else "backend/src/controllers"),
            "test": (r"^.*\.(test|spec)\.(js|jsx|ts|tsx|py)$", "tests"),
            "documentation": (r"^.*\.(md|mdx)$", "docs")
        }
        
        # Walk through project files
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.project_dir)
                
                # Skip common config files and hidden files
                if file.startswith(".") or file in ["package.json", "requirements.txt"]:
                    continue
                
                # Check if file matches a pattern
                for pattern_name, (pattern, expected_dir) in patterns.items():
                    if re.match(pattern, file, re.IGNORECASE):
                        # Check if file is in the expected directory
                        if not relative_path.startswith(expected_dir):
                            self.validation_messages.append(
                                ValidationMessage(
                                    level=ValidationLevel.INFO,
                                    message=f"File placement: {file} appears to be a {pattern_name} file but is not in {expected_dir}",
                                    file_path=file_path,
                                    recommendation=f"Consider moving to {expected_dir}"
                                )
                            )
    
    @trace_method
    def _validate_config_files(self) -> None:
        """Validate syntax of configuration files."""
        logger.debug("Validating configuration files")
        
        # Define config files to validate
        config_files = {
            "package.json": self._validate_json,
            "tsconfig.json": self._validate_json,
            ".eslintrc.json": self._validate_json,
            ".eslintrc.js": None,  # Skip JS configs for now
            "webpack.config.js": None,  # Skip JS configs for now
            "docker-compose.yml": self._validate_yaml,
            "docker-compose.yaml": self._validate_yaml,
            ".env.example": None  # No specific validation needed
        }
        
        # Check each config file
        for config_file, validator in config_files.items():
            file_path = os.path.join(self.project_dir, config_file)
            
            if os.path.exists(file_path):
                # Skip if no validator is specified
                if validator is None:
                    continue
                
                # Validate the file
                is_valid, error_message = validator(file_path)
                
                if not is_valid:
                    self.validation_messages.append(
                        ValidationMessage(
                            level=ValidationLevel.ERROR,
                            message=f"Invalid configuration: {config_file} has syntax errors",
                            file_path=file_path,
                            recommendation=f"Fix syntax error: {error_message}"
                        )
                    )
    
    def _validate_json(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON syntax.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def _validate_yaml(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate YAML syntax.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)
    
    @trace_method
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Returns:
            Dict[str, Any]: Validation report
        """
        logger.info("Generating validation report")
        
        # Count messages by level
        counts = {"error": 0, "warning": 0, "info": 0}
        for message in self.validation_messages:
            counts[message.level.value] += 1
        
        # Group messages by category
        categories = {
            "essential_files": [],
            "directory_structure": [],
            "file_placement": [],
            "config_files": [],
            "other": []
        }
        
        for message in self.validation_messages:
            if "Missing essential file" in message.message:
                categories["essential_files"].append(message.to_dict())
            elif "Missing directory" in message.message or "Missing expected item" in message.message:
                categories["directory_structure"].append(message.to_dict())
            elif "File placement" in message.message:
                categories["file_placement"].append(message.to_dict())
            elif "Invalid configuration" in message.message:
                categories["config_files"].append(message.to_dict())
            else:
                categories["other"].append(message.to_dict())
        
        # Create report
        report = {
            "project_type": self.project_type.value,
            "validation_summary": {
                "total_issues": len(self.validation_messages),
                "error_count": counts["error"],
                "warning_count": counts["warning"],
                "info_count": counts["info"],
                "has_errors": counts["error"] > 0
            },
            "issues_by_category": categories,
            "recommendations": self._generate_recommendations()
        }
        
        logger.info("Validation report generated")
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on validation issues.
        
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        # Check for critical issues
        error_messages = [msg for msg in self.validation_messages if msg.level == ValidationLevel.ERROR]
        if error_messages:
            error_recommendations = []
            for msg in error_messages:
                if msg.recommendation:
                    error_recommendations.append(msg.recommendation)
            
            if error_recommendations:
                recommendations.append("Critical issues to fix: " + ", ".join(error_recommendations))
            else:
                recommendations.append(f"Fix {len(error_messages)} critical issues")
        
        # Add general recommendations based on project structure
        if any("Missing essential file" in msg.message for msg in self.validation_messages):
            recommendations.append("Create all essential files for your project type")
        
        if any("directory structure" in msg.message.lower() for msg in self.validation_messages):
            recommendations.append("Organize your project according to standard directory structure")
        
        if any("File placement" in msg.message for msg in self.validation_messages):
            recommendations.append("Consider reorganizing files according to conventional patterns")
        
        # Add project type specific recommendations
        if self.project_type == ProjectType.WEB_APP:
            recommendations.append("Ensure your web application has clear separation of components and pages")
        elif self.project_type == ProjectType.BACKEND_API:
            recommendations.append("Follow the MVC pattern for your backend API")
        elif self.project_type == ProjectType.FULL_STACK:
            recommendations.append("Maintain clear separation between frontend and backend code")
        
        return recommendations