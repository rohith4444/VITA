# tools/project_planning/dependency_analyzer.py

from typing import Dict, Any, List, Set, Tuple
import networkx as nx
from dataclasses import dataclass
from enum import Enum
from .base import (
    BaseProjectPlanningTool,
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    ProjectPhase,
    PlanningError
)

class DependencyType(Enum):
    """Types of task dependencies."""
    FINISH_TO_START = "FS"  # Most common: task must finish before next can start
    START_TO_START = "SS"   # Tasks can start together
    FINISH_TO_FINISH = "FF" # Tasks must finish together
    START_TO_FINISH = "SF"  # Rarely used: task must start before other can finish

class DependencyStrength(Enum):
    """Strength/importance of dependencies."""
    MANDATORY = "mandatory"     # Must be respected
    DISCRETIONARY = "preferred" # Preferred but flexible
    EXTERNAL = "external"       # External dependency
    INTERNAL = "internal"       # Internal project dependency

@dataclass
class Dependency:
    """Represents a dependency between tasks."""
    from_task: str
    to_task: str
    dep_type: DependencyType = DependencyType.FINISH_TO_START
    strength: DependencyStrength = DependencyStrength.MANDATORY
    lag: int = 0  # Lag time in days
    description: str = ""

class DependencyAnalyzer(BaseProjectPlanningTool):
    """Tool for analyzing and managing task dependencies."""

    def __init__(self):
        super().__init__("DependencyAnalyzer")
        self.dependency_graph = None
        self.cached_analysis = {}

    def analyze_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive dependency analysis.
        
        Args:
            tasks: List of project tasks with dependencies
            
        Returns:
            Dictionary containing dependency analysis results
        """
        self.logger.info("Starting dependency analysis")
        try:
            # Create dependency graph
            self.dependency_graph = self._create_dependency_graph(tasks)
            
            # Perform various analyses
            cycles = self._detect_cycles()
            critical_deps = self._identify_critical_dependencies()
            bottlenecks = self._identify_bottlenecks()
            redundant = self._find_redundant_dependencies()
            
            analysis = {
                "dependency_count": self.dependency_graph.number_of_edges(),
                "cycles_detected": len(cycles) > 0,
                "cycles": cycles,
                "critical_dependencies": critical_deps,
                "bottlenecks": bottlenecks,
                "redundant_dependencies": redundant,
                "dependency_chains": self._analyze_dependency_chains(),
                "metrics": self._calculate_dependency_metrics(),
                "recommendations": self._generate_recommendations()
            }
            
            self.cached_analysis = analysis
            self.logger.info("Dependency analysis completed")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in dependency analysis: {str(e)}")
            raise PlanningError(f"Dependency analysis failed: {str(e)}")

    def _create_dependency_graph(self, tasks: List[Dict[str, Any]]) -> nx.DiGraph:
        """Create a directed graph representing task dependencies."""
        self.logger.debug("Creating dependency graph")
        try:
            G = nx.DiGraph()
            
            # Add nodes (tasks)
            for task in tasks:
                G.add_node(
                    task["id"],
                    name=task["name"],
                    duration=task["duration"],
                    phase=task.get("phase", "unknown"),
                    priority=task.get("priority", TaskPriority.MEDIUM)
                )
            
            # Add edges (dependencies)
            for task in tasks:
                for dep in task.get("dependencies", []):
                    dep_type = DependencyType.FINISH_TO_START  # Default
                    if isinstance(dep, dict):  # If dependency has additional info
                        dep_id = dep["task_id"]
                        dep_type = dep.get("type", DependencyType.FINISH_TO_START)
                        lag = dep.get("lag", 0)
                    else:
                        dep_id = dep
                        lag = 0
                        
                    G.add_edge(
                        dep_id,
                        task["id"],
                        type=dep_type,
                        lag=lag
                    )
            
            self.logger.debug(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            return G
            
        except Exception as e:
            self.logger.error(f"Error creating dependency graph: {str(e)}")
            raise

    def _detect_cycles(self) -> List[List[str]]:
        """Detect cycles in dependencies."""
        self.logger.debug("Detecting dependency cycles")
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            
            if cycles:
                self.logger.warning(f"Found {len(cycles)} dependency cycles")
                for cycle in cycles:
                    self.logger.warning(f"Cycle detected: {' -> '.join(cycle)}")
            
            return cycles
            
        except Exception as e:
            self.logger.error(f"Error detecting cycles: {str(e)}")
            return []

    def _identify_critical_dependencies(self) -> List[Dict[str, Any]]:
        """Identify critical dependencies that could impact project timeline."""
        self.logger.debug("Identifying critical dependencies")
        try:
            critical_deps = []
            
            # Find nodes with high in-degree (many dependencies)
            for node in self.dependency_graph.nodes():
                in_degree = self.dependency_graph.in_degree(node)
                if in_degree > 2:  # More than 2 dependencies
                    task_data = self.dependency_graph.nodes[node]
                    predecessors = list(self.dependency_graph.predecessors(node))
                    
                    critical_deps.append({
                        "task_id": node,
                        "task_name": task_data["name"],
                        "dependency_count": in_degree,
                        "dependencies": predecessors,
                        "risk_level": "HIGH" if in_degree > 3 else "MEDIUM",
                        "phase": task_data.get("phase", "unknown")
                    })
            
            self.logger.debug(f"Found {len(critical_deps)} critical dependencies")
            return sorted(critical_deps, key=lambda x: x["dependency_count"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error identifying critical dependencies: {str(e)}")
            return []

    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify dependency bottlenecks."""
        self.logger.debug("Identifying dependency bottlenecks")
        try:
            bottlenecks = []
            
            # Calculate betweenness centrality
            centrality = nx.betweenness_centrality(self.dependency_graph)
            
            # Find high centrality nodes (bottlenecks)
            for node, centrality_value in centrality.items():
                if centrality_value > 0.3:  # Significant bottleneck threshold
                    task_data = self.dependency_graph.nodes[node]
                    bottlenecks.append({
                        "task_id": node,
                        "task_name": task_data["name"],
                        "centrality_score": round(centrality_value, 3),
                        "incoming_deps": list(self.dependency_graph.predecessors(node)),
                        "outgoing_deps": list(self.dependency_graph.successors(node)),
                        "risk_level": "HIGH" if centrality_value > 0.5 else "MEDIUM"
                    })
            
            self.logger.debug(f"Found {len(bottlenecks)} dependency bottlenecks")
            return sorted(bottlenecks, key=lambda x: x["centrality_score"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error identifying bottlenecks: {str(e)}")
            return []

    def _find_redundant_dependencies(self) -> List[Dict[str, Any]]:
        """Find redundant dependencies that could be removed."""
        self.logger.debug("Finding redundant dependencies")
        try:
            redundant = []
            
            # Find transitive dependencies
            for node in self.dependency_graph.nodes():
                predecessors = set(self.dependency_graph.predecessors(node))
                for pred in predecessors:
                    # Check if there are indirect paths
                    indirect_paths = list(nx.all_simple_paths(
                        self.dependency_graph, pred, node
                    ))
                    
                    if len(indirect_paths) > 1:  # More than one path exists
                        redundant.append({
                            "task_id": node,
                            "redundant_dependency": pred,
                            "alternate_paths": [
                                path for path in indirect_paths 
                                if len(path) > 2  # Longer than direct path
                            ],
                            "recommendation": "Consider removing direct dependency"
                        })
            
            self.logger.debug(f"Found {len(redundant)} redundant dependencies")
            return redundant
            
        except Exception as e:
            self.logger.error(f"Error finding redundant dependencies: {str(e)}")
            return []
        
    def _analyze_dependency_chains(self) -> List[Dict[str, Any]]:
        """Analyze dependency chains and their characteristics."""
        self.logger.debug("Analyzing dependency chains")
        try:
            chains = []
            
            # Find all paths from start to end nodes
            start_nodes = [n for n in self.dependency_graph.nodes() 
                         if self.dependency_graph.in_degree(n) == 0]
            end_nodes = [n for n in self.dependency_graph.nodes() 
                        if self.dependency_graph.out_degree(n) == 0]
            
            for start in start_nodes:
                for end in end_nodes:
                    all_paths = list(nx.all_simple_paths(
                        self.dependency_graph, start, end
                    ))
                    
                    for path in all_paths:
                        if len(path) > 3:  # Significant chains only
                            chain_data = {
                                "length": len(path),
                                "path": path,
                                "total_duration": sum(
                                    self.dependency_graph.nodes[node]["duration"].days
                                    for node in path
                                ),
                                "complexity": self._calculate_chain_complexity(path),
                                "risk_level": "HIGH" if len(path) > 5 else "MEDIUM"
                            }
                            chains.append(chain_data)
            
            self.logger.debug(f"Found {len(chains)} significant dependency chains")
            return sorted(chains, key=lambda x: x["length"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependency chains: {str(e)}")
            return []

    def _calculate_chain_complexity(self, path: List[str]) -> str:
        """Calculate complexity of a dependency chain."""
        try:
            factors = []
            
            # Length complexity
            factors.append(0.3 if len(path) > 5 else 0.2)
            
            # Task complexity
            avg_complexity = sum(
                isinstance(self.dependency_graph.nodes[node].get("complexity"), TaskComplexity)
                for node in path
            ) / len(path)
            factors.append(avg_complexity)
            
            # Dependency types complexity
            edge_complexity = 0
            for i in range(len(path)-1):
                edge = self.dependency_graph.edges[path[i], path[i+1]]
                if edge.get("type") != DependencyType.FINISH_TO_START:
                    edge_complexity += 0.1
            factors.append(edge_complexity)
            
            # Calculate final score
            complexity_score = sum(factors) / len(factors)
            
            if complexity_score > 0.7:
                return "HIGH"
            elif complexity_score > 0.4:
                return "MEDIUM"
            return "LOW"
            
        except Exception as e:
            self.logger.error(f"Error calculating chain complexity: {str(e)}")
            return "MEDIUM"

    def _calculate_dependency_metrics(self) -> Dict[str, Any]:
        """Calculate various dependency metrics."""
        self.logger.debug("Calculating dependency metrics")
        try:
            metrics = {
                "total_dependencies": self.dependency_graph.number_of_edges(),
                "average_dependencies_per_task": round(
                    self.dependency_graph.number_of_edges() / 
                    self.dependency_graph.number_of_nodes(),
                    2
                ),
                "max_chain_length": max(
                    len(path) for path in nx.all_simple_paths(
                        self.dependency_graph,
                        *self._get_terminal_nodes()
                    )
                ),
                "dependency_density": round(
                    nx.density(self.dependency_graph),
                    3
                ),
                "critical_nodes": len([
                    n for n in self.dependency_graph.nodes()
                    if self.dependency_graph.degree(n) > 4
                ])
            }
            
            self.logger.debug(f"Calculated dependency metrics: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating dependency metrics: {str(e)}")
            return {}
        
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for dependency optimization."""
        self.logger.debug("Generating dependency recommendations")
        try:
            recommendations = []
            
            # Check for cycles
            if self.cached_analysis.get("cycles"):
                recommendations.append({
                    "type": "critical",
                    "issue": "Dependency cycles detected",
                    "impact": "HIGH",
                    "recommendation": "Resolve circular dependencies",
                    "affected_tasks": self.cached_analysis["cycles"]
                })
            
            # Check for bottlenecks
            for bottleneck in self.cached_analysis.get("bottlenecks", []):
                if bottleneck["centrality_score"] > 0.5:
                    recommendations.append({
                        "type": "optimization",
                        "issue": "High dependency bottleneck",
                        "impact": "HIGH",
                        "recommendation": "Consider splitting task or reducing dependencies",
                        "affected_task": bottleneck["task_id"]
                    })
            
            # Check for long chains
            long_chains = [
                chain for chain in self.cached_analysis.get("dependency_chains", [])
                if chain["length"] > 5
            ]
            if long_chains:
                recommendations.append({
                    "type": "optimization",
                    "issue": "Long dependency chains detected",
                    "impact": "MEDIUM",
                    "recommendation": "Consider parallelizing tasks or restructuring dependencies",
                    "affected_chains": [chain["path"] for chain in long_chains]
                })
            
            # Check for redundant dependencies
            if self.cached_analysis.get("redundant_dependencies"):
                recommendations.append({
                    "type": "improvement",
                    "issue": "Redundant dependencies found",
                    "impact": "LOW",
                    "recommendation": "Remove unnecessary direct dependencies",
                    "affected_dependencies": self.cached_analysis["redundant_dependencies"]
                })
            
            self.logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []

    def optimize_dependencies(self) -> Dict[str, Any]:
        """Attempt to optimize the dependency structure."""
        self.logger.info("Starting dependency optimization")
        try:
            optimizations = {
                "removals": self._identify_removable_dependencies(),
                "reorderings": self._suggest_dependency_reordering(),
                "parallelization": self._identify_parallelization_opportunities(),
                "impact": self._calculate_optimization_impact()
            }
            
            self.logger.info("Dependency optimization completed")
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Error in dependency optimization: {str(e)}")
            raise

    def _identify_removable_dependencies(self) -> List[Dict[str, Any]]:
        """Identify dependencies that could potentially be removed."""
        self.logger.debug("Identifying removable dependencies")
        try:
            removable = []
            
            # Check for transitive dependencies
            for edge in self.dependency_graph.edges():
                source, target = edge
                # Remove edge temporarily
                self.dependency_graph.remove_edge(source, target)
                
                # Check if there's still a path
                if nx.has_path(self.dependency_graph, source, target):
                    removable.append({
                        "from_task": source,
                        "to_task": target,
                        "reason": "Transitive dependency exists",
                        "alternative_path": next(nx.all_simple_paths(
                            self.dependency_graph, source, target
                        ))
                    })
                
                # Restore edge
                self.dependency_graph.add_edge(source, target)
            
            self.logger.debug(f"Found {len(removable)} removable dependencies")
            return removable
            
        except Exception as e:
            self.logger.error(f"Error identifying removable dependencies: {str(e)}")
            return []

    def _suggest_dependency_reordering(self) -> List[Dict[str, Any]]:
        """Suggest potential dependency reordering for optimization."""
        self.logger.debug("Analyzing dependency reordering opportunities")
        try:
            suggestions = []
            
            # Look for parallel execution opportunities
            for node in self.dependency_graph.nodes():
                predecessors = list(self.dependency_graph.predecessors(node))
                if len(predecessors) > 1:
                    # Check if predecessors could be executed in parallel
                    if not any(
                        nx.has_path(self.dependency_graph, p1, p2) or
                        nx.has_path(self.dependency_graph, p2, p1)
                        for i, p1 in enumerate(predecessors)
                        for p2 in predecessors[i+1:]
                    ):
                        suggestions.append({
                            "task_id": node,
                            "current_predecessors": predecessors,
                            "suggestion": "Consider parallel execution of predecessor tasks",
                            "potential_benefit": "Reduced total duration"
                        })
            
            self.logger.debug(f"Generated {len(suggestions)} reordering suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting dependency reordering: {str(e)}")
            return []

    def _identify_parallelization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for task parallelization."""
        self.logger.debug("Identifying parallelization opportunities")
        try:
            opportunities = []
            
            # Find independent task clusters
            undirected = self.dependency_graph.to_undirected()
            components = list(nx.connected_components(undirected))
            
            for component in components:
                if len(component) > 1:
                    # Check for tasks that could be parallelized
                    subgraph = self.dependency_graph.subgraph(component)
                    independent_sets = list(nx.algorithms.clique.find_cliques(
                        nx.complement(subgraph)
                    ))
                    
                    for ind_set in independent_sets:
                        if len(ind_set) > 1:
                            opportunities.append({
                                "tasks": list(ind_set),
                                "size": len(ind_set),
                                "type": "Independent Set",
                                "benefit": "Can be executed in parallel"
                            })
            
            self.logger.debug(f"Found {len(opportunities)} parallelization opportunities")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error identifying parallelization opportunities: {str(e)}")
            return []

    def _calculate_optimization_impact(self) -> Dict[str, Any]:
        """Calculate potential impact of suggested optimizations."""
        self.logger.debug("Calculating optimization impact")
        try:
            current_metrics = self._calculate_dependency_metrics()
            
            # Simulate optimizations
            potential_metrics = {
                "reduced_dependencies": len(self._identify_removable_dependencies()),
                "parallel_opportunities": len(self._identify_parallelization_opportunities()),
                "potential_duration_reduction": self._estimate_duration_reduction(),
                "complexity_reduction": self._estimate_complexity_reduction()
            }
            
            impact = {
                "current_state": current_metrics,
                "potential_improvements": potential_metrics,
                "estimated_benefit": {
                    "dependency_reduction_percent": round(
                        (potential_metrics["reduced_dependencies"] / 
                         current_metrics["total_dependencies"]) * 100,
                        1
                    ),
                    "parallelization_opportunities": potential_metrics["parallel_opportunities"],
                    "potential_duration_savings": "10-20%"  # Estimated range
                }
            }
            
            self.logger.debug(f"Calculated optimization impact: {impact}")
            return impact
            
        except Exception as e:
            self.logger.error(f"Error calculating optimization impact: {str(e)}")
            return {}
