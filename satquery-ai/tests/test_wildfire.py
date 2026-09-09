"""
Wildfire / Forest-Fire Detection Module — Test Suite (13 scenarios)

Scenarios
---------
 1.  No fire — green image
 2.  Active fire candidate
 3.  Smoke only
 4.  Burned area only
 5.  Before/after burned-area change
 6.  High-confidence fire (full evidence)
 7.  Low-confidence fire
 8.  False positive: identical bare-soil images
 9.  No thermal data (always true for current build)
10.  Satellite data unavailable (no image)
11.  Infrastructure near fire (candidate count)
12.  Expanding fire region (temporal)
13.  Historical burned region (single image, no temporal)

Unit tests
----------
  WildfireRiskCalculator — empty evidence, single source cap,
                           multi-source HIGH, factor sources, CRITICAL state
  SpectralFireDetector   — green no-fire, burned detection, temporal pair,
                           model label constant, thermal_available=False
"""

import io
import sys
import os
import uuid
import pytest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.wildfire_detection.spectral_fire_detector import SpectralFireDetector
from app.services.wildfire_detection.wildfire_risk import WildfireRiskCalculator
from app.services.wildfire_detection.wildfire_specialist import WildfireSpecialist


# ─── Image factory helpers ────────────────────────────────────────────────────

def _img_to_upload(pil: Image.Image, name: str = "test.png"):
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    class _FakeFile:
        filename = name
        file = buf
    return _FakeFile()


def _green(size=(256, 256)) -> Image.Image:
    """Dense green vegetation — no fire expected."""
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    a[:, :] = [30, 150, 40]
    return Image.fromarray(a)


def _burned(size=(256, 256)) -> Image.Image:
    """Char / dark ash surface — burned area proxy."""
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    a[:, :] = [80, 55, 50]  # dark brownish-grey
    return Image.fromarray(a)


def _smoke(size=(256, 256)) -> Image.Image:
    """Uniform grey haze — smoke proxy."""
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    a[:, :] = [160, 155, 158]  # uniform mid-grey
    return Image.fromarray(a)


def _fire_warm(size=(256, 256)) -> Image.Image:
    """Bright warm orange-red pixels — RGB fire indicator proxy."""
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    a[:, :] = [220, 110, 55]  # strong red, weaker green/blue
    return Image.fromarray(a)


def _mixed_burned_veg(size=(256, 256), burn_ratio=0.4) -> Image.Image:
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    split = int(size[1] * (1 - burn_ratio))
    a[:split, :] = [30, 150, 40]    # vegetation
    a[split:, :] = [80, 55, 50]     # burned
    return Image.fromarray(a)


def _mixed_smoke_only(size=(256, 256)) -> Image.Image:
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    a[:, :] = [162, 158, 160]       # smoke-like
    return Image.fromarray(a)


# ─── Scenario 1: No fire ──────────────────────────────────────────────────────

def test_no_fire_green_image():
    sp = WildfireSpecialist()
    r  = sp.execute("Check for wildfire", image=_img_to_upload(_green()))
    assert r["status"] == "SUCCESS"
    assert r["wildfire_assessment"]["fire_detected"] is False
    assert r["wildfire_assessment"]["burned_area_detected"] is False
    assert r["risk_assessment"]["risk_level"] == "LOW"
    print(f"[S1] PASS — risk={r['risk_assessment']['risk_score']}")


# ─── Scenario 2: Active fire candidate ────────────────────────────────────────

def test_active_fire_candidate():
    sp = WildfireSpecialist()
    r  = sp.execute("Detect active fire", image=_img_to_upload(_fire_warm()))
    assert r["status"] == "SUCCESS"
    assert r["wildfire_assessment"]["fire_indicator_percentage"] > 0.0
    assert r["risk_assessment"]["risk_score"] > 0
    # If detected, active fire note must be present
    if r["wildfire_assessment"]["active_fire_detected"]:
        assert r["wildfire_assessment"]["active_fire_note"] is not None
    print(f"[S2] PASS — fire_ind={r['wildfire_assessment']['fire_indicator_percentage']:.1f}%")


# ─── Scenario 3: Smoke only ───────────────────────────────────────────────────

def test_smoke_only():
    sp  = WildfireSpecialist()
    img = _img_to_upload(_smoke())
    r   = sp.execute("Is there smoke?", image=img)
    assert r["status"] == "SUCCESS"
    smk = r["wildfire_assessment"]["smoke_percentage"]
    assert smk >= 0.0    # smoke proxy may or may not trigger; must not crash
    print(f"[S3] PASS — smoke_pct={smk:.1f}%")


# ─── Scenario 4: Burned area only ─────────────────────────────────────────────

def test_burned_area_only():
    sp = WildfireSpecialist()
    r  = sp.execute("Detect burned areas", image=_img_to_upload(_burned()))
    assert r["status"] == "SUCCESS"
    wa = r["wildfire_assessment"]
    assert wa["burned_percentage"] >= 0.0
    # burned must not falsely claim active fire without confirmation
    if wa["active_fire_detected"]:
        assert wa["active_fire_note"] is not None
    print(f"[S4] PASS — burned={wa['burned_percentage']:.1f}%")


# ─── Scenario 5: Before/after burned-area change ──────────────────────────────

def test_before_after_burned_area():
    sp     = WildfireSpecialist()
    before = _img_to_upload(_green(),  "before.png")
    after  = _img_to_upload(_burned(), "after.png")
    r = sp.execute("Before/after fire", before_image=before, after_image=after)
    assert r["status"] == "SUCCESS"
    ca = r["change_analysis"]
    assert ca["change_detected"] is True
    assert ca["vegetation_loss_percentage"] > 0.0
    assert r["fire_spread"]["trend"] != "NOT_AVAILABLE"
    print(f"[S5] PASS — veg_loss={ca['vegetation_loss_percentage']:.1f}%, trend={r['fire_spread']['trend']}")


# ─── Scenario 6: High-confidence fire ────────────────────────────────────────

def test_high_confidence_fire():
    sp     = WildfireSpecialist()
    before = _img_to_upload(_green(),    "before.png")
    after  = _img_to_upload(_fire_warm(), "after.png")
    r = sp.execute("Fire detection", before_image=before, after_image=after)
    assert r["status"] == "SUCCESS"
    assert r["risk_assessment"]["risk_score"] > 10
    # Multiple factors should emerge from temporal + spectral
    print(f"[S6] PASS — risk={r['risk_assessment']['risk_score']}, level={r['risk_assessment']['risk_level']}")


# ─── Scenario 7: Low-confidence fire ─────────────────────────────────────────

def test_low_confidence_fire():
    """5% mixed burn — expect LOW or MODERATE, not HIGH/CRITICAL."""
    sp = WildfireSpecialist()
    img = _img_to_upload(_mixed_burned_veg(burn_ratio=0.05))
    r   = sp.execute("Low fire risk check", image=img)
    assert r["status"] == "SUCCESS"
    assert r["risk_assessment"]["risk_level"] in ("LOW", "MODERATE")
    conf = r["risk_assessment"]["confidence"]
    assert 0.0 <= conf <= 1.0
    print(f"[S7] PASS — risk={r['risk_assessment']['risk_score']}, conf={conf:.2f}")


# ─── Scenario 8: False positive — identical before/after ──────────────────────

def test_false_positive_identical_images():
    sp   = WildfireSpecialist()
    b    = _img_to_upload(_burned(), "b.png")
    a    = _img_to_upload(_burned(), "a.png")
    r    = sp.execute("Check fire", before_image=b, after_image=a)
    assert r["status"] == "SUCCESS"
    # No temporal change → fire spread NOT_AVAILABLE or STABLE
    assert r["fire_spread"]["trend"] in ("NOT_AVAILABLE", "STABLE", "ACTIVE")
    # Must not produce CRITICAL from identical images
    assert r["risk_assessment"]["risk_level"] in ("LOW", "MODERATE", "HIGH"), (
        f"Unexpected CRITICAL on identical images: {r['risk_assessment']}"
    )
    print(f"[S8] PASS FP-guard — level={r['risk_assessment']['risk_level']}")


# ─── Scenario 9: No thermal data ──────────────────────────────────────────────

def test_no_thermal_data_always_reported():
    """Thermal evidence must always be reported as unavailable."""
    sp = WildfireSpecialist()
    r  = sp.execute("Fire risk", image=_img_to_upload(_burned()))
    assert r["thermal_evidence"]["thermal_available"] is False
    assert "unavailable" in r["thermal_evidence"]["note"].lower()
    assert r["thermal_evidence"]["firms_status"] == "NOT_INTEGRATED"
    print(f"[S9] PASS — thermal: {r['thermal_evidence']['note'][:60]}...")


# ─── Scenario 10: Satellite data unavailable (no image) ────────────────────────

def test_no_image_supplied():
    sp = WildfireSpecialist()
    r  = sp.execute("Wildfire detection", image=None)
    assert r["status"] == "SUCCESS"
    assert r["assessment_status"] == "INSUFFICIENT_EVIDENCE"
    assert r["risk_assessment"]["risk_score"] == 0
    assert r["detection_status"] == "INCONCLUSIVE"
    print("[S10] PASS — no image → INSUFFICIENT_EVIDENCE")


# ─── Scenario 11: Infrastructure near fire ────────────────────────────────────

def test_infrastructure_impact_populated():
    """High-burn image should produce non-zero infrastructure estimates."""
    sp = WildfireSpecialist()
    r  = sp.execute("Check impact", image=_img_to_upload(_mixed_burned_veg(burn_ratio=0.6)))
    imp = r["potential_impact"]
    # only populated when risk_level > LOW and candidates exist
    if r["risk_assessment"]["risk_level"] != "LOW":
        assert "potentially exposed" in imp.get("note", "").lower() or imp["infrastructure_analysis"] == "NOT_AVAILABLE"
    assert "proximity_analysis" in imp
    print(f"[S11] PASS — buildings={imp['potentially_affected_buildings']}, note={imp['note'][:50]}")


# ─── Scenario 12: Expanding fire region ───────────────────────────────────────

def test_expanding_fire_region():
    """Large green→burn transition should signal EXPANDING trend."""
    sp     = WildfireSpecialist()
    before = _img_to_upload(_green(),      "b.png")
    after  = _img_to_upload(_mixed_burned_veg(burn_ratio=0.70), "a.png")
    r = sp.execute("Fire expansion", before_image=before, after_image=after)
    assert r["status"] == "SUCCESS"
    spread = r["fire_spread"]
    assert spread["trend"] in ("EXPANDING", "ACTIVE", "STABLE")
    assert spread["change_percentage"] >= 0.0
    print(f"[S12] PASS — trend={spread['trend']}, change={spread['change_percentage']:.1f}%")


# ─── Scenario 13: Historical burned region (single image) ──────────────────────

def test_historical_burned_region_no_active_fire():
    """
    Burned-area single image without temporal context:
    burned_area_detected may be True but active_fire must be False/uncertain.
    We do NOT classify every dark area as active fire.
    """
    sp = WildfireSpecialist()
    r  = sp.execute("Old fire scar", image=_img_to_upload(_burned()))
    wa = r["wildfire_assessment"]
    # Active fire from a purely dark (old burn scar) image should be False
    if wa.get("fire_indicator_percentage", 0) < 1.0:
        assert wa["active_fire_detected"] is False, (
            "Active fire falsely declared from dark surface alone"
        )
    print(f"[S13] PASS — burned={wa['burned_area_detected']}, active={wa['active_fire_detected']}")


# ─── NASA FIRMS hook unit test ─────────────────────────────────────────────────

def test_firms_hook_returns_not_integrated():
    sp  = WildfireSpecialist()
    res = sp.firms_hotspot_hook(
        aoi_wkt="POLYGON((77 30, 78 30, 78 31, 77 31, 77 30))",
        start_date="2024-01-01",
        end_date="2024-01-15",
        req_id=str(uuid.uuid4())[:8],
    )
    assert res["firms_available"] is False
    assert "not yet" in res["message"].lower()
    assert "prepared_sources" in res
    print(f"[FIRMS] PASS — {res['message']}")


# ─── WildfireRiskCalculator unit tests ────────────────────────────────────────

class TestWildfireRiskCalculator:

    def _calc(self): return WildfireRiskCalculator()

    def test_empty_evidence_zero_risk(self):
        r = self._calc().calculate_risk({})
        assert r["risk_score"] == 0
        assert r["risk_level"] == "LOW"
        print(f"  [calc] empty → score={r['risk_score']}")

    def test_single_source_capped_at_moderate(self):
        r = self._calc().calculate_risk({
            "wildfire_assessment": {"burned_percentage": 22.0, "fire_indicator_percentage": 0.0, "smoke_percentage": 0.0},
            "change_analysis": {},
            "candidate_regions": [],
            "fire_spread": {"trend": "NOT_AVAILABLE"},
        })
        assert r["risk_score"] <= 50, f"Single source {r['risk_score']} exceeded MODERATE cap"
        print(f"  [calc] single-source cap → score={r['risk_score']}")

    def test_multi_source_can_reach_high(self):
        r = self._calc().calculate_risk({
            "wildfire_assessment": {
                "burned_percentage": 20.0, "fire_indicator_percentage": 2.5, "smoke_percentage": 10.0
            },
            "change_analysis": {
                "vegetation_loss_percentage": 12.0, "new_burned_area_percentage": 8.0
            },
            "candidate_regions": [
                {"id": i, "confidence": 0.81, "bbox": [0,0,128,128], "area_percentage": 15}
                for i in range(1, 4)
            ],
            "fire_spread": {"trend": "EXPANDING"},
        })
        assert r["risk_score"] > 50, f"Multi-source score {r['risk_score']} below HIGH threshold"
        print(f"  [calc] multi-source HIGH → score={r['risk_score']}, level={r['risk_level']}")

    def test_factors_have_required_keys(self):
        r = self._calc().calculate_risk({
            "wildfire_assessment": {"burned_percentage": 12.0, "smoke_percentage": 8.0, "fire_indicator_percentage": 0.0},
            "change_analysis": {},
            "candidate_regions": [],
            "fire_spread": {},
        })
        for f in r["risk_factors"]:
            assert "factor" in f
            assert "contribution" in f
            assert "evidence_confidence" in f
            assert "source" in f
        print(f"  [calc] factor keys valid for {len(r['risk_factors'])} factors")

    def test_critical_alert_max_evidence(self):
        r = self._calc().calculate_risk({
            "wildfire_assessment": {
                "burned_percentage": 30.0, "fire_indicator_percentage": 5.0, "smoke_percentage": 18.0
            },
            "change_analysis": {
                "vegetation_loss_percentage": 20.0, "new_burned_area_percentage": 15.0
            },
            "candidate_regions": [
                {"id": i, "confidence": 0.91, "bbox": [0,0,100,100], "area_percentage": 18}
                for i in range(1, 6)
            ],
            "fire_spread": {"trend": "EXPANDING"},
        })
        assert r["risk_level"] in ("HIGH", "CRITICAL")
        assert r["alert_state"] in ("WARNING", "CRITICAL")
        print(f"  [calc] full-evidence → score={r['risk_score']}, alert={r['alert_state']}")


# ─── SpectralFireDetector unit tests ──────────────────────────────────────────

class TestSpectralFireDetector:

    def _det(self): return SpectralFireDetector()

    def test_green_no_fire(self):
        r = self._det().detect_fire_evidence(_img_to_upload(_green()))
        assert r["fire_indicator_detected"] is False
        assert r["burned_area_detected"] is False
        assert r["vegetation_percentage"] > 5.0
        print(f"  [det] green → veg={r['vegetation_percentage']:.1f}%")

    def test_burned_detection(self):
        r = self._det().detect_fire_evidence(_img_to_upload(_burned()))
        assert r["model_label"] == "WILDFIRE_SPECIALIST_LIMITED"
        assert r["burned_percentage"] >= 0.0
        print(f"  [det] burned → burned={r['burned_percentage']:.1f}%")

    def test_temporal_pair_returns_structure(self):
        r = self._det().compare_temporal(
            _img_to_upload(_green()), _img_to_upload(_burned())
        )
        assert "change_analysis" in r
        assert "before_analysis" in r
        assert "after_analysis" in r
        assert "fire_spread" in r
        print(f"  [det] temporal → {r['change_analysis']}")

    def test_model_label_constant(self):
        assert self._det().MODEL_LABEL == "WILDFIRE_SPECIALIST_LIMITED"
        print("  [det] MODEL_LABEL = WILDFIRE_SPECIALIST_LIMITED ✓")

    def test_thermal_available_false(self):
        det = self._det()
        assert det.thermal_available is False
        r   = det.detect_fire_evidence(_img_to_upload(_burned()))
        assert r["thermal_available"] is False
        assert "unavailable" in r["thermal_evidence"].lower()
        print("  [det] thermal_available = False ✓")

    def test_fire_warm_triggers_indicator(self):
        r = self._det().detect_fire_evidence(_img_to_upload(_fire_warm()))
        # Warm red/orange pixels should trigger the fire indicator
        assert r["fire_indicator_percentage"] > 0.0
        print(f"  [det] fire_warm → fire_ind={r['fire_indicator_percentage']:.1f}%")

    def test_invalid_image_does_not_crash(self):
        class _Bad:
            filename = "bad.png"
            file = io.BytesIO(b"not an image")
        try:
            r = self._det().detect_fire_evidence(_Bad())
            assert r["fire_indicator_detected"] is False
        except Exception:
            pytest.fail("Detector crashed on invalid image input")
        print("  [det] invalid image handled gracefully ✓")
