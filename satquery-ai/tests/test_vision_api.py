import io
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def create_mock_png_bytes(color: str = "green") -> bytes:
    img = Image.new("RGB", (10, 10), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ──────────────── /analyze-image endpoint tests ──────────────────────────────

def test_analyze_image_endpoint_success():
    """Full pipeline call to /analyze-image with mocked HF vision service."""
    png_bytes = create_mock_png_bytes("green")

    with patch(
        "app.services.huggingface_vision_service.HuggingFaceVisionService.analyze_image",
        return_value="Vegetation patches and a river are clearly visible."
    ):
        response = client.post(
            "/analyze-image",
            data={"query": "What can you see in this satellite image?"},
            files={"image": ("sat.png", png_bytes, "image/png")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert "vegetation" in body["result"]["answer"].lower()
    assert body["model"]["provider"] == "huggingface"
    assert len(body["limitations"]) > 0


def test_analyze_image_endpoint_missing_hf_token():
    """HF token missing → controlled ERROR response, no secret exposed."""
    png_bytes = create_mock_png_bytes()

    with patch(
        "app.services.huggingface_vision_service.HuggingFaceVisionService.analyze_image",
        side_effect=ValueError("Vision service configuration is missing.")
    ):
        response = client.post(
            "/analyze-image",
            data={"query": "Describe this image."},
            files={"image": ("sat.png", png_bytes, "image/png")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ERROR"
    assert "Vision service configuration is missing." in body["message"]


def test_analyze_image_endpoint_timeout():
    """All models at capacity → ERROR with descriptive retry message."""
    png_bytes = create_mock_png_bytes()

    with patch(
        "app.services.huggingface_vision_service.HuggingFaceVisionService.analyze_image",
        side_effect=RuntimeError(
            "All vision models are currently at capacity. Please try again in a few minutes."
        )
    ):
        response = client.post(
            "/analyze-image",
            data={"query": "What is visible here?"},
            files={"image": ("sat.png", png_bytes, "image/png")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ERROR"
    assert "capacity" in body["message"].lower()
    assert "try again" in body["message"].lower()



# ─────────────────── /orchestrate vision routing tests ───────────────────────

def test_orchestrate_single_image_analysis_success():
    """Single image + description query → routes to SingleImageAnalysisAgent via /orchestrate."""
    png_bytes = create_mock_png_bytes("green")

    with patch(
        "app.services.huggingface_vision_service.HuggingFaceVisionService.analyze_image",
        return_value="Agricultural fields and urban settlements are visible."
    ):
        response = client.post(
            "/orchestrate",
            data={"query": "What can you see in this satellite image?"},
            files={"image": ("sat.png", png_bytes, "image/png")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["query_understanding"]["intent"] == "SINGLE_IMAGE_ANALYSIS"
    plan = body["orchestration"]["execution_plan"]
    assert plan[0]["capability"] == "single_image_analysis"
    assert plan[0]["status"] == "COMPLETED"
    assert "single_image_analysis" in body["result"]
    assert "Agricultural" in body["result"]["single_image_analysis"]["answer"]


def test_orchestrate_visual_question_answering_success():
    """VQA query + single image → routes to SingleImageAnalysisAgent via /orchestrate."""
    png_bytes = create_mock_png_bytes("blue")

    with patch(
        "app.services.huggingface_vision_service.HuggingFaceVisionService.analyze_image",
        return_value="Yes, a visible water body is present in the lower half of the image."
    ):
        response = client.post(
            "/orchestrate",
            data={"query": "Is there a water body visible?"},
            files={"image": ("sat.png", png_bytes, "image/png")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["query_understanding"]["intent"] == "VISUAL_QUESTION_ANSWERING"
    plan = body["orchestration"]["execution_plan"]
    assert plan[0]["capability"] == "visual_question_answering"
    assert plan[0]["status"] == "COMPLETED"


def test_orchestrate_change_detection_still_works():
    """Change detection must not be broken by Phase 4 changes."""
    before_bytes = create_mock_png_bytes("blue")
    after_bytes = create_mock_png_bytes("red")

    response = client.post(
        "/orchestrate",
        data={"query": "What changed between these two satellite images?"},
        files={
            "before_image": ("before.png", before_bytes, "image/png"),
            "after_image": ("after.png", after_bytes, "image/png")
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["query_understanding"]["intent"] == "CHANGE_DETECTION"
    assert body["result"]["change_detection"]["alignment_status"] == "SUCCESS"


def test_orchestrate_single_image_missing_image():
    """Single image query with no image provided → NEEDS_INPUT."""
    response = client.post(
        "/orchestrate",
        data={"query": "What can you see in this satellite image?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NEEDS_INPUT"
    assert "image" in body["missing_inputs"]
