from typing import Dict, Any, List, Tuple
from app.models.disaster_models import RiskAssessment, NormalizedEvidence
from app.config.disaster_rules import (
    CHANGE_WEIGHT, WATER_EXPANSION_WEIGHT, INFRASTRUCTURE_WEIGHT,
    BUILDING_IMPACT_WEIGHT, VISION_EVIDENCE_WEIGHT,
    get_risk_level
)

class RiskAssessor:
    """
    Calculates numerical risk scores and provides mathematical explanations 
    based on available specialist evidence inputs.
    """
    
    def assess_flood_risk(self, evidences: List[NormalizedEvidence], affected_buildings_count: int) -> RiskAssessment:
        """
        Calculates explainable risk score specifically for FLOOD hazards.
        """
        # Find active evidence blocks
        change_ev = next((e for e in evidences if e.source == "change_detection" and e.available), None)
        water_ev = next((e for e in evidences if e.source == "water_detection" and e.available), None)
        building_ev = next((e for e in evidences if e.source == "building_segmentation" and e.available), None)
        vlm_ev = next((e for e in evidences if e.source == "vision_language_analysis" and e.available), None)
        
        active_weights_sum = 0.0
        weighted_score_sum = 0.0
        risk_factors = []
        
        # 1. Surface Change Severity
        if change_ev:
            active_weights_sum += CHANGE_WEIGHT
            pct_changed = change_ev.metrics.get("changed_area_percentage", 0.0) if change_ev.metrics else 0.0
            # Higher change ratio -> higher change score (capped at 100)
            change_score = min(100.0, (pct_changed / 15.0) * 100.0)
            weighted_score_sum += change_score * CHANGE_WEIGHT
            risk_factors.append({
                "factor": "Surface Change Severity",
                "score_value": change_score,
                "weight": CHANGE_WEIGHT
            })
            
        # 2. Water Expansion
        if water_ev:
            active_weights_sum += WATER_EXPANSION_WEIGHT
            water_pixels = water_ev.metrics.get("total_water_area_pixels", 0) if water_ev.metrics else 0
            # Larger water body detected -> higher water expansion index
            water_score = min(100.0, (water_pixels / 30000.0) * 100.0)
            weighted_score_sum += water_score * WATER_EXPANSION_WEIGHT
            risk_factors.append({
                "factor": "Water Expansion Index",
                "score_value": water_score,
                "weight": WATER_EXPANSION_WEIGHT
            })
            
        # 3. Affected Infrastructure (Spatial Overlap Zone)
        # We classify this if we have building evidence and we detected affected buildings
        if building_ev:
            active_weights_sum += INFRASTRUCTURE_WEIGHT
            infra_score = 0.0
            # If buildings are in the overlap / affected list
            if affected_buildings_count > 0:
                infra_score = min(100.0, 50.0 + (affected_buildings_count * 10.0))
            weighted_score_sum += infra_score * INFRASTRUCTURE_WEIGHT
            risk_factors.append({
                "factor": "Infrastructure Exposure",
                "score_value": infra_score,
                "weight": INFRASTRUCTURE_WEIGHT
            })
            
        # 4. Building Impact Severity
        if building_ev:
            active_weights_sum += BUILDING_IMPACT_WEIGHT
            building_count = building_ev.metrics.get("building_count", 0) if building_ev.metrics else 0
            building_score = min(100.0, (building_count / 12.0) * 100.0)
            weighted_score_sum += building_score * BUILDING_IMPACT_WEIGHT
            risk_factors.append({
                "factor": "Building Footprint Count Impact",
                "score_value": building_score,
                "weight": BUILDING_IMPACT_WEIGHT
            })
            
        # 5. Vision-Language Evidence
        if vlm_ev:
            active_weights_sum += VISION_EVIDENCE_WEIGHT
            vision_score = 0.0
            metrics = vlm_ev.metrics or {}
            if metrics.get("water_indicated"):
                vision_score = 90.0
            elif metrics.get("water_indicated") is False:
                vision_score = 10.0
            weighted_score_sum += vision_score * VISION_EVIDENCE_WEIGHT
            risk_factors.append({
                "factor": "Vision Model Analysis Indicators",
                "score_value": vision_score,
                "weight": VISION_EVIDENCE_WEIGHT
            })
            
        # Fallback if no evidence available
        if active_weights_sum == 0.0:
            return RiskAssessment(
                risk_score=0,
                risk_level="UNKNOWN",
                confidence=0.0,
                risk_factors=[]
            )
            
        # Calculate normalized risk score between 0 and 100
        final_score = int(round(weighted_score_sum / active_weights_sum))
        final_score = max(0, min(100, final_score))
        
        # Calculate exactly explainable factor contributions
        factor_contributions = []
        for factor in risk_factors:
            contribution = int(round((factor["score_value"] * factor["weight"]) / active_weights_sum))
            factor_contributions.append({
                "factor": factor["factor"],
                "contribution": contribution
            })
            
        # Resolve confidence (derived as average confidence of available inputs)
        available_confidences = [e.confidence for e in evidences if e.available]
        confidence = round(sum(available_confidences) / len(available_confidences), 2) if available_confidences else 0.50
        
        return RiskAssessment(
            risk_score=final_score,
            risk_level=get_risk_level(final_score),
            confidence=confidence,
            risk_factors=factor_contributions
        )
