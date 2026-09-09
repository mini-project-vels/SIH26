from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RiskAssessment(BaseModel):
    risk_score: Optional[int] = Field(default=None, description="Calculated risk score between 0 and 100")
    risk_level: str = Field(default="UNKNOWN", description="LOW, MODERATE, ELEVATED, HIGH, CRITICAL, or UNKNOWN")
    confidence: Optional[float] = Field(default=None, description="System confidence in this risk score (0.0 to 1.0)")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Factored contributions to the risk score")

class NormalizedEvidence(BaseModel):
    source: str = Field(..., description="The specialist module providing the evidence (e.g. change_detection, building_segmentation, etc.)")
    evidence_type: str = Field(..., description="The type of observations: surface_change, building_detection, etc.")
    available: bool = Field(default=True, description="Whether this specialist's analysis was successful and is present")
    confidence: float = Field(default=1.0, description="The confidence score of this specialist's observation")
    affected_region: Optional[Dict[str, Any]] = Field(default=None, description="Metadata location and bounding box")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Associated numerical metrics (pixel counts, percentages, etc.)")

class AffectedRegionDetail(BaseModel):
    region: Optional[str] = Field(default=None, description="Relative orientation (e.g. northwest, center)")
    severity: str = Field(..., description="LOW, MODERATE, ELEVATED, HIGH, or CRITICAL")
    bbox: Optional[List[int]] = Field(default=None, description="Bounding box of the affected region")
    region_id: Optional[int] = Field(default=None, description="ID of region under flood specialist")
    location: Optional[str] = Field(default=None, description="Location text mapping flood zones")
    water_overlap_percentage: Optional[float] = Field(default=None, description="Overlap with water body percent")

class PotentialImpact(BaseModel):
    buildings: Optional[Dict[str, Any]] = Field(default=None, description="Details on building count and structural exposure")
    infrastructure: Optional[str] = Field(default=None, description="Details on non-building infrastructure exposure (roads, bridges, etc.)")
    potentially_affected_buildings: Optional[int] = Field(default=None, description="Number of potentially affected buildings")
    infrastructure_analysis: Optional[str] = Field(default=None, description="Non-building infrastructure analysis string status")

class DisasterReport(BaseModel):
    request_id: str = Field(..., description="Unique report ID")
    status: str = Field(default="SUCCESS", description="SUCCESS, NOT_FOUND, or ERROR")
    query: str = Field(..., description="Original user query input")
    analysis_type: str = Field(default="disaster_analysis", description="The analysis mode descriptor")
    disaster_type: str = Field(..., description="FLOOD, GLOF, GLACIER_RISK, LANDSLIDE, WILDFIRE, CYCLONE_DAMAGE, or UNKNOWN")
    assessment_status: str = Field(..., description="SUPPORTED, INSUFFICIENT_EVIDENCE, NOT_IMPLEMENTED, COMPLETED, or UNKNOWN")
    
    # Generic reporting fields
    risk_assessment: Optional[RiskAssessment] = Field(default_factory=RiskAssessment, description="Calculated risk metrics and factor breakdown")
    evidence: List[NormalizedEvidence] = Field(default_factory=list, description="All collected specialist observation evidences")
    affected_regions: List[Any] = Field(default_factory=list, description="Locations and bounds of impacted zones")
    potential_impact: Optional[Any] = Field(default=None, description="Evaluation of exposed elements")
    recommendations: List[str] = Field(default_factory=list, description="Response management guidance steps")
    
    # Flood-specific extension fields (Phase 7)
    flood_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Flood scoring results mapping Phase 7")
    water_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Water segmentation metrics summary")
    risk_factors: Optional[List[Dict[str, Any]]] = Field(default=None, description="Factors of flood evidence score")
    annotated_image: Optional[Dict[str, Any]] = Field(default=None, description="Result pathway detail mapping annotation PNG")
    potentially_affected_buildings_detail: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed list of affected buildings with overlap metrics")
    
    # Glacier-specific extension fields (Phase 8)
    glacier_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Glacier detection metrics")
    change_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Glacier change detection metrics")
    glacial_lake_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Glacial lake parameters")

    limitations: List[str] = Field(
        default_factory=lambda: [
            "Assessment is based on available satellite imagery.",
            "Satellite evidence alone may not confirm disasters.",
            "Ground verification may be required."
        ],
        description="Systems disclaimer list"
    )

