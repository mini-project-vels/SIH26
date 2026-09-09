import pytest
from app.services.rule_based_classifier import RuleBasedClassifier
from app.config.intents import Intents, HazardTypes

@pytest.fixture
def classifier():
    return RuleBasedClassifier()

@pytest.mark.parametrize(
    "query,expected_intent,expected_hazard",
    [
        # Single Image Analysis
        ("What can you see in this satellite image?", Intents.SINGLE_IMAGE_ANALYSIS, None),
        ("Describe this region.", Intents.SINGLE_IMAGE_ANALYSIS, None),
        
        # Visual Question Answering
        ("Is there a river in this image?", Intents.VISUAL_QUESTION_ANSWERING, None),
        ("Is this area covered with vegetation?", Intents.VISUAL_QUESTION_ANSWERING, None),
        
        # Change Detection
        ("What changed between these images?", Intents.CHANGE_DETECTION, None),
        ("Has the forest decreased?", Intents.CHANGE_DETECTION, None),
        ("Compare these satellite images.", Intents.CHANGE_DETECTION, None),
        
        # Multimodal Analysis
        ("Compare Optical and SAR imagery.", Intents.MULTIMODAL_ANALYSIS, None),
        ("Analyze this region using radar and optical data.", Intents.MULTIMODAL_ANALYSIS, None),
        
        # Region Grounding
        ("Where is the river?", Intents.REGION_GROUNDING, None),
        ("Highlight the water body.", Intents.REGION_GROUNDING, None),
        
        # Disaster / Hazard Analysis
        ("Is this area flooded?", Intents.DISASTER_HAZARD_ANALYSIS, HazardTypes.FLOOD),
        ("Is the glacier becoming unstable?", Intents.DISASTER_HAZARD_ANALYSIS, HazardTypes.GLACIER_GLOF),
        ("Are there landslide indicators?", Intents.DISASTER_HAZARD_ANALYSIS, HazardTypes.LANDSLIDE),
        ("Show wildfire damage.", Intents.DISASTER_HAZARD_ANALYSIS, HazardTypes.WILDFIRE),
        
        # Unknown / Ambiguous / Conversational
        ("Hello, how are you?", Intents.UNKNOWN, None),
        ("Analyze this.", Intents.UNKNOWN, None)
    ]
)
def test_classification_logic(classifier, query, expected_intent, expected_hazard):
    intent, confidence, hazard = classifier.classify(query)
    
    assert intent == expected_intent, f"Failed for query '{query}': expected intent {expected_intent}, got {intent}"
    assert hazard == expected_hazard, f"Failed for query '{query}': expected hazard {expected_hazard}, got {hazard}"
    assert 0.0 <= confidence <= 1.0, f"Confidence score {confidence} is out of bounds [0.0, 1.0]"
    
    # Check that confidence is high (>0.8) for matched ones, unless fallback
    if expected_intent != Intents.UNKNOWN or query in ["Hello, how are you?", "Analyze this."]:
        assert confidence >= 0.80, f"Mock classifier confidence too low for '{query}': {confidence}"
    else:
        assert confidence == 0.50, f"Fallback confidence should be 0.50 but got {confidence}"
