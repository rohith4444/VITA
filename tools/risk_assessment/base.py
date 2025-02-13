from enum import Enum
from typing import Dict, Any, List
from core.logging.logger import setup_logger

class RiskProbability(Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

class RiskImpact(Enum):
    NEGLIGIBLE = 1
    MINOR = 2
    MODERATE = 3
    MAJOR = 4
    CRITICAL = 5

class RiskCategory(Enum):
    TECHNICAL = "technical"
    SCHEDULE = "schedule"
    RESOURCE = "resource"
    BUDGET = "budget"
    SCOPE = "scope"
    SECURITY = "security"
    INTEGRATION = "integration"
    EXTERNAL = "external"

class RiskStatus(Enum):
    IDENTIFIED = "identified"
    ANALYZED = "analyzed"
    MONITORED = "monitored"
    MITIGATED = "mitigated"
    CLOSED = "closed"

class RiskAssessmentError(Exception):
    """Base exception for risk assessment errors."""
    pass

class BaseRiskTool:
    """Base class for all risk assessment tools."""
    
    def __init__(self):
        self.logger = setup_logger(f"tools.risk.{self.__class__.__name__.lower()}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    def calculate_risk_score(self, probability: RiskProbability, impact: RiskImpact) -> float:
        """Calculate risk score based on probability and impact."""
        return (probability.value * impact.value) / 25  # Normalized to 0-1 scale
    
    def get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "NEGLIGIBLE"