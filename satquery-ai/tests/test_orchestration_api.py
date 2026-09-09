import io
from fastapi.testclient import TestClient
from PIL import Image
from main import app

client = TestClient(app)

def create_mock_png_bytes(color="blue") -> bytes:
    """
    Creates a simple mock 10x10 PNG image in memory and returns raw bytes.
    """
    img = Image.new("RGB", (10, 10), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_api_orchestrates_success():
    before_bytes = create_mock_png_bytes("blue")
    after_bytes = create_mock_png_bytes("red")
    
    files = {
        "before_image": ("before.png", before_bytes, "image/png"),
        "after_image": ("after.png", after_bytes, "image/png")
    }
    data = {
        "query": "What changed between these two satellite images?"
    }
    
    response = client.post("/orchestrate", data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "SUCCESS"
    assert res_data["query_understanding"]["intent"] == "CHANGE_DETECTION"
    assert res_data["orchestration"]["status"] == "SUCCESS"
    assert res_data["orchestration"]["execution_plan"][0]["status"] == "COMPLETED"
    assert "change_detection" in res_data["result"]
    assert res_data["result"]["change_detection"]["alignment_status"] == "SUCCESS"

def test_api_orchestrates_missing_input():
    before_bytes = create_mock_png_bytes("blue")
    
    # Only upload before_image
    files = {
        "before_image": ("before.png", before_bytes, "image/png")
    }
    data = {
        "query": "What changed between these satellite images?"
    }
    
    response = client.post("/orchestrate", data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "NEEDS_INPUT"
    assert "after_image" in res_data["missing_inputs"]
    assert "Change detection requires both before and after" in res_data["message"]

def test_api_orchestrates_unsupported():
    data = {
        "query": "Compare Optical and SAR imagery."
    }
    
    response = client.post("/orchestrate", data=data)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "UNSUPPORTED"
    assert "multimodal_analysis" in res_data["unavailable_capabilities"]
    assert "has not been implemented yet" in res_data["message"]

def test_api_orchestrates_needs_clarification():
    data = {
        "query": "Hello, how are you?"
    }
    
    response = client.post("/orchestrate", data=data)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["status"] == "NEEDS_CLARIFICATION"
    assert "could not understand your request" in res_data["message"]
