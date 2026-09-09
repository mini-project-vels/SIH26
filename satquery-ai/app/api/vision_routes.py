from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.agents.single_image_analysis_agent import SingleImageAnalysisAgent
from app.models.vision_schemas import SingleImageAnalysisResponse

router = APIRouter()
_agent = SingleImageAnalysisAgent()


@router.post(
    "/analyze-image",
    response_model=SingleImageAnalysisResponse,
    summary="Single Image Vision-Language Analysis",
    description=(
        "Accepts one satellite image and a natural language question via multipart form. "
        "Routes the request to the Single Image Analysis Agent, which builds a remote "
        "sensing-specific prompt and queries the Hugging Face Qwen2.5-VL vision model."
    )
)
def analyze_image(
    query: str = Form(
        ...,
        description="Natural language question about the satellite image (e.g. 'What can you see in this satellite image?')"
    ),
    image: UploadFile = File(
        ...,
        description="Satellite or remote sensing image file (PNG, JPG, JPEG, WEBP)"
    )
) -> SingleImageAnalysisResponse:
    """
    POST /analyze-image

    Accepts:
        - query: Natural language question.
        - image: Satellite image file.

    Returns:
        SingleImageAnalysisResponse with AI-generated answer.
    """
    try:
        return _agent.execute(image=image, query=query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Vision analysis system error: {str(e)}"
        )
