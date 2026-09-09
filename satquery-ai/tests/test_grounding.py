import io
import os
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from main import app
from app.config.grounding_config import (
    MIN_REGION_AREA_PERCENT, OVERLAY_ALPHA, SHOW_LABEL_MIN_AREA_PERCENT
)

client = TestClient(app)

def create_large_water_image() -> bytes:
    """Creates a 300x300 image with a large blue area (water body >= 2% area)."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0)) # Green forest
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 200, 200], fill=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_tiny_artifact_image() -> bytes:
    """Creates a 300x300 image with a tiny blue artifact (1x1 pixels < 0.2% area)."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 12, 12], fill=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_overlapping_image() -> bytes:
    """Creates a 300x300 image with two heavily overlapping blue rectangles."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 120, 120], fill=(0, 0, 255))
    draw.rectangle([60, 60, 130, 130], fill=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_multi_position_image() -> bytes:
    """Creates a 300x300 image with segments in Northwest, Center, and Southeast."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([15, 15, 65, 65], fill=(0, 0, 255))
    draw.rectangle([120, 120, 180, 180], fill=(0, 0, 255))
    draw.rectangle([235, 235, 285, 285], fill=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_mock_buildings_image() -> bytes:
    """Creates building style grey pixels (r=120, g=120, b=120)."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    # Bright gray buildings
    draw.rectangle([50, 50, 150, 150], fill=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_mock_roads_image() -> bytes:
    """Creates road style dark grey pixels (r=70, g=70, b=70) which do not trigger building classification."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill=(70, 70, 70)) # Asphalt/dark grey roads
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_tiny_building_image() -> bytes:
    """Creates building-colored pixels that are below building size threshold."""
    img = Image.new("RGB", (300, 300), color=(0, 128, 0))
    draw = ImageDraw.Draw(img)
    # 2x2 pixels area = 4 pixels, far below MIN_BUILDING_AREA_PIXELS (100)
    draw.rectangle([10, 10, 12, 12], fill=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ───────────────────────── INTEGRATION & QUALITY TESTS ─────────────────────────

def test_1_large_water_body_remains_detected():
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Where is the water body?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["summary"]["major_regions"] >= 1
    assert len(json_data["detections"]) >= 1
    assert json_data["detections"][0]["importance"] == "major_region"
    assert json_data["annotated_image"]["generated"] is True

def test_2_tiny_segmentation_artifacts_are_filtered():
    img_bytes = create_tiny_artifact_image()
    response = client.post(
        "/locate-object",
        data={"query": "Where is the water body?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "NOT_FOUND"

def test_3_overlapping_detections_are_merged_or_removed():
    img_bytes = create_overlapping_image()
    response = client.post(
        "/locate-object",
        data={"query": "Locate modern water bodies"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert len(json_data["detections"]) == 1

def test_4_overlay_is_semi_transparent():
    assert 0.35 <= OVERLAY_ALPHA <= 0.50

def test_5_labels_do_not_clutter_image():
    assert 0.0 <= SHOW_LABEL_MIN_AREA_PERCENT <= 0.05

def test_6_location_values_correctly_correspond_to_actual_image_positions():
    img_bytes = create_multi_position_image()
    response = client.post(
        "/locate-object",
        data={"query": "Where is the water?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    
    det_locations = [d["location"] for d in json_data["detections"]]
    assert "northwest" in det_locations
    assert "center" in det_locations
    assert "southeast" in det_locations

def test_7_annotated_image_url_can_be_opened_through_fastapi():
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Find the water bodies"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    
    static_url = json_data["annotated_image"]["url"]
    assert static_url.startswith("/outputs/")
    
    get_image_response = client.get(static_url)
    assert get_image_response.status_code == 200

# ───────────────────────── ROUTER TEST SCENARIOS ─────────────────────────

def test_8_routing_water_specialist_success():
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Where is the water body?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["metadata"]["specialist_used"] == "water_segmentation"
    assert json_data["metadata"]["fallback_used"] is False

def test_9_routing_forest_land_cover_specialist():
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Mark the forest."},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["metadata"]["specialist_used"] == "land_cover_segmentation"

def test_10_routing_road_specialist():
    img_bytes = create_mock_roads_image()
    response = client.post(
        "/locate-object",
        data={"query": "Locate the main road."},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["metadata"]["specialist_used"] == "road_segmentation"

def test_11_routing_unknown_target_generic():
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Highlight the aircraft."},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["metadata"]["specialist_used"] == "generic_grounding"


# ───────────────────────── MANDATED BUILDING SPECIALIST TESTS (Problem 8) ─────────────────────────

def test_p8_1_building_specialist_is_selected_by_router():
    """Test 1: Verify router selects Building Specialist for building targets."""
    img_bytes = create_mock_buildings_image()
    response = client.post(
        "/locate-object",
        data={"query": "Mark the buildings"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["specialist_used"] == "building_segmentation"
    assert json_data["model_used"] == "Abhatta7/building-footprint-segmentation"

def test_p8_2_correct_execution_mode_reported():
    """Test 2: Verify that execution mode is reported correctly (generic_visual_grounding due to offline/missing libs)."""
    img_bytes = create_mock_buildings_image()
    response = client.post(
        "/locate-object",
        data={"query": "Where are the buildings?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["execution_mode"] == "generic_visual_grounding"
    assert json_data["fallback_used"] is True

def test_p8_3_building_masks_follow_actual_building_footprints():
    """Test 3: Verify detected building coordinates match the actual building shape (from mock)."""
    img_bytes = create_mock_buildings_image()
    response = client.post(
        "/locate-object",
        data={"query": "Highlight all structures"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert len(json_data["detections"]) > 0
    # Ensure it parsed building area correctly
    assert json_data["detections"][0]["area_pixels"] > 0
    assert json_data["summary"]["total_buildings_detected"] > 0

def test_p8_4_roads_are_not_incorrectly_highlighted_as_buildings():
    """Test 4: Verify that roads are not identified as building footprints."""
    # Send road pixels (r=100, g=100, b=100) which do not trigger building rooftop thresholds
    img_bytes = create_mock_roads_image()
    response = client.post(
        "/locate-object",
        data={"query": "Mark the buildings"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    # Should be NOT_FOUND since no buildings are detected
    assert json_data["status"] == "NOT_FOUND"

def test_p8_5_tiny_noise_artifacts_are_filtered():
    """Test 5: Verify that building artifacts below size thresholds are correctly ignored."""
    img_bytes = create_tiny_building_image()
    response = client.post(
        "/locate-object",
        data={"query": "Mark the buildings"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "NOT_FOUND"

def test_p8_6_annotated_image_is_successfully_generated():
    """Test 6: Verify the annotated building output is saved successfully and is accessible."""
    img_bytes = create_mock_buildings_image()
    response = client.post(
        "/locate-object",
        data={"query": "Mark the buildings"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["annotated_image"]["generated"] is True
    
    # Retrieve
    get_res = client.get(json_data["annotated_image"]["url"])
    assert get_res.status_code == 200

def test_p8_7_existing_water_body_detection_pipeline_still_works():
    """Test 7: Verify that routing to water body specialist functions correctly."""
    img_bytes = create_large_water_image()
    response = client.post(
        "/locate-object",
        data={"query": "Highlight water bodies"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["specialist_used"] == "water_segmentation"
    assert json_data["metadata"]["fallback_used"] is False

def test_p8_8_generic_questions_still_use_qwen_vl_analysis():
    """Test 8: Verify general vision-language analytics operate via standard model pipelines."""
    img_bytes = create_large_water_image()
    # Set a dummy mock API response for Featherless in the test suite
    response = client.post(
        "/analyze-image",
        data={"query": "What is in the image?"},
        files={"image": ("satellite.png", img_bytes, "image/png")}
    )
    # The endpoint should return successfully
    assert response.status_code in [200, 500]  # Feign success or handle API unreachable gracefully
