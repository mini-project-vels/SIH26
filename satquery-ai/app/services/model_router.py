from typing import Dict, Any, Optional
from PIL import Image
from app.config.grounding_config import SPECIALIST_REGISTRY, DEFAULT_CONFIDENCE
from app.services.specialists import (
    BuildingSegmentationService,
    WaterSegmentationService,
    RoadSegmentationService,
    LandCoverSegmentationService
)

SPECIALIST_CLASSES = {
    "BuildingSegmentationService": BuildingSegmentationService,
    "WaterSegmentationService": WaterSegmentationService,
    "RoadSegmentationService": RoadSegmentationService,
    "LandCoverSegmentationService": LandCoverSegmentationService
}

class RemoteSensingModelRouter:
    """
    Remote Sensing Specialist Model Router.
    Evaluates requested target extracted concepts and intent to determine the 
    best-fit remote sensing specialist model. Handles fallback routing to 
    generic classification logic if specialists are offline or unavailable.
    """

    def route_request(
        self,
        target: str,
        query_intent: str,
        image: Any
    ) -> Dict[str, Any]:
        """
        Runs routing evaluation and selects the specialist pipeline or generic fallback.
        
        Args:
            target (str): The target category, e.g. 'building', 'water_body'
            query_intent (str): The query intent code, e.g. 'REGION_GROUNDING'
            image: Image source inputs
            
        Returns:
            Dict[str, Any] containing:
                - "selected_specialist": ID string of candidate specialist model
                - "reason": Contextual routing rationale explanation
                - "confidence": Specialist model reliability rating
                - "fallback_used": Boolean flag indicating fallback was triggered
        """
        # Look up category registry
        spec_info = SPECIALIST_REGISTRY.get(target)
        
        if not spec_info:
            # Target is unknown -> route directly to generic grounding
            return {
                "selected_specialist": "generic_grounding",
                "reason": "No specialist registered for this target class. Bypassed to Generic Grounding Specialist.",
                "confidence": DEFAULT_CONFIDENCE,
                "fallback_used": False
            }

        # Check availability of the registered specialist service
        service_class_name = spec_info.get("service_class")
        cls = SPECIALIST_CLASSES.get(service_class_name)
        
        is_available = spec_info.get("is_available", True)
        if cls:
            # Allow instantiated class to dictate dynamic availability
            try:
                inst = cls()
                is_available = getattr(inst, "is_available", True)
            except Exception:
                pass

        if is_available:
            return {
                "selected_specialist": spec_info["specialist_id"],
                "reason": spec_info["reason"],
                "confidence": spec_info["confidence"],
                "fallback_used": False
            }
        else:
            # Specialist offline or unavailable -> Fall back to generic mapping
            return {
                "selected_specialist": spec_info["specialist_id"],
                "reason": f"{spec_info['reason']} (Specialist model offline/unavailable; fell back to Generic Grounding Specialist.)",
                "confidence": DEFAULT_CONFIDENCE,
                "fallback_used": True
            }
