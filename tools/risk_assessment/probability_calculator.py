from typing import Dict, Any, List
from .base import BaseRiskTool, RiskProbability, RiskCategory, RiskAssessmentError

class RiskProbabilityCalculator(BaseRiskTool):
    """Tool for calculating risk probabilities based on project characteristics."""
    
    def __init__(self):
        super().__init__()
        self.logger.info("Initializing Risk Probability Calculator")
        
        # Risk factor weights for different categories
        self.category_weights = {
            RiskCategory.TECHNICAL: {
                "team_experience": 0.3,
                "technology_maturity": 0.4,
                "complexity": 0.3
            },
            RiskCategory.SCHEDULE: {
                "timeline_pressure": 0.4,
                "dependencies": 0.3,
                "resource_availability": 0.3
            },
            RiskCategory.RESOURCE: {
                "skill_availability": 0.4,
                "team_stability": 0.3,
                "resource_constraints": 0.3
            }
            # Add other categories as needed
        }
    
    def calculate_probability(self, 
                            risk_category: RiskCategory,
                            risk_factors: Dict[str, float]) -> RiskProbability:
        """
        Calculate risk probability based on category and risk factors.
        
        Args:
            risk_category: Category of the risk
            risk_factors: Dictionary of risk factors and their values (0-1)
        
        Returns:
            RiskProbability enum value
        """
        try:
            self.logger.debug(f"Calculating probability for {risk_category.value} risk")
            self.logger.debug(f"Risk factors: {risk_factors}")
            
            if risk_category not in self.category_weights:
                raise RiskAssessmentError(f"Unsupported risk category: {risk_category}")
            
            # Get weights for the category
            weights = self.category_weights[risk_category]
            
            # Validate risk factors
            for required_factor in weights.keys():
                if required_factor not in risk_factors:
                    raise RiskAssessmentError(f"Missing required risk factor: {required_factor}")
            
            # Calculate weighted probability
            weighted_sum = sum(
                weights[factor] * risk_factors[factor]
                for factor in weights.keys()
            )
            
            # Convert to probability level
            probability = self._map_to_probability(weighted_sum)
            self.logger.info(f"Calculated probability: {probability.name} (Score: {weighted_sum:.2f})")
            
            return probability
            
        except Exception as e:
            self.logger.error(f"Error calculating risk probability: {str(e)}")
            raise RiskAssessmentError(f"Probability calculation failed: {str(e)}")
    
    def calculate_technical_probability(self, 
                                     team_experience: float,
                                     technology_maturity: float,
                                     complexity: float) -> RiskProbability:
        """Specialized method for technical risk probability."""
        self.logger.debug("Calculating technical risk probability")
        
        return self.calculate_probability(
            RiskCategory.TECHNICAL,
            {
                "team_experience": team_experience,
                "technology_maturity": technology_maturity,
                "complexity": complexity
            }
        )
    
    def calculate_schedule_probability(self,
                                    timeline_pressure: float,
                                    dependencies: float,
                                    resource_availability: float) -> RiskProbability:
        """Specialized method for schedule risk probability."""
        self.logger.debug("Calculating schedule risk probability")
        
        return self.calculate_probability(
            RiskCategory.SCHEDULE,
            {
                "timeline_pressure": timeline_pressure,
                "dependencies": dependencies,
                "resource_availability": resource_availability
            }
        )
    
    def _map_to_probability(self, score: float) -> RiskProbability:
        """Map calculated score to RiskProbability enum."""
        if score >= 0.8:
            return RiskProbability.VERY_HIGH
        elif score >= 0.6:
            return RiskProbability.HIGH
        elif score >= 0.4:
            return RiskProbability.MEDIUM
        elif score >= 0.2:
            return RiskProbability.LOW
        else:
            return RiskProbability.VERY_LOW
    
    def get_probability_factors(self, risk_category: RiskCategory) -> List[str]:
        """Get the required risk factors for a given category."""
        self.logger.debug(f"Getting probability factors for {risk_category.value}")
        
        if risk_category not in self.category_weights:
            raise RiskAssessmentError(f"Unsupported risk category: {risk_category}")
            
        return list(self.category_weights[risk_category].keys())