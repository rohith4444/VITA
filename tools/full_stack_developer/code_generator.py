from typing import Dict, List, Any, Optional
import re
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.full_stack_developer.llm.service import LLMService

# Initialize logger
logger = setup_logger("tools.full_stack_developer.code_generator")

@trace_method
async def generate_code(
    task_specification: str,
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any],
    llm_service: LLMService
) -> Dict[str, Dict[str, str]]:
    """
    Orchestrate the generation of code for all components.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        solution_design: Technical design for all components
        llm_service: LLM service for code generation
        
    Returns:
        Dict[str, Dict[str, str]]: Dictionary mapping component types to their generated code files
    """
    logger.info("Starting code generation process")
    
    try:
        generated_code = {}
        
        # Detect technology stack
        tech_stack = detect_technology_stack(requirements, solution_design)
        logger.info(f"Detected technology stack: {tech_stack}")
        
        # Generate code for each component
        components = ["frontend", "backend", "database"]
        for component in components:
            logger.info(f"Generating code for {component} component")
            
            component_design = solution_design.get(component, {})
            if not component_design:
                logger.warning(f"No design found for {component} component")
                continue
                
            # Generate code for this component
            component_code = await generate_component_code(
                component_type=component,
                component_design=component_design,
                requirements=requirements,
                task_specification=task_specification,
                tech_stack=tech_stack,
                llm_service=llm_service
            )
            
            if component_code:
                # Process and structure the generated code
                processed_code = process_generated_code(
                    raw_generated_code=component_code,
                    component_type=component,
                    tech_stack=tech_stack
                )
                
                generated_code[component] = processed_code
                logger.info(f"Successfully generated {len(processed_code)} files for {component}")
            else:
                logger.warning(f"Failed to generate code for {component}")
        
        # Validate consistency across components
        if len(generated_code) > 1:
            consistency_result = validate_code_consistency(generated_code)
            if not consistency_result["is_consistent"]:
                logger.warning(f"Code consistency issues detected: {consistency_result['issues']}")
        
        logger.info(f"Code generation completed with {sum(len(files) for files in generated_code.values())} total files")
        return generated_code
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}", exc_info=True)
        # Return basic fallback code
        #return generate_fallback_code(requirements, solution_design)

@trace_method
async def generate_component_code(
    component_type: str,
    component_design: Dict[str, Any],
    requirements: Dict[str, Any],
    task_specification: str,
    tech_stack: Dict[str, str],
    llm_service: LLMService
) -> Dict[str, str]:
    """
    Generate code for a specific component.
    
    Args:
        component_type: Type of component ("frontend", "backend", or "database")
        component_design: Technical design for the component
        requirements: Analyzed requirements
        task_specification: Original task specification
        tech_stack: Detected technology stack
        llm_service: LLM service for code generation
        
    Returns:
        Dict[str, str]: Dictionary mapping file paths to file content
    """
    logger.info(f"Generating code for {component_type} component")
    
    try:
        # Use LLM service to generate code
        component_code = await llm_service.generate_component_code(
            task_specification=task_specification,
            requirements=requirements,
            solution_design={"component_type": component_type, component_type: component_design},
            component=component_type
        )
        
        if not component_code:
            raise ValueError(f"LLM returned empty code for {component_type}")
        
        logger.info(f"LLM successfully generated {len(component_code)} files for {component_type}")
        return component_code
        
    except Exception as e:
        logger.error(f"Error generating {component_type} code: {str(e)}", exc_info=True)
        # return handle_code_generation_errors(
        #     component_type=component_type,
        #     error=str(e),
        #     requirements=requirements,
        #     component_design=component_design,
        #     tech_stack=tech_stack
        # )

@trace_method
def process_generated_code(
    raw_generated_code: Dict[str, str],
    component_type: str,
    tech_stack: Dict[str, str]
) -> Dict[str, str]:
    """
    Process and validate the raw generated code.
    
    Args:
        raw_generated_code: Dictionary of generated file paths and content
        component_type: Type of component
        tech_stack: Detected technology stack
        
    Returns:
        Dict[str, str]: Processed code files
    """
    logger.info(f"Processing generated {component_type} code")
    
    try:
        processed_code = {}
        
        # Create proper file structure
        structured_code = create_file_structure(
            component_type=component_type,
            tech_stack=tech_stack,
            code_content=raw_generated_code
        )
        
        # Perform basic validation and fixes
        for file_path, content in structured_code.items():
            # Fix common issues
            fixed_content = fix_common_code_issues(content, file_path, component_type, tech_stack)
            
            processed_code[file_path] = fixed_content
        
        logger.info(f"Processed {len(processed_code)} code files for {component_type}")
        return processed_code
        
    except Exception as e:
        logger.error(f"Error processing {component_type} code: {str(e)}", exc_info=True)
        return raw_generated_code  # Return original code if processing fails

@trace_method
def detect_technology_stack(
    requirements: Dict[str, Any],
    solution_design: Dict[str, Any]
) -> Dict[str, str]:
    """
    Identify appropriate technologies based on requirements and solution design.
    
    Args:
        requirements: Analyzed requirements
        solution_design: Technical solution design
        
    Returns:
        Dict[str, str]: Detected technology stack
    """
    logger.info("Detecting technology stack")
    
    tech_stack = {
        "frontend": "react",
        "backend": "node",
        "database": "mongodb"
    }
    
    try:
        # Check tech recommendations in requirements
        tech_recommendations = requirements.get("technology_recommendations", {})
        
        if "frontend" in tech_recommendations and tech_recommendations["frontend"]:
            frontend_techs = tech_recommendations["frontend"]
            # Determine primary frontend technology
            if any("react" in tech.lower() for tech in frontend_techs):
                tech_stack["frontend"] = "react"
            elif any("angular" in tech.lower() for tech in frontend_techs):
                tech_stack["frontend"] = "angular"
            elif any("vue" in tech.lower() for tech in frontend_techs):
                tech_stack["frontend"] = "vue"
        
        if "backend" in tech_recommendations and tech_recommendations["backend"]:
            backend_techs = tech_recommendations["backend"]
            # Determine primary backend technology
            if any("node" in tech.lower() or "express" in tech.lower() for tech in backend_techs):
                tech_stack["backend"] = "node"
            elif any("python" in tech.lower() or "django" in tech.lower() or "flask" in tech.lower() for tech in backend_techs):
                tech_stack["backend"] = "python"
            elif any("java" in tech.lower() or "spring" in tech.lower() for tech in backend_techs):
                tech_stack["backend"] = "java"
        
        if "database" in tech_recommendations and tech_recommendations["database"]:
            db_techs = tech_recommendations["database"]
            # Determine primary database technology
            if any("mongodb" in tech.lower() or "nosql" in tech.lower() for tech in db_techs):
                tech_stack["database"] = "mongodb"
            elif any("postgres" in tech.lower() or "postgresql" in tech.lower() for tech in db_techs):
                tech_stack["database"] = "postgresql"
            elif any("mysql" in tech.lower() for tech in db_techs):
                tech_stack["database"] = "mysql"
            elif any("sqlite" in tech.lower() for tech in db_techs):
                tech_stack["database"] = "sqlite"
        
        # Check solution design for more specific technology information
        if "frontend" in solution_design and solution_design["frontend"]:
            frontend_design = solution_design["frontend"]
            # Extract from architecture or frameworks field
            frameworks = frontend_design.get("ui_frameworks", [])
            if frameworks:
                if any("react" in fw.lower() for fw in frameworks):
                    tech_stack["frontend"] = "react"
                elif any("angular" in fw.lower() for fw in frameworks):
                    tech_stack["frontend"] = "angular"
                elif any("vue" in fw.lower() for fw in frameworks):
                    tech_stack["frontend"] = "vue"
        
        if "backend" in solution_design and solution_design["backend"]:
            backend_design = solution_design["backend"]
            # Extract from frameworks field
            frameworks = backend_design.get("frameworks", [])
            if frameworks:
                if any("node" in fw.lower() or "express" in fw.lower() for fw in frameworks):
                    tech_stack["backend"] = "node"
                elif any("python" in fw.lower() or "django" in fw.lower() or "flask" in fw.lower() for fw in frameworks):
                    tech_stack["backend"] = "python"
                elif any("java" in fw.lower() or "spring" in fw.lower() for fw in frameworks):
                    tech_stack["backend"] = "java"
        
        if "database" in solution_design and solution_design["database"]:
            db_design = solution_design["database"]
            # Extract from database_type field
            db_type = db_design.get("database_type", "")
            if db_type:
                if "mongodb" in db_type.lower() or "nosql" in db_type.lower():
                    tech_stack["database"] = "mongodb"
                elif "postgres" in db_type.lower() or "postgresql" in db_type.lower():
                    tech_stack["database"] = "postgresql"
                elif "mysql" in db_type.lower():
                    tech_stack["database"] = "mysql"
                elif "sqlite" in db_type.lower():
                    tech_stack["database"] = "sqlite"
        
        logger.info(f"Detected technology stack: {tech_stack}")
        return tech_stack
        
    except Exception as e:
        logger.error(f"Error detecting technology stack: {str(e)}", exc_info=True)
        return tech_stack  # Return default tech stack if detection fails

@trace_method
def create_file_structure(
    component_type: str,
    tech_stack: Dict[str, str],
    code_content: Dict[str, str]
) -> Dict[str, str]:
    """
    Organize code into appropriate file structure.
    
    Args:
        component_type: Type of component
        tech_stack: Detected technology stack
        code_content: Raw code content
        
    Returns:
        Dict[str, str]: Structured code files
    """
    logger.info(f"Creating file structure for {component_type}")
    
    structured_code = {}
    
    try:
        # Get technology for this component
        tech = tech_stack.get(component_type, "")
        
        if component_type == "frontend":
            # Handle frontend structure based on technology
            if tech == "react":
                structured_code = create_react_structure(code_content)
            elif tech == "angular":
                structured_code = create_angular_structure(code_content)
            elif tech == "vue":
                structured_code = create_vue_structure(code_content)
            else:
                # Default structure
                structured_code = create_generic_frontend_structure(code_content)
        
        elif component_type == "backend":
            # Handle backend structure based on technology
            if tech == "node":
                structured_code = create_node_structure(code_content)
            elif tech == "python":
                structured_code = create_python_structure(code_content)
            elif tech == "java":
                structured_code = create_java_structure(code_content)
            else:
                # Default structure
                structured_code = create_generic_backend_structure(code_content)
        
        elif component_type == "database":
            # Handle database structure
            structured_code = create_database_structure(code_content, tech)
        
        logger.info(f"Created file structure with {len(structured_code)} files for {component_type}")
        return structured_code
        
    except Exception as e:
        logger.error(f"Error creating file structure for {component_type}: {str(e)}", exc_info=True)
        return code_content  # Return original structure if creation fails

def create_react_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for React frontend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Add src/ prefix if not present for component files
        if file_path.endswith(".jsx") or file_path.endswith(".tsx") or file_path.endswith(".js") or file_path.endswith(".ts"):
            if not file_path.startswith("src/"):
                file_path = f"src/{file_path}"
        
        # Organize components in components directory
        if ("component" in file_path.lower() and not file_path.startswith("src/components/")):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/components/{file_name}"
        
        # Organize pages
        if ("page" in file_path.lower() and not file_path.startswith("src/pages/")):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/pages/{file_name}"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any(file.endswith("App.jsx") or file.endswith("App.tsx") or file.endswith("App.js") for file in structured_code.keys()):
        # Add basic App component if missing
        structured_code["src/App.jsx"] = "import React from 'react';\n\nfunction App() {\n  return (\n    <div className=\"App\">\n      <h1>React App</h1>\n    </div>\n  );\n}\n\nexport default App;\n"
    
    if not any(file.endswith("index.jsx") or file.endswith("index.js") for file in structured_code.keys()):
        # Add basic index file if missing
        structured_code["src/index.jsx"] = "import React from 'react';\nimport ReactDOM from 'react-dom';\nimport App from './App';\n\nReactDOM.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>,\n  document.getElementById('root')\n);\n"
    
    return structured_code

def create_angular_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for Angular frontend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Add src/app prefix if not present for component files
        if file_path.endswith(".ts") or file_path.endswith(".html") or file_path.endswith(".css"):
            if not file_path.startswith("src/"):
                file_path = f"src/app/{file_path}"
        
        # Organize components in their own folders
        if "component" in file_path.lower() and ".component." in file_path.lower():
            parts = file_path.split("/")
            file_name = parts[-1]
            component_name = file_name.split(".")[0]
            if not file_path.startswith(f"src/app/{component_name}/"):
                file_path = f"src/app/{component_name}/{file_name}"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any("app.module.ts" in file.lower() for file in structured_code.keys()):
        # Add basic AppModule if missing
        structured_code["src/app/app.module.ts"] = "import { NgModule } from '@angular/core';\nimport { BrowserModule } from '@angular/platform-browser';\nimport { AppComponent } from './app.component';\n\n@NgModule({\n  declarations: [AppComponent],\n  imports: [BrowserModule],\n  providers: [],\n  bootstrap: [AppComponent]\n})\nexport class AppModule { }\n"
    
    if not any("app.component.ts" in file.lower() for file in structured_code.keys()):
        # Add basic AppComponent if missing
        structured_code["src/app/app.component.ts"] = "import { Component } from '@angular/core';\n\n@Component({\n  selector: 'app-root',\n  templateUrl: './app.component.html',\n  styleUrls: ['./app.component.css']\n})\nexport class AppComponent {\n  title = 'angular-app';\n}\n"
        structured_code["src/app/app.component.html"] = "<h1>{{title}}</h1>\n"
        structured_code["src/app/app.component.css"] = "/* App Component Styles */\n"
    
    return structured_code

def create_vue_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for Vue frontend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Add src/ prefix if not present
        if not file_path.startswith("src/"):
            file_path = f"src/{file_path}"
        
        # Organize components in components directory
        if "component" in file_path.lower() and not file_path.startswith("src/components/"):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/components/{file_name}"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any(file.endswith("App.vue") for file in structured_code.keys()):
        # Add basic App component if missing
        structured_code["src/App.vue"] = "<template>\n  <div id=\"app\">\n    <h1>{{ msg }}</h1>\n  </div>\n</template>\n\n<script>\nexport default {\n  name: 'App',\n  data() {\n    return {\n      msg: 'Vue App'\n    }\n  }\n}\n</script>\n\n<style>\n#app {\n  font-family: 'Avenir', Helvetica, Arial, sans-serif;\n  text-align: center;\n  margin-top: 60px;\n}\n</style>\n"
    
    if not any(file.endswith("main.js") for file in structured_code.keys()):
        # Add basic main.js if missing
        structured_code["src/main.js"] = "import Vue from 'vue'\nimport App from './App.vue'\n\nVue.config.productionTip = false\n\nnew Vue({\n  render: h => h(App),\n}).$mount('#app')\n"
    
    return structured_code

def create_generic_frontend_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create a generic structure for frontend code."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Ensure all code is under src/
        if not file_path.startswith("src/"):
            file_path = f"src/{file_path}"
            
        structured_code[file_path] = content
    
    return structured_code

def create_node_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for Node.js backend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Organize routes
        if "route" in file_path.lower() and not file_path.startswith("src/routes/"):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/routes/{file_name}"
        
        # Organize controllers
        if "controller" in file_path.lower() and not file_path.startswith("src/controllers/"):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/controllers/{file_name}"
            
        # Organize models
        if "model" in file_path.lower() and not file_path.startswith("src/models/"):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/models/{file_name}"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any(file.endswith("server.js") or file.endswith("app.js") or file.endswith("index.js") for file in structured_code.keys()):
        # Add basic server file if missing
        structured_code["src/server.js"] = "const express = require('express');\nconst app = express();\nconst port = process.env.PORT || 3000;\n\napp.use(express.json());\n\napp.get('/', (req, res) => {\n  res.send('API Running');\n});\n\napp.listen(port, () => {\n  console.log(`Server running on port ${port}`);\n});\n"
    
    return structured_code

def create_python_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for Python backend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Ensure file has .py extension
        if not file_path.endswith(".py"):
            file_path = f"{file_path}.py"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any(file.endswith("app.py") or file.endswith("main.py") for file in structured_code.keys()):
        # Add basic app file if missing
        structured_code["app.py"] = "from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return jsonify({'message': 'API Running'})\n\nif __name__ == '__main__':\n    app.run(debug=True)\n"
    
    return structured_code

def create_java_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create file structure for Java backend."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Ensure file has .java extension
        if not file_path.endswith(".java"):
            file_path = f"{file_path}.java"
            
        # Organize files into packages
        if "controller" in file_path.lower() and not "src/main/java/com/app/controller" in file_path:
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/main/java/com/app/controller/{file_name}"
            
        if "model" in file_path.lower() and not "src/main/java/com/app/model" in file_path:
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/main/java/com/app/model/{file_name}"
            
        if "service" in file_path.lower() and not "src/main/java/com/app/service" in file_path:
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"src/main/java/com/app/service/{file_name}"
            
        structured_code[file_path] = content
    
    # Ensure core files exist
    if not any("Application.java" in file for file in structured_code.keys()):
        # Add basic application file if missing
        structured_code["src/main/java/com/app/Application.java"] = "package com.app;\n\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n\n@SpringBootApplication\npublic class Application {\n\n    public static void main(String[] args) {\n        SpringApplication.run(Application.class, args);\n    }\n}\n"
    
    return structured_code

def create_generic_backend_structure(code_content: Dict[str, str]) -> Dict[str, str]:
    """Create a generic structure for backend code."""
    structured_code = {}
    
    for file_path, content in code_content.items():
        # Ensure all code is under src/
        if not file_path.startswith("src/"):
            file_path = f"src/{file_path}"
            
        structured_code[file_path] = content
    
    return structured_code

def create_database_structure(code_content: Dict[str, str], db_tech: str) -> Dict[str, str]:
    """Create file structure for database code."""
    structured_code = {}
    
    # Directory based on database technology
    db_dir = "database"
    if db_tech == "mongodb":
        db_dir = "models"
    elif db_tech in ["postgresql", "mysql", "sqlite"]:
        db_dir = "migrations"
    
    for file_path, content in code_content.items():
        # Organize files into appropriate directory
        if not file_path.startswith(f"{db_dir}/"):
            parts = file_path.split("/")
            file_name = parts[-1]
            file_path = f"{db_dir}/{file_name}"
            
        structured_code[file_path] = content
    
    return structured_code

def fix_common_code_issues(
    content: str,
    file_path: str,
    component_type: str,
    tech_stack: Dict[str, str]
) -> str:
    """
    Fix common issues in generated code.
    
    Args:
        content: File content
        file_path: Path to the file
        component_type: Type of component
        tech_stack: Detected technology stack
        
    Returns:
        str: Fixed code content
    """
    fixed_content = content
    
    try:
        # Fix incorrect imports
        if component_type == "frontend" and tech_stack.get("frontend") == "react":
            # Fix React imports
            if "import React" not in fixed_content and (file_path.endswith(".jsx") or file_path.endswith(".tsx")):
                fixed_content = "import React from 'react';\n" + fixed_content
        
        # Fix missing exports
        if component_type == "frontend":
            # Check for component definitions without exports
            if tech_stack.get("frontend") == "react":
                if "function " in fixed_content and "export default " not in fixed_content:
                    # Extract component name
                    match = re.search(r"function\s+(\w+)", fixed_content)
                    if match:
                        component_name = match.group(1)
                        fixed_content += f"\n\nexport default {component_name};\n"
        
        # Fix incorrect path references
        if component_type == "backend" and tech_stack.get("backend") == "node":
            # Fix path modules
            if "require('path')" not in fixed_content and "__dirname" in fixed_content:
                fixed_content = "const path = require('path');\n" + fixed_content
            
            # Fix model imports in controllers
            if "controller" in file_path.lower() and "require('../models/" not in fixed_content and "models" in fixed_content.lower():
                fixed_content = fixed_content.replace("require('./models/", "require('../models/")
                fixed_content = fixed_content.replace("require('models/", "require('../models/")
        
        return fixed_content
        
    except Exception as e:
        logger.error(f"Error fixing code issues in {file_path}: {str(e)}", exc_info=True)
        return content  # Return original content if fixing fails

@trace_method
def validate_code_consistency(generated_code: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    Ensure code components work together properly.
    
    Args:
        generated_code: Dictionary of generated code by component
        
    Returns:
        Dict[str, Any]: Consistency validation results
    """
    logger.info("Validating code consistency across components")
    
    result = {
        "is_consistent": True,
        "issues": []
    }
    
    try:
        # Frontend-Backend API consistency check
        frontend_code = generated_code.get("frontend", {})
        backend_code = generated_code.get("backend", {})
        
        if frontend_code and backend_code:
            # Check API endpoint consistency
            api_endpoints_backend = extract_api_endpoints(backend_code)
            api_endpoints_frontend = extract_api_calls(frontend_code)
            
            # Find mismatches
            for endpoint in api_endpoints_frontend:
                if endpoint not in api_endpoints_backend:
                    result["is_consistent"] = False
                    result["issues"].append(f"Frontend calls API endpoint '{endpoint}' which is not defined in backend")
        
        # Backend-Database model consistency check
        database_code = generated_code.get("database", {})
        
        if backend_code and database_code:
            # Check model usage consistency
            db_models = extract_db_models(database_code)
            backend_models = extract_model_usage(backend_code)
            
            # Find mismatches
            for model in backend_models:
                if model not in db_models:
                    result["is_consistent"] = False
                    result["issues"].append(f"Backend uses database model '{model}' which is not defined in database code")
        
        logger.info(f"Code consistency validation completed: {'Passed' if result['is_consistent'] else 'Failed'}")
        if not result["is_consistent"]:
            logger.warning(f"Consistency issues found: {result['issues']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Error validating code consistency: {str(e)}", exc_info=True)
        result["is_consistent"] = False
        result["issues"].append(f"Error during consistency validation: {str(e)}")
        return result

def extract_api_endpoints(backend_code: Dict[str, str]) -> List[str]:
    """Extract API endpoints from backend code."""
    endpoints = []
    
    for _, content in backend_code.items():
        # Look for common API endpoint patterns
        # Express.js pattern
        for method in ["get", "post", "put", "delete", "patch"]:
            pattern = rf"\.{method}\(['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, content, re.IGNORECASE)
            endpoints.extend(matches)
        
        # Flask pattern
        flask_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
        matches = re.findall(flask_pattern, content, re.IGNORECASE)
        endpoints.extend(matches)
        
        # Spring Boot pattern
        spring_pattern = r"@(Get|Post|Put|Delete|Patch)Mapping\(['\"]([^'\"]*)['\"]"
        matches = re.findall(spring_pattern, content, re.IGNORECASE)
        endpoints.extend([m[1] if m[1] else "/" for m in matches])
    
    # Normalize endpoints
    normalized = []
    for endpoint in endpoints:
        # Ensure it starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        normalized.append(endpoint)
    
    return normalized

def extract_api_calls(frontend_code: Dict[str, str]) -> List[str]:
    """Extract API calls from frontend code."""
    endpoints = []
    
    for _, content in frontend_code.items():
        # Look for common API call patterns
        # Fetch pattern
        fetch_pattern = r"fetch\(['\"]([^'\"]+)['\"]"
        matches = re.findall(fetch_pattern, content)
        for match in matches:
            # Extract just the path from URLs
            if match.startswith("http"):
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(match)
                    endpoints.append(parsed.path)
                except:
                    # If parsing fails, just use as is
                    endpoints.append(match)
            else:
                endpoints.append(match)
        
        # Axios pattern
        axios_pattern = r"axios\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"
        matches = re.findall(axios_pattern, content)
        endpoints.extend([m[1] for m in matches])
        
        # General URL pattern
        url_pattern = r"(url|URL|endpoint|api)\s*:\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(url_pattern, content)
        endpoints.extend([m[1] for m in matches])
    
    # Normalize endpoints
    normalized = []
    for endpoint in endpoints:
        # Filter out non-API endpoints
        if not endpoint.startswith("/api") and not "/api/" in endpoint:
            continue
        # Ensure it starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        normalized.append(endpoint)
    
    return normalized

def extract_db_models(database_code: Dict[str, str]) -> List[str]:
    """Extract database models from database code."""
    models = []
    
    for file_path, content in database_code.items():
        # Look for common model definition patterns
        # Mongoose pattern
        mongoose_pattern = r"mongoose\.model\(['\"]([^'\"]+)['\"]"
        matches = re.findall(mongoose_pattern, content)
        models.extend(matches)
        
        # Sequelize pattern
        sequelize_pattern = r"sequelize\.define\(['\"]([^'\"]+)['\"]"
        matches = re.findall(sequelize_pattern, content)
        models.extend(matches)
        
        # SQL table pattern
        sql_pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?"
        matches = re.findall(sql_pattern, content, re.IGNORECASE)
        models.extend(matches)
        
        # Extract model names from filenames
        if "models/" in file_path or "models\\" in file_path:
            filename = file_path.split("/")[-1].split("\\")[-1]
            model_name = filename.split(".")[0].capitalize()
            models.append(model_name)
    
    # Normalize model names
    normalized = []
    for model in models:
        # Convert to lowercase for case-insensitive comparison
        normalized.append(model.lower())
    
    return normalized

def extract_model_usage(backend_code: Dict[str, str]) -> List[str]:
    """Extract model usage from backend code."""
    models = []
    
    for file_path, content in backend_code.items():
        # Common model import or require patterns
        import_pattern = r"(?:require|import)\s*\(?['\"].*models?\/([^'\"\/]+)['\"]"
        matches = re.findall(import_pattern, content)
        models.extend(matches)
        
        # Model usage patterns
        model_pattern = r"(Model|Entity|Table|Document)\s*[:{<]\s*['\"]?([a-zA-Z0-9_]+)['\"]?"
        matches = re.findall(model_pattern, content)
        models.extend([m[1] for m in matches])
        
        # Variable name patterns that likely represent models
        var_pattern = r"(?:const|let|var)\s+([A-Z][a-zA-Z0-9_]*(?:Model|Entity|Schema))\s*="
        matches = re.findall(var_pattern, content)
        models.extend([m.replace("Model", "").replace("Entity", "").replace("Schema", "") for m in matches])
    
    # Normalize model names
    normalized = []
    for model in models:
        # Convert to lowercase for case-insensitive comparison
        normalized.append(model.lower())
    
    return normalized

 