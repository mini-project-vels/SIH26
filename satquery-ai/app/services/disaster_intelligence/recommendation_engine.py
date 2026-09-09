from typing import List
from app.config.disaster_rules import DEFAULT_RECOMMENDATIONS

class RecommendationEngine:
    """
    Decides response management recommendations depending on hazard category,
    severity level, and available observations.
    """
    
    def generate_recommendations(self, disaster_type: str, risk_level: str) -> List[str]:
        """
        Retrieves appropriate warning actions from config rules and builds advice logs.
        """
        # Clean type inputs
        d_type = disaster_type.upper()
        r_level = risk_level.upper()
        
        # Check if disaster is supported
        if d_type not in DEFAULT_RECOMMENDATIONS:
            return [
                "Recommend local authorities establish routine hazard observation grids.",
                "Verify ground condition reports to identify potential regional activity."
            ]
            
        rules = DEFAULT_RECOMMENDATIONS[d_type]
        
        # If specific risk level recommendations are found
        if r_level in rules:
            return list(rules[r_level])
            
        # Match GENERIC fallback actions if specific risk level mapping is missing
        if "GENERIC" in rules:
            return list(rules["GENERIC"])
            
        return [
            "Satellite observations provide auxiliary intelligence; verify conditions via local weather reports.",
            "Recommend local response agencies assess emergency communication readiness."
        ]
