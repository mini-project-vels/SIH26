from typing import Dict, Any, List

class EarlyWarningEngine:
    """
    Generates operational warning thresholds based on unified risk scores.
    """
    
    def generate_warning(self, risk_score: int, risk_level: str) -> Dict[str, Any]:
        """
        GREEN: 0-25
        YELLOW: 26-50
        ORANGE: 51-75
        RED: 76-100
        """
        if risk_score <= 25:
            return {
                "warning_level": "GREEN",
                "headline": "Normal Status Detected",
                "actions": ["Continue routine monitoring."]
            }
        elif risk_score <= 50:
            return {
                "warning_level": "YELLOW",
                "headline": "Moderate Hazard Indicator Detected",
                "actions": ["Increase monitoring frequency to daily sweeps."]
            }
        elif risk_score <= 75:
            return {
                "warning_level": "ORANGE",
                "headline": "Potential High-Risk Anomaly Detected",
                "actions": [
                    "Detailed assessment recommended.",
                    "Relevant authorities should review the situation.",
                    "Evacuation assessment may be required."
                ]
            }
        else:
            return {
                "warning_level": "RED",
                "headline": "Critical Emergency Status Indicated",
                "actions": [
                    "Immediate expert assessment and emergency preparedness actions are recommended.",
                    "Authorities should evaluate evacuation requirements."
                ]
            }
