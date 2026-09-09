from typing import Tuple, Optional
from app.models.schemas import AvailableInputs
from app.config.intents import Intents, HazardTypes, INTENT_CONFIGS, HAZARD_CONFIGS

class InputValidator:
    """
    Validates available inputs against the requirements of the classified intent.
    Supported statuses: SUFFICIENT, INSUFFICIENT, UNKNOWN.
    """

    def validate(
        self, 
        intent: str, 
        hazard_type: Optional[str], 
        available_inputs: Optional[AvailableInputs]
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Validates the available inputs and determines sufficiency and clarification needs.

        Args:
            intent (str): The classified intent.
            hazard_type (Optional[str]): The classified hazard type if any.
            available_inputs (Optional[AvailableInputs]): Metadata detailing inputs available.

        Returns:
            Tuple[str, bool, Optional[str]]: 
                - input_sufficiency ("SUFFICIENT", "INSUFFICIENT", "UNKNOWN")
                - needs_clarification (bool)
                - clarification_message (Optional[str])
        """
        # 1. Handle UNKNOWN intent immediately
        if intent == Intents.UNKNOWN:
            return (
                "UNKNOWN",
                True,
                "I could not understand your request. Please specify a remote sensing task such as "
                "single image analysis, change detection, visual question answering, or hazard assessment."
            )

        # 2. Get baseline configuration requirements
        config = INTENT_CONFIGS.get(intent, {})
        min_images = config.get("min_images", 1)
        req_modalities = config.get("required_modalities", [])

        # Override requirements if it is a disaster hazard
        if intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type:
            h_config = HAZARD_CONFIGS.get(hazard_type, {})
            min_images = h_config.get("min_images", min_images)
            req_modalities = h_config.get("required_modalities", req_modalities)

        # 3. If available_inputs is not provided at all, sufficiency is UNKNOWN
        if not available_inputs or (
            available_inputs.image_count is None and
            available_inputs.modalities is None and
            available_inputs.has_metadata is None
        ):
            # Special case: Glacier hazard has an inherent clarification warning even with UNKNOWN inputs
            if intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type == HazardTypes.GLACIER_GLOF:
                return (
                    "UNKNOWN",
                    True,
                    HAZARD_CONFIGS[HazardTypes.GLACIER_GLOF]["clarification_message"]
                )
            
            # Default for missing/unknown available inputs
            return "UNKNOWN", False, None

        # 4. We have available inputs metadata. Perform checks.
        errors = []

        # Check image count sufficiency
        if available_inputs.image_count is not None:
            if available_inputs.image_count < min_images:
                if intent == Intents.CHANGE_DETECTION:
                    errors.append("Change detection requires at least two satellite images from different time periods.")
                elif intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type == HazardTypes.GLACIER_GLOF:
                    errors.append("Glacier change monitoring requires at least two temporal satellite images (current vs historical).")
                elif intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type == HazardTypes.WILDFIRE:
                    errors.append("Wildfire burn severity analysis requires comparing pre-fire and post-fire imagery.")
                else:
                    errors.append(f"The requested task requires at least {min_images} satellite images, but only {available_inputs.image_count} is/are available.")

        # Check modalities sufficiency (e.g. MULTIMODAL requires OPTICAL and SAR)
        if req_modalities and available_inputs.modalities is not None:
            available_mods_upper = [m.upper() for m in available_inputs.modalities]
            missing_mods = [rm for rm in req_modalities if rm.upper() not in available_mods_upper]
            if missing_mods:
                errors.append(f"Multimodal analysis requires both OPTICAL and SAR imagery. Missing: {', '.join(missing_mods)}.")

        # 5. Determine result based on validation errors
        if errors:
            return "INSUFFICIENT", True, " ".join(errors)

        # Basic sufficiency is met
        # Standard warning/clarification for specific hazards if they have them but we have enough images
        if intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type:
            # Let's say inputs are sufficient but we can display the warning if needed,
            # or if image count is sufficient we don't necessarily NEED clarification,
            # but let's look at glacier GLOF again. If count is 2, it is SUFFICIENT and needs_clarification is False.
            pass

        return "SUFFICIENT", False, None
