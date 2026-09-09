import io
import pytest
from PIL import Image
from app.agents.orchestrator import Orchestrator
from app.agents.change_detection_agent import ChangeDetectionAgent
from app.services.execution_planner import ExecutionPlanner
from app.models.schemas import AvailableInputs
from app.config.intents import Intents, HazardTypes

def create_mock_image(color="blue") -> io.BytesIO:
    """
    Creates a simple mock 10x10 PNG image in memory.
    """
    img = Image.new("RGB", (10, 10), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@pytest.fixture
def orchestrator():
    return Orchestrator()

def test_orchestrate_change_detection_success(orchestrator):
    # Setup mock images
    before = create_mock_image("blue")
    after = create_mock_image("red")
    
    query = "What changed between these two satellite images?"
    
    # Run orchestrator
    response = orchestrator.orchestrate(
        query=query,
        before_image=before,
        after_image=after
    )
    
    assert response.status == "SUCCESS"
    assert response.query_understanding.intent == Intents.CHANGE_DETECTION
    assert "change_detection" in response.query_understanding.required_capabilities
    assert response.orchestration.status == "SUCCESS"
    assert len(response.orchestration.execution_plan) == 1
    assert response.orchestration.execution_plan[0].capability == "change_detection"
    assert response.orchestration.execution_plan[0].status == "COMPLETED"
    
    # Check that real Change Detection Agent was invoked and generated output
    assert "change_detection" in response.result
    cd_result = response.result["change_detection"]
    assert cd_result["alignment_status"] == "SUCCESS"
    assert "statistics" in cd_result
    assert cd_result["statistics"]["total_pixels"] == 100
    assert "outputs" in cd_result
    assert "change_mask" in cd_result["outputs"]
    assert "change_overlay" in cd_result["outputs"]

def test_orchestrate_change_detection_missing_input(orchestrator):
    # Only before_image is provided
    before = create_mock_image("blue")
    query = "What changed between these images?"
    
    response = orchestrator.orchestrate(
        query=query,
        before_image=before,
        after_image=None
    )
    
    assert response.status == "NEEDS_INPUT"
    assert "after_image" in response.missing_inputs
    assert "Change detection requires both before and after" in response.message
    assert response.result is None

def test_orchestrate_unsupported_capability(orchestrator):
    # Query requests optical and SAR comparison which is MULTIMODAL_ANALYSIS (unsupported)
    query = "Compare Optical and SAR imagery."
    
    response = orchestrator.orchestrate(
        query=query,
        before_image=None,
        after_image=None
    )
    
    assert response.status == "UNSUPPORTED"
    assert "multimodal_analysis" in response.unavailable_capabilities
    assert "has not been implemented yet" in response.message
    assert response.result is None

def test_orchestrate_needs_clarification(orchestrator):
    # Query is Ambiguous and triggers clarification in query agent
    query = "Analyze this."
    
    response = orchestrator.orchestrate(
        query=query,
        before_image=None,
        after_image=None
    )
    
    assert response.status == "NEEDS_CLARIFICATION"
    assert "could not understand your request" in response.message
    assert response.result is None
