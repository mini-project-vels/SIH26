from fastapi.testclient import TestClient
from main import app
from app.agents.query_understanding_agent import QueryUnderstandingAgent
from app.models.schemas import AvailableInputs
from app.config.intents import Intents, HazardTypes

client = TestClient(app)
agent = QueryUnderstandingAgent()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "SatQuery AI Query Understanding Agent"
    }

def test_agent_directly_change_detection():
    # Test change detection with sufficient inputs
    inputs = AvailableInputs(image_count=2, modalities=["OPTICAL"], has_metadata=True)
    res = agent.analyze("What changed between these two satellite images?", available_inputs=inputs)
    
    assert res.intent == Intents.CHANGE_DETECTION
    assert res.analysis_type == "multi_temporal"
    assert "change_detection" in res.required_capabilities
    assert "satellite_image_before" in res.required_inputs
    assert "satellite_image_after" in res.required_inputs
    assert res.hazard_type is None
    assert res.input_sufficiency == "SUFFICIENT"
    assert res.needs_clarification is False
    assert res.clarification_message is None

def test_agent_directly_glacier_unstable():
    # Test glacier stability with no inputs (unknown inputs)
    res = agent.analyze("Is this glacier becoming unstable?", available_inputs=None)
    
    assert res.intent == Intents.DISASTER_HAZARD_ANALYSIS
    assert res.hazard_type == HazardTypes.GLACIER_GLOF
    assert res.analysis_type == "hazard_monitoring"
    assert "change_detection" in res.required_capabilities
    assert "surface_analysis" in res.required_capabilities
    assert "hazard_assessment" in res.required_capabilities
    assert "current_satellite_imagery" in res.required_inputs
    assert "historical_satellite_imagery" in res.required_inputs
    assert res.input_sufficiency == "UNKNOWN"
    assert res.needs_clarification is True
    assert "Historical satellite imagery may be required" in res.clarification_message

def test_api_change_detection_insufficient():
    # Test change detection over POST API with 1 image (insufficient)
    payload = {
        "query": "What changed between these images?",
        "available_inputs": {
            "image_count": 1,
            "modalities": ["OPTICAL"],
            "has_metadata": True
        }
    }
    response = client.post("/analyze-query", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["intent"] == Intents.CHANGE_DETECTION
    assert res_data["input_sufficiency"] == "INSUFFICIENT"
    assert res_data["needs_clarification"] is True
    assert "requires at least two satellite images" in res_data["clarification_message"]

def test_api_unknown_conversational():
    # Test conversational query over API
    payload = {
        "query": "Hello, how are you?"
    }
    response = client.post("/analyze-query", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["intent"] == Intents.UNKNOWN
    assert res_data["input_sufficiency"] == "UNKNOWN"
    assert res_data["needs_clarification"] is True
    assert "could not understand your request" in res_data["clarification_message"]
