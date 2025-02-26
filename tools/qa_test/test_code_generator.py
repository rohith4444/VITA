from typing import Dict, List, Any, Optional
import re
from core.logging.logger import setup_logger
from core.tracing.service import trace_method
from agents.qa_test.llm.service import QATestLLMService

# Initialize logger
logger = setup_logger("tools.qa_test.test_code_generator")

@trace_method
async def generate_test_code(
    test_cases: Dict[str, Any],
    code: Dict[str, Any],
    programming_language: str = None,
    test_framework: str = None,
    llm_service: QATestLLMService = None
) -> Dict[str, str]:
    """
    Generate executable test code from test case specifications using LLM.
    
    Args:
        test_cases: Test case specifications
        code: Code to be tested
        programming_language: Target programming language for tests (auto-detected if None)
        test_framework: Testing framework to use (auto-selected if None)
        llm_service: QA-specific LLM service
        
    Returns:
        Dict[str, str]: Dictionary of test files with generated code
        
    Raises:
        ValueError: If language or framework detection fails
        RuntimeError: If code generation fails
    """
    logger.info("Starting test code generation")
    
    # Validate required parameters
    if not test_cases:
        raise ValueError("Test cases are required for test code generation")
    
    if not code:
        raise ValueError("Code is required for test code generation")
    
    if not llm_service:
        raise ValueError("LLM service is required for test code generation")
    
    try:
        # Detect programming language if not provided
        if not programming_language:
            programming_language = detect_programming_language(code)
            logger.info(f"Detected programming language: {programming_language}")
        
        # Recommend test framework if not provided
        if not test_framework:
            test_framework = recommend_test_framework(programming_language, code)
            logger.info(f"Recommended test framework: {test_framework}")
        
        # Analyze code structure to extract metadata
        code_metadata = analyze_code_structure(code, programming_language)
        logger.debug(f"Extracted code metadata for {len(code_metadata['components'])} components")
        
        # Generate test code using LLM
        test_code = await generate_code_with_llm(
            test_cases=test_cases,
            code=code,
            code_metadata=code_metadata,
            language=programming_language,
            framework=test_framework,
            llm_service=llm_service
        )
        
        logger.info(f"Successfully generated {len(test_code)} test files")
        return test_code
        
    except Exception as e:
        logger.error(f"Error generating test code: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to generate test code: {str(e)}")

@trace_method
def detect_programming_language(code: Dict[str, Any]) -> str:
    """
    Analyze code to determine the primary programming language.
    
    Args:
        code: Code components to analyze
        
    Returns:
        str: Detected programming language ("javascript", "python", "java", etc.)
        
    Raises:
        ValueError: If language cannot be confidently detected
    """
    logger.debug("Detecting programming language")
    
    # Language detection patterns
    language_patterns = {
        "javascript": [
            r"function\s+\w+\s*\(", 
            r"const\s+\w+\s*=", 
            r"let\s+\w+\s*=",
            r"class\s+\w+\s*\{",
            r"export\s+default",
            r"module\.exports",
            r"import\s+.*\s+from"
        ],
        "typescript": [
            r"interface\s+\w+\s*\{",
            r"type\s+\w+\s*=",
            r"export\s+interface",
            r"import\s+\{\s*\w+\s*\}\s+from"
        ],
        "python": [
            r"def\s+\w+\s*\(",
            r"class\s+\w+\s*:",
            r"import\s+\w+",
            r"from\s+\w+\s+import",
            r"if\s+__name__\s*==\s*['\"]__main__['\"]"
        ],
        "java": [
            r"public\s+class",
            r"private\s+\w+\s+\w+\s*\(",
            r"protected\s+\w+\s+\w+\s*\(",
            r"import\s+java\."
        ]
    }
    
    # Count pattern matches for each language
    language_scores = {lang: 0 for lang in language_patterns}
    
    for component_name, component_code in code.items():
        # Extract code content if it's in a container
        if isinstance(component_code, dict) and "content" in component_code:
            component_code = component_code["content"]
        
        # Skip if not a string
        if not isinstance(component_code, str):
            continue
        
        # Check patterns for each language
        for language, patterns in language_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, component_code)
                language_scores[language] += len(matches)
    
    # Find language with highest score
    max_score = 0
    detected_language = None
    
    for language, score in language_scores.items():
        if score > max_score:
            max_score = score
            detected_language = language
    
    # Special case for TypeScript (is often similar to JavaScript)
    if detected_language == "javascript" and language_scores["typescript"] > 0:
        detected_language = "typescript"
    
    if not detected_language or max_score < 3:
        # Default to JavaScript if detection confidence is low
        logger.warning("Could not confidently detect language, defaulting to JavaScript")
        return "javascript"
    
    logger.info(f"Detected programming language: {detected_language}")
    return detected_language

@trace_method
def recommend_test_framework(language: str, code: Dict[str, Any]) -> str:
    """
    Recommend the best testing framework for the language and codebase.
    
    Args:
        language: Detected programming language
        code: Code components
        
    Returns:
        str: Recommended test framework
    """
    logger.debug(f"Recommending test framework for {language}")
    
    # Default frameworks by language
    default_frameworks = {
        "javascript": "jest",
        "typescript": "jest",
        "python": "pytest",
        "java": "junit"
    }
    
    # Framework detection patterns
    framework_patterns = {
        "jest": [r"jest", r"test\(", r"describe\(", r"it\(", r"expect\("],
        "mocha": [r"mocha", r"describe\(", r"it\(", r"chai"],
        "pytest": [r"pytest", r"@pytest", r"test_", r"assert"],
        "unittest": [r"unittest", r"TestCase", r"setUp", r"tearDown"],
        "junit": [r"JUnit", r"@Test", r"assertEquals", r"assertThat"]
    }
    
    # Count framework references in code
    framework_scores = {framework: 0 for framework in framework_patterns}
    
    for component_name, component_code in code.items():
        # Extract code content if it's in a container
        if isinstance(component_code, dict) and "content" in component_code:
            component_code = component_code["content"]
        
        # Skip if not a string
        if not isinstance(component_code, str):
            continue
        
        # Check patterns for each framework
        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, component_code, re.IGNORECASE)
                framework_scores[framework] += len(matches)
    
    # Find compatible frameworks for the language
    compatible_frameworks = []
    
    if language in ["javascript", "typescript"]:
        compatible_frameworks = ["jest", "mocha"]
    elif language == "python":
        compatible_frameworks = ["pytest", "unittest"]
    elif language == "java":
        compatible_frameworks = ["junit"]
    
    # Find highest scoring compatible framework
    max_score = -1
    recommended_framework = None
    
    for framework in compatible_frameworks:
        if framework_scores[framework] > max_score:
            max_score = framework_scores[framework]
            recommended_framework = framework
    
    # Use default if no framework detected
    if not recommended_framework or max_score == 0:
        recommended_framework = default_frameworks.get(language, "jest")
        logger.debug(f"No specific framework detected, using default: {recommended_framework}")
    else:
        logger.debug(f"Recommended framework based on code analysis: {recommended_framework}")
    
    return recommended_framework

@trace_method
def analyze_code_structure(code: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Extract component structure, methods, params, and dependencies.
    
    Args:
        code: Code components
        language: Programming language
        
    Returns:
        Dict[str, Any]: Code metadata including components, methods, and dependencies
    """
    logger.debug(f"Analyzing code structure for {len(code)} components")
    
    metadata = {
        "language": language,
        "components": {},
        "dependencies": {}
    }
    
    for component_name, component_code in code.items():
        # Extract code content if it's in a container
        if isinstance(component_code, dict) and "content" in component_code:
            component_code = component_code["content"]
        
        # Skip if not a string
        if not isinstance(component_code, str):
            continue
        
        # Extract component metadata based on language
        if language in ["javascript", "typescript"]:
            component_metadata = extract_js_component_metadata(component_name, component_code)
        elif language == "python":
            component_metadata = extract_python_component_metadata(component_name, component_code)
        else:
            # Default extraction for unsupported languages
            component_metadata = {
                "name": component_name,
                "methods": [],
                "dependencies": []
            }
        
        metadata["components"][component_name] = component_metadata
        
        # Track dependencies
        for dependency in component_metadata.get("dependencies", []):
            if dependency not in metadata["dependencies"]:
                metadata["dependencies"][dependency] = []
            
            metadata["dependencies"][dependency].append(component_name)
    
    logger.debug(f"Completed code structure analysis for {len(metadata['components'])} components")
    return metadata

@trace_method
def extract_js_component_metadata(component_name: str, component_code: str) -> Dict[str, Any]:
    """
    Extract metadata from JavaScript/TypeScript component.
    
    Args:
        component_name: Name of the component
        component_code: Component source code
        
    Returns:
        Dict[str, Any]: Component metadata
    """
    metadata = {
        "name": component_name,
        "methods": [],
        "dependencies": []
    }
    
    # Extract class definition
    class_match = re.search(r"class\s+(\w+)", component_code)
    if class_match:
        metadata["class_name"] = class_match.group(1)
    
    # Extract constructor and dependencies
    constructor_match = re.search(r"constructor\s*\(([^)]*)\)", component_code)
    if constructor_match:
        params = constructor_match.group(1).split(',')
        dependencies = [param.strip() for param in params if param.strip()]
        metadata["dependencies"] = dependencies
    
    # Extract methods
    method_matches = re.finditer(r"(?:async\s+)?(?:function\s+)?(\w+)\s*\(([^)]*)\)", component_code)
    for match in method_matches:
        method_name = match.group(1)
        params = [param.strip() for param in match.group(2).split(',') if param.strip()]
        
        # Skip constructor and private methods
        if method_name == "constructor" or method_name.startswith("_"):
            continue
        
        metadata["methods"].append({
            "name": method_name,
            "params": params,
            "is_async": "async" in match.group(0)
        })
    
    return metadata

@trace_method
def extract_python_component_metadata(component_name: str, component_code: str) -> Dict[str, Any]:
    """
    Extract metadata from Python component.
    
    Args:
        component_name: Name of the component
        component_code: Component source code
        
    Returns:
        Dict[str, Any]: Component metadata
    """
    metadata = {
        "name": component_name,
        "methods": [],
        "dependencies": []
    }
    
    # Extract class definition
    class_match = re.search(r"class\s+(\w+)", component_code)
    if class_match:
        metadata["class_name"] = class_match.group(1)
    
    # Extract initialization and dependencies
    init_match = re.search(r"def\s+__init__\s*\(self,\s*([^)]*)\)", component_code)
    if init_match:
        params = init_match.group(1).split(',')
        dependencies = [param.strip() for param in params if param.strip()]
        metadata["dependencies"] = dependencies
    
    # Extract methods
    method_matches = re.finditer(r"def\s+(\w+)\s*\(self(?:,\s*([^)]*))?\)", component_code)
    for match in method_matches:
        method_name = match.group(1)
        params_str = match.group(2) or ""
        params = [param.strip() for param in params_str.split(',') if param.strip()]
        
        # Skip init and private methods
        if method_name == "__init__" or method_name.startswith("_"):
            continue
        
        # Check if method is async
        method_content = component_code[match.start():]
        method_content = method_content[:method_content.find('\n    def ')] if '\n    def ' in method_content else method_content
        is_async = "async" in component_code[max(0, match.start()-10):match.start()] or "await" in method_content
        
        metadata["methods"].append({
            "name": method_name,
            "params": params,
            "is_async": is_async
        })
    
    return metadata

@trace_method
async def generate_code_with_llm(
    test_cases: Dict[str, Any],
    code: Dict[str, Any],
    code_metadata: Dict[str, Any],
    language: str,
    framework: str,
    llm_service: QATestLLMService
) -> Dict[str, str]:
    """
    Use LLM to generate test code based on test cases and code structure.
    
    Args:
        test_cases: Test case specifications
        code: Original code to be tested
        code_metadata: Extracted code structure
        language: Programming language
        framework: Testing framework
        llm_service: QA-specific LLM service
        
    Returns:
        Dict[str, str]: Dictionary of test files with generated code
        
    Raises:
        RuntimeError: If LLM fails to generate valid test code
    """
    logger.info(f"Generating test code using LLM for {language}/{framework}")
    
    try:
        # Call LLM service to generate test code
        test_code_files = await llm_service.generate_test_code(
            test_cases=test_cases,
            code=code,
            programming_language=language,
            test_framework=framework
        )
        
        if not test_code_files:
            raise RuntimeError("LLM returned empty test code")
        
        logger.info(f"LLM successfully generated {len(test_code_files)} test files")
        return test_code_files
        
    except Exception as e:
        logger.error(f"LLM test code generation failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to generate test code: {str(e)}")