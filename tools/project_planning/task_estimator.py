# tools/project_planning/task_estimator.py

from typing import Dict, Any, List, Optional
from datetime import timedelta
from .base import (
    BaseProjectPlanningTool,
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    PlanningError
)

class TaskEstimationFactors(Dict[str, float]):
    """Predefined estimation factors for different task aspects."""
    
    def __init__(self):
        super().__init__()
        # Technical factors
        self["technical_complexity"] = 1.0
        self["technology_maturity"] = 1.0
        self["integration_complexity"] = 1.0
        
        # Team factors
        self["team_expertise"] = 1.0
        self["team_familiarity"] = 1.0
        self["team_availability"] = 1.0
        
        # Project factors
        self["requirements_clarity"] = 1.0
        self["project_complexity"] = 1.0
        self["dependencies"] = 1.0

class TaskEstimator(BaseProjectPlanningTool):
    """Tool for estimating task durations, effort, and complexity."""

    def __init__(self):
        super().__init__("TaskEstimator")
        self.estimation_factors = TaskEstimationFactors()
        self.historical_data = {}  # For future use with historical estimations
        
    def estimate_task(self, task: Dict[str, Any], factors: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Estimate task duration, effort, and complexity based on various factors.
        
        Args:
            task: Task information dictionary
            factors: Optional custom estimation factors
        
        Returns:
            Dictionary with estimation details
        """
        self.logger.info(f"Estimating task: {task.get('name', 'Unknown')}")
        try:
            # Validate task
            if not self.validate_task(task):
                raise PlanningError("Invalid task structure")
            
            # Use provided factors or defaults
            estimation_factors = factors or self.estimation_factors
            
            # Calculate complexity
            complexity = self._calculate_complexity(task, estimation_factors)
            task["complexity"] = complexity
            
            # Calculate base duration and adjust it
            base_duration = self.calculate_base_duration(task)
            adjusted_duration = self._adjust_duration(base_duration, estimation_factors)
            
            # Calculate effort
            effort = self._calculate_total_effort(task, estimation_factors)
            
            # Generate estimation details
            estimation = {
                "task_id": task["id"],
                "original_estimate": base_duration,
                "adjusted_duration": adjusted_duration,
                "effort_days": effort,
                "complexity": complexity.name,
                "confidence_score": self._calculate_confidence_score(estimation_factors),
                "risk_level": self._assess_estimation_risk(task, estimation_factors),
                "factors_used": dict(estimation_factors),
                "recommended_buffer": self._calculate_buffer(adjusted_duration, complexity)
            }
            
            self.logger.info(f"Estimation completed for task {task['id']}")
            self.logger.debug(f"Estimation details: {estimation}")
            
            return estimation
            
        except Exception as e:
            self.logger.error(f"Error estimating task: {str(e)}")
            raise PlanningError(f"Task estimation failed: {str(e)}")

    def _calculate_complexity(self, task: Dict[str, Any], factors: Dict[str, float]) -> TaskComplexity:
        """Calculate task complexity based on various factors."""
        try:
            # Base complexity score
            complexity_score = 0.0
            
            # Technical aspects (40% weight)
            complexity_score += 0.4 * (
                factors["technical_complexity"] * 0.4 +
                factors["technology_maturity"] * 0.3 +
                factors["integration_complexity"] * 0.3
            )
            
            # Team aspects (30% weight)
            complexity_score += 0.3 * (
                factors["team_expertise"] * 0.4 +
                factors["team_familiarity"] * 0.3 +
                factors["team_availability"] * 0.3
            )
            
            # Project aspects (30% weight)
            complexity_score += 0.3 * (
                factors["requirements_clarity"] * 0.4 +
                factors["project_complexity"] * 0.3 +
                factors["dependencies"] * 0.3
            )
            
            # Map score to complexity
            if complexity_score <= 0.3:
                return TaskComplexity.LOW
            elif complexity_score <= 0.6:
                return TaskComplexity.MEDIUM
            elif complexity_score <= 0.8:
                return TaskComplexity.HIGH
            else:
                return TaskComplexity.VERY_HIGH
                
        except Exception as e:
            self.logger.error(f"Error calculating complexity: {str(e)}")
            return TaskComplexity.MEDIUM

    def _adjust_duration(self, base_duration: timedelta, factors: Dict[str, float]) -> timedelta:
        """Adjust base duration based on estimation factors."""
        try:
            # Calculate adjustment multiplier
            multiplier = 1.0
            
            # Technical factors (40% weight)
            tech_multiplier = (
                factors["technical_complexity"] * 0.4 +
                factors["technology_maturity"] * 0.3 +
                factors["integration_complexity"] * 0.3
            )
            multiplier *= (1 + (tech_multiplier - 1) * 0.4)
            
            # Team factors (30% weight)
            team_multiplier = (
                factors["team_expertise"] * 0.4 +
                factors["team_familiarity"] * 0.3 +
                factors["team_availability"] * 0.3
            )
            multiplier *= (1 + (team_multiplier - 1) * 0.3)
            
            # Project factors (30% weight)
            project_multiplier = (
                factors["requirements_clarity"] * 0.4 +
                factors["project_complexity"] * 0.3 +
                factors["dependencies"] * 0.3
            )
            multiplier *= (1 + (project_multiplier - 1) * 0.3)
            
            # Apply multiplier to base duration
            adjusted_days = base_duration.days * multiplier
            return timedelta(days=round(adjusted_days, 1))
            
        except Exception as e:
            self.logger.error(f"Error adjusting duration: {str(e)}")
            return base_duration

    def _calculate_total_effort(self, task: Dict[str, Any], factors: Dict[str, float]) -> float:
        """Calculate total effort in person-days."""
        try:
            # Get base effort
            base_effort = self.calculate_effort(task)
            
            # Adjust based on factors
            effort_multiplier = (
                factors["team_expertise"] * 0.4 +
                factors["team_familiarity"] * 0.3 +
                factors["requirements_clarity"] * 0.3
            )
            
            adjusted_effort = base_effort * effort_multiplier
            return round(adjusted_effort, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculating total effort: {str(e)}")
            return base_effort

    def _calculate_confidence_score(self, factors: Dict[str, float]) -> float:
        """Calculate confidence score for the estimation."""
        try:
            confidence_score = (
                factors["requirements_clarity"] * 0.3 +
                factors["team_expertise"] * 0.2 +
                factors["technology_maturity"] * 0.2 +
                factors["team_familiarity"] * 0.15 +
                factors["team_availability"] * 0.15
            )
            
            return round(confidence_score, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5

    def _assess_estimation_risk(self, task: Dict[str, Any], factors: Dict[str, float]) -> str:
        """Assess the risk level of the estimation."""
        try:
            risk_score = (
                (1 - factors["requirements_clarity"]) * 0.3 +
                (1 - factors["team_expertise"]) * 0.2 +
                (1 - factors["technology_maturity"]) * 0.2 +
                factors["technical_complexity"] * 0.15 +
                factors["project_complexity"] * 0.15
            )
            
            if risk_score <= 0.3:
                return "LOW"
            elif risk_score <= 0.6:
                return "MEDIUM"
            else:
                return "HIGH"
                
        except Exception as e:
            self.logger.error(f"Error assessing estimation risk: {str(e)}")
            return "MEDIUM"

    def _calculate_buffer(self, duration: timedelta, complexity: TaskComplexity) -> timedelta:
        """Calculate recommended buffer time based on duration and complexity."""
        try:
            buffer_multipliers = {
                TaskComplexity.LOW: 0.1,
                TaskComplexity.MEDIUM: 0.2,
                TaskComplexity.HIGH: 0.3,
                TaskComplexity.VERY_HIGH: 0.4
            }
            
            buffer_days = duration.days * buffer_multipliers[complexity]
            return timedelta(days=round(buffer_days, 1))
            
        except Exception as e:
            self.logger.error(f"Error calculating buffer: {str(e)}")
            return timedelta(days=duration.days * 0.2)  # Default 20% buffer