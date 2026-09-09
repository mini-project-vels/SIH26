from typing import Dict, Any, List

class FloodRiskCalculator:
    """
    Step 8 & 9: Transparent evidence scoring system and flood classification.
    """
    WATER_EXPANSION_WEIGHT = 30
    CHANGE_DETECTION_WEIGHT = 20
    BUILDING_IMPACT_WEIGHT = 25
    VLM_EVIDENCE_WEIGHT = 15
    ADDITIONAL_EVIDENCE_WEIGHT = 10

    def calculate_risk(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        risk_factors = []
        score = 0.0
        
        water_analysis = evidence.get("water_analysis", {})
        water_detected = water_analysis.get("water_detected", False)
        total_water_pct = water_analysis.get("total_water_percentage", 0.0)
        
        # If no water is detected at all, risk is near zero
        if not water_detected:
            return {
                "risk_score": 0,
                "risk_level": "LOW",
                "confidence": 0.95,
                "risk_factors": []
            }

        # 1. Water Expansion (Weight: 30)
        comparison = evidence.get("water_comparison")
        if comparison:
            expansion_pct = comparison.get("water_expansion_percentage", 0.0)
            if expansion_pct >= 50.0:
                contrib = 30
                risk_factors.append({
                    "factor": "Severe water body expansion detected (>= 50%)",
                    "contribution": contrib,
                    "evidence_confidence": 0.95
                })
                score += contrib
            elif expansion_pct >= 15.0:
                contrib = 20
                risk_factors.append({
                    "factor": "Moderate water expansion detected (>= 15%)",
                    "contribution": contrib,
                    "evidence_confidence": 0.91
                })
                score += contrib
            elif expansion_pct > 0.0:
                contrib = 10
                risk_factors.append({
                    "factor": "Minor water expansion detected",
                    "contribution": contrib,
                    "evidence_confidence": 0.88
                })
                score += contrib
                
        # 2. Change Detection (Weight: 20)
        if comparison and comparison.get("water_expansion_percentage", 0.0) > 0.0:
            contrib = 20
            risk_factors.append({
                "factor": "Multi-temporal surface changes match water boundaries",
                "contribution": contrib,
                "evidence_confidence": 0.90
            })
            score += contrib

        # 3. Building Impact (Weight: 25)
        affected_buildings = evidence.get("potentially_affected_buildings", [])
        if affected_buildings:
            max_risk = max(b["risk"] for b in affected_buildings)
            if max_risk == "HIGH":
                contrib = 25
                risk_factors.append({
                    "factor": "Water overlaps with detected buildings (HIGH overlap)",
                    "contribution": contrib,
                    "evidence_confidence": 0.93
                })
                score += contrib
            elif max_risk == "MODERATE":
                contrib = 15
                risk_factors.append({
                    "factor": "Water overlaps with detected buildings (MODERATE overlap)",
                    "contribution": contrib,
                    "evidence_confidence": 0.89
                })
                score += contrib
            else:
                contrib = 10
                risk_factors.append({
                    "factor": "Water overlaps with detected buildings (LOW overlap)",
                    "contribution": contrib,
                    "evidence_confidence": 0.85
                })
                score += contrib

        # 4. VLM Evidence (Weight: 15)
        vlm_indicated = evidence.get("vlm_indicated", False)
        if vlm_indicated:
            contrib = 15
            risk_factors.append({
                "factor": "Vision Model indicates flooding or inundated land",
                "contribution": contrib,
                "evidence_confidence": 0.88
            })
            score += contrib

        # 5. Additional Evidence / Water area size (Weight: 10)
        if total_water_pct >= 5.0:
            contrib = 10
            risk_factors.append({
                "factor": "Significant portion of scene covered by water (>= 5%)",
                "contribution": contrib,
                "evidence_confidence": 0.92
            })
            score += contrib
        elif total_water_pct >= 1.0:
            contrib = 5
            risk_factors.append({
                "factor": "Notable water bodies present in scene",
                "contribution": contrib,
                "evidence_confidence": 0.88
            })
            score += contrib

        # Cap score
        final_score = int(min(100, max(0, score)))
        
        # Risk classification
        if final_score <= 20:
            level = "LOW"
        elif final_score <= 40:
            level = "MODERATE"
        elif final_score <= 60:
            level = "ELEVATED"
        elif final_score <= 80:
            level = "HIGH"
        else:
            level = "CRITICAL"
            
        # Determine confidence based on evidence availability
        confidence = 0.85
        if vlm_indicated and comparison:
            confidence = 0.93
        elif comparison:
            confidence = 0.90
            
        return {
            "risk_score": final_score,
            "risk_level": level,
            "confidence": confidence,
            "risk_factors": risk_factors
        }
