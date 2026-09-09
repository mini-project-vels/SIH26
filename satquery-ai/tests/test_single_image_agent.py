import io
import uuid
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PIL import Image

from app.agents.single_image_analysis_agent import SingleImageAnalysisAgent
from app.services.vision_prompt_builder import VisionPromptBuilder
from app.models.vision_schemas import SingleImageAnalysisResponse


def create_mock_upload_file(color: str = "blue", filename: str = "test.png"):
    """Creates a mock FastAPI UploadFile from a PIL image."""
    img = Image.new("RGB", (10, 10), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.file = buf
    return mock_file


def create_mock_vision_service(return_text: str = "This is a satellite image showing vegetation."):
    """Returns a mock HuggingFaceVisionService that yields a fixed response."""
    mock_svc = MagicMock()
    mock_svc.analyze_image.return_value = return_text
    return mock_svc


# ─────────────────────────────── UNIT TESTS ──────────────────────────────────


def test_single_image_analysis_success():
    """Valid image + query → SUCCESS with AI answer."""
    mock_svc = create_mock_vision_service("Visible vegetation and water bodies detected.")
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)
    img = create_mock_upload_file("green")

    result = agent.execute(image=img, query="What can you see in this satellite image?")

    assert result.status == "SUCCESS"
    assert result.query == "What can you see in this satellite image?"
    assert result.result is not None
    assert "vegetation" in result.result.answer
    assert result.model is not None
    assert result.model.provider == "huggingface"
    assert result.limitations is not None
    assert len(result.limitations) > 0
    mock_svc.analyze_image.assert_called_once()


def test_visual_question_answering_success():
    """Valid image + VQA question → SUCCESS with direct object answer."""
    mock_svc = create_mock_vision_service("Yes, a river is visible on the left side of the image.")
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)
    img = create_mock_upload_file("blue")

    result = agent.execute(image=img, query="Is there a water body visible?")

    assert result.status == "SUCCESS"
    assert "river" in result.result.answer
    mock_svc.analyze_image.assert_called_once()


def test_missing_image_returns_needs_input():
    """No image passed → NEEDS_INPUT."""
    agent = SingleImageAnalysisAgent()

    result = agent.execute(image=None, query="Describe the terrain.")

    assert result.status == "NEEDS_INPUT"
    assert "image is required" in result.message


def test_missing_query_returns_needs_input():
    """No query → NEEDS_INPUT."""
    agent = SingleImageAnalysisAgent()
    img = create_mock_upload_file()

    result = agent.execute(image=img, query="")

    assert result.status == "NEEDS_INPUT"
    assert "question is required" in result.message


def test_missing_hf_token_returns_error():
    """Missing HF_TOKEN → controlled ERROR (no crash, no secret exposure)."""
    mock_svc = MagicMock()
    mock_svc.analyze_image.side_effect = ValueError("Vision service configuration is missing.")
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)
    img = create_mock_upload_file()

    result = agent.execute(image=img, query="Describe this image.")

    assert result.status == "ERROR"
    assert "Vision service configuration is missing." in result.message
    # Ensure the actual token is never in the message
    assert "HF_TOKEN" not in result.message


def test_api_timeout_returns_error():
    """API timeout → controlled ERROR (no crash)."""
    mock_svc = MagicMock()
    mock_svc.analyze_image.side_effect = RuntimeError(
        "All vision models are currently at capacity. Please try again in a few minutes."
    )
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)
    img = create_mock_upload_file()

    result = agent.execute(image=img, query="What is in this image?")

    assert result.status == "ERROR"
    assert "capacity" in result.message.lower()


def test_all_models_capacity_exhausted():
    """When every fallback model is at capacity → controlled ERROR with descriptive message."""
    mock_svc = MagicMock()
    mock_svc.analyze_image.side_effect = RuntimeError(
        "All vision models are currently at capacity. Please try again in a few minutes. "
        "Last error: Error code: 503 - capacity_exhausted"
    )
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)
    img = create_mock_upload_file()

    result = agent.execute(image=img, query="Describe the terrain.")

    assert result.status == "ERROR"
    assert "at capacity" in result.message.lower()
    assert "try again" in result.message.lower()


def test_invalid_image_format_returns_error():
    """Unsupported image extension → controlled ERROR from vision service."""
    mock_svc = MagicMock()
    mock_svc.analyze_image.side_effect = ValueError("Unsupported image format '.tif'.")
    agent = SingleImageAnalysisAgent(vision_service=mock_svc)

    # Create a mock UploadFile with .tif extension
    mock_file = MagicMock()
    mock_file.filename = "scene.tif"
    buf = io.BytesIO(b"fake tif content")
    mock_file.file = buf

    result = agent.execute(image=mock_file, query="Analyze this.")

    assert result.status == "ERROR"
    assert "Unsupported image format" in result.message


# ──────────────────── PROMPT BUILDER UNIT TEST ───────────────────────────────

def test_prompt_builder_injects_query():
    """Ensure the prompt builder includes user query text."""
    builder = VisionPromptBuilder()
    prompt = builder.build_prompt("Is this area flooded?")

    assert "Is this area flooded?" in prompt
    assert "SatQuery AI" in prompt
    assert "Do not invent" in prompt
