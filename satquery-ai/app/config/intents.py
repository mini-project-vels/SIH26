import re
from typing import List, Dict, Any, Optional

# Supported intents
class Intents:
    SINGLE_IMAGE_ANALYSIS = "SINGLE_IMAGE_ANALYSIS"
    VISUAL_QUESTION_ANSWERING = "VISUAL_QUESTION_ANSWERING"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    MULTIMODAL_ANALYSIS = "MULTIMODAL_ANALYSIS"
    REGION_GROUNDING = "REGION_GROUNDING"
    DISASTER_HAZARD_ANALYSIS = "DISASTER_HAZARD_ANALYSIS"
    UNKNOWN = "UNKNOWN"

# Supported hazard types (Updated for Phase 6 and backwards compatibility)
class HazardTypes:
    FLOOD = "FLOOD"
    GLACIER_GLOF = "GLACIER_GLOF"
    GLACIER_RISK = "GLACIER_RISK"
    GLOF = "GLOF"
    LANDSLIDE = "LANDSLIDE"
    WILDFIRE = "WILDFIRE"
    CYCLONE_DAMAGE = "CYCLONE_DAMAGE"
    UNKNOWN = "UNKNOWN"

# Intent Configuration Mapping (Updated DISASTER_HAZARD_ANALYSIS default confidence to override CHANGE_DETECTION on compound queries)
INTENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    Intents.SINGLE_IMAGE_ANALYSIS: {
        "analysis_type": "single_temporal",
        "required_capabilities": ["single_image_analysis"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.85
    },
    Intents.VISUAL_QUESTION_ANSWERING: {
        "analysis_type": "visual_qa",
        "required_capabilities": ["visual_question_answering"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.85
    },
    Intents.CHANGE_DETECTION: {
        "analysis_type": "multi_temporal",
        "required_capabilities": ["change_detection"],
        "required_inputs": ["satellite_image_before", "satellite_image_after"],
        "min_images": 2,
        "default_confidence": 0.95
    },
    Intents.MULTIMODAL_ANALYSIS: {
        "analysis_type": "multimodal_fusion",
        "required_capabilities": ["multimodal_analysis"],
        "required_inputs": ["optical_satellite_image", "sar_satellite_image"],
        "min_images": 2,
        "required_modalities": ["OPTICAL", "SAR"],
        "default_confidence": 0.90
    },
    Intents.REGION_GROUNDING: {
        "analysis_type": "spatial_grounding",
        "required_capabilities": ["visual_grounding", "image_annotation"],
        "required_inputs": ["image"],
        "min_images": 1,
        "default_confidence": 0.88
    },
    Intents.DISASTER_HAZARD_ANALYSIS: {
        "analysis_type": "disaster_analysis",
        "required_capabilities": ["disaster_hazard_analysis"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.98  # Make higher so it wins on compound query matching
    },
    Intents.UNKNOWN: {
        "analysis_type": "unknown",
        "required_capabilities": [],
        "required_inputs": [],
        "min_images": 0,
        "default_confidence": 0.50
    }
}

# Specific rules/capabilities/inputs for disaster analysis based on hazard type
HAZARD_CONFIGS: Dict[str, Dict[str, Any]] = {
    HazardTypes.FLOOD: {
        "analysis_type": "flood_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.98,
        "clarification_message": "Flood extent mapping can be enhanced if pre-flood and post-flood imagery are both provided."
    },
    HazardTypes.GLACIER_GLOF: {
        "analysis_type": "hazard_monitoring",
        "required_capabilities": ["change_detection", "surface_analysis", "hazard_assessment"],
        "required_inputs": ["current_satellite_imagery", "historical_satellite_imagery"],
        "min_images": 2,
        "default_confidence": 0.92,
        "clarification_message": "Historical satellite imagery may be required for reliable glacier change analysis."
    },
    HazardTypes.GLACIER_RISK: {
        "analysis_type": "glacier_risk_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.95,
        "clarification_message": "Historical satellite imagery may be required for reliable glacier change analysis."
    },
    HazardTypes.GLOF: {
        "analysis_type": "glof_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.95,
        "clarification_message": "Historical satellite imagery may be required for reliable glacier change analysis."
    },
    HazardTypes.LANDSLIDE: {
        "analysis_type": "landslide_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.95,
        "clarification_message": "Landslide hazard analysis can be enhanced with elevation models."
    },
    HazardTypes.WILDFIRE: {
        "analysis_type": "wildfire_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.95,
        "clarification_message": "Wildfire assessment can be enhanced with thermal infrared bands."
    },
    HazardTypes.CYCLONE_DAMAGE: {
        "analysis_type": "cyclone_damage_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.95,
        "clarification_message": "Cyclone damage assessment analyzes damage footprint and structural losses."
    },
    HazardTypes.UNKNOWN: {
        "analysis_type": "general_disaster_assessment",
        "required_capabilities": ["disaster_hazard_analysis", "risk_assessment"],
        "required_inputs": ["satellite_image"],
        "min_images": 1,
        "default_confidence": 0.90,
        "clarification_message": "Please specify the type of hazard (e.g. flood, landslide, wildfire, glacier stability) you wish to analyze."
    }
}

# Rule Patterns for classification
INTENT_PATTERNS: List[Dict[str, Any]] = [
    {
        "intent": Intents.DISASTER_HAZARD_ANALYSIS,
        "patterns": [
            # Flood patterns
            (r"\b(flood|flooded|flooding|inundated|inundation|water logging)\b", HazardTypes.FLOOD),
            # Glacier GLOF patterns (Keep GLACIER_GLOF mapping for baseline test cases)
            (r"\b(glacier|glof|glaciers|glacial lake|glacier instability|unstable glacier|glaciological|glacial lake outburst|glacier movement|glacier retreat)\b", HazardTypes.GLACIER_GLOF),
            # Landslide patterns
            (r"\b(landslide|landslides|mudslide|mudslides|debris flow|slope failure|rockfall)\b", HazardTypes.LANDSLIDE),
            # Wildfire patterns
            (r"\b(wildfire|wildfires|forest fire|fire damage|burn scar|burnt area|fire risk)\b", HazardTypes.WILDFIRE),
            # Cyclone Damage patterns
            (r"\b(cyclone|hurricane|typhoon|storm damage|wind damage)\b", HazardTypes.CYCLONE_DAMAGE),
            # Generics
            (r"\b(hazard|disaster|natural disaster|damage assessment|indicators|disaster risk|disaster activity|disaster-related)\b", HazardTypes.UNKNOWN)
        ]
    },
    {
        "intent": Intents.MULTIMODAL_ANALYSIS,
        "patterns": [
            r"\b(compare|combine|fuse|fusing|fusion)\b.*\b(optical and sar|sar and optical|radar and optical|optical and radar)\b",
            r"\b(optical|sar|radar|multispectral)\b.*\b(and|with)\b.*\b(sar|optical|radar|multispectral)\b.*(data|imagery|images)",
            r"\b(combine|multimodal|sensor fusion)\b"
        ]
    },
    {
        "intent": Intents.CHANGE_DETECTION,
        "patterns": [
            r"\b(what changed|has changed|how has.*changed|difference|differences|compare|comparison)\b.*\b(between|before and after|over time|temporally)\b",
            r"\bchanged between\b",
            r"\bcompare (these|two|multiple)\b.*\bimages\b",
            r"\bhas the (forest|glacier|vegetation|water) (decreased|increased|shrunk|grown|changed)\b",
            r"\bchange detection\b",
            r"\btemporal change\b"
        ]
    },
    {
        "intent": Intents.REGION_GROUNDING,
        "patterns": [
            r"\b(where is|where are|locate|highlight|find|show) the\b.*\b(river|water|lake|forest|urban|building|buildings|road|roads|airport|port)\b",
            r"\b(draw a bounding box|localize|locate the)\b",
            r"\bhighlight\b.*\b(on the|in the|image)\b"
        ]
    },
    {
        "intent": Intents.VISUAL_QUESTION_ANSWERING,
        "patterns": [
            r"^(is there|are there|can you find|does this image contain)\b",
            r"\b(is this area|is this region) (covered|forested|urbanized|flooded)\b",
            r"\bwhat is the dominant (land cover|land use|vegetation|soil|terrain)\b",
            r"\bare there (any|signs of)\b.*\b(in this|in their)\b"
        ]
    },
    {
        "intent": Intents.SINGLE_IMAGE_ANALYSIS,
        "patterns": [
            r"what (can you see|is visible|is in) (in this|on this|here)\b",
            r"^describe (this|the) (satellite|image|region|area|scene)\b",
            r"^analyze (this|the) (satellite|image|region|area|scene)\b",
            r"\b(general|overall) description of\b"
        ]
    }
]

# Words indicating conversational/non-remote-sensing queries
CONVERSATIONAL_KEYWORDS = [
    r"^(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b",
    r"^(how are you|who are you|what is your name|what can you do)\b",
    r"^(thank you|thanks|bye|goodbye)\b"
]

AMBIGUOUS_KEYWORDS = [
    r"^(analyze this|process this|run this|check this|do it|go)$",
    r"^(what is this|tell me|show me)$"
]
