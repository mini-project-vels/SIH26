import pytest
import io
from PIL import Image
from typing import Dict, Any

from app.agents.query_understanding_agent import QueryUnderstandingAgent
from app.agents.orchestrator import Orchestrator
from app.config.intents import Intents, HazardTypes
from app.services.disaster_intelligence.disaster_engine import DisasterIntelligenceEngine
from app.services.disaster_intelligence.evidence_analyzer import EvidenceAnalyzer
from app.services.disaster_intelligence.risk_assessor import RiskAssessor
from app.services.disaster_intelligence.recommendation_engine import RecommendationEngine
from app.utils.spatial_analysis import calculate_bbox_overlap, calculate_mask_overlap, find_affected_objects

# Helper to create a dummy image in-memory
def create_dummy_image(width=100, height=100, color=(0, 255, 0)) -> io.BytesIO:
    img = Image.new("RGB", (width, height), color)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_query_understanding_disaster():
    """
    Test 1, 2, 3, 4 Query Classifications.
    Verifies that the Query Agent identifies disaster analysis correctly.
    """
    agent = QueryUnderstandingAgent()
    
    # Test 1: Analyze this image for disaster risk
    res1 = agent.analyze("Analyze this image for disaster risk")
    assert res1.intent == Intents.DISASTER_HAZARD_ANALYSIS
    assert res1.hazard_type == HazardTypes.UNKNOWN
    
    # Test 2: Is there a flood risk?
    res2 = agent.analyze("Is there a flood risk?")
    assert res2.intent == Intents.DISASTER_HAZARD_ANALYSIS
    assert res2.hazard_type == HazardTypes.FLOOD
    
    # Test 3: Check this region for possible disaster activity
    res3 = agent.analyze("Check this region for possible disaster activity")
    assert res3.intent == Intents.DISASTER_HAZARD_ANALYSIS
    assert res3.hazard_type == HazardTypes.UNKNOWN
    
    # Test 4: Compare these images and identify possible disaster-related changes
    res4 = agent.analyze("Compare these images and identify possible disaster-related changes")
    assert res4.intent == Intents.DISASTER_HAZARD_ANALYSIS
    assert res4.hazard_type == HazardTypes.UNKNOWN

def test_risk_explanation_and_normalization():
    """
    Verifies that risk score is explainable, weights are applied correctly,
    and missing evidence does not crash the system.
    """
    engine = DisasterIntelligenceEngine()
    
    # Stub specialist results with some missing evidence
    # Here, we only have change_detection and building_segmentation, and no water or VLM
    specialist_results = {
        "change_detection": {
            "status": "SUCCESS",
            "changed_pixels": 5000,
            "change_ratio": 0.10, # 10% change
            "detections": [{
                "location": "northwest",
                "bbox": [50, 50, 200, 200]
            }]
        },
        "visual_grounding": {
            "status": "SUCCESS",
            "target": "buildings",
            "detections": [
                {
                    "id": 1,
                    "label": "buildings",
                    "bbox": [60, 60, 100, 100],  # Overlaps with change bounding box!
                    "area_pixels": 1600
                },
                {
                    "id": 2,
                    "label": "buildings",
                    "bbox": [300, 300, 350, 350], # No overlap
                    "area_pixels": 2500
                }
            ]
        }
    }
    
    report = engine.analyze(
        query="Is there a flood risk?",
        disaster_type="FLOOD",
        request_id="test-req-id",
        specialist_results=specialist_results
    )
    
    assert report.status == "SUCCESS"
    assert report.disaster_type == "FLOOD"
    assert report.assessment_status == "SUPPORTED"
    
    # Assert risk assessment score is calculated
    risk = report.risk_assessment
    assert risk.risk_score is not None
    assert risk.risk_score > 0
    assert risk.risk_level != "UNKNOWN"
    
    # Assert factors are explainable and sum up properly
    assert len(risk.risk_factors) > 0
    calculated_sum = sum(f["contribution"] for f in risk.risk_factors)
    # The sum of contributions should match the final risk score due to our normalized weight scoring method
    assert calculated_sum == pytest.approx(risk.risk_score, abs=2)
    
    # Check that exposed buildings are tracked via spatial overlap
    assert report.potential_impact is not None
    assert report.potential_impact.buildings is not None
    assert report.potential_impact.buildings["affected_count"] == 1
    assert 1 in report.potential_impact.buildings["exposed_buildings"]
    assert 2 not in report.potential_impact.buildings["exposed_buildings"]

def test_missing_evidence_graceful_handling():
    """
    Verify that missing evidence does not crash the system.
    """
    engine = DisasterIntelligenceEngine()
    
    # Complete lack of evidence from specialists
    report = engine.analyze(
        query="Is there a flood risk?",
        disaster_type="FLOOD",
        request_id="test-req-id",
        specialist_results={}
    )
    
    assert report.status == "SUCCESS"
    assert report.assessment_status == "INSUFFICIENT_EVIDENCE"
    assert report.risk_assessment.risk_score is None
    assert report.risk_assessment.risk_level == "UNKNOWN"
    assert len(report.recommendations) > 0

def test_no_disaster_inventing():
    """
    Ensure the system never invents a disaster when there is positive evidence of safety.
    """
    engine = DisasterIntelligenceEngine()
    
    # Minimal changes, no building impacts, negative VLM checks
    specialist_results = {
        "change_detection": {
            "status": "SUCCESS",
            "changed_pixels": 0,
            "change_ratio": 0.0,
            "detections": []
        },
        "single_image_analysis": {
            "status": "SUCCESS",
            "answer": "The satellite image shows steady agricultural topography with no signs of flooding or damage."
        }
    }
    
    report = engine.analyze(
        query="Is there a flood risk?",
        disaster_type="FLOOD",
        request_id="test-req-id",
        specialist_results=specialist_results
    )
    
    assert report.risk_assessment.risk_score <= 20
    assert report.risk_assessment.risk_level == "LOW"

def test_spatial_analysis():
    """
    Verify bbox overlaps and spatial utilities.
    """
    # Half overlap
    boxA = [0, 0, 100, 100]  # area = 10000
    boxB = [0, 0, 100, 50]   # area = 5000, overlap is 5000
    overlap = calculate_bbox_overlap(boxA, boxB)
    assert overlap == 0.50
    
    # No overlap
    boxC = [200, 200, 300, 300]
    assert calculate_bbox_overlap(boxA, boxC) == 0.0
