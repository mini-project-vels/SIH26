from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class VisionModelInfo(BaseModel):
    provider: str = Field(..., description="Model provider (e.g. 'huggingface')")
    model_name: str = Field(..., description="Model identifier used for completion")


class VisionAnalysisResult(BaseModel):
    answer: str = Field(..., description="AI-generated descriptive analysis of the image")


class SingleImageAnalysisResponse(BaseModel):
    """
    Structured response for the /analyze-image endpoint.
    """
    request_id: Optional[str] = Field(None, description="Unique UUID for this request")
    status: str = Field(..., description="Request status: SUCCESS, NEEDS_INPUT, ERROR, etc.")
    query: Optional[str] = Field(None, description="The original user question")
    analysis_type: str = Field("single_image_analysis", description="Type of analysis performed")

    model: Optional[VisionModelInfo] = Field(None, description="Details about the vision model used")
    result: Optional[VisionAnalysisResult] = Field(None, description="Analysis result from the model")

    limitations: Optional[List[str]] = Field(None, description="Scientific limitations and disclaimers")
    message: Optional[str] = Field(None, description="Error or informational message")
