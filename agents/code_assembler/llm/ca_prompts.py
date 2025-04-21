from typing import Dict, List, Any, Optional
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("code_assembler.llm.prompts")

@trace_method
def format_component_analysis_prompt(
    components: Dict[str, Any],
    project_type: str,
    project_description: str
) -> str:
    """
    Format prompt for analyzing components and their relationships.
    
    Args:
        components: Dictionary of collected components
        project_type: Type of project being assembled
        project_description: Description of the project
        
    Returns:
        str: Formatted prompt for component analysis
    """
    logger.debug("Formatting component analysis prompt")
    
    try:
        # Format component list for readability
        components_text = ""
        for component_id, component in components.items():
            component_name = component.get("name", component_id)
            component_type = component.get("type", "unknown")
            source_agent = component.get("source_agent", "unknown")
            
            # Extract a preview of the content
            content_preview = str(component.get("content", ""))[:300]
            if len(content_preview) == 300:
                content_preview += "..."
            
            components_text += f"Component ID: {component_id}\n"
            components_text += f"Name: {component_name}\n"
            components_text += f"Type: {component_type}\n"
            components_text += f"Source Agent: {source_agent}\n"
            components_text += f"Content Preview: {content_preview}\n\n"
        
        prompt = f"""
        As a Code Assembler AI, analyze the following components to determine their relationships, dependencies, and optimal organization:

        PROJECT DESCRIPTION:
        {project_description}

        PROJECT TYPE:
        {project_type}

        COMPONENTS:
        {components_text}

        I need you to:
        1. Identify dependencies between components (imports, references, inheritance, etc.)
        2. Determine the logical organization of components into a cohesive project structure
        3. Identify any missing components that would be needed for a complete project
        4. Recommend a file naming and organization scheme that follows best practices for this project type

        Format your response as a JSON object with:
        {{
            "component_dependencies": [
                {{
                    "source_component": "component_id",
                    "target_component": "component_id",
                    "dependency_type": "import/reference/inheritance/etc.",
                    "details": "Description of the dependency"
                }}
            ],
            "file_organization": {{
                "root_directory": "name",
                "directory_structure": [
                    {{
                        "path": "path/from/root",
                        "purpose": "What this directory is for",
                        "components": ["component_ids", "that", "belong", "here"]
                    }}
                ]
            }},
            "missing_components": [
                {{
                    "name": "Name of missing component",
                    "purpose": "What this component would do",
                    "related_to": ["existing_component_ids"]
                }}
            ],
            "build_order": ["component_id1", "component_id2", "etc."]
        }}
        """
        
        logger.debug("Component analysis prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting component analysis prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, analyze the following project with {len(components)} components.
        
        Project Type: {project_type}
        
        Identify dependencies between components and determine the optimal organization.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_structure_planning_prompt(
    dependency_analysis: Dict[str, Any],
    components: Dict[str, Any],
    project_type: str
) -> str:
    """
    Format prompt for planning project structure based on dependency analysis.
    
    Args:
        dependency_analysis: Result of component dependency analysis
        components: Dictionary of collected components
        project_type: Type of project being assembled
        
    Returns:
        str: Formatted prompt for structure planning
    """
    logger.debug("Formatting structure planning prompt")
    
    try:
        # Format dependency information
        dependencies_text = ""
        for dep in dependency_analysis.get("component_dependencies", []):
            source = dep.get("source_component", "unknown")
            target = dep.get("target_component", "unknown")
            dep_type = dep.get("dependency_type", "unknown")
            
            dependencies_text += f"- {source} depends on {target} ({dep_type})\n"
            
        # Format missing components information
        missing_text = ""
        for missing in dependency_analysis.get("missing_components", []):
            name = missing.get("name", "unknown")
            purpose = missing.get("purpose", "")
            related_to = ", ".join(missing.get("related_to", []))
            
            missing_text += f"- {name}: {purpose} (Related to: {related_to})\n"
        
        # Format build order
        build_order = ", ".join(dependency_analysis.get("build_order", []))
        
        prompt = f"""
        As a Code Assembler AI, create a detailed project structure plan based on the following dependency analysis:

        PROJECT TYPE:
        {project_type}

        COMPONENT DEPENDENCIES:
        {dependencies_text}

        MISSING COMPONENTS:
        {missing_text}

        BUILD ORDER:
        {build_order}

        I need you to:
        1. Design a detailed file and directory structure for this project
        2. Map components to specific file paths
        3. Specify naming conventions and file organization principles
        4. Recommend approaches for handling missing components
        5. Ensure the structure follows best practices for this project type ({project_type})

        Format your response as a JSON object with:
        {{
            "directory_structure": {{
                "root_directory": "name",
                "directories": [
                    {{
                        "path": "path/from/root",
                        "purpose": "Description of directory purpose",
                        "subdirectories": ["sub1", "sub2"]
                    }}
                ]
            }},
            "file_mappings": [
                {{
                    "component_id": "id",
                    "file_path": "path/from/root/file.ext",
                    "naming_justification": "Why this name and location"
                }}
            ],
            "organization_principles": [
                "Principle 1: Explanation",
                "Principle 2: Explanation"
            ],
            "missing_component_strategy": [
                {{
                    "missing_component": "name",
                    "recommendation": "How to handle this missing component"
                }}
            ],
            "configuration_files": [
                {{
                    "file_path": "path/from/root/config.ext",
                    "purpose": "Purpose of this configuration file",
                    "required": true/false
                }}
            ]
        }}
        """
        
        logger.debug("Structure planning prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting structure planning prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, create a detailed project structure plan for a {project_type} project
        based on the dependency analysis provided. Design a file and directory structure following best practices.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_integration_planning_prompt(
    file_structure: Dict[str, Any],
    validation_results: Dict[str, Any],
    components: Dict[str, Any]
) -> str:
    """
    Format prompt for planning component integration.
    
    Args:
        file_structure: Planned file and directory structure
        validation_results: Results of structure validation
        components: Dictionary of collected components
        
    Returns:
        str: Formatted prompt for integration planning
    """
    logger.debug("Formatting integration planning prompt")
    
    try:
        # Format validation results
        validation_text = ""
        if validation_results.get("has_errors", False):
            error_count = validation_results.get("error_count", 0)
            warning_count = validation_results.get("warning_count", 0)
            
            validation_text += f"Validation found {error_count} errors and {warning_count} warnings.\n\n"
            
            # Format specific issues
            issues = validation_results.get("issues_by_category", {})
            for category, category_issues in issues.items():
                if category_issues:
                    validation_text += f"{category.replace('_', ' ').title()} Issues:\n"
                    for issue in category_issues[:5]:  # Limit to 5 issues per category
                        level = issue.get("level", "").upper()
                        message = issue.get("message", "")
                        validation_text += f"- [{level}] {message}\n"
                    
                    if len(category_issues) > 5:
                        validation_text += f"  (and {len(category_issues) - 5} more...)\n"
                    
                    validation_text += "\n"
        else:
            validation_text = "No significant validation issues found."
        
        # Format file mappings
        file_mappings_text = ""
        for mapping in file_structure.get("file_mappings", []):
            component_id = mapping.get("component_id", "")
            file_path = mapping.get("file_path", "")
            
            file_mappings_text += f"- {component_id} → {file_path}\n"
        
        prompt = f"""
        As a Code Assembler AI, create an integration plan for combining components into a cohesive project.

        FILE STRUCTURE:
        {file_mappings_text}

        VALIDATION RESULTS:
        {validation_text}

        I need you to:
        1. Create a plan for integrating components that addresses any validation issues
        2. Identify conflicts between components and propose resolutions
        3. Specify adjustments needed to make components work together
        4. Plan for handling import path updates and dependency management
        5. Define steps to ensure component interfaces are compatible

        Format your response as a JSON object with:
        {{
            "integration_strategies": [
                {{
                    "component_id": "id",
                    "adjustments": [
                        "Adjustment description",
                        "Another adjustment"
                    ],
                    "justification": "Why these adjustments are needed"
                }}
            ],
            "conflict_resolutions": [
                {{
                    "conflicting_components": ["component_id1", "component_id2"],
                    "conflict_type": "Type of conflict",
                    "resolution": "How to resolve this conflict"
                }}
            ],
            "import_path_updates": [
                {{
                    "component_id": "id",
                    "original_import": "original/path",
                    "updated_import": "new/path"
                }}
            ],
            "integration_sequence": [
                {{
                    "step": "Step description",
                    "components": ["component_ids", "involved"],
                    "dependencies": ["prior", "steps"]
                }}
            ],
            "post_integration_checks": [
                "Check description",
                "Another check"
            ]
        }}
        """
        
        logger.debug("Integration planning prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting integration planning prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, create an integration plan for combining components into a cohesive project.
        
        Address any validation issues, identify conflicts, and propose resolutions.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_config_generation_prompt(
    file_structure: Dict[str, Any],
    components: Dict[str, Any],
    project_type: str,
    dependency_analysis: Dict[str, Any]
) -> str:
    """
    Format prompt for generating configuration files.
    
    Args:
        file_structure: Planned file and directory structure
        components: Dictionary of collected components
        project_type: Type of project being assembled
        dependency_analysis: Result of component dependency analysis
        
    Returns:
        str: Formatted prompt for configuration generation
    """
    logger.debug("Formatting config generation prompt")
    
    try:
        # Determine technologies used in project
        technologies = []
        for component in components.values():
            if "technology" in component:
                technologies.append(component["technology"])
            elif "type" in component:
                tech_type = component["type"].lower()
                if "react" in tech_type or "jsx" in tech_type:
                    technologies.append("React")
                elif "vue" in tech_type:
                    technologies.append("Vue")
                elif "angular" in tech_type:
                    technologies.append("Angular")
                elif "python" in tech_type:
                    technologies.append("Python")
                elif "node" in tech_type or "express" in tech_type:
                    technologies.append("Node.js")
                elif "database" in tech_type or "sql" in tech_type:
                    technologies.append("Database")
        
        # Remove duplicates
        technologies = list(set(technologies))
        
        # Format directory structure
        directory_structure = ""
        for directory in file_structure.get("directory_structure", {}).get("directories", []):
            path = directory.get("path", "")
            purpose = directory.get("purpose", "")
            
            directory_structure += f"- {path}: {purpose}\n"
        
        prompt = f"""
        As a Code Assembler AI, generate the necessary configuration files for this project.

        PROJECT TYPE:
        {project_type}

        TECHNOLOGIES USED:
        {', '.join(technologies)}

        DIRECTORY STRUCTURE:
        {directory_structure}

        I need you to:
        1. Identify all necessary configuration files for this project type and technology stack
        2. Generate the content for each configuration file with appropriate settings
        3. Ensure compatibility between different configuration files
        4. Include appropriate documentation and comments
        5. Follow best practices for each configuration file type

        Format your response as a JSON object with:
        {{
            "configuration_files": [
                {{
                    "file_path": "path/to/config/file",
                    "file_content": "Complete content of the file",
                    "purpose": "Purpose of this configuration file",
                    "dependencies": ["other", "config", "files"]
                }}
            ],
            "environment_variables": [
                {{
                    "variable": "VARIABLE_NAME",
                    "default_value": "default",
                    "description": "What this variable is used for",
                    "required": true/false
                }}
            ],
            "build_configuration": {{
                "build_tool": "Tool name",
                "build_command": "Command to build project",
                "build_output": "Output directory"
            }},
            "deployment_recommendations": [
                "Recommendation description",
                "Another recommendation"
            ]
        }}
        """
        
        logger.debug("Config generation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting config generation prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, generate the necessary configuration files for this {project_type} project.
        
        Identify all required configuration files and generate their content with appropriate settings.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_project_compilation_prompt(
    file_structure: Dict[str, Any],
    integration_plan: Dict[str, Any],
    config_files: Dict[str, Any],
    validation_results: Dict[str, Any]
) -> str:
    """
    Format prompt for compiling the final project.
    
    Args:
        file_structure: Planned file and directory structure
        integration_plan: Plan for integrating components
        config_files: Generated configuration files
        validation_results: Results of structure validation
        
    Returns:
        str: Formatted prompt for project compilation
    """
    logger.debug("Formatting project compilation prompt")
    
    try:
        # Format config files
        config_files_text = ""
        for config_file in config_files.get("configuration_files", []):
            file_path = config_file.get("file_path", "")
            purpose = config_file.get("purpose", "")
            
            config_files_text += f"- {file_path}: {purpose}\n"
        
        # Format integration strategy
        integration_text = ""
        for strategy in integration_plan.get("integration_strategies", []):
            component_id = strategy.get("component_id", "")
            adjustments = strategy.get("adjustments", [])
            
            integration_text += f"Component {component_id}:\n"
            for adj in adjustments:
                integration_text += f"  - {adj}\n"
        
        prompt = f"""
        As a Code Assembler AI, compile the final project based on the following information:

        FILE STRUCTURE:
        {file_structure.get("directory_structure", {}).get("root_directory", "unknown")} (root)
        With {len(file_structure.get("file_mappings", []))} file mappings

        CONFIGURATION FILES:
        {config_files_text}

        INTEGRATION PLAN:
        {integration_text}

        I need you to:
        1. Create a detailed compilation plan for assembling the complete project
        2. Define the final output structure including all files and directories
        3. Specify any adjustments needed to components during compilation
        4. Create a comprehensive validation checklist for the compiled project
        5. Provide documentation for the compiled project

        Format your response as a JSON object with:
        {{
            "compilation_plan": [
                {{
                    "step": "Step description",
                    "components_involved": ["component_ids"],
                    "actions": ["Action description"]
                }}
            ],
            "output_structure": {{
                "root_directory": "name",
                "directories": ["dir1", "dir2"],
                "primary_files": ["file1", "file2"]
            }},
            "component_adjustments": [
                {{
                    "component_id": "id",
                    "adjustments": ["Adjustment description"]
                }}
            ],
            "validation_checklist": [
                "Check description",
                "Another check"
            ],
            "documentation": [
                {{
                    "file_path": "path/to/doc/file",
                    "content_summary": "What this document will contain",
                    "primary_audience": "Who this documentation is for"
                }}
            ]
        }}
        """
        
        logger.debug("Project compilation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting project compilation prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, compile the final project based on the provided information.
        
        Create a detailed compilation plan with steps to assemble the complete project.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_conflict_resolution_prompt(
    conflict: Dict[str, Any],
    components: Dict[str, Any],
    project_type: str
) -> str:
    """
    Format prompt for resolving conflicts between components.
    
    Args:
        conflict: Information about the conflict
        components: Dictionary of collected components
        project_type: Type of project being assembled
        
    Returns:
        str: Formatted prompt for conflict resolution
    """
    logger.debug("Formatting conflict resolution prompt")
    
    try:
        # Extract conflicting components
        conflicting_ids = conflict.get("conflicting_components", [])
        conflict_type = conflict.get("conflict_type", "unknown")
        
        conflict_components_text = ""
        for comp_id in conflicting_ids:
            component = components.get(comp_id, {})
            name = component.get("name", comp_id)
            content = str(component.get("content", ""))[:500]  # Limit content length
            if len(content) == 500:
                content += "..."
            
            conflict_components_text += f"Component ID: {comp_id}\n"
            conflict_components_text += f"Name: {name}\n"
            conflict_components_text += f"Content:\n{content}\n\n"
        
        prompt = f"""
        As a Code Assembler AI, resolve the following conflict between components:

        CONFLICT TYPE:
        {conflict_type}

        PROJECT TYPE:
        {project_type}

        CONFLICTING COMPONENTS:
        {conflict_components_text}

        I need you to:
        1. Analyze the specific conflict between these components
        2. Propose multiple resolution strategies
        3. Recommend the best approach for resolving the conflict
        4. Provide the modified code or structure needed to implement the resolution
        5. Explain any trade-offs in your chosen resolution

        Format your response as a JSON object with:
        {{
            "conflict_analysis": "Detailed analysis of the conflict",
            "resolution_strategies": [
                {{
                    "approach": "Strategy name",
                    "description": "How this strategy works",
                    "pros": ["Pro 1", "Pro 2"],
                    "cons": ["Con 1", "Con 2"]
                }}
            ],
            "recommended_strategy": "Name of recommended strategy",
            "implementation": {{
                "modified_components": [
                    {{
                        "component_id": "id",
                        "original_content": "Relevant part of original content",
                        "modified_content": "Modified content with conflict resolved",
                        "explanation": "Explanation of the changes"
                    }}
                ],
                "new_components": [
                    {{
                        "name": "New component name",
                        "content": "Content for the new component",
                        "purpose": "Why this new component is needed"
                    }}
                ]
            }},
            "trade_offs": "Explanation of trade-offs in the chosen resolution"
        }}
        """
        
        logger.debug("Conflict resolution prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting conflict resolution prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, resolve the conflict between the provided components.
        
        Analyze the conflict, propose resolution strategies, and recommend the best approach.
        
        Format your response as a structured JSON object.
        """

@trace_method
def format_documentation_generation_prompt(
    components: Dict[str, Any],
    project_type: str,
    file_structure: Dict[str, Any],
    project_description: str
) -> str:
    """
    Format prompt for generating project documentation.
    
    Args:
        components: Dictionary of collected components
        project_type: Type of project being assembled
        file_structure: Planned file and directory structure
        project_description: Description of the project
        
    Returns:
        str: Formatted prompt for documentation generation
    """
    logger.debug("Formatting documentation generation prompt")
    
    try:
        # Format file structure
        file_structure_text = ""
        for mapping in file_structure.get("file_mappings", [])[:10]:  # Limit to 10 entries
            component_id = mapping.get("component_id", "")
            file_path = mapping.get("file_path", "")
            
            file_structure_text += f"- {file_path}: (Component {component_id})\n"
            
        if len(file_structure.get("file_mappings", [])) > 10:
            file_structure_text += f"(and {len(file_structure.get('file_mappings', [])) - 10} more...)\n"
        
        prompt = f"""
        As a Code Assembler AI, generate comprehensive documentation for this project:

        PROJECT DESCRIPTION:
        {project_description}

        PROJECT TYPE:
        {project_type}

        FILE STRUCTURE:
        {file_structure_text}

        I need you to:
        1. Create a complete README file explaining the project
        2. Generate setup instructions with installation and configuration steps
        3. Create usage documentation with examples
        4. Document the architecture and component relationships
        5. Provide API documentation if applicable
        6. Create any additional documentation files needed for this project type

        Format your response as a JSON object with:
        {{
            "readme": "Complete content for README.md",
            "setup_guide": "Complete content for SETUP.md or installation section",
            "usage_documentation": "Complete content for usage documentation",
            "architecture_documentation": "Content explaining the project architecture",
            "api_documentation": "API documentation if applicable",
            "additional_documentation": [
                {{
                    "file_name": "filename.md",
                    "content": "Complete content for this documentation file",
                    "purpose": "Purpose of this documentation"
                }}
            ]
        }}
        """
        
        logger.debug("Documentation generation prompt formatted successfully")
        return prompt
        
    except Exception as e:
        logger.error(f"Error formatting documentation generation prompt: {str(e)}", exc_info=True)
        return f"""
        As a Code Assembler AI, generate comprehensive documentation for this {project_type} project.
        
        Create a README file, setup instructions, usage documentation, and architecture documentation.
        
        Format your response as a structured JSON object.
        """