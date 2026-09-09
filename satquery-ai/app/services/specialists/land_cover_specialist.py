from PIL import Image
from typing import Dict, Any, List, Tuple
from app.services.grounding_interface import VisualGroundingModelInterface

class LandCoverSegmentationService(VisualGroundingModelInterface):
    """
    Land Cover Vegetation and Surface Classification Specialist.
    Available model utilizing land classification range mappings.
    """
    def __init__(self) -> None:
        self.is_available = True

    def segment(self, image: Image.Image) -> Dict[str, Any]:
        return {
            "detections": [],
            "masks": [],
            "bboxes": [],
            "confidence": []
        }

    def detect(self, image: Image.Image, target: str) -> Tuple[List[Dict[str, Any]], List[List[Tuple[int, int]]]]:
        # Dynamic import to avoid circular dependency at module loading
        from app.services.visual_grounding_service import LocalGroundingService
        local_engine = LocalGroundingService()
        return local_engine.detect(image, target)
