from typing import Optional
from app.models.schemas import QueryAnalysisResponse
from app.config.intents import Intents, HazardTypes, INTENT_CONFIGS, HAZARD_CONFIGS

class TaskBuilder:
    """
    Combines the classification results and input validation to construct
    the final structured Task Description (QueryAnalysisResponse).
    """

    def build(
        self,
        query: str,
        intent: str,
        confidence: float,
        hazard_type: Optional[str],
        input_sufficiency: str,
        needs_clarification: bool,
        clarification_message: Optional[str]
    ) -> QueryAnalysisResponse:
        """
        Builds a QueryAnalysisResponse Pydantic model by merging intent configs,
        hazard specifics, and validation results.
        """
        # Start with default intent config
        config = INTENT_CONFIGS.get(intent, INTENT_CONFIGS[Intents.UNKNOWN])
        
        analysis_type = config["analysis_type"]
        required_capabilities = list(config["required_capabilities"])
        required_inputs = list(config["required_inputs"])

        # If it is a disaster hazard query with a recognized hazard type, override/extend properties
        if intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type:
            h_config = HAZARD_CONFIGS.get(hazard_type, HAZARD_CONFIGS[HazardTypes.UNKNOWN])
            analysis_type = h_config["analysis_type"]
            required_capabilities = list(h_config["required_capabilities"])
            required_inputs = list(h_config["required_inputs"])

        # If needs_clarification is True, the clarification message should be set.
        # If it is not set, we can provide a default message.
        if needs_clarification and not clarification_message:
            if intent == Intents.UNKNOWN:
                clarification_message = (
                    "I could not understand your request. Please specify a remote sensing task such as "
                    "single image analysis, change detection, visual question answering, or hazard assessment."
                )
            else:
                clarification_message = "Additional inputs or information are required to perform this analysis."

        requires_flood = False
        if intent == Intents.DISASTER_HAZARD_ANALYSIS and hazard_type in (HazardTypes.FLOOD, "flood"):
            requires_flood = True

        return QueryAnalysisResponse(
            query=query,
            intent=intent,
            confidence=round(confidence, 2),
            analysis_type=analysis_type,
            required_capabilities=required_capabilities,
            required_inputs=required_inputs,
            hazard_type=hazard_type if intent == Intents.DISASTER_HAZARD_ANALYSIS else None,
            input_sufficiency=input_sufficiency,
            needs_clarification=needs_clarification,
            clarification_message=clarification_message,
            requires_flood_analysis=requires_flood
        )
