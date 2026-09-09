from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PotentialImpactDetail(BaseModel):
    impact_detected: bool = Field(False)
    affected_regions: List[str] = Field(default_factory=list)
    infrastructure_exposure: List[str] = Field(default_factory=list)
    downstream_analysis_available: bool = Field(False)

class EarlyWarningReport(BaseModel):
    warning_id: str
    warning_level: str = Field(..., description="GREEN, YELLOW, ORANGE, or RED")
    disaster_type: str
    risk_score: int
    confidence: float
    headline: str
    detected_indicators: List[str] = Field(default_factory=list)
    potential_impact: PotentialImpactDetail
    recommended_actions: List[str] = Field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
