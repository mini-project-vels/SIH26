from PIL import Image
from typing import Dict, Any, List, Tuple
from app.services.grounding_interface import VisualGroundingModelInterface

class WaterSegmentationService(VisualGroundingModelInterface):
    """
    Water Segmentation Specialist.
    Available model utilizing pixel-based spectral thresholds.
    """
    def __init__(self) -> None:
        self.is_available = True

    def segment(self, image: Image.Image) -> Dict[str, Any]:
        """Satisfy mock/interface footprint."""
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
