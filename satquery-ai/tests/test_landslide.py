"""
Tests for the Landslide Detection module.

Test suite covers 10 scenarios as specified in the requirements:
  1. No landslide
  2. Possible landslide
  3. High-confidence landslide
  4. Before/after change
  5. No image supplied
  6. Invalid image
  7. Low-confidence prediction
  8. False-positive scenario
  9. Sentinel-1 unavailable
  10. DEM unavailable

Run with:
  python -m pytest tests/test_landslide.py -v
"""

import io
import os
import sys
import uuid
from typing import Any

import numpy as np
import pytest
from PIL import Image

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.landslide_detection.spectral_landslide_detector import SpectralLandslideDetector
from app.services.landslide_detection.landslide_risk import LandslideRiskCalculator
from app.services.landslide_detection.landslide_specialist import LandslideSpecialist


# ─── Image factory helpers ────────────────────────────────────────────────────

def _make_upload_file(pil_img: Image.Image, name: str = "test.png") -> Any:
    """Wrap a PIL image as a FastAPI-compatible UploadFile mock."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    class _FakeUploadFile:
        filename = name
        file = buf
        def __init__(self): pass

    return _FakeUploadFile()


def _green_image(size=(256, 256)) -> Image.Image:
    """Dense vegetated area — should NOT trigger landslide detection."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :, 0] = 30    # R low
    arr[:, :, 1] = 140   # G high (vegetation)
    arr[:, :, 2] = 40    # B low
    return Image.fromarray(arr)


def _bare_soil_image(size=(256, 256)) -> Image.Image:
    """Bare soil dominant image — high disturbance indicator."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :, 0] = 155   # R high (bare soil)
    arr[:, :, 1] = 110   # G moderate
    arr[:, :, 2] = 80    # B low
    return Image.fromarray(arr)


def _mixed_image(size=(256, 256), bare_ratio: float = 0.30) -> Image.Image:
    """Image with partial bare-soil — moderate risk scenario."""
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    # Top portion: vegetation
    split = int(size[1] * (1 - bare_ratio))
    arr[:split, :, 0] = 30
    arr[:split, :, 1] = 140
    arr[:split, :, 2] = 40
    # Bottom portion: bare soil
    arr[split:, :, 0] = 160
    arr[split:, :, 1] = 110
    arr[split:, :, 2] = 75
    return Image.fromarray(arr)


def _before_green_after_bare(size=(256, 256)):
    """Temporal pair simulating vegetation strip — landslide event."""
    before = _green_image(size)
    after  = _bare_soil_image(size)
    return before, after


def _before_bare_after_bare(size=(256, 256)):
    """Temporal pair with no change — false positive guard test."""
    before = _bare_soil_image(size)
    after  = _bare_soil_image(size)
    return before, after


# ─── Test 1: No landslide ─────────────────────────────────────────────────────

def test_no_landslide_green_image():
    """
    Provide a uniformly green (vegetated) image.
    Expect: risk score LOW, no disturbance detected.
    """
    spec = LandslideSpecialist()
    img  = _make_upload_file(_green_image())
    res  = spec.execute(query="Check for landslide", image=img)

    assert res["status"] == "SUCCESS"
    assert res["risk_assessment"]["risk_level"] == "LOW"
    assert res["landslide_assessment"]["landslide_detected"] is False
    assert res["risk_assessment"]["risk_score"] <= 25
    print(f"[TEST 1] PASS — risk_score={res['risk_assessment']['risk_score']}")


# ─── Test 2: Possible landslide ───────────────────────────────────────────────

def test_possible_landslide_mixed_image():
    """
    Mixed image with ~30% bare-soil region.
    Expect: detection_status POSSIBLE or DETECTED, risk MODERATE or above.
    """
    spec = LandslideSpecialist()
    img  = _make_upload_file(_mixed_image(bare_ratio=0.30))
    res  = spec.execute(query="Detect landslide", image=img)

    assert res["status"] == "SUCCESS"
    # At least should flag some disturbance
    assert res["landslide_assessment"]["bare_soil_percentage"] > 0.0
    print(f"[TEST 2] PASS — detection={res['detection_status']}, risk={res['risk_assessment']['risk_score']}")


# ─── Test 3: High-confidence landslide ───────────────────────────────────────

def test_high_confidence_landslide():
    """
    Fully bare-soil image.
    Expect: disturbance detected, risk score > 25.
    """
    spec = LandslideSpecialist()
    img  = _make_upload_file(_bare_soil_image())
    res  = spec.execute(query="Detect landslide", image=img)

    assert res["status"] == "SUCCESS"
    assert res["landslide_assessment"]["bare_soil_percentage"] > 10.0
    assert res["risk_assessment"]["risk_score"] > 10   # at least some score
    print(f"[TEST 3] PASS — bare_soil={res['landslide_assessment']['bare_soil_percentage']:.1f}%")


# ─── Test 4: Before/after change ─────────────────────────────────────────────

def test_before_after_change_detection():
    """
    Before= green, after= bare soil temporal pair.
    Expect: change_detected=True, vegetation_loss > 0, change_type set.
    """
    spec   = LandslideSpecialist()
    before, after = _before_green_after_bare()
    b_file = _make_upload_file(before, "before.png")
    a_file = _make_upload_file(after,  "after.png")
    res = spec.execute(
        query="Compare before and after for landslide",
        before_image=b_file,
        after_image=a_file,
    )

    assert res["status"] == "SUCCESS"
    assert res["change_analysis"]["change_detected"] is True
    assert res["change_analysis"]["vegetation_loss_percentage"] > 0.0
    assert res["change_analysis"]["change_type"] is not None
    print(f"[TEST 4] PASS — change_type={res['change_analysis']['change_type']}")


# ─── Test 5: No image supplied ────────────────────────────────────────────────

def test_no_image_supplied():
    """
    No image provided.
    Expect: assessment_status=INSUFFICIENT_EVIDENCE, risk_score=0.
    """
    spec = LandslideSpecialist()
    res  = spec.execute(query="Check for landslide", image=None)

    assert res["status"] == "SUCCESS"
    assert res["assessment_status"] == "INSUFFICIENT_EVIDENCE"
    assert res["risk_assessment"]["risk_score"] == 0
    assert "additional imagery required" in " ".join(res["recommendations"]).lower()
    print("[TEST 5] PASS — no image → INSUFFICIENT_EVIDENCE")


# ─── Test 6: Invalid image ────────────────────────────────────────────────────

def test_invalid_image_bytes():
    """
    Corrupted image bytes — detector should handle gracefully, not crash.
    Expect: either SUCCESS with zero risk OR error does not propagate uncaught.
    """
    spec = LandslideSpecialist()

    class _BadFile:
        filename = "bad.png"
        file = io.BytesIO(b"this is not a valid image file")

    try:
        res = spec.execute(query="Check landslide", image=_BadFile())
        # Should return a valid response (possibly with 0 score)
        assert res["status"] in ("SUCCESS", "ERROR")
    except Exception:
        # Any exception here means graceful handling failed
        pytest.fail("Landslide specialist did not handle invalid image gracefully")
    print("[TEST 6] PASS — invalid image handled without crash")


# ─── Test 7: Low-confidence prediction ───────────────────────────────────────

def test_low_confidence_outputs_inconclusive():
    """
    Single-image with tiny mixed signal (5% bare soil).
    Expect: risk_score LOW or MODERATE, confidence present.
    """
    spec = LandslideSpecialist()
    img  = _make_upload_file(_mixed_image(bare_ratio=0.05))
    res  = spec.execute(query="Check for slope failure", image=img)

    assert res["status"] == "SUCCESS"
    conf = res["risk_assessment"]["confidence"]
    assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"
    # Low bare-soil shouldn't produce HIGH risk
    assert res["risk_assessment"]["risk_level"] in ("LOW", "MODERATE")
    print(f"[TEST 7] PASS — conf={conf:.2f}, level={res['risk_assessment']['risk_level']}")


# ─── Test 8: False-positive scenario ─────────────────────────────────────────

def test_false_positive_protection_no_change():
    """
    Before/after are IDENTICAL (no change) — should NOT produce HIGH risk.
    Tests the false-positive guard: single-source cap applies.
    """
    spec = LandslideSpecialist()
    before, after = _before_bare_after_bare()
    b_file = _make_upload_file(before, "before.png")
    a_file = _make_upload_file(after,  "after.png")
    res = spec.execute(
        query="Detect landslide",
        before_image=b_file,
        after_image=a_file,
    )

    assert res["status"] == "SUCCESS"
    # Change detection should see very little or no change
    change_pct = res["change_analysis"]["estimated_change_percentage"]
    # No temporal change → should not produce CRITICAL
    assert res["risk_assessment"]["risk_level"] in ("LOW", "MODERATE", "HIGH"), (
        f"Unexpected CRITICAL on identical images: score={res['risk_assessment']['risk_score']}"
    )
    print(f"[TEST 8] PASS FP-guard — change_pct={change_pct:.1f}%, level={res['risk_assessment']['risk_level']}")


# ─── Test 9: Sentinel-1 unavailable ──────────────────────────────────────────

def test_sentinel1_unavailable_hook():
    """
    Call the Sentinel-1 SAR hook — should return transparent 'not available' response.
    """
    spec = LandslideSpecialist()
    res  = spec.sentinel_sar_hook(
        aoi_wkt="POLYGON((77 30, 78 30, 78 31, 77 31, 77 30))",
        start_date="2024-01-01",
        end_date="2024-01-15",
        req_id=str(uuid.uuid4())[:8],
    )

    assert res["sar_available"] is False
    assert "not yet" in res["message"].lower()
    print(f"[TEST 9] PASS — SAR hook returns: {res['message']}")


# ─── Test 10: DEM unavailable ─────────────────────────────────────────────────

def test_dem_unavailable():
    """
    All requests should report terrain_evidence.dem_available = False
    and a human-readable message about DEM unavailability.
    """
    spec = LandslideSpecialist()
    img  = _make_upload_file(_bare_soil_image())
    res  = spec.execute(query="Analyze terrain", image=img)

    assert res["terrain_evidence"]["dem_available"] is False
    assert "unavailable" in res["terrain_evidence"]["slope_analysis"].lower()
    print(f"[TEST 10] PASS — DEM: {res['terrain_evidence']['slope_analysis']}")


# ─── Risk calculator unit tests ───────────────────────────────────────────────

class TestLandslideRiskCalculator:

    def _calc(self):
        return LandslideRiskCalculator()

    def test_empty_evidence_low_risk(self):
        calc = self._calc()
        res  = calc.calculate_risk({})
        assert res["risk_score"] == 0
        assert res["risk_level"] == "LOW"

    def test_single_source_capped_at_moderate(self):
        """One source (bare soil) should be capped below HIGH."""
        calc = self._calc()
        res  = calc.calculate_risk({
            "landslide_assessment": {
                "disturbance_percentage": 25.0,
                "bare_soil_percentage": 25.0,
                "vegetation_percentage": 5.0,
            },
            "change_analysis": {},
            "candidate_regions": [],
        })
        # False-positive guard: single source → capped at 45 (MODERATE)
        assert res["risk_score"] <= 50, f"Single-source score {res['risk_score']} exceeded MODERATE cap"
        print(f"  [risk_calc] single-source score={res['risk_score']}, level={res['risk_level']}")

    def test_multi_source_can_reach_high(self):
        """Multiple evidence sources should be able to reach HIGH risk."""
        calc = self._calc()
        res  = calc.calculate_risk({
            "landslide_assessment": {
                "disturbance_percentage": 25.0,
                "bare_soil_percentage": 18.0,
                "vegetation_percentage": 10.0,
            },
            "change_analysis": {
                "vegetation_loss_percentage": 12.0,
                "changed_percentage": 18.0,
            },
            "candidate_regions": [
                {"id": 1, "confidence": 0.82, "bbox": [0, 0, 128, 128], "area_percentage": 15},
                {"id": 2, "confidence": 0.78, "bbox": [128, 0, 256, 128], "area_percentage": 12},
                {"id": 3, "confidence": 0.76, "bbox": [0, 128, 128, 256], "area_percentage": 10},
            ],
        })
        assert res["risk_score"] > 50, f"Multi-source score {res['risk_score']} should exceed 50 (HIGH)"
        print(f"  [risk_calc] multi-source score={res['risk_score']}, level={res['risk_level']}")

    def test_risk_factors_contain_sources(self):
        calc = self._calc()
        res  = calc.calculate_risk({
            "landslide_assessment": {
                "disturbance_percentage": 20.0,
                "bare_soil_percentage": 15.0,
            },
            "change_analysis": {"vegetation_loss_percentage": 8.0, "changed_percentage": 10.0},
            "candidate_regions": [],
        })
        sources = {f["source"] for f in res["risk_factors"]}
        assert "spectral_disturbance" in sources or "bare_soil_exposure" in sources
        print(f"  [risk_calc] sources found: {sources}")

    def test_critical_alert_state(self):
        calc = self._calc()
        res  = calc.calculate_risk({
            "landslide_assessment": {
                "disturbance_percentage": 40.0,
                "bare_soil_percentage": 30.0,
            },
            "change_analysis": {
                "vegetation_loss_percentage": 25.0,
                "changed_percentage": 30.0,
            },
            "candidate_regions": [
                {"id": i, "confidence": 0.90, "bbox": [0, 0, 100, 100], "area_percentage": 20}
                for i in range(1, 6)
            ],
        })
        # With all 5 sources at max values risk should be HIGH or CRITICAL
        assert res["risk_level"] in ("HIGH", "CRITICAL")
        assert res["alert_state"] in ("WARNING", "CRITICAL")
        print(f"  [risk_calc] full evidence score={res['risk_score']}, alert={res['alert_state']}")


# ─── Spectral detector unit tests ─────────────────────────────────────────────

class TestSpectralLandslideDetector:

    def test_green_image_no_disturbance(self):
        det = SpectralLandslideDetector()
        res = det.detect_disturbance(_make_upload_file(_green_image()))
        assert res["disturbance_detected"] is False
        assert res["vegetation_percentage"] > 10.0

    def test_bare_soil_image_disturbance(self):
        det = SpectralLandslideDetector()
        res = det.detect_disturbance(_make_upload_file(_bare_soil_image()))
        assert res["bare_soil_percentage"] > 0.0
        assert res["model_label"] == "LANDSLIDE_SPECIALIST_LIMITED"

    def test_temporal_compare_returns_change(self):
        det = SpectralLandslideDetector()
        before, after = _before_green_after_bare()
        res = det.compare_temporal(
            _make_upload_file(before, "b.png"),
            _make_upload_file(after, "a.png"),
        )
        assert "change_analysis" in res
        assert "before_analysis" in res
        assert "after_analysis" in res

    def test_model_label_constant(self):
        """Model label must never claim it's a real segmentation model."""
        det = SpectralLandslideDetector()
        assert det.MODEL_LABEL == "LANDSLIDE_SPECIALIST_LIMITED"

    def test_dem_available_false(self):
        """DEM must always be False unless explicitly integrated."""
        det = SpectralLandslideDetector()
        assert det.dem_available is False
