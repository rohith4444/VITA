from typing import List, TypedDict
from langchain.docstore.document import Document
from src.utils.logger import setup_logger

logger = setup_logger("AgentGraphState")

class AgentGraphState(TypedDict):
    """
    State dictionary for the agent processing graph.
    
    Attributes:
        question (str): The current query being processed
        generation (str): Generated response content
        web_search_needed (str): Flag indicating if web search is required ("Yes"/"No")
        documents (List[Document]): List of relevant documents
        agent_name (str): Name of the processing agent
    """
    question: str 
    generation: str
    web_search_needed: str
    documents: List[Document]
    agent_name: str

def validate_state(state: AgentGraphState) -> bool:
    """
    Validate the state dictionary structure and types.
    
    Args:
        state: The state dictionary to validate
        
    Returns:
        bool: True if valid, raises exception if invalid
    """
    logger.debug("Validating agent graph state")
    try:
        # Check all required keys are present
        required_keys = {'question', 'generation', 'web_search_needed', 'documents', 'agent_name'}
        missing_keys = required_keys - set(state.keys())
        if missing_keys:
            raise KeyError(f"Missing required keys: {missing_keys}")
            
        # Validate types
        if not isinstance(state['question'], str):
            raise TypeError(f"'question' must be str, got {type(state['question'])}")
        if not isinstance(state['generation'], str):
            raise TypeError(f"'generation' must be str, got {type(state['generation'])}")
        if not isinstance(state['web_search_needed'], str):
            raise TypeError(f"'web_search_needed' must be str, got {type(state['web_search_needed'])}")
        if not isinstance(state['documents'], list):
            raise TypeError(f"'documents' must be list, got {type(state['documents'])}")
        if not isinstance(state['agent_name'], str):
            raise TypeError(f"'agent_name' must be str, got {type(state['agent_name'])}")
            
        # Validate web_search_needed value
        if state['web_search_needed'] not in ['Yes', 'No']:
            raise ValueError(f"'web_search_needed' must be 'Yes' or 'No', got {state['web_search_needed']}")
            
        # Validate documents list elements
        for i, doc in enumerate(state['documents']):
            if not isinstance(doc, Document):
                raise TypeError(f"Document at index {i} must be Document type, got {type(doc)}")
        
        logger.info("State validation successful")
        logger.debug(f"Current state: question='{state['question'][:50]}...', "
                    f"agent={state['agent_name']}, "
                    f"documents={len(state['documents'])}, "
                    f"web_search={state['web_search_needed']}")
        return True
        
    except Exception as e:
        logger.error(f"State validation failed: {str(e)}", exc_info=True)
        raise

def create_initial_state(question: str, agent_name: str) -> AgentGraphState:
    """
    Create an initial state dictionary with default values.
    
    Args:
        question: The initial query
        agent_name: The name of the processing agent
        
    Returns:
        AgentGraphState: Initialized state dictionary
    """
    logger.debug(f"Creating initial state for agent: {agent_name}")
    try:
        state: AgentGraphState = {
            'question': question,
            'generation': '',
            'web_search_needed': 'No',
            'documents': [],
            'agent_name': agent_name
        }
        validate_state(state)
        logger.info("Initial state created successfully")
        return state
    except Exception as e:
        logger.error(f"Error creating initial state: {str(e)}", exc_info=True)
        raise