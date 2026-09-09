from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.agents.visual_grounding_agent import VisualGroundingAgent
from app.models.grounding_schemas import GroundingResponse

router = APIRouter()
_grounding_agent = VisualGroundingAgent()

@router.post(
    "/locate-object",
    response_model=GroundingResponse,
    summary="Locate Target Objects in Satellite Image",
    description=(
        "Accepts a satellite image and a location query (e.g. 'Where are the water bodies?') via multipart form. "
        "Performs real color and geometry segmentation, extracts target boundaries, draws semi-transparent overlays "
        "with contour boundaries, and writes professional spatial explanations."
    )
)
def locate_object(
    query: str = Form(
        ...,
        description="Grounding question/command (e.g. 'Where is the water body?', 'Highlight the forest areas.')"
    ),
    image: UploadFile = File(
        ...,
        description="The target satellite image to analyze (PNG, JPG, JPEG, WEBP)"
    )
) -> GroundingResponse:
    """
    POST /locate-object
    
    Accepts:
        - query: Grounding command/question
        - image: Satellite image file
        
    Returns:
        GroundingResponse containing detections, explanation, and output image URL/path.
    """
    try:
        # Execute the agent
        response = _grounding_agent.execute(image=image, query=query)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Visual grounding system error: {str(e)}"
        )
