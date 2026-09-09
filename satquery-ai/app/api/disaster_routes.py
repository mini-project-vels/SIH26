from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import uuid

from app.agents.disaster_agent import DisasterAgent
from app.agents.query_understanding_agent import QueryUnderstandingAgent
from app.models.disaster_models import DisasterReport
from app.models.schemas import AvailableInputs

router = APIRouter()
_disaster_agent = DisasterAgent()
_query_agent = QueryUnderstandingAgent()

@router.post(
    "/disaster-analysis",
    response_model=DisasterReport,
    summary="Analyze Satellite Image for Natural Disaster Risks",
    description=(
        "Performs comprehensive disaster threat assessments on satellite images. "
        "Integrates surface change metrics, building segmentation, and visual indications "
        "to output explainable risk scores, potential infrastructure impact boundaries, and response recommendations."
    )
)
def disaster_analysis(
    query: str = Form(
        ...,
        description="Disaster intelligence query (e.g., 'Is there a flood risk?', 'Check for wildfire damage.')"
    ),
    image: Optional[UploadFile] = File(
        None,
        description="Target satellite image for single temporal or high-res analysis"
    ),
    before_image: Optional[UploadFile] = File(
        None,
        description="Optional satellite image representing baseline state"
    ),
    after_image: Optional[UploadFile] = File(
        None,
        description="Optional satellite image representing post-disaster state"
    )
) -> DisasterReport:
    """
    POST /disaster-analysis
    
    Coordinates the Query Understanding Agent, AI Brain routing, and Disaster Intelligence calculations.
    """
    try:
        request_id = str(uuid.uuid4())
        
        # 1. Gather AvailableInputs metadata
        image_count = 0
        if image:
            image_count += 1
        if before_image:
            image_count += 1
        if after_image:
            image_count += 1
            
        available_metadata = None
        if image_count > 0:
            available_metadata = AvailableInputs(
                image_count=image_count,
                modalities=["OPTICAL"],
                has_metadata=True
            )
            
        # 2. Query Understanding classification
        task_desc = _query_agent.analyze(query, available_inputs=available_metadata)
        
        disaster_type = "UNKNOWN"
        if task_desc.intent == "DISASTER_HAZARD_ANALYSIS" and task_desc.hazard_type:
            disaster_type = task_desc.hazard_type
            
        # 3. Route to DisasterAgent
        report = _disaster_agent.execute(
            query=query,
            disaster_type=disaster_type,
            image=image,
            before_image=before_image,
            after_image=after_image,
            request_id=request_id
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Disaster Intelligence Engine execution failure: {str(e)}"
        )


@router.post(
    "/analyze/glacier",
    response_model=DisasterReport,
    summary="Analyze Satellite Image for Glacier & GLOF Risks",
    description="Dedicated endpoint for Glacier Detection & Glacier Risk Specialist."
)
def glacier_analysis_endpoint(
    query: str = Form(..., description="Query about glacier changes or GLOF"),
    image: Optional[UploadFile] = File(None, description="Single target image"),
    before_image: Optional[UploadFile] = File(None, description="Baseline image"),
    after_image: Optional[UploadFile] = File(None, description="Recent image")
) -> DisasterReport:
    """
    POST /analyze/glacier
    Directly delegates to the Glacier Specialist via the DisasterAgent pipeline.
    """
    try:
        request_id = str(uuid.uuid4())
        
        # We bypass query string analysis here since they've hit the explicit glacier endpoint,
        # but we use the common DisasterAgent entry point which will route to GlacierSpecialist.
        report = _disaster_agent.execute(
            query=query,
            disaster_type="GLACIER_RISK",
            image=image,
            before_image=before_image,
            after_image=after_image,
            request_id=request_id
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Glacier Specialist execution failure: {str(e)}"
        )
