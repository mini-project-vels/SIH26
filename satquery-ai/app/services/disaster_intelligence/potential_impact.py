from typing import Dict, Any, List

class PotentialImpactAnalyzer:
    """
    Combines only real evidence from multiple specialists to determine
    infrastructure exposure safely without falsely claiming absolute outcomes.
    """
    
    def analyze(self, disaster_report: Dict[str, Any]) -> Dict[str, Any]:
        specialist_results = disaster_report.get("specialist_results", {})
        query = disaster_report.get("query", "").lower()
        
        exposure = []
        
        # Pull data checks
        has_water = "water_detection" in specialist_results or "flood" in disaster_report.get("disaster_type", "").lower()
        has_glacier_retreat = "glacier_risk" in disaster_report.get("disaster_type", "").lower()
        
        vg_data = specialist_results.get("visual_grounding", {})
        has_buildings = vg_data.get("status") == "SUCCESS" and "building" in vg_data.get("target", "").lower()
        
        if has_water and has_buildings:
            exposure.append("Potential infrastructure exposure detected near the identified flooded/water-affected region.")
        elif has_glacier_retreat and has_buildings:
            exposure.append("Potential infrastructure exposure indicated near glacial retreat perimeters.")
        elif has_buildings:
            exposure.append("Infrastructure (buildings/roads) visually detected in the analyzed framework.")
            
        return {
            "infrastructure_exposure": exposure,
            "impact_detected": len(exposure) > 0 or has_water or has_glacier_retreat
        }
