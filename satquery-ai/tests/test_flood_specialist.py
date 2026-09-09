import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def create_mock_scene(water_color=None, building_color=None):
    # Base green vegetation (0, 150, 20)
    img = Image.new("RGB", (400, 400), color=(0, 150, 20))
    draw = ImageDraw.Draw(img)
    
    # If water_color is specified, draw a water body (RGB format: blue-ish)
    if water_color:
        draw.rectangle([100, 100, 300, 300], fill=water_color)
        
    # If building_color is specified, draw building rooftops (Grey)
    if building_color:
        # Building inside the water region overlap
        draw.rectangle([150, 150, 220, 220], fill=building_color)
        # Building outside water
        draw.rectangle([20, 20, 80, 80], fill=building_color)
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def test_flood_single_image():
    """
    TEST 1: Single Image
    Analyze this image for possible flooding.
    Expected: Water Detection + VLM Verification + Flood Evidence
    """
    # Image with water and buildings
    img_bytes = create_mock_scene(water_color=(0, 10, 240), building_color=(120, 120, 120))
    
    response = client.post(
        "/disaster-analysis",
        data={"query": "Analyze this image for possible flooding."},
        files={"image": ("image.png", img_bytes, "image/png")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "SUCCESS"
    assert res_json["disaster_type"] == "flood"
    
    # Verify water analysis
    assert res_json["water_analysis"]["water_detected"] is True
    
    # Verify presence of flood_assessment
    assert "flood_assessment" in res_json
    assert res_json["flood_assessment"]["risk_score"] > 0
    
    # Verify annotated image generated
    assert res_json["annotated_image"]["generated"] is True

def test_flood_two_images():
    """
    TEST 2: Two Images
    Compare these images and check whether flooding increased.
    Expected: Water Comparison + Change Detection + Flood Risk
    """
    # Before image: normal dry vegetation (green)
    before_bytes = create_mock_scene(water_color=None, building_color=(120, 120, 120))
    # After image: water expands over center of the scene
    after_bytes = create_mock_scene(water_color=(0, 10, 240), building_color=(120, 120, 120))
    
    response = client.post(
        "/disaster-analysis",
        data={"query": "Compare these images and check whether flooding increased."},
        files={
            "before_image": ("before.png", before_bytes, "image/png"),
            "after_image": ("after.png", after_bytes, "image/png")
        }
    )
    
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "SUCCESS"
    
    # Verify expansion is calculated and positive
    assert res_json["water_analysis"]["water_expansion_detected"] is True
    assert res_json["water_analysis"]["water_expansion_percentage"] > 0
    
    # Verify factors lists expansion
    risk_factors = [f["factor"] for f in res_json["risk_factors"]]
    assert any("expansion" in f.lower() for f in risk_factors)

def test_flood_building_impact():
    """
    TEST 3: Building Impact
    Identify buildings potentially affected by flooding.
    Expected: Flood Region + Building Segmentation -> Spatial Overlap
    """
    # Image with water at center (100, 100, 300, 300)
    # A building at (150, 150, 220, 220) which is fully inside the water body
    img_bytes = create_mock_scene(water_color=(0, 10, 240), building_color=(120, 120, 120))
    
    response = client.post(
        "/disaster-analysis",
        data={"query": "Identify buildings potentially affected by flooding."},
        files={"image": ("image.png", img_bytes, "image/png")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    
    # Verify potential impact buildings
    assert res_json["potential_impact"]["potentially_affected_buildings"] > 0
    
    # Verify detailed building overlaps exist
    assert "potentially_affected_buildings_detail" in res_json
    details = res_json["potentially_affected_buildings_detail"]
    assert len(details) > 0
    assert any(b["risk"] == "HIGH" for b in details)

def test_flood_no_evidence():
    """
    TEST 4: No Flood Evidence
    Use a normal satellite image without flood/water features.
    Expected: LOW RISK or INSUFFICIENT_EVIDENCE
    """
    # Completely dry scene with building, no water (green)
    dry_bytes = create_mock_scene(water_color=None, building_color=(120, 120, 120))
    
    response = client.post(
        "/disaster-analysis",
        data={"query": "Analyze this image for possible flooding."},
        files={"image": ("image.png", dry_bytes, "image/png")}
    )
    
    assert response.status_code == 200
    res_json = response.json()
    
    # System should not invent flooding
    assert res_json["water_analysis"]["water_detected"] is False
    assert res_json["flood_assessment"]["risk_level"] == "LOW"
    assert res_json["flood_assessment"]["risk_score"] == 0
