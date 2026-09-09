from typing import Dict, Any, Optional

class CapabilityRegistry:
    """
    Central Capability Registry.
    Registers all system capabilities, their availability, provider agent names,
    required inputs, and general descriptions.
    """

    def __init__(self) -> None:
        # Central registry configuration
        self._registry: Dict[str, Dict[str, Any]] = {
            "change_detection": {
                "available": True,
                "agent_name": "ChangeDetectionAgent",
                "required_inputs": [
                    "before_image",
                    "after_image"
                ],
                "description": "Detects visual changes between two temporal satellite images."
            },
            "single_image_analysis": {
                "available": True,
                "agent_name": "SingleImageAnalysisAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Performs vision-language analysis of a single satellite image using Qwen2.5-VL via Hugging Face."
            },
            "visual_question_answering": {
                "available": True,
                "agent_name": "SingleImageAnalysisAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Answers natural language questions about visual content of a satellite image using Qwen2.5-VL."
            },
            "multimodal_analysis": {
                "available": False,
                "agent_name": "MultimodalAnalysisAgent",
                "required_inputs": [
                    "optical_satellite_image",
                    "sar_satellite_image"
                ],
                "description": "Compares and combines optical and SAR imagery."
            },
            "region_grounding": {
                "available": True,
                "agent_name": "VisualGroundingAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Detects and localizes specific geographic segments (e.g. water bodies, rivers)."
            },
            "visual_grounding": {
                "available": True,
                "agent_name": "VisualGroundingAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Locate features in a satellite image."
            },
            "image_annotation": {
                "available": True,
                "agent_name": "VisualGroundingAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Annotate satellite imagery with masks and bounding boxes."
            },
            "disaster_hazard_analysis": {
                "available": True,
                "agent_name": "DisasterAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Evaluates risks and damages from natural hazards (e.g., floods, landslides, fires)."
            },
            "risk_assessment": {
                "available": True,
                "agent_name": "DisasterAgent",
                "required_inputs": [
                    "image"
                ],
                "description": "Ranks risk scoring and explains safety recommendations."
            }
        }

    def get_capability(self, capability: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves capability details by its name (normalized to lower case).
        """
        return self._registry.get(capability.strip().lower())

    def is_available(self, capability: str) -> bool:
        """
        Returns True if the capability is registered and currently available, else False.
        """
        cap = self.get_capability(capability)
        return cap.get("available", False) if cap else False

    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves the complete registry dictionary.
        """
        return self._registry
