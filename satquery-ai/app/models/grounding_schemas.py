from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GroundingSummary(BaseModel):
    major_regions: int = Field(..., description="Number of large significant regions detected")
    minor_regions: int = Field(..., description="Number of small valid regions detected")
    total_valid_regions: int = Field(..., description="Sum total of all valid regions detected after filtering")
    total_buildings_detected: Optional[int] = Field(default=None, description="Detailed count for building specialist output")

class GroundingDetection(BaseModel):
    id: int = Field(..., description="Unique identifier for the detection")
    label: str = Field(..., description="Target concept class label, e.g. water_body")
    importance: str = Field(default="minor_region", description="Region importance level: major_region or minor_region")
    location: str = Field(..., description="Image-relative location: northwest, center, southeast, etc.")
    visualization_type: str = Field(..., description="Visualization method used: segmentation_mask or bounding_box")
    bbox: Optional[List[int]] = Field(default=None, description="Bounding box coordinates in original image coordinates: [ymin, xmin, ymax, xmax]")
    relative_area: Optional[float] = Field(default=None, description="Proportion of the image area occupied by this region (0.0 to 1.0)")
    area_pixels: Optional[int] = Field(default=None, description="Area in pixels")

class AnnotatedImageBrief(BaseModel):
    generated: bool = Field(..., description="Indicates if an annotated output was successfully generated")
    url: Optional[str] = Field(None, description="Static relative path URL to the annotated output image, e.g. /outputs/annotated_request_id.png")
    path_or_url: Optional[str] = Field(None, description="Legacy field for path compatibility")

class GroundingResponse(BaseModel):
    request_id: str = Field(..., description="Unique request identification UUID")
    status: str = Field(..., description="Processing status: SUCCESS, NOT_FOUND, or ERROR")
    query: str = Field(..., description="The original user query text")
    analysis_type: str = Field(default="visual_grounding", description="Type of visual grounding analysis performed")
    target: str = Field(..., description="The target extracted concept from the query")
    specialist_used: Optional[str] = Field(None, description="Model specialist name if route matched")
    model_used: Optional[str] = Field(None, description="Specific HF identifier model used")
    execution_mode: Optional[str] = Field(None, description="Inference mode context")
    fallback_used: Optional[bool] = Field(None, description="Diagnostic flag indicating fallback status")
    processing_time_seconds: Optional[float] = Field(None, description="Total execution time in seconds")
    summary: Optional[GroundingSummary] = Field(default=None, description="Summary counts of segmented regions")
    detections: List[GroundingDetection] = Field(default_factory=list, description="List of all detected target regions")
    text_answer: str = Field(..., description="Natural language explanation of the grounding report")
    annotated_image: Optional[AnnotatedImageBrief] = Field(default=None, description="Details of the generated marked/annotated image")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Specialist model routing diagnostic metadata")
    limitations: List[str] = Field(default_factory=list, description="Listing of technical and spatial constraints")
