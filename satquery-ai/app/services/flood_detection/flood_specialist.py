import uuid
from typing import Dict, Any, Optional

from app.services.flood_detection.water_analyzer import WaterAnalyzer
from app.services.flood_detection.flood_evidence import FloodEvidenceCollector
from app.services.flood_detection.flood_risk import FloodRiskCalculator
from app.services.flood_detection.flood_visualizer import FloodVisualizer

class FloodSpecialist:
    """
    Coordinates flood detection and risk assessment under Phase 7.
    """
    def __init__(
        self,
        water_analyzer: Optional[WaterAnalyzer] = None,
        evidence_collector: Optional[FloodEvidenceCollector] = None,
        risk_calculator: Optional[FloodRiskCalculator] = None,
        visualizer: Optional[FloodVisualizer] = None
    ) -> None:
        self.water_analyzer = water_analyzer or WaterAnalyzer()
        self.evidence_collector = evidence_collector or FloodEvidenceCollector(water_analyzer=self.water_analyzer)
        self.risk_calculator = risk_calculator or FloodRiskCalculator()
        self.visualizer = visualizer or FloodVisualizer()

    def execute(
        self,
        image: Any,
        before_image: Optional[Any] = None,
        after_image: Optional[Any] = None,
        query: str = "",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main execution workflow logic for single or dual image flood analysis.
        """
        req_id = request_id or str(uuid.uuid4())[:8]
        
        # 1. Collect all evidence metrics recursively
        evidence = self.evidence_collector.collect_evidence(
            image=image,
            before_image=before_image,
            after_image=after_image,
            query=query,
            request_id=req_id
        )
        
        # Determine targeting source image for visualization
        target_img = after_image if after_image is not None else image
        
        # 2. Compute risk score and category
        risk_report = self.risk_calculator.calculate_risk(evidence)
        risk_score = risk_report["risk_score"]
        risk_level = risk_report["risk_level"]
        risk_factors = risk_report["risk_factors"]
        confidence = risk_report["confidence"]
        
        # 3. Create annotation overlay visual
        annotated_path = None
        if target_img is not None and evidence.get("water_analysis", {}).get("water_detected", False):
            try:
                annotated_path = self.visualizer.draw_visualization(target_img, evidence, req_id)
            except Exception:
                pass
                
        # 4. Generate recommendations based on risk classification levels
        recommendations = []
        if risk_level == "LOW":
            recommendations.extend([
                "Continue routine atmospheric and satellite observations.",
                "Monitor low-lying areas during high-precipitation periods."
            ])
        elif risk_level == "MODERATE":
            recommendations.extend([
                "Initiate regular monitoring of low-lying terrain and water bodies.",
                "Verify local emergency communication channels are active."
            ])
        else: # ELEVATED, HIGH, CRITICAL
            recommendations.extend([
                "Continue satellite monitoring.",
                "Recommend authorities verify conditions on the ground.",
                "Assess potentially affected infrastructure.",
                "Increase monitoring frequency for high-risk regions."
            ])
            
        # Determine water expansion flags (from new comparison structure)
        water_expansion_detected = False
        water_expansion_pct = 0.0
        before_water_pct = 0.0
        after_water_pct = 0.0
        
        water_comparison = evidence.get("water_comparison") or {}
        if water_comparison:
            water_expansion_pct = water_comparison.get("water_expansion_percentage", 0.0)
            water_expansion_detected = water_expansion_pct > 0.0
            before_water_pct = water_comparison.get("previous_water_percentage", 0.0)
            after_water_pct = water_comparison.get("current_water_percentage", 0.0)

        water_analysis_obj = evidence.get("water_analysis", {})
        water_analysis_summarized = {
            "water_detected": water_analysis_obj.get("water_detected", False),
            "water_expansion_detected": water_expansion_detected,
            "water_expansion_percentage": water_expansion_pct,
            "before_water_percentage": before_water_pct,
            "after_water_percentage": after_water_pct,
            "total_water_area_pixels": water_analysis_obj.get("total_water_area_pixels", 0),
            "total_water_percentage": water_analysis_obj.get("total_water_percentage", 0.0),
            "mask_path": water_analysis_obj.get("mask_path"),
            "expansion_mask_path": water_comparison.get("water_expansion_mask_path")
        }
        
        # Formulate output structure exactly corresponding to Step 15 requirements
        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "query": query,
            "analysis_type": "disaster_analysis",
            "disaster_type": "flood",
            "assessment_status": "COMPLETED",
            "flood_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence": confidence
            },
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence": confidence,
                "risk_factors": risk_factors
            },
            "evidence": [
                {
                    "source": "water_segmentation",
                    "evidence_type": "water_detection",
                    "available": evidence.get("water_analysis", {}).get("water_detected", False),
                    "confidence": 0.92,
                    "metrics": {
                        "total_water_area_pixels": evidence.get("water_analysis", {}).get("total_water_area_pixels", 0),
                        "total_water_percentage": evidence.get("water_analysis", {}).get("total_water_percentage", 0.0)
                    }
                }
            ],
            "water_analysis": water_analysis_summarized,
            "affected_regions": evidence.get("affected_regions", []),
            "potential_impact": {
                "potentially_affected_buildings": len(evidence.get("potentially_affected_buildings", [])),
                "infrastructure_analysis": evidence.get("infrastructure_analysis", "NOT_AVAILABLE")
            },
            "potentially_affected_buildings_detail": evidence.get("potentially_affected_buildings", []),
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "annotated_image": {
                "generated": annotated_path is not None,
                "path_or_url": annotated_path
            },
            "limitations": [
                "Assessment is based on available satellite imagery.",
                "Satellite evidence alone may not confirm flooding.",
                "Ground verification may be required."
            ]
        }
