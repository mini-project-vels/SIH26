from pydantic import BaseModel, Field
from typing import List, Optional
from app.config.intents import Intents, HazardTypes

class AvailableInputs(BaseModel):
    image_count: Optional[int] = Field(
        default=None, 
        description="The number of satellite images available for analysis"
    )
    modalities: Optional[List[str]] = Field(
        default=None, 
        description="The modalities of available images, e.g. ['OPTICAL', 'SAR']"
    )
    has_metadata: Optional[bool] = Field(
        default=None, 
        description="Indicates if geospatial/metadata is available"
    )

class QueryRequest(BaseModel):
    query: str = Field(
        ..., 
        description="The natural language query describing the remote sensing request"
    )
    available_inputs: Optional[AvailableInputs] = Field(
        default=None, 
        description="Optional metadata about inputs currently available to the system"
    )

class QueryAnalysisResponse(BaseModel):
    query: str = Field(
        ...,
        description="The original user query"
    )
    intent: str = Field(
        ..., 
        description="The classified intent, e.g. CHANGE_DETECTION, DISASTER_HAZARD_ANALYSIS"
    )
    confidence: float = Field(
        ..., 
        description="The confidence score of the classification (between 0.0 and 1.0)"
    )
    analysis_type: str = Field(
        ..., 
        description="The type of remote sensing analysis required (e.g. single_temporal, multi_temporal, hazard_monitoring)"
    )
    required_capabilities: List[str] = Field(
        ..., 
        description="List of specific functional capabilities required to solve the query"
    )
    required_inputs: List[str] = Field(
        ..., 
        description="List of data source inputs required to perform the analysis"
    )
    hazard_type: Optional[str] = Field(
        default=None, 
        description="The identified disaster/hazard type if intent is DISASTER_HAZARD_ANALYSIS"
    )
    input_sufficiency: str = Field(
        ..., 
        description="Validation status of available inputs: SUFFICIENT, INSUFFICIENT, UNKNOWN"
    )
    needs_clarification: bool = Field(
        ..., 
        description="True if the query is ambiguous, missing parameters, or missing resources"
    )
    clarification_message: Optional[str] = Field(
        default=None, 
        description="A helpful feedback message requesting specific details if needs_clarification is True"
    )
    requires_flood_analysis: Optional[bool] = Field(
        default=None,
        description="True if the query requires dedicated flood detection analysis"
    )
