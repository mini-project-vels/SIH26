import uuid
from typing import Any, Optional
from app.services.vision_prompt_builder import VisionPromptBuilder
from app.services.huggingface_vision_service import HuggingFaceVisionService
from app.models.vision_schemas import SingleImageAnalysisResponse, VisionModelInfo, VisionAnalysisResult
from app.config import vision_config


STANDARD_LIMITATIONS = [
    "The response is based on visual interpretation of the provided image.",
    "This result should not be treated as a precise scientific remote sensing measurement.",
    "SatQuery AI may not detect fine-grained features at low image resolution.",
]


class SingleImageAnalysisAgent:
    """
    Phase 4 Specialist Agent: Vision-Language analysis of a single satellite image.
    
    Responsibilities:
    - Validate image and user query.
    - Build a remote sensing-specific prompt using VisionPromptBuilder.
    - Delegate API communication to HuggingFaceVisionService.
    - Return a structured, limitations-aware result.
    """

    def __init__(
        self,
        prompt_builder: Optional[VisionPromptBuilder] = None,
        vision_service: Optional[HuggingFaceVisionService] = None
    ) -> None:
        self.prompt_builder = prompt_builder or VisionPromptBuilder()
        self.vision_service = vision_service or HuggingFaceVisionService()

    def execute(
        self,
        image: Any,
        query: str
    ) -> SingleImageAnalysisResponse:
        """
        Runs the vision-language analysis pipeline.
        
        Args:
            image: FastAPI UploadFile, (filename, bytes) tuple, or file path string.
            query: The natural-language question asked by the user.
            
        Returns:
            SingleImageAnalysisResponse
        """
        request_id = str(uuid.uuid4())

        # --- Input Validation ---
        if image is None:
            return SingleImageAnalysisResponse(
                request_id=request_id,
                status="NEEDS_INPUT",
                query=query,
                message="A satellite image is required for single image analysis.",
                limitations=None
            )

        if not query or not query.strip():
            return SingleImageAnalysisResponse(
                request_id=request_id,
                status="NEEDS_INPUT",
                query=query,
                message="A natural language question is required.",
                limitations=None
            )

        # --- Build Remote Sensing Prompt ---
        prompt = self.prompt_builder.build_prompt(query.strip())

        # --- Call Vision Service ---
        try:
            answer = self.vision_service.analyze_image(image=image, prompt=prompt)
        except ValueError as ve:
            return SingleImageAnalysisResponse(
                request_id=request_id,
                status="ERROR",
                query=query,
                message=str(ve),
                limitations=None
            )
        except RuntimeError as re:
            return SingleImageAnalysisResponse(
                request_id=request_id,
                status="ERROR",
                query=query,
                message=str(re),
                limitations=None
            )

        # --- Return Structured Result ---
        return SingleImageAnalysisResponse(
            request_id=request_id,
            status="SUCCESS",
            query=query,
            analysis_type="single_image_analysis",
            model=VisionModelInfo(
                provider="huggingface",
                model_name=vision_config.HF_VISION_MODEL
            ),
            result=VisionAnalysisResult(answer=answer),
            limitations=STANDARD_LIMITATIONS
        )
