from langchain_core.pydantic_v1 import BaseModel, Field, validator
from src.utils.logger import setup_logger

logger = setup_logger("GradeModels")

class GradeDocuments(BaseModel):
    """Binary relevance score for documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
    
    @validator('binary_score')
    def validate_score(cls, v):
        """Validate that score is either 'yes' or 'no'."""
        v = v.lower()
        logger.debug(f"Validating binary score: {v}")
        if v not in ['yes', 'no']:
            error_msg = f"Binary score must be 'yes' or 'no', got {v}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return v