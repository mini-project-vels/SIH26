import uuid
from typing import Dict, Any, Optional

from app.services.glacier_detection.spectral_glacier_detector import SpectralGlacierDetector
from app.services.glacier_detection.glacier_risk import GlacierRiskCalculator
from app.services.glacier_detection.glacier_visualizer import GlacierVisualizer

class GlacierSpecialist:
    """
    Coordinates Glacier and Glacial Lake Outburst Flood (GLOF) detection.
    """
    def __init__(self):
        self.detector = SpectralGlacierDetector()
        self.risk_calc = GlacierRiskCalculator()
        self.visualizer = GlacierVisualizer()

    def execute(
        self,
        query: str,
        image: Optional[Any] = None,
        before_image: Optional[Any] = None,
        after_image: Optional[Any] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        
        req_id = request_id or str(uuid.uuid4())[:8]

        # 1. Detection
        evidence = {}
        target_img = after_image if after_image is not None else image
        
        if before_image is not None and after_image is not None:
            comparison = self.detector.compare_temporal(before_image, after_image, req_id)
            
            # Map full temporal data
            glacier = comparison["after_glacier"]
            glacier_change = comparison["glacier_change"]
            lake = comparison["after_lake"]
            lake_change = comparison["lake_change"]
            
            evidence["glacier_assessment"] = {
                "glacier_detected": glacier.get("glacier_detected", False),
                "confidence": 0.92,
                "glacier_area_pixels": glacier.get("total_glacier_area_pixels", 0),
                "glacier_percentage": glacier.get("total_glacier_percentage", 0.0),
                "glacier_mask_array": glacier.get("glacier_mask_array")
            }
            
            evidence["change_analysis"] = {
                "change_detected": glacier_change.get("change_detected", False),
                "change_type": glacier_change.get("change_type"),
                "estimated_change_percentage": glacier_change.get("estimated_change_percentage", 0.0),
                "confidence": 0.94 if glacier_change.get("change_detected", False) else 0.8,
                "lost_ice_mask_array": comparison["before_glacier"].get("glacier_mask_array")
                # Visualizer will compute diff later if needed
            }
            
            evidence["glacial_lake_analysis"] = {
                "lake_detected": lake.get("lake_detected", False),
                "lake_expansion_detected": lake_change.get("lake_expansion_detected", False),
                "estimated_expansion_percentage": lake_change.get("estimated_expansion_percentage", 0.0),
                "lake_mask_array": lake.get("lake_mask_array")
            }
            
            # Compute actual mask array for lost ice in visualizer
            bm = comparison["before_glacier"].get("glacier_mask_array")
            am = comparison["after_glacier"].get("glacier_mask_array")
            if bm is not None and am is not None:
                if bm.shape == am.shape:
                    evidence["change_analysis"]["lost_ice_mask_array"] = bm & ~am

        else:
             # Single image
             glacier = self.detector.detect_glacier(target_img, req_id, "single")
             lake = self.detector.detect_glacial_lake(target_img, req_id, "single")
             
             evidence["glacier_assessment"] = {
                 "glacier_detected": glacier.get("glacier_detected", False),
                 "confidence": 0.90,
                 "glacier_area_pixels": glacier.get("total_glacier_area_pixels", 0),
                 "glacier_percentage": glacier.get("total_glacier_percentage", 0.0),
                 "glacier_mask_array": glacier.get("glacier_mask_array")
             }
             evidence["change_analysis"] = {
                 "change_detected": False,
                 "change_type": None,
                 "estimated_change_percentage": 0.0,
                 "confidence": 0.0
             }
             evidence["glacial_lake_analysis"] = {
                 "lake_detected": lake.get("lake_detected", False),
                 "lake_expansion_detected": False,
                 "estimated_expansion_percentage": 0.0,
                 "lake_mask_array": lake.get("lake_mask_array")
             }

        # 2. Risk Calculation
        risk_report = self.risk_calc.calculate_risk(evidence)
        
        # 3. Visualization
        annotated_path = None
        if target_img is not None and (evidence["glacier_assessment"]["glacier_detected"] or evidence["glacial_lake_analysis"]["lake_detected"]):
            annotated_path = self.visualizer.draw_visualization(target_img, evidence, req_id)

        # 4. Packaging
        recs = [
            "Monitor glacial lake extent using satellite imagery.",
            "Assess potential downstream flood risk (GLOF)."
        ] if evidence["glacial_lake_analysis"]["lake_detected"] else ["Continue routine satellite monitoring of glacier."]

        # Clean mask arrays before returning JSON
        clean_evidence = dict(evidence)
        for k in ["glacier_assessment", "change_analysis", "glacial_lake_analysis"]:
             if k in clean_evidence:
                 clean_evidence[k] = {k2: v2 for k2, v2 in clean_evidence[k].items() if not k2.endswith("_array")}

        return {
          "request_id": req_id,
          "status": "SUCCESS",
          "query": query,
          "analysis_type": "glacier_analysis",
          "disaster_type": "GLACIER_RISK",
          "assessment_status": "COMPLETED",
          "evidence": [
             {
                 "source": "glacier_specialist",
                 "evidence_type": "spectral_analysis",
                 "available": True,
                 "confidence": risk_report.get("confidence", 0.9),
                 "metrics": {}
             }
          ],
          "glacier_assessment": clean_evidence["glacier_assessment"],
          "change_analysis": clean_evidence["change_analysis"],
          "glacial_lake_analysis": clean_evidence["glacial_lake_analysis"],
          "risk_assessment": risk_report,
          "affected_regions": [],
          "recommendations": recs,
          "annotated_image": {
            "generated": annotated_path is not None,
            "path_or_url": annotated_path
          },
          "limitations": [
             "Assessment based on spectral analysis of satellite imagery.",
             "Does not measure ice volume or thickness.",
             "Ground verification required for precise hazard modeling."
          ]
        }
