from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from PIL import Image

class VisualGroundingModelInterface(ABC):
    """
    Interface for visual grounding/localization models.
    Enables future replacement with models like GroundingDINO, HuggingFace grounders, etc.
    """
    @abstractmethod
    def detect(self, image: Image.Image, target: str) -> Tuple[List[Dict[str, Any]], List[List[Tuple[int, int]]]]:
        pass
