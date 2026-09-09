from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SignificantRegion(BaseModel):
    region_id: int
    bounding_box: List[float]  # [min_y, min_x, max_y, max_x]
    area_pixels: int
    change_percentage: float
    confidence: float
    methods_detected: List[str]

class ChangeDetectionResponse(BaseModel):
    request_id: str
    status: str
    analysis_type: str = "automated_change_detection"
    change_detected: bool
    overall_change_percentage: float
    change_intensity: str
    significant_regions: List[SignificantRegion]
    visualizations: Dict[str, str]
    ready_for_disaster_analysis: bool

class ChangeAnalysisRequest(BaseModel):
    before_image_path: str
    after_image_path: str
    analysis_target: str = "general"
    satellite_type: Optional[str] = None
    bounding_box: Optional[List[float]] = None
