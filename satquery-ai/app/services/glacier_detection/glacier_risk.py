"""
GlacierRiskCalculator — Glacial Lake Outburst Flood (GLOF) and glacier risk scoring.
"""

from typing import Dict, Any, List


class GlacierRiskCalculator:
    """
    Computes a disaster risk score (0-100) based on glacier changes and glacial lake expansion.
    """

    def calculate_risk(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        risk_factors = []
        score = 0.0

        glacier_analysis = evidence.get("glacier_assessment", {})
        change_analysis = evidence.get("change_analysis", {})
        lake_analysis = evidence.get("glacial_lake_analysis", {})

        # If no glacier is detected, risk is zero
        if not glacier_analysis.get("glacier_detected", False):
            return {
                "risk_score": 0,
                "risk_level": "LOW",
                "confidence": 0.95,
                "risk_factors": []
            }

        # 1. Glacial Lake Expansion (Highest Risk - potential GLOF)
        if lake_analysis.get("lake_expansion_detected", False):
            lake_exp_pct = lake_analysis.get("estimated_expansion_percentage", 0.0)
            if lake_exp_pct >= 30.0:
                contrib = 40
                risk_factors.append({
                    "factor": f"Severe glacial lake expansion detected ({lake_exp_pct}%) - High GLOF risk",
                    "contribution": contrib,
                    "evidence_confidence": 0.92
                })
                score += contrib
            elif lake_exp_pct >= 10.0:
                contrib = 25
                risk_factors.append({
                    "factor": "Moderate glacial lake expansion detected",
                    "contribution": contrib,
                    "evidence_confidence": 0.90
                })
                score += contrib
            elif lake_exp_pct > 0:
                contrib = 10
                risk_factors.append({
                    "factor": "Minor glacial lake growth observed",
                    "contribution": contrib,
                    "evidence_confidence": 0.85
                })
                score += contrib

        # 2. Glacier Retreat (Significant Ice Loss)
        if change_analysis.get("change_detected", False) and change_analysis.get("change_type") == "GLACIER_RETREAT":
            retreat_pct = change_analysis.get("estimated_change_percentage", 0.0)
            if retreat_pct >= 20.0:
                contrib = 25
                risk_factors.append({
                    "factor": f"Significant glacier retreat/ice loss detected ({retreat_pct}%)",
                    "contribution": contrib,
                    "evidence_confidence": 0.94
                })
                score += contrib
            elif retreat_pct >= 5.0:
                contrib = 15
                risk_factors.append({
                    "factor": "Moderate glacier retreat observed",
                    "contribution": contrib,
                    "evidence_confidence": 0.90
                })
                score += contrib

        # 3. New Glacial Lake Formation
        if lake_analysis.get("lake_detected", False) and lake_analysis.get("estimated_expansion_percentage", 0.0) == 100.0:
             contrib = 30
             risk_factors.append({
                 "factor": "New glacial lake formation detected",
                 "contribution": contrib,
                 "evidence_confidence": 0.90
             })
             score += contrib

        # Cap score
        final_score = int(min(100, max(0, score)))

        # Risk classification
        if final_score <= 25:
            level = "LOW"
        elif final_score <= 50:
            level = "MODERATE"
        elif final_score <= 75:
            level = "HIGH"
        else:
            level = "CRITICAL"

        # General confidence
        confidence = 0.88
        if evidence.get("change_analysis", {}).get("change_detected"):
            confidence = 0.93  # Higher confidence when temporal comparison exists

        return {
            "risk_score": final_score,
            "risk_level": level,
            "confidence": confidence,
            "risk_factors": risk_factors
        }
