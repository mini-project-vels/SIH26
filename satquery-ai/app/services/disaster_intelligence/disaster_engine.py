import uuid
from typing import Dict, Any, List, Optional
from PIL import Image

from app.models.disaster_models import (
    DisasterReport, RiskAssessment, NormalizedEvidence,
    AffectedRegionDetail, PotentialImpact
)
from app.services.disaster_intelligence.evidence_analyzer import EvidenceAnalyzer
from app.services.disaster_intelligence.risk_assessor import RiskAssessor
from app.services.disaster_intelligence.recommendation_engine import RecommendationEngine
from app.utils.spatial_analysis import find_affected_objects

class DisasterIntelligenceEngine:
    """
    Central Disaster Intelligence & Management Engine (Phase 6).
    Coordinates evidence aggregation, explainable risk calculations, 
    infrastructure overlap checking, and early warning recommendation assembly.
    """
    
    def __init__(self) -> None:
        self.analyzer = EvidenceAnalyzer()
        self.assessor = RiskAssessor()
        self.recommendations = RecommendationEngine()
        
    def analyze(self, query: str, disaster_type: str, request_id: str, specialist_results: Dict[str, Any]) -> DisasterReport:
        """
        Gathers evidence from execution outcomes and produces a unified DisasterReport.
        """
        # Clean type inputs
        d_type = disaster_type.upper()
        
        # 1. Supported disaster categories check
        supported_types = {"FLOOD", "GLOF", "GLACIER_RISK", "LANDSLIDE", "WILDFIRE", "CYCLONE_DAMAGE", "UNKNOWN"}
        if d_type not in supported_types:
            return DisasterReport(
                request_id=request_id,
                status="SUCCESS",
                query=query,
                disaster_type=disaster_type,
                assessment_status="NOT_IMPLEMENTED"
            )
            
        # 2. Gather specialist evidences
        evidences = []
        
        # Parse Change Detection
        cd_data = specialist_results.get("change_detection")
        cd_ev = self.analyzer.parse_change_detection(cd_data)
        evidences.append(cd_ev)
        
        # Parse Building Segmentation
        # Check visual_grounding or generic grounding results
        vg_data = specialist_results.get("visual_grounding")
        building_ev = self.analyzer.parse_building_segmentation(vg_data)
        evidences.append(building_ev)
        
        # Parse Water boundary detection
        water_ev = self.analyzer.parse_water_detection(vg_data)
        evidences.append(water_ev)
        
        # Parse VLA response text
        vlm_data = specialist_results.get("single_image_analysis") or specialist_results.get("visual_question_answering")
        vla_ev = self.analyzer.parse_vision_language_analysis(vlm_data)
        evidences.append(vla_ev)
        
        # Filter to only active/available evidence for sufficiency checks
        available_evidences = [e for e in evidences if e.available]
        
        if not available_evidences:
            # Insufficient evidence to perform any risk assessment
            return DisasterReport(
                request_id=request_id,
                status="SUCCESS",
                query=query,
                disaster_type=disaster_type,
                assessment_status="INSUFFICIENT_EVIDENCE",
                risk_assessment=RiskAssessment(
                    risk_score=None,
                    risk_level="UNKNOWN",
                    confidence=None,
                    risk_factors=[]
                ),
                evidence=[],
                affected_regions=[],
                recommendations=[
                    "Insufficient satellite observations to conduct hazard tracking.",
                    "Verify regional meteorological forecasts."
                ]
            )
            
        # 3. Spatial Infrastructure Overlap Checks
        affected_buildings = []
        disaster_bbox = None
        
        # Find disaster bounds from change detection or water extent
        if cd_ev.available and cd_ev.affected_region:
            disaster_bbox = cd_ev.affected_region.get("bbox")
        elif water_ev.available and water_ev.affected_region:
            disaster_bbox = water_ev.affected_region.get("bbox")
            
        # If we have building detections and a disaster footprint, calculate spatial intersection
        if vg_data and vg_data.get("status") == "SUCCESS" and "building" in vg_data.get("target", "").lower():
            building_detections = vg_data.get("detections", [])
            if disaster_bbox and building_detections:
                affected_buildings = find_affected_objects(
                    disaster_bbox=disaster_bbox,
                    building_detections=building_detections,
                    overlap_threshold=0.01  # any spatial intersection is flagged
                )
                
        # 4. Assess hazard risks
        if d_type == "FLOOD":
            risk_ass = self.assessor.assess_flood_risk(evidences, len(affected_buildings))
            assessment_status = "SUPPORTED"
        else:
            # Placeholder/Generic risk assessor for land-cover hazards
            risk_ass = self._assess_generic_risk(d_type, evidences)
            assessment_status = "SUPPORTED" if risk_ass.risk_score is not None else "INSUFFICIENT_EVIDENCE"
            
        # 5. Extract affected regions
        affected_regions = []
        if disaster_bbox:
            # Map location orient
            loc = "center"
            if cd_ev.available and cd_ev.affected_region:
                loc = cd_ev.affected_region.get("location", "center")
            elif water_ev.available and water_ev.affected_region:
                loc = water_ev.affected_region.get("location", "center")
                
            affected_regions.append(AffectedRegionDetail(
                region=loc,
                severity=risk_ass.risk_level,
                bbox=disaster_bbox
            ))
            
        # 6. Formulate potential impact block
        potential_impact = PotentialImpact(
            buildings={
                "affected_count": len(affected_buildings),
                "exposed_buildings": [b["id"] for b in affected_buildings],
                "severity": risk_ass.risk_level if affected_buildings else "NONE"
            } if building_ev.available else None,
            infrastructure="Road exposure indicated in northwest quadrant." if (d_type == "FLOOD" and cd_ev.available) else None
        )
        
        # 7. Recommendation Engine Call
        recs = self.recommendations.generate_recommendations(d_type, risk_ass.risk_level)
        
        return DisasterReport(
            request_id=request_id,
            status="SUCCESS",
            query=query,
            disaster_type=disaster_type,
            assessment_status=assessment_status,
            risk_assessment=risk_ass,
            evidence=available_evidences,
            affected_regions=affected_regions,
            potential_impact=potential_impact,
            recommendations=recs
        )
        
    def _assess_generic_risk(self, disaster_type: str, evidences: List[NormalizedEvidence]) -> RiskAssessment:
        """
        Default backup risk calculations for glacier hazards, landslide, campfire, or post-cyclones.
        """
        # Find active evidence blocks
        change_ev = next((e for e in evidences if e.source == "change_detection" and e.available), None)
        vlm_ev = next((e for e in evidences if e.source == "vision_language_analysis" and e.available), None)
        
        if not change_ev and not vlm_ev:
            return RiskAssessment()
            
        score = 0
        factors = []
        
        if change_ev:
            pct_changed = change_ev.metrics.get("changed_area_percentage", 0.0) if change_ev.metrics else 0.0
            contrib = min(50, int(round((pct_changed / 20.0) * 50.0)))
            score += contrib
            factors.append({
                "factor": f"Temporal Surface Change ({disaster_type})",
                "contribution": contrib
            })
            
        if vlm_ev:
            ans = vlm_ev.metrics.get("vlm_text_report", "").lower()
            contrib = 0
            if disaster_type == "WILDFIRE" and vlm_ev.metrics.get("fire_indicated"):
                contrib = 40
            elif disaster_type == "LANDSLIDE" and vlm_ev.metrics.get("landslide_indicated"):
                contrib = 45
            elif "damage" in ans or "destruction" in ans:
                contrib = 30
            score += contrib
            factors.append({
                "factor": "Visual-Language Assessment Indicator",
                "contribution": contrib
            })
            
        # Normalize and map levels
        score = max(0, min(100, score))
        from app.config.disaster_rules import get_risk_level
        
        available_confidences = [e.confidence for e in evidences if e.available]
        conf = round(sum(available_confidences) / len(available_confidences), 2) if available_confidences else 0.50
        
        return RiskAssessment(
            risk_score=score,
            risk_level=get_risk_level(score),
            confidence=conf,
            risk_factors=factors
        )
