# src/retrievers/retrieval_strategies.py
from enum import Enum, auto

class RetrievalStrategy(Enum):
    """Enumeration of available retrieval strategies."""
    BASIC = "basic"                    # Simple similarity search
    COMPRESSION = "compression"         # ContextualCompressionRetriever
    MULTI_QUERY = "multi_query"        # MultiQueryRetriever
    CHAINED = "chained"                # Full chained retrieval pipeline