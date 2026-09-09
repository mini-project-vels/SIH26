from typing import Optional
from app.models.schemas import AvailableInputs, QueryAnalysisResponse
from app.services.classifier_interface import QueryClassifierInterface
from app.services.rule_based_classifier import RuleBasedClassifier
from app.services.input_validator import InputValidator
from app.services.task_builder import TaskBuilder

class QueryUnderstandingAgent:
    """
    Query Understanding Agent that acts as the initial entry stage of the SatQuery AI system.
    Its job is to understand the query, classify intent, validate input sufficiency,
    and generate a structured task description without executing the analysis.
    """

    def __init__(
        self,
        classifier: Optional[QueryClassifierInterface] = None,
        validator: Optional[InputValidator] = None,
        builder: Optional[TaskBuilder] = None
    ) -> None:
        # Dependency injection / default instances
        self.classifier = classifier or RuleBasedClassifier()
        self.validator = validator or InputValidator()
        self.builder = builder or TaskBuilder()

    def analyze(
        self, 
        query: str, 
        available_inputs: Optional[AvailableInputs] = None
    ) -> QueryAnalysisResponse:
        """
        Coordinates the staging flow:
        1. Classify the user query (intent, confidence, hazard type).
        2. Validate input sufficiency using metadata.
        3. Build and return the structured task description.
        
        Args:
            query (str): User's natural language request.
            available_inputs (Optional[AvailableInputs]): Metadata detailing inputs available.
            
        Returns:
            QueryAnalysisResponse: Structured Task Description.
        """
        # Step 1: Classify intent and hazard
        intent, confidence, hazard_type = self.classifier.classify(query)

        # Step 2: Validate available inputs against required inputs
        input_sufficiency, needs_clarification, clarification_message = self.validator.validate(
            intent=intent,
            hazard_type=hazard_type,
            available_inputs=available_inputs
        )

        # Step 3: Build structured response
        response = self.builder.build(
            query=query,
            intent=intent,
            confidence=confidence,
            hazard_type=hazard_type,
            input_sufficiency=input_sufficiency,
            needs_clarification=needs_clarification,
            clarification_message=clarification_message
        )

        return response
