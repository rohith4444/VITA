from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.full_stack_developer.llm.service import LLMService

# Initialize logger
logger = setup_logger("tools.full_stack_developer.solution_designer")

@trace_method
async def design_solution(
    task_specification: str,
    requirements: Dict[str, Any],
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Design comprehensive solution for all components.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        llm_service: LLM service for design generation
        
    Returns:
        Dict[str, Any]: Complete solution design for all components
    """
    logger.info("Starting solution design process")
    
    try:
        solution_design = {}
        
        # Design each component
        components = ["frontend", "backend", "database"]
        for component in components:
            logger.info(f"Designing {component} component")
            component_design = await design_component(
                task_specification=task_specification,
                requirements=requirements,
                component=component,
                llm_service=llm_service
            )
            solution_design[component] = component_design
            logger.info(f"{component.capitalize()} design completed")
        
        # Integrate the components
        solution_design = integrate_components(solution_design)
        
        logger.info("Complete solution design finished")
        return solution_design
        
    except Exception as e:
        logger.error(f"Error designing solution: {str(e)}", exc_info=True)
        return generate_fallback_design(requirements)

@trace_method
async def design_component(
    task_specification: str,
    requirements: Dict[str, Any],
    component: str,
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Design a specific component of the solution.
    
    Args:
        task_specification: Original task specification
        requirements: Analyzed requirements
        component: Component to design ("frontend", "backend", or "database")
        llm_service: LLM service for design generation
        
    Returns:
        Dict[str, Any]: Component design
    """
    logger.info(f"Starting {component} component design")
    
    try:
        # Use LLM to design the component
        component_design = await llm_service.design_solution_component(
            task_specification=task_specification,
            requirements=requirements,
            component=component
        )
        
        # Validate and enhance the design
        enhanced_design = enhance_component_design(component_design, component, requirements)
        
        logger.info(f"{component.capitalize()} component design completed")
        return enhanced_design
        
    except Exception as e:
        logger.error(f"Error designing {component} component: {str(e)}", exc_info=True)
        return generate_fallback_component_design(component, requirements)

def enhance_component_design(
    design: Dict[str, Any],
    component: str,
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate and enhance component design.
    
    Args:
        design: Initial component design
        component: Component type
        requirements: Requirements analysis
        
    Returns:
        Dict[str, Any]: Enhanced component design
    """
    logger.debug(f"Enhancing {component} design")
    
    try:
        enhanced = design.copy()
        
        # Ensure component-specific structures are present
        if component == "frontend":
            required_keys = [
                "architecture", "components", "state_management", 
                "routing", "ui_frameworks", "api_integration", "file_structure"
            ]
        elif component == "backend":
            required_keys = [
                "architecture", "api_endpoints", "business_logic", 
                "middleware", "auth_approach", "frameworks", "data_access", "file_structure"
            ]
        else:  # database
            required_keys = [
                "database_type", "models", "relationships", 
                "indexing_strategy", "optimization", "migrations", "schema_diagram"
            ]
        
        # Check and add missing keys
        for key in required_keys:
            if key not in enhanced or not enhanced[key]:
                logger.warning(f"Missing key in {component} design: {key}")
                if key in ["components", "api_endpoints", "models", "relationships", "file_structure"]:
                    enhanced[key] = []
                elif key == "architecture":
                    enhanced[key] = get_default_architecture(component)
                elif key == "state_management":
                    enhanced[key] = {"approach": "Context API + Hooks", "stores": ["AppState"]}
                elif key == "routing":
                    enhanced[key] = [{"path": "/", "component": "MainPage", "purpose": "Main application page"}]
                elif key == "ui_frameworks":
                    enhanced[key] = ["React", "Tailwind CSS"]
                elif key == "api_integration":
                    enhanced[key] = {"approach": "Axios for API calls", "endpoints": ["/api/data"]}
                elif key == "business_logic":
                    enhanced[key] = {"approach": "Service modules", "modules": ["UserService", "DataService"]}
                elif key == "middleware":
                    enhanced[key] = [{"name": "Authentication", "purpose": "Validate user authentication"}]
                elif key == "auth_approach":
                    enhanced[key] = {"strategy": "JWT", "implementation": "Token-based authentication"}
                elif key == "frameworks":
                    enhanced[key] = tech_recommendations_for_component(component, requirements)
                elif key == "data_access":
                    enhanced[key] = {"approach": "Repository pattern", "models": ["UserModel"]}
                elif key == "database_type":
                    enhanced[key] = tech_recommendations_for_component("database", requirements)[0]
                elif key == "indexing_strategy":
                    enhanced[key] = [{"model": "User", "fields": ["email"], "purpose": "Fast lookup by email"}]
                elif key == "optimization":
                    enhanced[key] = {"strategies": ["Indexing", "Query optimization"], "considerations": ["Performance", "Scalability"]}
                elif key == "migrations":
                    enhanced[key] = {"approach": "Version-controlled migrations", "tooling": "Migration scripts"}
                elif key == "schema_diagram":
                    enhanced[key] = "User -> Posts (one-to-many), User -> Profile (one-to-one)"
        
        logger.debug(f"{component.capitalize()} design enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing {component} design: {str(e)}", exc_info=True)
        return design

def integrate_components(solution_design: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrate component designs to ensure consistency.
    
    Args:
        solution_design: Component designs
        
    Returns:
        Dict[str, Any]: Integrated solution design
    """
    logger.debug("Integrating component designs")
    
    try:
        # Add integration metadata
        solution_design["integration"] = {
            "frontend_to_backend": {
                "approach": "REST API",
                "endpoints": extract_api_endpoints(solution_design)
            },
            "backend_to_database": {
                "approach": extract_database_approach(solution_design),
                "models": extract_database_models(solution_design)
            },
            "authentication_flow": {
                "method": extract_auth_method(solution_design),
                "flow": "Login -> Generate Token -> Validate Token on Requests"
            },
            "deployment_considerations": {
                "frontend": "Static hosting",
                "backend": "Container-based deployment",
                "database": "Managed database service"
            }
        }
        
        logger.debug("Component integration completed")
        return solution_design
        
    except Exception as e:
        logger.error(f"Error integrating components: {str(e)}", exc_info=True)
        return solution_design

def generate_fallback_design(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate fallback solution design when normal design fails.
    
    Args:
        requirements: Requirements analysis
        
    Returns:
        Dict[str, Any]: Fallback solution design
    """
    logger.info("Generating fallback solution design")
    
    # Generate fallback design for each component
    frontend_design = generate_fallback_component_design("frontend", requirements)
    backend_design = generate_fallback_component_design("backend", requirements)
    database_design = generate_fallback_component_design("database", requirements)
    
    # Combine component designs
    fallback_design = {
        "frontend": frontend_design,
        "backend": backend_design,
        "database": database_design
    }
    
    # Add integration
    fallback_design["integration"] = {
        "frontend_to_backend": {
            "approach": "REST API",
            "endpoints": ["/api/data", "/api/auth/login", "/api/auth/logout"]
        },
        "backend_to_database": {
            "approach": "ORM",
            "models": ["User", "Data"]
        },
        "authentication_flow": {
            "method": "JWT",
            "flow": "Login -> Generate Token -> Validate Token on Requests"
        },
        "deployment_considerations": {
            "frontend": "Static hosting",
            "backend": "Container-based deployment",
            "database": "Managed database service"
        }
    }
    
    logger.info("Fallback solution design generated successfully")
    return fallback_design

def generate_fallback_component_design(
    component: str,
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate fallback design for a specific component.
    
    Args:
        component: Component to design
        requirements: Requirements analysis
        
    Returns:
        Dict[str, Any]: Fallback component design
    """
    logger.info(f"Generating fallback {component} design")
    
    tech_recommendations = requirements.get("technology_recommendations", {})
    features = requirements.get("features", [])
    
    if component == "frontend":
        # Extract feature names for components
        component_names = [
            feature.get("name", "").replace(" ", "") + "Component" 
            for feature in features[:3]
        ]
        if not component_names:
            component_names = ["HomeComponent", "DataComponent", "ProfileComponent"]
            
        return {
            "architecture": "Component-based architecture using React",
            "components": [
                {
                    "name": comp_name,
                    "purpose": f"Handles {comp_name.replace('Component', '')} functionality",
                    "subcomponents": [f"{comp_name}Header", f"{comp_name}Body"]
                } for comp_name in component_names
            ],
            "state_management": {
                "approach": "Context API + Hooks",
                "stores": ["AppState", "UserState"]
            },
            "routing": [
                {"path": "/", "component": "HomePage", "purpose": "Main landing page"},
                {"path": "/profile", "component": "ProfilePage", "purpose": "User profile"},
                {"path": "/data", "component": "DataPage", "purpose": "Data display"}
            ],
            "ui_frameworks": tech_recommendations_for_component("frontend", requirements),
            "api_integration": {
                "approach": "Axios for API calls",
                "endpoints": ["/api/data", "/api/user", "/api/auth"]
            },
            "file_structure": [
                {"path": "src/components", "purpose": "React components"},
                {"path": "src/pages", "purpose": "Page components"},
                {"path": "src/context", "purpose": "Context providers"},
                {"path": "src/api", "purpose": "API integration"},
                {"path": "src/utils", "purpose": "Utility functions"}
            ]
        }
    elif component == "backend":
        # Extract feature names for API endpoints
        endpoint_names = [
            feature.get("name", "").replace(" ", "").lower() 
            for feature in features[:3]
        ]
        if not endpoint_names:
            endpoint_names = ["users", "data", "auth"]
            
        return {
            "architecture": "Layered architecture with MVC pattern",
            "api_endpoints": [
                {
                    "path": f"/api/{endpoint}", 
                    "method": "GET",
                    "purpose": f"Retrieve {endpoint} data",
                    "request_params": ["limit", "offset"],
                    "response_format": "JSON array of objects"
                } for endpoint in endpoint_names
            ] + [
                {
                    "path": f"/api/{endpoint}", 
                    "method": "POST",
                    "purpose": f"Create new {endpoint} entry",
                    "request_params": ["data object"],
                    "response_format": "JSON object with ID"
                } for endpoint in endpoint_names
            ],
            "business_logic": {
                "approach": "Service-based architecture",
                "modules": [f"{endpoint.capitalize()}Service" for endpoint in endpoint_names]
            },
            "middleware": [
                {"name": "Authentication", "purpose": "Validate user authentication"},
                {"name": "Validation", "purpose": "Validate request data"},
                {"name": "Error Handling", "purpose": "Global error handling"}
            ],
            "auth_approach": {
                "strategy": "JWT",
                "implementation": "Token-based authentication"
            },
            "frameworks": tech_recommendations_for_component("backend", requirements),
            "data_access": {
                "approach": "Repository pattern",
                "models": [f"{endpoint.capitalize()}Model" for endpoint in endpoint_names]
            },
            "file_structure": [
                {"path": "src/controllers", "purpose": "Request handlers"},
                {"path": "src/services", "purpose": "Business logic"},
                {"path": "src/models", "purpose": "Data models"},
                {"path": "src/middleware", "purpose": "Middleware functions"},
                {"path": "src/utils", "purpose": "Utility functions"}
            ]
        }
    else:  # database
        # Extract entity names from features
        entity_names = [
            feature.get("name", "").replace(" ", "") 
            for feature in features[:3]
        ]
        if not entity_names:
            entity_names = ["User", "Data", "Profile"]
            
        return {
            "database_type": tech_recommendations_for_component("database", requirements)[0],
            "models": [
                {
                    "name": entity_name,
                    "attributes": [
                        {"name": "id", "type": "String/UUID", "constraints": ["Primary Key"]},
                        {"name": "name", "type": "String", "constraints": ["Not Null"]},
                        {"name": "created_at", "type": "DateTime", "constraints": ["Not Null"]}
                    ]
                } for entity_name in entity_names
            ],
            "relationships": [
                {
                    "source": "User",
                    "target": "Profile",
                    "type": "One-to-One",
                    "description": "Each user has one profile"
                },
                {
                    "source": "User",
                    "target": "Data",
                    "type": "One-to-Many",
                    "description": "Each user has many data entries"
                }
            ],
            "indexing_strategy": [
                {
                    "model": "User",
                    "fields": ["email"],
                    "purpose": "Fast lookup by email"
                },
                {
                    "model": "Data",
                    "fields": ["created_at"],
                    "purpose": "Time-based queries"
                }
            ],
            "optimization": {
                "strategies": ["Indexing", "Query optimization", "Caching"],
                "considerations": ["Performance", "Scalability", "Data integrity"]
            },
            "migrations": {
                "approach": "Version-controlled migrations",
                "tooling": "Migration scripts"
            },
            "schema_diagram": "User(id, name, email) -> Profile(id, user_id, details), User(id) -> Data(id, user_id, content)"
        }

# Helper functions

def get_default_architecture(component: str) -> str:
    """Get default architecture pattern for component."""
    if component == "frontend":
        return "Component-based architecture with React"
    elif component == "backend":
        return "Layered architecture with MVC pattern"
    else:  # database
        return "Relational database with ORM"

def tech_recommendations_for_component(component: str, requirements: Dict[str, Any]) -> List[str]:
    """Extract technology recommendations for a component."""
    try:
        tech_recs = requirements.get("technology_recommendations", {})
        component_recs = tech_recs.get(component, [])
        
        if not component_recs:
            if component == "frontend":
                return ["React", "TypeScript", "Tailwind CSS"]
            elif component == "backend":
                return ["Node.js", "Express"]
            else:  # database
                return ["MongoDB", "PostgreSQL"]
        
        return component_recs
    except Exception:
        logger.error(f"Error extracting tech recommendations for {component}", exc_info=True)
        if component == "frontend":
            return ["React", "TypeScript", "Tailwind CSS"]
        elif component == "backend":
            return ["Node.js", "Express"]
        else:  # database
            return ["MongoDB", "PostgreSQL"]

def extract_api_endpoints(solution_design: Dict[str, Any]) -> List[str]:
    """Extract API endpoints from backend design."""
    try:
        backend_design = solution_design.get("backend", {})
        api_endpoints = backend_design.get("api_endpoints", [])
        
        endpoints = []
        for endpoint in api_endpoints:
            path = endpoint.get("path", "")
            if path:
                endpoints.append(path)
        
        if not endpoints:
            endpoints = ["/api/data", "/api/users", "/api/auth"]
            
        return endpoints
    except Exception:
        logger.error("Error extracting API endpoints", exc_info=True)
        return ["/api/data", "/api/users", "/api/auth"]

def extract_database_approach(solution_design: Dict[str, Any]) -> str:
    """Extract database approach from designs."""
    try:
        backend_design = solution_design.get("backend", {})
        data_access = backend_design.get("data_access", {})
        approach = data_access.get("approach", "")
        
        if not approach:
            db_design = solution_design.get("database", {})
            db_type = db_design.get("database_type", "").lower()
            
            if "mongo" in db_type or "nosql" in db_type:
                return "ODM (Object Document Mapper)"
            else:
                return "ORM (Object Relational Mapper)"
        
        return approach
    except Exception:
        logger.error("Error extracting database approach", exc_info=True)
        return "ORM (Object Relational Mapper)"

def extract_database_models(solution_design: Dict[str, Any]) -> List[str]:
    """Extract database models from designs."""
    try:
        db_design = solution_design.get("database", {})
        models = db_design.get("models", [])
        
        model_names = []
        for model in models:
            name = model.get("name", "")
            if name:
                model_names.append(name)
        
        if not model_names:
            backend_design = solution_design.get("backend", {})
            data_access = backend_design.get("data_access", {})
            backend_models = data_access.get("models", [])
            
            if backend_models:
                return backend_models
            
            model_names = ["User", "Data", "Profile"]
            
        return model_names
    except Exception:
        logger.error("Error extracting database models", exc_info=True)
        return ["User", "Data", "Profile"]

def extract_auth_method(solution_design: Dict[str, Any]) -> str:
    """Extract authentication method from backend design."""
    try:
        backend_design = solution_design.get("backend", {})
        auth_approach = backend_design.get("auth_approach", {})
        strategy = auth_approach.get("strategy", "")
        
        if not strategy:
            return "JWT"
        
        return strategy
    except Exception:
        logger.error("Error extracting authentication method", exc_info=True)
        return "JWT"