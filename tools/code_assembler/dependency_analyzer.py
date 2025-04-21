from typing import Dict, List, Any, Optional, Set, Tuple
import re
import os
import json
from pathlib import Path
from enum import Enum
from collections import defaultdict
import networkx as nx
from core.logging.logger import setup_logger
from core.tracing.service import trace_method

# Initialize logger
logger = setup_logger("tools.code_assembler.dependency_analyzer")

class DependencyType(Enum):
    """Enum representing types of dependencies between components."""
    IMPORT = "import"           # Direct import dependency
    REFERENCE = "reference"     # Reference to another component
    INHERITANCE = "inheritance" # Class inheritance relationship
    USAGE = "usage"             # Usage of another component's function/method
    UNKNOWN = "unknown"         # Unknown dependency type

class Dependency:
    """Class representing a dependency between components."""
    
    def __init__(
        self,
        source: str,
        target: str,
        dependency_type: DependencyType = DependencyType.UNKNOWN,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a dependency.
        
        Args:
            source: Source component identifier
            target: Target component identifier
            dependency_type: Type of dependency
            details: Additional details about the dependency
        """
        self.source = source
        self.target = target
        self.dependency_type = dependency_type
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"{self.source} -> {self.target} ({self.dependency_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()

class DependencyGraph:
    """Class representing a graph of dependencies between components."""
    
    def __init__(self):
        """Initialize a dependency graph."""
        self.graph = nx.DiGraph()
        self.components = set()
        self.dependencies: List[Dependency] = []
    
    def add_component(self, component_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a component to the graph.
        
        Args:
            component_id: Identifier for the component
            metadata: Additional metadata about the component
        """
        self.components.add(component_id)
        self.graph.add_node(component_id, metadata=metadata or {})
    
    def add_dependency(self, dependency: Dependency) -> None:
        """
        Add a dependency to the graph.
        
        Args:
            dependency: Dependency to add
        """
        # Add components if they don't exist
        if dependency.source not in self.components:
            self.add_component(dependency.source)
        if dependency.target not in self.components:
            self.add_component(dependency.target)
        
        # Add the dependency as an edge
        self.graph.add_edge(
            dependency.source, 
            dependency.target, 
            type=dependency.dependency_type.value,
            details=dependency.details
        )
        
        self.dependencies.append(dependency)
    
    def get_dependencies(self, component_id: str) -> List[Dependency]:
        """
        Get all dependencies where the given component is the source.
        
        Args:
            component_id: Identifier for the component
            
        Returns:
            List[Dependency]: List of dependencies
        """
        dependencies = []
        
        if component_id in self.graph:
            for target in self.graph.successors(component_id):
                edge_data = self.graph.get_edge_data(component_id, target)
                dependency_type = DependencyType(edge_data.get('type', DependencyType.UNKNOWN.value))
                details = edge_data.get('details', {})
                
                dependencies.append(Dependency(
                    source=component_id,
                    target=target,
                    dependency_type=dependency_type,
                    details=details
                ))
        
        return dependencies
    
    def get_dependents(self, component_id: str) -> List[Dependency]:
        """
        Get all dependencies where the given component is the target.
        
        Args:
            component_id: Identifier for the component
            
        Returns:
            List[Dependency]: List of dependencies
        """
        dependencies = []
        
        if component_id in self.graph:
            for source in self.graph.predecessors(component_id):
                edge_data = self.graph.get_edge_data(source, component_id)
                dependency_type = DependencyType(edge_data.get('type', DependencyType.UNKNOWN.value))
                details = edge_data.get('details', {})
                
                dependencies.append(Dependency(
                    source=source,
                    target=component_id,
                    dependency_type=dependency_type,
                    details=details
                ))
        
        return dependencies
    
    def has_circular_dependencies(self) -> bool:
        """
        Check if the graph has any circular dependencies.
        
        Returns:
            bool: True if circular dependencies exist, False otherwise
        """
        try:
            nx.find_cycle(self.graph, orientation="original")
            return True
        except nx.NetworkXNoCycle:
            return False
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find all circular dependencies in the graph.
        
        Returns:
            List[List[str]]: List of cycles, where each cycle is a list of component IDs
        """
        cycles = []
        
        try:
            # Get all simple cycles
            simple_cycles = list(nx.simple_cycles(self.graph))
            for cycle in simple_cycles:
                # Append the first element to close the cycle for display
                closed_cycle = cycle + [cycle[0]]
                cycles.append(closed_cycle)
                
        except nx.NetworkXNoCycle:
            pass  # No cycles found
        
        return cycles
    
    def get_build_order(self) -> List[str]:
        """
        Calculate the build order based on dependencies.
        
        Returns:
            List[str]: Component IDs in build order
        """
        try:
            # Attempt topological sort
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            # If graph has cycles, fall back to a greedy approach
            logger.warning("Graph has cycles, using approximate build order")
            
            # Create a copy of the graph for modification
            temp_graph = self.graph.copy()
            
            # Find all cycles
            cycles = self.find_circular_dependencies()
            
            # Break cycles by temporarily removing edges
            for cycle in cycles:
                if len(cycle) > 1:  # Ensure it's actually a cycle
                    # Remove the last edge in the cycle
                    temp_graph.remove_edge(cycle[-2], cycle[-1])
            
            # Now we can do a topological sort
            return list(nx.topological_sort(temp_graph))

class DependencyAnalyzer:
    """Class for analyzing dependencies between code components."""
    
    def __init__(self):
        """Initialize a dependency analyzer."""
        self.dependency_graph = DependencyGraph()
        self.components: Dict[str, Dict[str, Any]] = {}
        self.file_paths: Dict[str, str] = {}
    
    @trace_method
    def register_component(self, component_id: str, file_path: str, content: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a component for dependency analysis.
        
        Args:
            component_id: Identifier for the component
            file_path: Path to the component file
            content: Content of the component
            metadata: Additional metadata about the component
        """
        logger.debug(f"Registering component: {component_id}")
        
        self.components[component_id] = {
            "file_path": file_path,
            "content": content,
            "metadata": metadata or {}
        }
        
        self.file_paths[file_path] = component_id
        self.dependency_graph.add_component(component_id, metadata)
    
    @trace_method
    def analyze_all_dependencies(self) -> DependencyGraph:
        """
        Analyze dependencies for all registered components.
        
        Returns:
            DependencyGraph: Graph of dependencies
        """
        logger.info(f"Analyzing dependencies for {len(self.components)} components")
        
        # Extract dependencies for each component
        for component_id, component_data in self.components.items():
            file_path = component_data["file_path"]
            content = component_data["content"]
            
            # Determine file type based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Extract dependencies based on file type
            dependencies = []
            
            if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                dependencies = self._extract_js_dependencies(component_id, content)
            elif file_ext == '.py':
                dependencies = self._extract_python_dependencies(component_id, content)
            elif file_ext in ['.java', '.kt']:
                dependencies = self._extract_java_dependencies(component_id, content)
            else:
                logger.debug(f"No specialized parser for {file_ext}, using generic approach")
                dependencies = self._extract_generic_dependencies(component_id, content)
            
            # Add dependencies to the graph
            for dependency in dependencies:
                self.dependency_graph.add_dependency(dependency)
        
        logger.info(f"Dependency analysis completed with {len(self.dependency_graph.dependencies)} dependencies")
        return self.dependency_graph
    
    def _extract_js_dependencies(self, component_id: str, content: str) -> List[Dependency]:
        """
        Extract dependencies from JavaScript/TypeScript code.
        
        Args:
            component_id: Identifier for the component
            content: Content of the component
            
        Returns:
            List[Dependency]: Extracted dependencies
        """
        logger.debug(f"Extracting JS dependencies for {component_id}")
        
        dependencies = []
        
        # Extract import statements
        # Match ES6 imports: import X from 'Y';, import { X } from 'Y';, etc.
        import_pattern = r"import\s+(?:{[^}]*}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]"
        
        # Match require statements: const X = require('Y');, require('Y');
        require_pattern = r"(?:const|let|var)\s+(?:{[^}]*}|\w+)\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]"
        
        # Find all imports
        for match in re.finditer(import_pattern, content):
            target_module = match.group(1)
            dependency = self._create_dependency_for_module(component_id, target_module, DependencyType.IMPORT)
            if dependency:
                dependencies.append(dependency)
        
        # Find all requires
        for match in re.finditer(require_pattern, content):
            target_module = match.group(1)
            dependency = self._create_dependency_for_module(component_id, target_module, DependencyType.IMPORT)
            if dependency:
                dependencies.append(dependency)
        
        # Find class inheritance (simple detection)
        # Match: class X extends Y
        inheritance_pattern = r"class\s+\w+\s+extends\s+(\w+)"
        
        for match in re.finditer(inheritance_pattern, content):
            target_class = match.group(1)
            # This is a naive approach - in a real system, we'd need to match this
            # with actual component IDs or imports
            for other_id, other_data in self.components.items():
                if other_id != component_id and target_class in other_data["content"]:
                    dependencies.append(Dependency(
                        source=component_id,
                        target=other_id,
                        dependency_type=DependencyType.INHERITANCE,
                        details={"class": target_class}
                    ))
        
        return dependencies
    
    def _extract_python_dependencies(self, component_id: str, content: str) -> List[Dependency]:
        """
        Extract dependencies from Python code.
        
        Args:
            component_id: Identifier for the component
            content: Content of the component
            
        Returns:
            List[Dependency]: Extracted dependencies
        """
        logger.debug(f"Extracting Python dependencies for {component_id}")
        
        dependencies = []
        
        # Extract import statements
        # Match: import X, from X import Y, import X as Y
        import_pattern = r"^\s*import\s+(\w+(?:\s*,\s*\w+)*)"
        from_import_pattern = r"^\s*from\s+([.\w]+)\s+import\s+"
        
        # Find all direct imports
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            modules = [m.strip() for m in match.group(1).split(',')]
            for module in modules:
                dependency = self._create_dependency_for_module(component_id, module, DependencyType.IMPORT)
                if dependency:
                    dependencies.append(dependency)
        
        # Find all from imports
        for match in re.finditer(from_import_pattern, content, re.MULTILINE):
            module = match.group(1)
            dependency = self._create_dependency_for_module(component_id, module, DependencyType.IMPORT)
            if dependency:
                dependencies.append(dependency)
        
        # Find class inheritance (simple detection)
        # Match: class X(Y): or class X(Y, Z):
        inheritance_pattern = r"class\s+\w+\s*\(([^)]+)\):"
        
        for match in re.finditer(inheritance_pattern, content):
            parent_classes = [p.strip() for p in match.group(1).split(',')]
            for parent in parent_classes:
                # Same naive approach as with JS
                for other_id, other_data in self.components.items():
                    if other_id != component_id and f"class {parent}" in other_data["content"]:
                        dependencies.append(Dependency(
                            source=component_id,
                            target=other_id,
                            dependency_type=DependencyType.INHERITANCE,
                            details={"class": parent}
                        ))
        
        return dependencies
    
    def _extract_java_dependencies(self, component_id: str, content: str) -> List[Dependency]:
        """
        Extract dependencies from Java code.
        
        Args:
            component_id: Identifier for the component
            content: Content of the component
            
        Returns:
            List[Dependency]: Extracted dependencies
        """
        logger.debug(f"Extracting Java dependencies for {component_id}")
        
        dependencies = []
        
        # Extract import statements
        # Match: import x.y.z; or import x.y.z.*;
        import_pattern = r"^\s*import\s+([^;]+);"
        
        # Find all imports
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            import_path = match.group(1).strip()
            dependency = self._create_dependency_for_module(component_id, import_path, DependencyType.IMPORT)
            if dependency:
                dependencies.append(dependency)
        
        # Find class inheritance (simple detection)
        # Match: class X extends Y or class X extends Y implements Z
        inheritance_pattern = r"class\s+\w+\s+extends\s+(\w+)"
        
        for match in re.finditer(inheritance_pattern, content):
            parent_class = match.group(1)
            # Naive approach again
            for other_id, other_data in self.components.items():
                if other_id != component_id and f"class {parent_class}" in other_data["content"]:
                    dependencies.append(Dependency(
                        source=component_id,
                        target=other_id,
                        dependency_type=DependencyType.INHERITANCE,
                        details={"class": parent_class}
                    ))
        
        return dependencies
    
    def _extract_generic_dependencies(self, component_id: str, content: str) -> List[Dependency]:
        """
        Extract dependencies using a generic approach.
        
        Args:
            component_id: Identifier for the component
            content: Content of the component
            
        Returns:
            List[Dependency]: Extracted dependencies
        """
        logger.debug(f"Using generic dependency extraction for {component_id}")
        
        dependencies = []
        
        # Look for references to other component IDs or file paths
        for other_id, other_data in self.components.items():
            if other_id != component_id:
                # Check if other component is referenced by ID
                if other_id in content:
                    dependencies.append(Dependency(
                        source=component_id,
                        target=other_id,
                        dependency_type=DependencyType.REFERENCE,
                        details={"type": "id_reference"}
                    ))
                
                # Check if other component's file path is referenced
                file_path = os.path.basename(other_data["file_path"])
                if file_path in content:
                    dependencies.append(Dependency(
                        source=component_id,
                        target=other_id,
                        dependency_type=DependencyType.REFERENCE,
                        details={"type": "path_reference"}
                    ))
        
        return dependencies
    
    def _create_dependency_for_module(
        self, 
        component_id: str, 
        module_name: str, 
        dependency_type: DependencyType
    ) -> Optional[Dependency]:
        """
        Create a dependency based on an imported module name.
        
        Args:
            component_id: Source component identifier
            module_name: Target module name
            dependency_type: Type of dependency
            
        Returns:
            Optional[Dependency]: Dependency if a matching component is found, None otherwise
        """
        # Clean up the module name
        module_name = module_name.strip()
        
        # Check for relative imports
        is_relative = module_name.startswith('.') or module_name.startswith('/')
        
        if is_relative:
            # Resolve relative import
            source_path = self.components[component_id]["file_path"]
            source_dir = os.path.dirname(source_path)
            
            # Remove leading ./ or / and replace with actual directory
            if module_name.startswith('./'):
                module_name = module_name[2:]
            elif module_name.startswith('/'):
                module_name = module_name[1:]
            
            # Resolve ../ in path
            if '../' in module_name:
                parts = source_dir.split(os.sep)
                module_parts = module_name.split('/')
                
                # Count and remove '../' segments
                up_count = 0
                while module_parts and module_parts[0] == '..':
                    up_count += 1
                    module_parts.pop(0)
                
                # Adjust source_dir
                if up_count > 0:
                    parts = parts[:-up_count]
                    source_dir = os.sep.join(parts)
                
                # Rebuild module_name
                module_name = '/'.join(module_parts)
            
            # Create potential target path
            target_path = os.path.join(source_dir, module_name)
            
            # Check extensions if no extension in module_name
            if '.' not in os.path.basename(module_name):
                # Check common extensions
                for ext in ['.js', '.jsx', '.ts', '.tsx', '.py', '.java']:
                    test_path = f"{target_path}{ext}"
                    if test_path in self.file_paths:
                        target_path = test_path
                        break
                    
                    # Also check for index files in directories
                    if os.path.isdir(target_path):
                        for index_file in ['index.js', 'index.jsx', 'index.ts', 'index.tsx', '__init__.py']:
                            test_path = os.path.join(target_path, index_file)
                            if test_path in self.file_paths:
                                target_path = test_path
                                break
            
            # Check if we have a component at this path
            if target_path in self.file_paths:
                target_id = self.file_paths[target_path]
                return Dependency(
                    source=component_id,
                    target=target_id,
                    dependency_type=dependency_type,
                    details={"module": module_name, "resolved_path": target_path}
                )
        else:
            # For non-relative imports, we'll do a simple check for components
            # with names that match this module
            
            # Extract the base name (e.g., 'lodash' from '@types/lodash')
            base_name = module_name.split('/')[-1]
            
            # Check if any component has this name
            for other_id, other_data in self.components.items():
                other_name = os.path.basename(other_data["file_path"])
                other_name_no_ext = os.path.splitext(other_name)[0]
                
                if other_id != component_id and (
                    other_name_no_ext == base_name or 
                    f"class {base_name}" in other_data["content"] or
                    f"function {base_name}" in other_data["content"]
                ):
                    return Dependency(
                        source=component_id,
                        target=other_id,
                        dependency_type=dependency_type,
                        details={"module": module_name}
                    )
        
        # If we get here, no matching component was found
        return None
    
    @trace_method
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the component graph.
        
        Returns:
            List[List[str]]: List of cycles, where each cycle is a list of component IDs
        """
        logger.info("Detecting circular dependencies")
        
        cycles = self.dependency_graph.find_circular_dependencies()
        
        if cycles:
            logger.warning(f"Detected {len(cycles)} circular dependencies")
            for i, cycle in enumerate(cycles):
                logger.warning(f"Cycle {i+1}: {' -> '.join(cycle)}")
        else:
            logger.info("No circular dependencies detected")
        
        return cycles
    
    @trace_method
    def calculate_build_order(self) -> List[str]:
        """
        Calculate the optimal build order for components.
        
        Returns:
            List[str]: Component IDs in build order
        """
        logger.info("Calculating build order")
        
        build_order = self.dependency_graph.get_build_order()
        
        logger.info(f"Build order calculated with {len(build_order)} components")
        logger.debug(f"Build order: {' -> '.join(build_order[:5])}{'...' if len(build_order) > 5 else ''}")
        
        return build_order
    
    @trace_method
    def generate_dependency_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report on component dependencies.
        
        Returns:
            Dict[str, Any]: Dependency report
        """
        logger.info("Generating dependency report")
        
        # Detect circular dependencies
        circular_dependencies = self.detect_circular_dependencies()
        
        # Calculate build order
        build_order = self.calculate_build_order()
        
        # Analyze component connectivity
        isolated_components = []
        for component_id in self.components.keys():
            if not self.dependency_graph.get_dependencies(component_id) and not self.dependency_graph.get_dependents(component_id):
                isolated_components.append(component_id)
        
        # Generate report
        report = {
            "total_components": len(self.components),
            "total_dependencies": len(self.dependency_graph.dependencies),
            "circular_dependencies": [
                {"cycle": cycle} for cycle in circular_dependencies
            ],
            "has_circular_dependencies": len(circular_dependencies) > 0,
            "build_order": build_order,
            "isolated_components": isolated_components,
            "component_dependencies": {},
            "most_depended_on": [],
            "most_dependent": []
        }
        
        # Analyze dependencies for each component
        dependency_counts = {}
        dependent_counts = {}
        
        for component_id in self.components.keys():
            dependencies = self.dependency_graph.get_dependencies(component_id)
            dependents = self.dependency_graph.get_dependents(component_id)
            
            dependency_counts[component_id] = len(dependencies)
            dependent_counts[component_id] = len(dependents)
            
            report["component_dependencies"][component_id] = {
                "dependencies": [dep.target for dep in dependencies],
                "dependents": [dep.source for dep in dependents],
                "dependency_count": len(dependencies),
                "dependent_count": len(dependents)
            }
        
        # Find most depended on components
        most_depended = sorted([(k, v) for k, v in dependent_counts.items()], key=lambda x: x[1], reverse=True)
        report["most_depended_on"] = [
            {"component_id": k, "dependent_count": v} 
            for k, v in most_depended[:5] if v > 0
        ]
        
        # Find components with most dependencies
        most_dependent = sorted([(k, v) for k, v in dependency_counts.items()], key=lambda x: x[1], reverse=True)
        report["most_dependent"] = [
            {"component_id": k, "dependency_count": v} 
            for k, v in most_dependent[:5] if v > 0
        ]
        
        logger.info("Dependency report generated")
        return report

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = DependencyAnalyzer()
    
    # Register some sample components
    analyzer.register_component(
        component_id="app",
        file_path="src/App.js",
        content="""
import React from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <div className="App">
      <Header />
      <main>Content</main>
      <Footer />
    </div>
  );
}

export default App;
"""
    )
    
    analyzer.register_component(
        component_id="header",
        file_path="src/components/Header.js",
        content="""
import React from 'react';
import Navigation from './Navigation';
import './Header.css';

function Header() {
  return (
    <header>
      <h1>My App</h1>
      <Navigation />
    </header>
  );
}

export default Header;
"""
    )
    
    analyzer.register_component(
        component_id="navigation",
        file_path="src/components/Navigation.js",
        content="""
import React from 'react';
import './Navigation.css';

function Navigation() {
  return (
    <nav>
      <ul>
        <li>Home</li>
        <li>About</li>
        <li>Contact</li>
      </ul>
    </nav>
  );
}

export default Navigation;
"""
    )
    
    analyzer.register_component(
        component_id="footer",
        file_path="src/components/Footer.js",
        content="""
import React from 'react';
import './Footer.css';

function Footer() {
  return (
    <footer>
      <p>Copyright 2023</p>
    </footer>
  );
}

export default Footer;
"""
    )
    
    # Analyze dependencies
    dependency_graph = analyzer.analyze_all_dependencies()
    
    # Generate report
    report = analyzer.generate_dependency_report()
    
    print(f"Total components: {report['total_components']}")
    print(f"Total dependencies: {report['total_dependencies']}")
    print(f"Build order: {' -> '.join(report['build_order'])}")
    print("Circular dependencies:", "Yes" if report['has_circular_dependencies'] else "No")
    
    if report['most_depended_on']:
        print("Most depended on components:")
        for item in report['most_depended_on']:
            print(f"  - {item['component_id']}: {item['dependent_count']} dependents")