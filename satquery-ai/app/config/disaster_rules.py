import os

# --- Risk Assess Weights ---
CHANGE_WEIGHT = float(os.getenv("CHANGE_WEIGHT", "0.25"))
WATER_EXPANSION_WEIGHT = float(os.getenv("WATER_EXPANSION_WEIGHT", "0.35"))
INFRASTRUCTURE_WEIGHT = float(os.getenv("INFRASTRUCTURE_WEIGHT", "0.15"))
BUILDING_IMPACT_WEIGHT = float(os.getenv("BUILDING_IMPACT_WEIGHT", "0.15"))
VISION_EVIDENCE_WEIGHT = float(os.getenv("VISION_EVIDENCE_WEIGHT", "0.10"))

# Thresholds for severity levels
RISK_LEVEL_LOW = "LOW"
RISK_LEVEL_MODERATE = "MODERATE"
RISK_LEVEL_ELEVATED = "ELEVATED"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_CRITICAL = "CRITICAL"

def get_risk_level(score: int) -> str:
    if score <= 20:
        return RISK_LEVEL_LOW
    elif score <= 40:
        return RISK_LEVEL_MODERATE
    elif score <= 60:
        return RISK_LEVEL_ELEVATED
    elif score <= 80:
        return RISK_LEVEL_HIGH
    else:
        return RISK_LEVEL_CRITICAL

# Reusable disaster management system actions (decision support only)
DEFAULT_RECOMMENDATIONS = {
    "FLOOD": {
        "LOW": [
            "Continue routine atmospheric and satellite observations.",
            "Confirm regional drainage systems remain unblocked."
        ],
        "MODERATE": [
            "Initiate regular monitoring of low-lying terrain and water bodies.",
            "Verify local emergency communication channels are active."
        ],
        "ELEVATED": [
            "Alert regional disaster management focal points to monitoring status.",
            "Deploy localized sensors if ground verification shows surface trends.",
            "Inspect vulnerable drainage pathways and flood gates."
        ],
        "HIGH": [
            "Recommend authorities assess evacuation preparedness for low-lying settlements.",
            "Increase satellite observation query frequencies for the affected region.",
            "Coordinate with local emergency management agencies to review flood maps."
        ],
        "CRITICAL": [
            "Provide immediate decision-support information to regional response command.",
            "Identify likely safe routes and high-ground muster coordinates.",
            "Recommend emergency management leaders prepare immediate community alerts."
        ]
    },
    "GLACIER_RISK": {
        "GENERIC": [
            "Enhance multi-temporal satellite change analysis for glacier retreat rates.",
            "Map moraine stability thresholds via elevation contour references.",
            "Provide decision support maps to glaciological monitoring bodies."
        ]
    },
    "GLOF": {
        "GENERIC": [
            "Establish continuous radar monitoring over the target glacial lake.",
            "Map potential drainage path topography to identify exposed downstream communities.",
            "Recommend authorities inspect warning sirens and early detector systems."
        ]
    },
    "LANDSLIDE": {
        "GENERIC": [
            "Analyze slope indicators using multi-temporal sar coherence maps.",
            "Recommend weather bureaus track precipitation levels over steep terrains."
        ]
    },
    "WILDFIRE": {
        "GENERIC": [
            "Track moisture indexes and vegetative drying indices over forest regions.",
            "Identify nearby firebreak buffers and natural water access reservoirs."
        ]
    },
    "CYCLONE_DAMAGE": {
        "GENERIC": [
            "Deploy damage assessment specialists to parse structural damage scales.",
            "Coordinate imagery tasking schedules to capture cloud-free overlays."
        ]
    },
    "UNKNOWN": {
        "GENERIC": [
            "Monitor area using visual grounding specialists as queries flow.",
            "Recommend ground verification of suspicious visual anomalies."
        ]
    }
}
