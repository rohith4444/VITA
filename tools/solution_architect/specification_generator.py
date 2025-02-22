from core.logging.logger import setup_logger
from typing import Dict, List, Any, Optional
from core.tracing.service import trace_method
from agents.solution_architect.llm.service import LLMService

# Initialize logger
logger = setup_logger("tools.solution_architect.specification_generator")

# Specification templates
SPECIFICATION_TEMPLATES = {
    "component": {
        "component": "",
        "purpose": "",
        "functionality": [],
        "technical_requirements": [],
        "dependencies": []
    },
    "api": {
        "api_name": "",
        "description": "",
        "endpoints": [
            {
                "path": "",
                "method": "",
                "parameters": [],
                "request_format": "",
                "response_format": "",
                "description": ""
            }
        ],
        "authentication": "",
        "rate_limiting": ""
    },
    "database": {
        "database": "",
        "type": "",
        "purpose": "",
        "entities": [
            {
                "name": "",
                "attributes": [],
                "relationships": [],
                "constraints": []
            }
        ],
        "indexing_strategy": "",
        "scaling_strategy": ""
    }
}

@trace_method
async def generate_specifications(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    validation_results: Dict[str, Any],
    llm_service: LLMService
) -> Dict[str, Any]:
    """
    Generate detailed technical specifications based on architecture design.
    
    Args:
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        validation_results: Architecture validation results
        llm_service: LLM service for specification generation
        
    Returns:
        Dict[str, Any]: Detailed technical specifications
    """
    logger.info("Starting technical specification generation")
    
    try:
        # Generate specifications using LLM
        enhance_specs = await llm_service.generate_technical_specifications(
            architecture_design=architecture_design,
            tech_stack=tech_stack,
            validation_results=validation_results
        )
        
        logger.debug(f"Generated specifications: {enhance_specs}")
        
        # Validate and enhance specifications
        # enhanced_specs = enhance_specifications(
        #     specifications,
        #     architecture_design,
        #     tech_stack,
        #     validation_results
        # )
        
        logger.debug(f"Enhanced specifications: {enhance_specs}")
        
        return enhance_specs
        
    except Exception as e:
        logger.error(f"Error generating specifications: {str(e)}", exc_info=True)
        # Generate basic specifications if LLM generation fails
        return generate_basic_specifications(architecture_design, tech_stack, validation_results)

@trace_method
def enhance_specifications(
    specifications: Dict[str, Any],
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate and enhance generated specifications.
    
    Args:
        specifications: Generated specifications
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        validation_results: Validation results
        
    Returns:
        Dict[str, Any]: Enhanced specifications
    """
    logger.info("Enhancing specifications")
    
    try:
        enhanced = {}
        
        # Copy existing specifications
        for key, value in specifications.items():
            enhanced[key] = value
            
        # Ensure all required sections are present
        required_sections = [
            "component_specifications",
            "api_specifications",
            "database_specifications",
            "security_specifications",
            "integration_specifications",
            "performance_specifications",
            "deployment_specifications"
        ]
        
        for section in required_sections:
            if section not in enhanced or not enhanced[section]:
                logger.warning(f"Missing section: {section}")
                enhanced[section] = generate_section(
                    section, 
                    architecture_design, 
                    tech_stack,
                    validation_results
                )
                
        # Address validation concerns
        address_validation_concerns(enhanced, validation_results)
        
        logger.info("Specifications enhancement completed")
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing specifications: {str(e)}", exc_info=True)
        return specifications

@trace_method
def generate_section(
    section_name: str,
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    validation_results: Dict[str, Any]
) -> Any:
    """
    Generate a specific specification section.
    
    Args:
        section_name: Name of the section to generate
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        validation_results: Validation results
        
    Returns:
        Any: Generated section content
    """
    logger.info(f"Generating section: {section_name}")
    
    try:
        if section_name == "component_specifications":
            return generate_component_specs(architecture_design)
        elif section_name == "api_specifications":
            return generate_api_specs(architecture_design)
        elif section_name == "database_specifications":
            return generate_database_specs(architecture_design, tech_stack)
        elif section_name == "security_specifications":
            return generate_security_specs(architecture_design, validation_results)
        elif section_name == "integration_specifications":
            return generate_integration_specs(architecture_design)
        elif section_name == "performance_specifications":
            return generate_performance_specs(validation_results)
        elif section_name == "deployment_specifications":
            return generate_deployment_specs(architecture_design, tech_stack)
        else:
            logger.warning(f"Unknown section: {section_name}")
            return []
            
    except Exception as e:
        logger.error(f"Error generating section {section_name}: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_component_specs(architecture_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate component specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        
    Returns:
        List[Dict[str, Any]]: Component specifications
    """
    logger.info("Generating component specifications")
    
    component_specs = []
    
    try:
        components = architecture_design.get("system_components", [])
        
        for component in components:
            spec = SPECIFICATION_TEMPLATES["component"].copy()
            spec["component"] = component.get("name", "Unnamed Component")
            spec["purpose"] = component.get("description", "")
            spec["functionality"] = component.get("responsibilities", [])
            spec["technical_requirements"] = ["Implementation required"] 
            spec["dependencies"] = []
            
            # Find dependencies from relationships
            relationships = architecture_design.get("component_relationships", [])
            for rel in relationships:
                if rel.get("source") == spec["component"]:
                    spec["dependencies"].append(rel.get("target", ""))
                    
            component_specs.append(spec)
            
        logger.info(f"Generated {len(component_specs)} component specifications")
        return component_specs
        
    except Exception as e:
        logger.error(f"Error generating component specs: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_api_specs(architecture_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate API specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        
    Returns:
        List[Dict[str, Any]]: API specifications
    """
    logger.info("Generating API specifications")
    
    api_specs = []
    
    try:
        apis = architecture_design.get("api_interfaces", [])
        
        for api in apis:
            spec = {
                "api_name": api.get("name", "Unnamed API"),
                "description": api.get("description", ""),
                "endpoints": api.get("endpoints", []),
                "authentication": "JWT Authentication",  # Default
                "rate_limiting": "Standard rate limiting applied"  # Default
            }
            
            # Enhance endpoints if they're minimal
            for i, endpoint in enumerate(spec["endpoints"]):
                if not endpoint.get("parameters"):
                    endpoint["parameters"] = ["id", "authentication_token"]
                if not endpoint.get("request_format"):
                    endpoint["request_format"] = "JSON"
                if not endpoint.get("response_format"):
                    endpoint["response_format"] = "JSON"
                    
            api_specs.append(spec)
            
        logger.info(f"Generated {len(api_specs)} API specifications")
        return api_specs
        
    except Exception as e:
        logger.error(f"Error generating API specs: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_database_specs(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Generate database specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        
    Returns:
        List[Dict[str, Any]]: Database specifications
    """
    logger.info("Generating database specifications")
    
    database_specs = []
    
    try:
        # Extract database technologies
        database_techs = [tech["technology"] for tech in tech_stack.get("database", [])]
        default_db = database_techs[0] if database_techs else "PostgreSQL"
        
        # Get database schema from architecture design
        db_schema = architecture_design.get("database_schema", [])
        
        # If no schema defined, create a basic one
        if not db_schema:
            logger.warning("No database schema found in architecture design")
            db_schema = [
                {"entity": "User", "attributes": ["id", "username", "email"], "relationships": ["has many posts"]},
                {"entity": "Post", "attributes": ["id", "title", "content"], "relationships": ["belongs to user"]}
            ]
            
        # Create database spec
        db_spec = {
            "database": "ApplicationDB",
            "type": default_db,
            "purpose": "Main application database",
            "entities": [],
            "indexing_strategy": "Index on primary keys and foreign keys",
            "scaling_strategy": "Horizontal scaling with read replicas"
        }
        
        # Process entities
        for entity in db_schema:
            entity_spec = {
                "name": entity.get("entity", "UnknownEntity"),
                "attributes": entity.get("attributes", []),
                "relationships": entity.get("relationships", []),
                "constraints": ["Primary key on id"]
            }
            db_spec["entities"].append(entity_spec)
            
        database_specs.append(db_spec)
        
        # Check if we need a caching database
        if "Redis" in str(tech_stack) or "Memcached" in str(tech_stack):
            cache_db = {
                "database": "CacheDB",
                "type": "Redis" if "Redis" in str(tech_stack) else "Memcached",
                "purpose": "Application caching",
                "entities": [
                    {
                        "name": "Cache",
                        "attributes": ["key", "value", "expiration"],
                        "relationships": [],
                        "constraints": ["TTL on all keys"]
                    }
                ],
                "indexing_strategy": "Key-based lookup",
                "scaling_strategy": "Memory scaling with clustering"
            }
            database_specs.append(cache_db)
            
        logger.info(f"Generated {len(database_specs)} database specifications")
        return database_specs
        
    except Exception as e:
        logger.error(f"Error generating database specs: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_security_specs(
    architecture_design: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate security specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        validation_results: Validation results
        
    Returns:
        Dict[str, Any]: Security specifications
    """
    logger.info("Generating security specifications")
    
    try:
        # Get security architecture from design
        security_arch = architecture_design.get("security_architecture", {})
        
        # Check validation results for security concerns
        security_assessment = validation_results.get("security_assessment", {})
        security_findings = security_assessment.get("findings", [])
        security_recommendations = security_assessment.get("recommendations", [])
        
        # Create security spec
        security_spec = {
            "authentication": security_arch.get("authentication", "JWT-based authentication"),
            "authorization": security_arch.get("authorization", "Role-based access control (RBAC)"),
            "data_protection": security_arch.get("data_protection", "Encryption for sensitive data at rest and in transit"),
            "secure_communication": security_arch.get("secure_communication", "HTTPS with TLS 1.3"),
            "security_monitoring": "Regular security auditing and logging"
        }
        
        # Add additional details based on validation findings
        if security_findings or security_recommendations:
            security_spec["additional_measures"] = []
            
            for recommendation in security_recommendations:
                security_spec["additional_measures"].append(recommendation)
                
        logger.info("Generated security specifications")
        return security_spec
        
    except Exception as e:
        logger.error(f"Error generating security specs: {str(e)}", exc_info=True)
        return {
            "authentication": "JWT-based authentication",
            "authorization": "Role-based access control (RBAC)",
            "data_protection": "Encryption for sensitive data",
            "secure_communication": "HTTPS with TLS 1.3",
            "security_monitoring": "Security auditing and logging"
        }

@trace_method
def generate_integration_specs(architecture_design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate integration specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        
    Returns:
        List[Dict[str, Any]]: Integration specifications
    """
    logger.info("Generating integration specifications")
    
    integration_specs = []
    
    try:
        # Look for integration points in data flows
        data_flows = architecture_design.get("data_flows", [])
        
        # Track processed flows to avoid duplicates
        processed_flows = set()
        
        for flow in data_flows:
            source = flow.get("source", "")
            target = flow.get("target", "")
            flow_id = f"{source}-{target}"
            
            # Skip if already processed
            if flow_id in processed_flows:
                continue
                
            processed_flows.add(flow_id)
            
            # Consider flows between different components as integrations
            if source != target and "external" in (source.lower() + target.lower()):
                integration_spec = {
                    "integration_point": f"{source} to {target}",
                    "integration_type": "API" if "api" in flow_id.lower() else "Message Queue" if "queue" in flow_id.lower() else "Direct",
                    "communication_protocol": "REST" if "api" in flow_id.lower() else "AMQP" if "queue" in flow_id.lower() else "HTTP",
                    "data_format": "JSON",
                    "frequency": "Real-time",
                    "error_handling": "Retry with exponential backoff"
                }
                integration_specs.append(integration_spec)
                
        # If no integrations found, create a default one
        if not integration_specs:
            integration_specs.append({
                "integration_point": "Application to External Service",
                "integration_type": "API",
                "communication_protocol": "REST",
                "data_format": "JSON",
                "frequency": "On-demand",
                "error_handling": "Retry with exponential backoff"
            })
            
        logger.info(f"Generated {len(integration_specs)} integration specifications")
        return integration_specs
        
    except Exception as e:
        logger.error(f"Error generating integration specs: {str(e)}", exc_info=True)
        return []

@trace_method
def generate_performance_specs(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate performance specifications from validation results.
    
    Args:
        validation_results: Validation results
        
    Returns:
        Dict[str, Any]: Performance specifications
    """
    logger.info("Generating performance specifications")
    
    try:
        # Check performance assessment in validation results
        performance_assessment = validation_results.get("performance_assessment", {})
        bottlenecks = performance_assessment.get("potential_bottlenecks", [])
        recommendations = performance_assessment.get("recommendations", [])
        
        # Create performance spec
        performance_spec = {
            "response_time_requirements": "API responses <200ms for 95% of requests",
            "throughput_requirements": "System must handle 100 requests/second at peak",
            "scalability_requirements": "Horizontal scaling to handle increased load",
            "resource_usage_limits": "CPU usage <70%, memory usage <80% under normal load"
        }
        
        # Add optimizations based on validation results
        performance_spec["optimizations"] = []
        
        for recommendation in recommendations:
            performance_spec["optimizations"].append(recommendation)
            
        # Address bottlenecks
        if bottlenecks:
            performance_spec["bottleneck_mitigations"] = {}
            for bottleneck in bottlenecks:
                performance_spec["bottleneck_mitigations"][bottleneck] = "Implement appropriate optimization"
                
        logger.info("Generated performance specifications")
        return performance_spec
        
    except Exception as e:
        logger.error(f"Error generating performance specs: {str(e)}", exc_info=True)
        return {
            "response_time_requirements": "API responses <200ms for 95% of requests",
            "throughput_requirements": "System must handle 100 requests/second at peak",
            "scalability_requirements": "Horizontal scaling to handle increased load",
            "resource_usage_limits": "CPU usage <70%, memory usage <80% under normal load"
        }

@trace_method
def generate_deployment_specs(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Generate deployment specifications from architecture design.
    
    Args:
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        
    Returns:
        Dict[str, Any]: Deployment specifications
    """
    logger.info("Generating deployment specifications")
    
    try:
        # Get deployment architecture from design
        deployment_arch = architecture_design.get("deployment_architecture", {})
        
        # Extract infrastructure technologies
        infrastructure_techs = [tech["technology"] for tech in tech_stack.get("infrastructure", [])]
        default_infra = infrastructure_techs[0] if infrastructure_techs else "AWS"
        
        # Extract DevOps technologies
        devops_techs = [tech["technology"] for tech in tech_stack.get("devops", [])]
        has_containers = any(tech in ["Docker", "Kubernetes", "Podman"] for tech in devops_techs)
        
        # Create deployment spec
        deployment_spec = {
            "environments": deployment_arch.get("environments", ["Development", "Staging", "Production"]),
            "infrastructure_requirements": [
                f"{default_infra} cloud platform",
                "Container orchestration" if has_containers else "Virtual machines",
                "Load balancing",
                "Database services"
            ],
            "deployment_process": "CI/CD pipeline with automated testing",
            "monitoring_approach": "Centralized logging and metrics monitoring",
            "rollback_strategy": "Automated rollback on failure detection"
        }
        
        # Add container configuration if using containers
        if has_containers:
            deployment_spec["container_configuration"] = {
                "container_platform": "Docker",
                "orchestration": "Kubernetes" if "Kubernetes" in devops_techs else "Docker Compose",
                "registry": f"{default_infra} Container Registry",
                "scaling_policy": "Auto-scaling based on CPU and memory metrics"
            }
            
        logger.info("Generated deployment specifications")
        return deployment_spec
        
    except Exception as e:
        logger.error(f"Error generating deployment specs: {str(e)}", exc_info=True)
        return {
            "environments": ["Development", "Staging", "Production"],
            "infrastructure_requirements": ["Cloud platform", "Container orchestration", "Load balancing"],
            "deployment_process": "CI/CD pipeline with automated testing",
            "monitoring_approach": "Centralized logging and metrics monitoring",
            "rollback_strategy": "Automated rollback on failure detection"
        }

@trace_method
def address_validation_concerns(
    specifications: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> None:
    """
    Address validation concerns in specifications.
    
    Args:
        specifications: Specifications to update
        validation_results: Validation results with concerns
    """
    logger.info("Addressing validation concerns")
    
    try:
        # Extract concerns and risks
        validation_summary = validation_results.get("validation_summary", {})
        concerns = validation_summary.get("concerns", [])
        risks = validation_summary.get("risks", [])
        
        if not concerns and not risks:
            logger.info("No validation concerns to address")
            return
            
        # Add section for addressing concerns
        specifications["validation_concerns_addressed"] = []
        
        # Address each concern
        for concern in concerns + risks:
            concern_lower = concern.lower()
            
            if "security" in concern_lower:
                if "security_specifications" in specifications:
                    security_specs = specifications["security_specifications"]
                    security_specs["additional_security_measures"] = [f"Addressing concern: {concern}"]
                    specifications["validation_concerns_addressed"].append(f"Security concern addressed: {concern}")
            elif "performance" in concern_lower:
                if "performance_specifications" in specifications:
                    perf_specs = specifications["performance_specifications"]
                    perf_specs.setdefault("optimizations", []).append(f"Addressing concern: {concern}")
                    specifications["validation_concerns_addressed"].append(f"Performance concern addressed: {concern}")
            elif "requirement" in concern_lower:
                specifications["validation_concerns_addressed"].append(f"Requirement concern noted: {concern}")
            else:
                specifications["validation_concerns_addressed"].append(f"General concern noted: {concern}")
                
        logger.info(f"Addressed {len(concerns) + len(risks)} validation concerns")
        
    except Exception as e:
        logger.error(f"Error addressing validation concerns: {str(e)}", exc_info=True)

@trace_method
def generate_basic_specifications(
    architecture_design: Dict[str, Any],
    tech_stack: Dict[str, List[Dict[str, Any]]],
    validation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate basic specifications when LLM generation fails.
    
    Args:
        architecture_design: System architecture design
        tech_stack: Selected technology stack
        validation_results: Validation results
        
    Returns:
        Dict[str, Any]: Basic specifications
    """
    logger.info("Generating basic specifications")
    
    try:
        # Generate each specification section
        component_specs = generate_component_specs(architecture_design)
        api_specs = generate_api_specs(architecture_design)
        database_specs = generate_database_specs(architecture_design, tech_stack)
        security_specs = generate_security_specs(architecture_design, validation_results)
        integration_specs = generate_integration_specs(architecture_design)
        performance_specs = generate_performance_specs(validation_results)
        deployment_specs = generate_deployment_specs(architecture_design, tech_stack)
        
        # Combine into complete specifications
        specifications = {
            "component_specifications": component_specs,
            "api_specifications": api_specs,
            "database_specifications": database_specs,
            "security_specifications": security_specs,
            "integration_specifications": integration_specs,
            "performance_specifications": performance_specs,
            "deployment_specifications": deployment_specs
        }
        
        # Address any validation concerns
        address_validation_concerns(specifications, validation_results)
        
        logger.info("Basic specifications generation completed")
        return specifications
        
    except Exception as e:
        logger.error(f"Error generating basic specifications: {str(e)}", exc_info=True)
        return {
            "component_specifications": [],
            "api_specifications": [],
            "database_specifications": [],
            "security_specifications": {},
            "integration_specifications": [],
            "performance_specifications": {},
            "deployment_specifications": {}
        }