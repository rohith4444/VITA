from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.code_assembler.config_generator")

class ConfigType(Enum):
    """Enum representing types of configuration files that can be generated."""
    PACKAGE = "package"               # package.json, requirements.txt, etc.
    BUILD = "build"                   # webpack.config.js, tsconfig.json, etc.
    ENVIRONMENT = "environment"       # .env files, environment configs
    DEPLOYMENT = "deployment"         # Docker, CI/CD configs
    DOCUMENTATION = "documentation"   # README.md, etc.
    PROJECT = "project"               # General project configs (.gitignore, etc.)

class ConfigGenerator:
    """Class for generating configuration files for a project."""
    
    def __init__(
        self,
        project_name: str,
        dependency_info: Dict[str, Any],
        project_structure: Dict[str, Any],
        output_dir: str,
        llm_service: Any
    ):
        """
        Initialize a configuration generator.
        
        Args:
            project_name: Name of the project
            dependency_info: Information about project dependencies
            project_structure: Information about project structure
            output_dir: Directory to write configurations to
            llm_service: LLM service for generating configurations
        """
        self.project_name = project_name
        self.dependency_info = dependency_info
        self.project_structure = project_structure
        self.output_dir = output_dir
        self.llm_service = llm_service
        self.technologies = self._detect_technologies()
        
        logger.info(f"Initialized ConfigGenerator for project: {project_name}")
    
    def _detect_technologies(self) -> Dict[str, Any]:
        """
        Detect technologies used in the project based on dependencies and structure.
        
        Returns:
            Dict[str, Any]: Detected technologies and frameworks
        """
        logger.debug("Detecting project technologies")
        
        technologies = {
            "frontend": [],
            "backend": [],
            "database": [],
            "build": [],
            "testing": []
        }
        
        # Check dependencies for common technologies
        dependencies = self.dependency_info.get("component_dependencies", {})
        for component, deps in dependencies.items():
            # Frontend technologies
            if any(tech in str(deps).lower() for tech in ["react", "vue", "angular"]):
                if "react" in str(deps).lower():
                    technologies["frontend"].append("react")
                if "vue" in str(deps).lower():
                    technologies["frontend"].append("vue")
                if "angular" in str(deps).lower():
                    technologies["frontend"].append("angular")
            
            # Backend technologies
            if any(tech in str(deps).lower() for tech in ["express", "django", "flask", "spring"]):
                if "express" in str(deps).lower() or "node" in str(deps).lower():
                    technologies["backend"].append("node.js")
                if "django" in str(deps).lower() or "flask" in str(deps).lower():
                    technologies["backend"].append("python")
                if "spring" in str(deps).lower():
                    technologies["backend"].append("java")
            
            # Database technologies
            if any(tech in str(deps).lower() for tech in ["mongo", "postgres", "mysql", "sqlite"]):
                if "mongo" in str(deps).lower():
                    technologies["database"].append("mongodb")
                if "postgres" in str(deps).lower():
                    technologies["database"].append("postgresql")
                if "mysql" in str(deps).lower():
                    technologies["database"].append("mysql")
                if "sqlite" in str(deps).lower():
                    technologies["database"].append("sqlite")
        
        # Check file extensions in project structure
        for component in self.project_structure.get("components", []):
            file_path = component.get("path", "")
            # JavaScript/TypeScript
            if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                if "javascript" not in technologies["frontend"] and "typescript" not in technologies["frontend"]:
                    if file_path.endswith((".ts", ".tsx")):
                        technologies["frontend"].append("typescript")
                    else:
                        technologies["frontend"].append("javascript")
            
            # Python
            if file_path.endswith(".py"):
                if "python" not in technologies["backend"]:
                    technologies["backend"].append("python")
            
            # Java
            if file_path.endswith(".java"):
                if "java" not in technologies["backend"]:
                    technologies["backend"].append("java")
            
            # Testing
            if "test" in file_path.lower() or "spec" in file_path.lower():
                if "jest" in str(component).lower() and "jest" not in technologies["testing"]:
                    technologies["testing"].append("jest")
                if "pytest" in str(component).lower() and "pytest" not in technologies["testing"]:
                    technologies["testing"].append("pytest")
                if "junit" in str(component).lower() and "junit" not in technologies["testing"]:
                    technologies["testing"].append("junit")
        
        # Deduplicate and ensure we have at least basic technologies inferred
        for category in technologies:
            technologies[category] = list(set(technologies[category]))
        
        # If no frontend tech detected but we have JS/TS files, default to React
        if not technologies["frontend"] and "javascript" in technologies.get("languages", []):
            technologies["frontend"].append("react")
        
        # If no backend tech detected but we have certain files, make a guess
        if not technologies["backend"]:
            if os.path.exists(os.path.join(self.output_dir, "package.json")):
                technologies["backend"].append("node.js")
            elif any(f.endswith(".py") for f in os.listdir(self.output_dir) if os.path.isfile(os.path.join(self.output_dir, f))):
                technologies["backend"].append("python")
        
        logger.info(f"Detected technologies: {technologies}")
        return technologies
    
    def determine_required_configs(self) -> List[ConfigType]:
        """
        Determine which configuration files are required for the project.
        
        Returns:
            List[ConfigType]: List of required configuration types
        """
        logger.info("Determining required configuration files")
        
        required_configs = []
        
        # Package configs are almost always needed
        required_configs.append(ConfigType.PACKAGE)
        
        # Determine if we need build configs
        if any(tech in self.technologies["frontend"] for tech in ["react", "vue", "angular", "typescript"]):
            required_configs.append(ConfigType.BUILD)
        
        # Environment configs for most projects
        required_configs.append(ConfigType.ENVIRONMENT)
        
        # Deployment configs if we detect certain technologies
        if self.technologies["database"] or "docker" in str(self.project_structure).lower():
            required_configs.append(ConfigType.DEPLOYMENT)
        
        # Documentation is always good to have
        required_configs.append(ConfigType.DOCUMENTATION)
        
        # General project configs
        required_configs.append(ConfigType.PROJECT)
        
        logger.info(f"Required configuration types: {[cfg.value for cfg in required_configs]}")
        return required_configs
    
    @trace_method
    async def generate_configs(self) -> Dict[str, Dict[str, str]]:
        """
        Generate all required configuration files.
        
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping config types to filenames and content
        """
        logger.info("Starting configuration generation")
        
        required_configs = self.determine_required_configs()
        generated_configs = {}
        
        for config_type in required_configs:
            logger.info(f"Generating {config_type.value} configuration")
            
            if config_type == ConfigType.PACKAGE:
                configs = await self.generate_package_config()
            elif config_type == ConfigType.BUILD:
                configs = await self.generate_build_config()
            elif config_type == ConfigType.ENVIRONMENT:
                configs = await self.generate_environment_config()
            elif config_type == ConfigType.DEPLOYMENT:
                configs = await self.generate_deployment_config()
            elif config_type == ConfigType.DOCUMENTATION:
                configs = await self.generate_documentation()
            elif config_type == ConfigType.PROJECT:
                configs = await self.generate_project_config()
            else:
                logger.warning(f"Unknown config type: {config_type.value}")
                configs = {}
            
            generated_configs[config_type.value] = configs
            
        logger.info(f"Generated {sum(len(configs) for configs in generated_configs.values())} configuration files")
        return generated_configs
    
    @trace_method
    async def generate_package_config(self) -> Dict[str, str]:
        """
        Generate package configuration files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating package configuration")
        
        configs = {}
        
        # Determine technologies to configure for
        has_nodejs = any(tech in ["node.js", "express"] for tech in self.technologies["backend"])
        has_python = "python" in self.technologies["backend"]
        
        if has_nodejs:
            # Generate package.json
            package_json = await self._generate_via_llm(
                config_name="package.json",
                config_description="Node.js package configuration file",
                config_type=ConfigType.PACKAGE
            )
            configs["package.json"] = package_json
        
        if has_python:
            # Generate requirements.txt
            requirements_txt = await self._generate_via_llm(
                config_name="requirements.txt",
                config_description="Python dependencies file",
                config_type=ConfigType.PACKAGE
            )
            configs["requirements.txt"] = requirements_txt
        
        # If no specific technology detected, generate both for safety
        if not has_nodejs and not has_python:
            package_json = await self._generate_via_llm(
                config_name="package.json",
                config_description="Node.js package configuration file",
                config_type=ConfigType.PACKAGE
            )
            configs["package.json"] = package_json
            
            requirements_txt = await self._generate_via_llm(
                config_name="requirements.txt",
                config_description="Python dependencies file",
                config_type=ConfigType.PACKAGE
            )
            configs["requirements.txt"] = requirements_txt
        
        logger.info(f"Generated {len(configs)} package configuration files")
        return configs
    
    @trace_method
    async def generate_build_config(self) -> Dict[str, str]:
        """
        Generate build configuration files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating build configuration")
        
        configs = {}
        
        # Determine technologies to configure for
        has_typescript = "typescript" in self.technologies["frontend"]
        has_react = "react" in self.technologies["frontend"]
        has_vue = "vue" in self.technologies["frontend"]
        
        if has_typescript:
            # Generate tsconfig.json
            tsconfig_json = await self._generate_via_llm(
                config_name="tsconfig.json",
                config_description="TypeScript configuration file",
                config_type=ConfigType.BUILD
            )
            configs["tsconfig.json"] = tsconfig_json
        
        if has_react or has_vue:
            # Generate webpack config or appropriate build tool config
            webpack_config = await self._generate_via_llm(
                config_name="webpack.config.js",
                config_description="Webpack configuration file",
                config_type=ConfigType.BUILD
            )
            configs["webpack.config.js"] = webpack_config
        
        # For modern frontend apps, also generate babel config
        if has_react or has_vue:
            babel_config = await self._generate_via_llm(
                config_name=".babelrc",
                config_description="Babel configuration file",
                config_type=ConfigType.BUILD
            )
            configs[".babelrc"] = babel_config
        
        logger.info(f"Generated {len(configs)} build configuration files")
        return configs
    
    @trace_method
    async def generate_environment_config(self) -> Dict[str, str]:
        """
        Generate environment configuration files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating environment configuration")
        
        configs = {}
        
        # Generate .env.example file
        env_example = await self._generate_via_llm(
            config_name=".env.example",
            config_description="Example environment variables file",
            config_type=ConfigType.ENVIRONMENT
        )
        configs[".env.example"] = env_example
        
        # If we have a database, create specific DB environment example
        if self.technologies["database"]:
            db_env_example = await self._generate_via_llm(
                config_name=".env.database.example",
                config_description="Database environment variables example",
                config_type=ConfigType.ENVIRONMENT
            )
            configs[".env.database.example"] = db_env_example
        
        logger.info(f"Generated {len(configs)} environment configuration files")
        return configs
    
    @trace_method
    async def generate_deployment_config(self) -> Dict[str, str]:
        """
        Generate deployment configuration files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating deployment configuration")
        
        configs = {}
        
        # Generate Dockerfile
        dockerfile = await self._generate_via_llm(
            config_name="Dockerfile",
            config_description="Docker configuration file",
            config_type=ConfigType.DEPLOYMENT
        )
        configs["Dockerfile"] = dockerfile
        
        # Generate docker-compose.yml if we have multiple services
        if self.technologies["database"]:
            docker_compose = await self._generate_via_llm(
                config_name="docker-compose.yml",
                config_description="Docker Compose configuration file",
                config_type=ConfigType.DEPLOYMENT
            )
            configs["docker-compose.yml"] = docker_compose
        
        # Generate .dockerignore
        dockerignore = await self._generate_via_llm(
            config_name=".dockerignore",
            config_description="Docker ignore file",
            config_type=ConfigType.DEPLOYMENT
        )
        configs[".dockerignore"] = dockerignore
        
        logger.info(f"Generated {len(configs)} deployment configuration files")
        return configs
    
    @trace_method
    async def generate_documentation(self) -> Dict[str, str]:
        """
        Generate documentation files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating documentation")
        
        configs = {}
        
        # Generate README.md
        readme = await self._generate_via_llm(
            config_name="README.md",
            config_description="Project README file",
            config_type=ConfigType.DOCUMENTATION
        )
        configs["README.md"] = readme
        
        # Generate CONTRIBUTING.md
        contributing = await self._generate_via_llm(
            config_name="CONTRIBUTING.md",
            config_description="Contribution guidelines",
            config_type=ConfigType.DOCUMENTATION
        )
        configs["CONTRIBUTING.md"] = contributing
        
        # Generate API docs if we have a backend
        if self.technologies["backend"]:
            api_docs = await self._generate_via_llm(
                config_name="API.md",
                config_description="API documentation",
                config_type=ConfigType.DOCUMENTATION
            )
            configs["docs/API.md"] = api_docs
        
        logger.info(f"Generated {len(configs)} documentation files")
        return configs
    
    @trace_method
    async def generate_project_config(self) -> Dict[str, str]:
        """
        Generate general project configuration files.
        
        Returns:
            Dict[str, str]: Dictionary mapping filenames to content
        """
        logger.info("Generating project configuration")
        
        configs = {}
        
        # Generate .gitignore
        gitignore = await self._generate_via_llm(
            config_name=".gitignore",
            config_description="Git ignore file",
            config_type=ConfigType.PROJECT
        )
        configs[".gitignore"] = gitignore
        
        # Generate .editorconfig
        editorconfig = await self._generate_via_llm(
            config_name=".editorconfig",
            config_description="Editor configuration file",
            config_type=ConfigType.PROJECT
        )
        configs[".editorconfig"] = editorconfig
        
        # Generate linting configs if we have JS/TS
        if any(tech in self.technologies["frontend"] for tech in ["javascript", "typescript", "react", "vue"]):
            eslintrc = await self._generate_via_llm(
                config_name=".eslintrc.js",
                config_description="ESLint configuration file",
                config_type=ConfigType.PROJECT
            )
            configs[".eslintrc.js"] = eslintrc
            
            prettierrc = await self._generate_via_llm(
                config_name=".prettierrc",
                config_description="Prettier configuration file",
                config_type=ConfigType.PROJECT
            )
            configs[".prettierrc"] = prettierrc
        
        # Generate pytest.ini if we have Python
        if "python" in self.technologies["backend"]:
            pytest_ini = await self._generate_via_llm(
                config_name="pytest.ini",
                config_description="Pytest configuration file",
                config_type=ConfigType.PROJECT
            )
            configs["pytest.ini"] = pytest_ini
        
        logger.info(f"Generated {len(configs)} project configuration files")
        return configs
    
    @trace_method
    async def _generate_via_llm(
        self,
        config_name: str,
        config_description: str,
        config_type: ConfigType
    ) -> str:
        """
        Generate configuration content using LLM.
        
        Args:
            config_name: Name of the configuration file
            config_description: Description of the configuration
            config_type: Type of configuration
            
        Returns:
            str: Generated configuration content
        """
        logger.debug(f"Generating {config_name} via LLM")
        
        try:
            # Format prompt for LLM
            prompt = self._format_config_prompt(
                config_name=config_name,
                config_description=config_description,
                config_type=config_type
            )
            
            # Call LLM to generate configuration
            response = await self.llm_service.generate_config(
                project_name=self.project_name,
                config_name=config_name,
                config_type=config_type.value,
                technologies=self.technologies,
                prompt=prompt
            )
            
            # Validate the generated configuration
            config_content = self._validate_config(config_name, response)
            
            logger.debug(f"Successfully generated {config_name}")
            return config_content
            
        except Exception as e:
            logger.error(f"Error generating {config_name}: {str(e)}", exc_info=True)
            # Fallback to a basic template if LLM generation fails
            return self._get_fallback_template(config_name, config_type)
    
    def _format_config_prompt(
        self,
        config_name: str,
        config_description: str,
        config_type: ConfigType
    ) -> str:
        """
        Format a prompt for the LLM to generate configuration.
        
        Args:
            config_name: Name of the configuration file
            config_description: Description of the configuration
            config_type: Type of configuration
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Format technologies as a string
        tech_summary = ""
        for category, techs in self.technologies.items():
            if techs:
                tech_summary += f"{category.capitalize()}: {', '.join(techs)}\n"
        
        # Format dependency information
        dependency_summary = "Dependencies:\n"
        if "build_order" in self.dependency_info:
            dependency_summary += "Build order: " + ", ".join(self.dependency_info["build_order"][:10])
            if len(self.dependency_info["build_order"]) > 10:
                dependency_summary += "... (and more)"
            dependency_summary += "\n"
        
        if "most_depended_on" in self.dependency_info:
            dependency_summary += "Most important components:\n"
            for item in self.dependency_info["most_depended_on"][:5]:
                dependency_summary += f"- {item.get('component_id', 'unknown')}\n"
        
        # Format project structure information
        structure_summary = "Project Structure:\n"
        components = self.project_structure.get("components", [])
        component_types = {}
        
        for component in components[:20]:  # Limit to first 20 for the prompt
            comp_type = component.get("name", "unknown")
            if comp_type not in component_types:
                component_types[comp_type] = 0
            component_types[comp_type] += 1
        
        for comp_type, count in component_types.items():
            structure_summary += f"- {comp_type}: {count} components\n"
        
        # Build the prompt
        prompt = f"""
        Generate a {config_description} for a project with the following characteristics:
        
        Project Name: {self.project_name}
        
        Technologies:
        {tech_summary}
        
        {dependency_summary}
        
        {structure_summary}
        
        Please generate a complete and properly formatted {config_name} file that:
        1. Is suitable for the technologies mentioned
        2. Follows best practices for this type of configuration
        3. Includes appropriate settings for the project structure described
        4. Is ready to use without modification
        
        The file should be in the correct format for {config_name} (e.g., JSON, YAML, plain text, etc.).
        """
        
        return prompt
    
    def _validate_config(self, config_name: str, content: str) -> str:
        """
        Validate generated configuration content.
        
        Args:
            config_name: Name of the configuration file
            content: Generated configuration content
            
        Returns:
            str: Validated configuration content
        """
        logger.debug(f"Validating {config_name}")
        
        try:
            # Validate based on file extension
            if config_name.endswith(".json"):
                # Validate JSON
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in {config_name}: {str(e)}")
                    # Try to extract JSON from response if it's not perfect JSON
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_content = content[json_start:json_end]
                        try:
                            json.loads(json_content)
                            return json_content
                        except json.JSONDecodeError:
                            pass
                    # Fall back to template if extraction fails
                    return self._get_fallback_template(config_name, ConfigType.PACKAGE)
            
            elif config_name.endswith((".yml", ".yaml")):
                # Validate YAML
                try:
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    logger.warning(f"Invalid YAML in {config_name}: {str(e)}")
                    return self._get_fallback_template(config_name, ConfigType.DEPLOYMENT)
            
            # Other files just need to be non-empty
            if not content.strip():
                logger.warning(f"Empty content for {config_name}")
                return self._get_fallback_template(config_name, ConfigType.PROJECT)
            
            logger.debug(f"Validation successful for {config_name}")
            return content
            
        except Exception as e:
            logger.error(f"Error validating {config_name}: {str(e)}", exc_info=True)
            return self._get_fallback_template(config_name, ConfigType.PROJECT)
    
    def _get_fallback_template(self, config_name: str, config_type: ConfigType) -> str:
        """
        Get a fallback template for a configuration file.
        
        Args:
            config_name: Name of the configuration file
            config_type: Type of configuration
            
        Returns:
            str: Fallback template content
        """
        logger.debug(f"Using fallback template for {config_name}")
        
        # Basic templates for common config files
        if config_name == "package.json":
            return f"""{{
  "name": "{self.project_name.lower().replace(' ', '-')}",
  "version": "0.1.0",
  "description": "A project generated by Code Assembler",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {{}}
}}"""
        
        elif config_name == "requirements.txt":
            return """# Project dependencies
# Add specific versions as needed
"""
        
        elif config_name == "tsconfig.json":
            return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react"
  },
  "include": ["src"]
}"""
        
        elif config_name == ".env.example":
            return """# Environment Variables
# Copy this file to .env and update the values

# Server configuration
PORT=3000
NODE_ENV=development

# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=user
DB_PASSWORD=password

# Secret keys
JWT_SECRET=your_jwt_secret_key
"""
        
        elif config_name == "Dockerfile":
            return """FROM node:14

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
"""
        
        elif config_name == "docker-compose.yml":
            return """version: '3'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      - db
    environment:
      - NODE_ENV=production
      - DB_HOST=db

  db:
    image: postgres:12
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydatabase
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
"""
        
        elif config_name == ".gitignore":
            return """# Dependencies
node_modules/
venv/
.env

# Build outputs
dist/
build/
*.pyc
__pycache__/

# Logs
logs/
*.log
npm-debug.log*

# Editor directories and files
.idea/
.vscode/
*.swp
*.swo

# Operating System
.DS_Store
Thumbs.db
"""
        
        elif config_name == "README.md":
            return f"""# {self.project_name}

A project generated by Code Assembler.

## Description

Add your project description here.

## Installation

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
npm install
```

## Usage

```bash
# Start the application
npm start
```

## License

This project is licensed under the ISC License.
"""
        
        else:
            # Generic template for other files
            return f"""# {config_name}
# Configuration for {self.project_name}
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    @trace_method
    async def write_configs(self, generated_configs: Dict[str, Dict[str, str]]) -> List[str]:
        """
        Write generated configurations to files.
        
        Args:
            generated_configs: Dictionary mapping config types to filenames and content
            
        Returns:
            List[str]: List of written file paths
        """
        logger.info("Writing configuration files")
        
        written_files = []
        
        try:
            # Flatten the config dictionary
            all_configs = {}
            for config_type, configs in generated_configs.items():
                all_configs.update(configs)
            
            # Write each configuration file
            for file_name, content in all_configs.items():
                # Ensure the directory exists
                file_path = os.path.join(self.output_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                written_files.append(file_path)
                logger.debug(f"Written file: {file_path}")
            
            logger.info(f"Successfully wrote {len(written_files)} configuration files")
            return written_files
            
        except Exception as e:
            logger.error(f"Error writing configuration files: {str(e)}", exc_info=True)
            return written_files