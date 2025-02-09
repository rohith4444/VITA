from enum import Enum
from src.utils.logger import setup_logger

# Initialize logger
logger = setup_logger("RetrievalStrategies")

class RetrievalStrategy(Enum):
    """Enumeration of available retrieval strategies."""
    BASIC = "basic"                    # Simple similarity search
    COMPRESSION = "compression"         # ContextualCompressionRetriever
    MULTI_QUERY = "multi_query"        # MultiQueryRetriever
    CHAINED = "chained"                # Full chained retrieval pipeline
    
    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        logger.debug(f"Registered retrieval strategy: {value}")
        return member
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_strategy(cls, strategy_name: str) -> 'RetrievalStrategy':
        """Get strategy by name with logging."""
        logger.debug(f"Attempting to get strategy: {strategy_name}")
        try:
            strategy = cls(strategy_name.lower())
            logger.info(f"Successfully retrieved strategy: {strategy}")
            return strategy
        except ValueError as e:
            logger.error(f"Invalid strategy name: {strategy_name}", exc_info=True)
            raise ValueError(f"Invalid strategy name: {strategy_name}. "
                           f"Valid options are: {[s.value for s in cls]}")

    @classmethod
    def list_strategies(cls) -> list:
        """List all available strategies."""
        strategies = [s.value for s in cls]
        logger.debug(f"Available strategies: {strategies}")
        return strategies