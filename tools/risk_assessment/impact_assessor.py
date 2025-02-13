# tools/risk_assessment/impact_assessor.py

from typing import Dict, Any, List, Tuple
from .base import BaseRiskTool, RiskImpact, RiskCategory, RiskAssessmentError

class ImpactAssessor(BaseRiskTool):
    """Tool for assessing the potential impact of identified risks."""
    
    def __init__(self):
        super().__init__()
        self.logger.info("Initializing Impact Assessor")
        
        # Impact criteria weights for different categories
        self.impact_criteria = {
            RiskCategory.TECHNICAL: {
                "quality_impact": 0.4,
                "maintenance_impact": 0.3,
                "performance_impact": 0.3
            },
            RiskCategory.SCHEDULE: {
                "delay_severity": 0.5,
                "downstream_impact": 0.3,
                "recovery_effort": 0.2
            },
            RiskCategory.BUDGET: {
                "cost_overrun": 0.5,
                "resource_cost": 0.3,
                "mitigation_cost": 0.2
            }
            # Add other categories as needed
        }
        
        # Impact thresholds for quantitative metrics
        self.schedule_thresholds = {
            RiskImpact.NEGLIGIBLE: 5,    # 5 days
            RiskImpact.MINOR: 10,        # 10 days
            RiskImpact.MODERATE: 20,     # 20 days
            RiskImpact.MAJOR: 30,        # 30 days
            RiskImpact.CRITICAL: 40      # 40+ days
        }
        
        self.budget_thresholds = {
            RiskImpact.NEGLIGIBLE: 0.05,  # 5% overrun
            RiskImpact.MINOR: 0.10,       # 10% overrun
            RiskImpact.MODERATE: 0.20,    # 20% overrun
            RiskImpact.MAJOR: 0.30,       # 30% overrun
            RiskImpact.CRITICAL: 0.40     # 40%+ overrun
        }
    
    def assess_impact(self,
                     risk_category: RiskCategory,
                     impact_factors: Dict[str, float]) -> Tuple[RiskImpact, Dict[str, Any]]:
        """
        Assess the impact of a risk based on category-specific factors.
        
        Args:
            risk_category: Category of the risk
            impact_factors: Dictionary of impact factors and their values (0-1)
            
        Returns:
            Tuple of (RiskImpact, impact details dictionary)
        """
        try:
            self.logger.debug(f"Assessing impact for {risk_category.value} risk")
            self.logger.debug(f"Impact factors: {impact_factors}")
            
            if risk_category not in self.impact_criteria:
                raise RiskAssessmentError(f"Unsupported risk category: {risk_category}")
            
            # Get criteria for the category
            criteria = self.impact_criteria[risk_category]
            
            # Validate impact factors
            for required_factor in criteria.keys():
                if required_factor not in impact_factors:
                    raise RiskAssessmentError(f"Missing required impact factor: {required_factor}")
            
            # Calculate weighted impact
            weighted_sum = sum(
                criteria[factor] * impact_factors[factor]
                for factor in criteria.keys()
            )
            
            # Determine impact level and details
            impact_level = self._map_to_impact(weighted_sum)
            impact_details = self._generate_impact_details(
                risk_category,
                impact_level,
                impact_factors
            )
            
            self.logger.info(f"Assessed impact: {impact_level.name} (Score: {weighted_sum:.2f})")
            return impact_level, impact_details
            
        except Exception as e:
            self.logger.error(f"Error assessing impact: {str(e)}")
            raise RiskAssessmentError(f"Impact assessment failed: {str(e)}")
    
    def assess_schedule_impact(self, delay_days: int) -> RiskImpact:
        """Assess impact based on schedule delay."""
        self.logger.debug(f"Assessing schedule impact for {delay_days} days delay")
        
        for impact_level in reversed(RiskImpact):
            if delay_days >= self.schedule_thresholds[impact_level]:
                return impact_level
        return RiskImpact.NEGLIGIBLE
    
    def assess_budget_impact(self, budget_overrun_percentage: float) -> RiskImpact:
        """Assess impact based on budget overrun."""
        self.logger.debug(f"Assessing budget impact for {budget_overrun_percentage:.1%} overrun")
        
        for impact_level in reversed(RiskImpact):
            if budget_overrun_percentage >= self.budget_thresholds[impact_level]:
                return impact_level
        return RiskImpact.NEGLIGIBLE
    
    def _map_to_impact(self, score: float) -> RiskImpact:
        """Map calculated score to RiskImpact enum."""
        if score >= 0.8:
            return RiskImpact.CRITICAL
        elif score >= 0.6:
            return RiskImpact.MAJOR
        elif score >= 0.4:
            return RiskImpact.MODERATE
        elif score >= 0.2:
            return RiskImpact.MINOR
        else:
            return RiskImpact.NEGLIGIBLE
    
    def _generate_impact_details(self,
                               category: RiskCategory,
                               impact: RiskImpact,
                               factors: Dict[str, float]) -> Dict[str, Any]:
        """Generate detailed impact assessment information."""
        self.logger.debug("Generating impact assessment details")
        
        details = {
            "category": category.value,
            "impact_level": impact.name,
            "factor_contributions": {
                factor: {
                    "value": value,
                    "weight": self.impact_criteria[category][factor],
                    "weighted_contribution": value * self.impact_criteria[category][factor]
                }
                for factor, value in factors.items()
            },
            "recommendations": self._get_impact_recommendations(category, impact)
        }
        
        return details
    
    def _get_impact_recommendations(self,
                                  category: RiskCategory,
                                  impact: RiskImpact) -> List[str]:
        """Get recommendations based on impact level and category."""
        recommendations = []
        
        if impact in [RiskImpact.CRITICAL, RiskImpact.MAJOR]:
            recommendations.extend([
                "Immediate escalation to project stakeholders required",
                "Develop detailed mitigation plan",
                "Consider project plan adjustments"
            ])
        elif impact == RiskImpact.MODERATE:
            recommendations.extend([
                "Regular monitoring required",
                "Prepare contingency measures",
                "Review mitigation strategies"
            ])
        else:
            recommendations.append("Monitor during regular risk reviews")
            
        # Add category-specific recommendations
        if category == RiskCategory.TECHNICAL:
            recommendations.append("Review technical architecture and dependencies")
            recommendations.append("Assess technology stack alternatives")
            recommendations.append("Plan for technical debt management")
            
        elif category == RiskCategory.SCHEDULE:
            recommendations.append("Review project timeline and resource allocation")
            recommendations.append("Identify schedule compression opportunities")
            recommendations.append("Evaluate fast-tracking possibilities")
            
        elif category == RiskCategory.BUDGET:
            recommendations.append("Review cost estimates and contingency reserves")
            recommendations.append("Identify cost optimization opportunities")
            recommendations.append("Consider budget reallocation strategies")
            
        elif category == RiskCategory.RESOURCE:
            recommendations.append("Review resource availability and skill requirements")
            recommendations.append("Consider resource cross-training options")
            recommendations.append("Evaluate external resource options")
            
        elif category == RiskCategory.SCOPE:
            recommendations.append("Review scope definition and requirements")
            recommendations.append("Identify potential scope reduction options")
            recommendations.append("Evaluate MVP alternatives")
            
        elif category == RiskCategory.SECURITY:
            recommendations.append("Conduct security assessment review")
            recommendations.append("Update security controls and measures")
            recommendations.append("Plan for security testing and auditing")
            
        elif category == RiskCategory.INTEGRATION:
            recommendations.append("Review integration points and dependencies")
            recommendations.append("Assess integration testing coverage")
            recommendations.append("Evaluate fallback options")
            
        elif category == RiskCategory.EXTERNAL:
            recommendations.append("Monitor external factors and dependencies")
            recommendations.append("Develop contingency plans for external changes")
            recommendations.append("Maintain stakeholder communication")
        
        self.logger.debug(f"Generated {len(recommendations)} recommendations for {category.value} risk")
        return recommendations

    def get_impact_criteria(self, risk_category: RiskCategory) -> Dict[str, float]:
        """Get the impact criteria and weights for a given category."""
        self.logger.debug(f"Getting impact criteria for {risk_category.value}")
        
        if risk_category not in self.impact_criteria:
            raise RiskAssessmentError(f"Unsupported risk category: {risk_category}")
            
        return self.impact_criteria[risk_category]

    def get_threshold_values(self, metric_type: str) -> Dict[RiskImpact, float]:
        """Get threshold values for quantitative metrics."""
        self.logger.debug(f"Getting threshold values for {metric_type}")
        
        if metric_type.lower() == 'schedule':
            return self.schedule_thresholds
        elif metric_type.lower() == 'budget':
            return self.budget_thresholds
        else:
            raise RiskAssessmentError(f"Unsupported metric type: {metric_type}")

    def evaluate_combined_impact(self, impacts: List[RiskImpact]) -> RiskImpact:
        """Evaluate the combined impact of multiple risks."""
        self.logger.debug(f"Evaluating combined impact of {len(impacts)} risks")
        
        if not impacts:
            return RiskImpact.NEGLIGIBLE
            
        # Use the maximum impact level as the combined impact
        combined = max(impact.value for impact in impacts)
        return RiskImpact(combined)