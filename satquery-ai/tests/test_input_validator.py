import pytest
from app.services.input_validator import InputValidator
from app.models.schemas import AvailableInputs
from app.config.intents import Intents, HazardTypes

@pytest.fixture
def validator():
    return InputValidator()

def test_missing_available_inputs(validator):
    # No available inputs should result in UNKNOWN sufficiency
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.CHANGE_DETECTION,
        hazard_type=None,
        available_inputs=None
    )
    assert sufficiency == "UNKNOWN"
    assert needs_clarify is False
    assert message is None

def test_glacier_missing_inputs(validator):
    # Glacier monitoring query should require clarification even with no available inputs provided
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.DISASTER_HAZARD_ANALYSIS,
        hazard_type=HazardTypes.GLACIER_GLOF,
        available_inputs=None
    )
    assert sufficiency == "UNKNOWN"
    assert needs_clarify is True
    assert "Historical satellite imagery may be required" in message

def test_change_detection_insufficient_inputs(validator):
    # Available inputs: only 1 image. Change detection requires 2.
    inputs = AvailableInputs(image_count=1, modalities=["OPTICAL"], has_metadata=True)
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.CHANGE_DETECTION,
        hazard_type=None,
        available_inputs=inputs
    )
    assert sufficiency == "INSUFFICIENT"
    assert needs_clarify is True
    assert "requires at least two satellite images" in message

def test_change_detection_sufficient_inputs(validator):
    # Available inputs: 2 images. Sufficient.
    inputs = AvailableInputs(image_count=2, modalities=["OPTICAL"], has_metadata=True)
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.CHANGE_DETECTION,
        hazard_type=None,
        available_inputs=inputs
    )
    assert sufficiency == "SUFFICIENT"
    assert needs_clarify is False
    assert message is None

def test_multimodal_insufficient_modalities(validator):
    # Available inputs: 2 images but both OPTICAL (missing SAR). Multimodal requires both.
    inputs = AvailableInputs(image_count=2, modalities=["OPTICAL"], has_metadata=True)
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.MULTIMODAL_ANALYSIS,
        hazard_type=None,
        available_inputs=inputs
    )
    assert sufficiency == "INSUFFICIENT"
    assert needs_clarify is True
    assert "requires both OPTICAL and SAR" in message

def test_multimodal_sufficient_modalities(validator):
    # Available inputs: 2 images containing OPTICAL and SAR.
    inputs = AvailableInputs(image_count=2, modalities=["OPTICAL", "SAR"], has_metadata=True)
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.MULTIMODAL_ANALYSIS,
        hazard_type=None,
        available_inputs=inputs
    )
    assert sufficiency == "SUFFICIENT"
    assert needs_clarify is False
    assert message is None

def test_unknown_intent_validation(validator):
    sufficiency, needs_clarify, message = validator.validate(
        intent=Intents.UNKNOWN,
        hazard_type=None,
        available_inputs=None
    )
    assert sufficiency == "UNKNOWN"
    assert needs_clarify is True
    assert "could not understand your request" in message
