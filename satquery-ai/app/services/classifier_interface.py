from abc import ABC, abstractmethod
from typing import Tuple, Optional

class QueryClassifierInterface(ABC):
    """
    Interface for Query Classifiers.
    Enables plug-and-play pattern for future LLM-based classifiers.
    """
    
    @abstractmethod
    def classify(self, query: str) -> Tuple[str, float, Optional[str]]:
        """
        Analyze the query text to determine the intent, confidence score, and hazard type.
        
        Args:
            query (str): The user's input text query.
            
        Returns:
            Tuple[str, float, Optional[str]]: A tuple containing:
                - intent (str): The primary intent classification.
                - confidence (float): The classification confidence score (0.0 to 1.0).
                - hazard_type (Optional[str]): The classified hazard type if intent is 
                  DISASTER_HAZARD_ANALYSIS, else None.
        """
        pass
