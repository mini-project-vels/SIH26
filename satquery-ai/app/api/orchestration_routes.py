from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
from app.services.orchestration_service import OrchestrationService
from app.models.orchestration_schemas import OrchestrateResponse

router = APIRouter()
orchestration_service = OrchestrationService()

@router.post(
    "/orchestrate", 
    response_model=OrchestrateResponse,
    summary="Orchestrate and Execute Remote-Sensing Tasks",
    description=(
        "Acts as the core orchestrator entrypoint. Receives user query and raw files via multipart form, "
        "resolves prerequisites, builds an execution plan, runs specialist agents, and returns consolidated results."
    )
)
def orchestrate(
    query: str = Form(
        ...,
        description="The natural language query describing the desired remote sensing analysis"
    ),
    image: Optional[UploadFile] = File(
        None,
        description="Optional single satellite image for vision-language analysis"
    ),
    before_image: Optional[UploadFile] = File(
        None,
        description="Optional satellite image representing the baseline/before state"
    ),
    after_image: Optional[UploadFile] = File(
        None,
        description="Optional satellite image representing the post/after state"
    )
) -> OrchestrateResponse:
    """
    Form-based endpoint that coordinates query understanding, execution planning,
    and specialist agent execution.
    """
    try:
        response = orchestration_service.orchestrate_request(
            query=query,
            image=image if image and image.filename else None,
            before_image=before_image if before_image and before_image.filename else None,
            after_image=after_image if after_image and after_image.filename else None
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Orchestration system error: {str(e)}"
        )

