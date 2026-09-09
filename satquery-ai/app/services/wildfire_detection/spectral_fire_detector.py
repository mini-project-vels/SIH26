"""
SpectralFireDetector
====================
Pixel-level spectral analysis for wildfire and burned-area detection
from optical satellite imagery (RGB / RGBA).

Methodology (fully disclosed)
------------------------------
No dedicated thermal or SWIR fire-detection sensor is available in this
deployment.  Instead, physically-motivated RGB spectral heuristics are used:

  1. Burned-area index  — dark, low-reflectance surfaces replacing green veg
  2. Smoke proxy        — hazy, greyish, washed-out pixels
  3. Vegetation proxy   — green-channel dominant pixels
  4. Char/ash proxy     — near-black low-value pixels
  5. Before/after temporal difference for fire-scar expansion

Thermal / SWIR
--------------
Active-fire hotspot detection normally requires SWIR/TIR bands (e.g.,
Band 7 Landsat, MODIS 21/22, VIIRS I4/M13).  These bands are NOT present
in standard RGB imagery.  The system therefore:
  - Labels all fire candidates as SPECTRAL_HEURISTIC_LIMITED
  - Explicitly reports "Thermal fire evidence unavailable."
  - Maintains architectural hooks for NASA FIRMS / MODIS / VIIRS / Sentinel-3

Detection labels
----------------
  WILDFIRE_SPECIALIST_LIMITED  — no dedicated fire segmentation model
  OPTICAL_SPECTRAL_HEURISTIC   — RGB-based spectral proxy detection
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger("satquery.wildfire.detector")

ANALYSIS_RESOLUTION = (512, 512)

# ── Tunable thresholds ──────────────────────────────────────────────────────
# Vegetation proxy: high green channel dominance
VEG_GREEN_MIN   = 0.32

# Burned-area proxy: dark surface (all channels low, red slightly dominant)
BURNED_MAX_VAL  = 0.40    # all channels below this for char/deep-burn
BURNED_RED_EDGE = 0.30    # red slightly higher than green for reddish ash

# Smoke proxy: uniformly grey/hazy (channels roughly equal, mid-range)
SMOKE_MIN_VAL   = 0.35
SMOKE_MAX_VAL   = 0.80
SMOKE_BALANCE   = 0.10    # max channel difference for grey balance

# Fire-indicator proxy: bright warm red/orange (RGB only)
FIRE_RED_MIN    = 0.60
FIRE_GREEN_MAX  = 0.55
FIRE_BLUE_MAX   = 0.40

# Change threshold for temporal difference
CHANGE_DIFF_THRESHOLD = 0.10


def _load_as_pil(src: Any) -> Image.Image:
    if isinstance(src, Image.Image):
        return src.convert("RGB")
    if hasattr(src, "file"):
        src.file.seek(0)
        return Image.open(src.file).convert("RGB")
    if isinstance(src, tuple) and len(src) == 2:
        _, data = src
        return Image.open(io.BytesIO(data)).convert("RGB")
    if isinstance(src, (str, bytes)):
        if isinstance(src, bytes):
            return Image.open(io.BytesIO(src)).convert("RGB")
        return Image.open(src).convert("RGB")
    raise TypeError(f"Cannot load image from {type(src)}")


def _resize(img: Image.Image, size=ANALYSIS_RESOLUTION) -> Image.Image:
    return img.resize(size, Image.Resampling.LANCZOS)


def _to_float(img: Image.Image) -> np.ndarray:
    return np.array(img, dtype=np.float32) / 255.0


class SpectralFireDetector:
    """
    RGB spectral heuristic detector for wildfire evidence in satellite imagery.

    Detection labels:
      WILDFIRE_SPECIALIST_LIMITED  — no trained fire-seg model
      OPTICAL_SPECTRAL_HEURISTIC   — proxy-based spectral analysis only
    """

    DATA_SOURCE  = "OPTICAL_SPECTRAL_HEURISTIC"
    MODEL_LABEL  = "WILDFIRE_SPECIALIST_LIMITED"
    thermal_available: bool = False   # NASA FIRMS / VIIRS not integrated

    # ── Single-image fire evidence analysis ─────────────────────────────────

    def detect_fire_evidence(
        self,
        image_src: Any,
        request_id: str = "N/A",
    ) -> Dict[str, Any]:
        """
        Analyse a single satellite image for wildfire evidence.

        Returns keys:
          fire_indicator_detected, burned_area_detected, smoke_detected,
          vegetation_percentage, burned_percentage, smoke_percentage,
          fire_indicator_percentage, candidate_regions, method, model_label
        """
        try:
            pil = _resize(_load_as_pil(image_src))
        except Exception as exc:
            logger.error("[%s] Cannot load image: %s", request_id, exc)
            return self._empty_single()

        arr = _to_float(pil)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        total_px = r.size

        # ── Vegetation mask ────────────────────────────────────────────────
        veg_mask = (g > VEG_GREEN_MIN) & (g > r) & (g > b)

        # ── Burned-area mask (char / dark ash / darkened surface) ──────────
        # Darkened surface, all channels low, red slightly >= others
        burned_mask = (
            (r < BURNED_MAX_VAL) &
            (g < BURNED_MAX_VAL - 0.05) &
            (b < BURNED_MAX_VAL - 0.05) &
            (r >= g) &
            ~veg_mask
        )

        # ── Smoke mask (uniform grey haze, mid-brightness) ─────────────────
        ch_max = np.maximum(np.maximum(r, g), b)
        ch_min = np.minimum(np.minimum(r, g), b)
        smoke_mask = (
            (ch_max > SMOKE_MIN_VAL) &
            (ch_max < SMOKE_MAX_VAL) &
            ((ch_max - ch_min) < SMOKE_BALANCE)
        )

        # ── Active-fire indicator (warm red/orange pixels — RGB only) ───────
        fire_mask = (
            (r > FIRE_RED_MIN) &
            (g < FIRE_GREEN_MAX) &
            (b < FIRE_BLUE_MAX) &
            (r > g * 1.20)
        )

        # ── Percentages ────────────────────────────────────────────────────
        veg_pct  = round(float(veg_mask.sum())    / total_px * 100, 2)
        burn_pct = round(float(burned_mask.sum()) / total_px * 100, 2)
        smk_pct  = round(float(smoke_mask.sum())  / total_px * 100, 2)
        fire_pct = round(float(fire_mask.sum())   / total_px * 100, 2)

        # ── Combined wildfire region mask ───────────────────────────────────
        combined = burned_mask | fire_mask
        candidate_regions = self._extract_candidates(combined, arr.shape)

        burned_detected = burn_pct > 4.0
        smoke_detected  = smk_pct  > 6.0
        fire_detected   = fire_pct > 0.5   # RGB proxy only — very uncertain

        logger.info(
            "[%s] Fire evidence: burned=%.1f%%, smoke=%.1f%%, "
            "fire_indicator=%.1f%%, veg=%.1f%%",
            request_id, burn_pct, smk_pct, fire_pct, veg_pct
        )

        return {
            "fire_indicator_detected":    fire_detected,
            "burned_area_detected":       burned_detected,
            "smoke_detected":             smoke_detected,
            "vegetation_percentage":      veg_pct,
            "burned_percentage":          burn_pct,
            "smoke_percentage":           smk_pct,
            "fire_indicator_percentage":  fire_pct,
            "affected_area_percentage":   round(burn_pct + fire_pct, 2),
            "affected_pixels":            int(combined.sum()),
            "burned_mask_array":          burned_mask,
            "smoke_mask_array":           smoke_mask,
            "fire_mask_array":            fire_mask,
            "candidate_regions":          candidate_regions,
            "method":                     "SPECTRAL_FIRE_INDEX",
            "model_label":                self.MODEL_LABEL,
            "data_source":                self.DATA_SOURCE,
            "thermal_available":          self.thermal_available,
            "thermal_evidence":           "Thermal fire evidence unavailable.",
        }

    # ── Before / after temporal change analysis ─────────────────────────────

    def compare_temporal(
        self,
        before_src: Any,
        after_src: Any,
        request_id: str = "N/A",
    ) -> Dict[str, Any]:
        """
        Detect burned-area expansion and fire-scar development between two
        satellite acquisitions.

        Workflow:
          1. Align (resize both to same resolution)
          2. Per-channel absolute difference
          3. Vegetation-loss layer (green reduction)
          4. New burned-area layer (darkening where green was)
          5. Smoke increase layer
          6. Candidate region extraction

        Returns combined analysis + per-image breakdowns.
        """
        try:
            b_pil = _resize(_load_as_pil(before_src))
            a_pil = _resize(_load_as_pil(after_src))
        except Exception as exc:
            logger.error("[%s] Temporal load failure: %s", request_id, exc)
            return self._empty_temporal()

        b_arr = _to_float(b_pil)
        a_arr = _to_float(a_pil)

        br, bg, bb_ = b_arr[:,:,0], b_arr[:,:,1], b_arr[:,:,2]
        ar, ag, ab_ = a_arr[:,:,0], a_arr[:,:,1], a_arr[:,:,2]

        # ── Overall change ────────────────────────────────────────────────
        diff = np.abs(a_arr - b_arr).mean(axis=2)
        change_mask = diff > CHANGE_DIFF_THRESHOLD

        # ── Vegetation loss ───────────────────────────────────────────────
        b_veg = (bg > VEG_GREEN_MIN) & (bg > br)
        a_veg = (ag > VEG_GREEN_MIN) & (ag > ar)
        veg_loss = b_veg & ~a_veg & change_mask

        # ── New burned area (pixels that darkened into burned category) ───
        b_burned = (br < BURNED_MAX_VAL) & (bg < BURNED_MAX_VAL - 0.05) & (br >= bg)
        a_burned = (ar < BURNED_MAX_VAL) & (ag < BURNED_MAX_VAL - 0.05) & (ar >= ag)
        new_burned = a_burned & ~b_burned & change_mask

        # ── Smoke increase ─────────────────────────────────────────────────
        b_mx = np.maximum(np.maximum(br,bg),bb_)
        a_mx = np.maximum(np.maximum(ar,ag),ab_)
        b_mn = np.minimum(np.minimum(br,bg),bb_)
        a_mn = np.minimum(np.minimum(ar,ag),ab_)
        b_smk = (b_mx>SMOKE_MIN_VAL)&(b_mx<SMOKE_MAX_VAL)&((b_mx-b_mn)<SMOKE_BALANCE)
        a_smk = (a_mx>SMOKE_MIN_VAL)&(a_mx<SMOKE_MAX_VAL)&((a_mx-a_mn)<SMOKE_BALANCE)
        new_smoke = a_smk & ~b_smk & change_mask

        total_px = diff.size
        changed_pct  = round(float(change_mask.sum()) / total_px * 100, 2)
        veg_loss_pct = round(float(veg_loss.sum())    / total_px * 100, 2)
        new_burn_pct = round(float(new_burned.sum())  / total_px * 100, 2)
        new_smk_pct  = round(float(new_smoke.sum())   / total_px * 100, 2)

        change_detected = changed_pct > 2.0

        # ── Change type ───────────────────────────────────────────────────
        if new_burn_pct > 5.0 and veg_loss_pct > 3.0:
            change_type = "VEGETATION_LOSS_BURNED_AREA_EXPANSION"
        elif new_burn_pct > 5.0:
            change_type = "NEW_BURNED_AREA"
        elif veg_loss_pct > 5.0:
            change_type = "VEGETATION_LOSS"
        elif new_smk_pct > 4.0:
            change_type = "SMOKE_INCREASE"
        elif change_detected:
            change_type = "SURFACE_CHANGE"
        else:
            change_type = None

        # ── Fire spread trend ─────────────────────────────────────────────
        if new_burn_pct > 10.0:
            trend = "EXPANDING"
        elif new_burn_pct > 3.0:
            trend = "ACTIVE"
        elif change_detected:
            trend = "STABLE"
        else:
            trend = "NOT_AVAILABLE"

        combined_mask = change_mask & (veg_loss | new_burned | new_smoke)
        candidate_regions = self._extract_candidates(combined_mask, a_arr.shape)

        before_analysis = self.detect_fire_evidence(before_src, request_id + "_before")
        after_analysis  = self.detect_fire_evidence(after_src,  request_id + "_after")

        logger.info(
            "[%s] Temporal fire: changed=%.1f%%, veg_loss=%.1f%%, "
            "new_burned=%.1f%%, new_smoke=%.1f%%, trend=%s",
            request_id, changed_pct, veg_loss_pct, new_burn_pct, new_smk_pct, trend
        )

        return {
            "before_analysis": before_analysis,
            "after_analysis":  after_analysis,
            "change_analysis": {
                "change_detected":             change_detected,
                "change_type":                 change_type,
                "changed_percentage":          changed_pct,
                "vegetation_loss_percentage":  veg_loss_pct,
                "new_burned_area_percentage":  new_burn_pct,
                "new_smoke_percentage":        new_smk_pct,
                "estimated_change_percentage": changed_pct,
                "confidence": 0.82 if change_detected else 0.65,
            },
            "fire_spread": {
                "trend":             trend,
                "change_percentage": new_burn_pct,
                "confidence":        0.78 if new_burn_pct > 3 else 0.50,
            },
            "combined_candidate_mask": combined_mask,
            "veg_loss_mask":           veg_loss,
            "new_burned_mask":         new_burned,
            "new_smoke_mask":          new_smoke,
            "candidate_regions":       candidate_regions,
            "method":       "TEMPORAL_BURNED_AREA_CHANGE",
            "model_label":  self.MODEL_LABEL,
            "data_source":  self.DATA_SOURCE,
            "thermal_available": self.thermal_available,
        }

    # ── Candidate region extraction ─────────────────────────────────────────

    def _extract_candidates(
        self, mask: np.ndarray, shape: Tuple
    ) -> List[Dict[str, Any]]:
        H, W = mask.shape[:2]
        candidates = []
        grid_r, grid_c = 4, 4
        row_h, col_w   = H // grid_r, W // grid_c

        for ri in range(grid_r):
            for ci in range(grid_c):
                y0, y1 = ri * row_h, (ri+1) * row_h
                x0, x1 = ci * col_w, (ci+1) * col_w
                cell     = mask[y0:y1, x0:x1]
                cell_pct = float(cell.sum()) / max(1, cell.size)
                if cell_pct > 0.08:
                    candidates.append({
                        "bbox":             [y0, x0, y1, x1],
                        "area_percentage":  round(cell_pct * 100, 1),
                        "confidence":       round(min(0.92, 0.45 + cell_pct * 3.0), 2),
                        "label":            "wildfire_candidate",
                    })

        candidates.sort(key=lambda c: c["confidence"], reverse=True)
        for i, c in enumerate(candidates[:5]):
            c["id"] = i + 1
        return candidates[:5]

    # ── NASA FIRMS / VIIRS integration hook ─────────────────────────────────

    def integrate_firms_data(self, firms_response: Any) -> None:
        """
        Hook for NASA FIRMS / VIIRS / MODIS active-fire product integration.
        When integrated, thermal hotspot confidence supersedes RGB proxy.
        """
        logger.info("NASA FIRMS integration hook called — not yet implemented.")
        # TODO: parse FIRMS JSON response, set thermal_available = True
        # Source: https://firms.modaps.eosdis.nasa.gov/api/

    # ── Empty result helpers ─────────────────────────────────────────────────

    def _empty_single(self) -> Dict[str, Any]:
        return {
            "fire_indicator_detected":   False,
            "burned_area_detected":      False,
            "smoke_detected":            False,
            "vegetation_percentage":     0.0,
            "burned_percentage":         0.0,
            "smoke_percentage":          0.0,
            "fire_indicator_percentage": 0.0,
            "affected_area_percentage":  0.0,
            "affected_pixels":           0,
            "burned_mask_array":         None,
            "smoke_mask_array":          None,
            "fire_mask_array":           None,
            "candidate_regions":         [],
            "method":          "SPECTRAL_FIRE_INDEX",
            "model_label":     self.MODEL_LABEL,
            "data_source":     self.DATA_SOURCE,
            "thermal_available": False,
            "thermal_evidence": "Thermal fire evidence unavailable.",
        }

    def _empty_temporal(self) -> Dict[str, Any]:
        return {
            "before_analysis": self._empty_single(),
            "after_analysis":  self._empty_single(),
            "change_analysis": {
                "change_detected": False, "change_type": None,
                "changed_percentage": 0.0, "vegetation_loss_percentage": 0.0,
                "new_burned_area_percentage": 0.0, "new_smoke_percentage": 0.0,
                "estimated_change_percentage": 0.0, "confidence": 0.0,
            },
            "fire_spread": {
                "trend": "NOT_AVAILABLE", "change_percentage": 0.0, "confidence": 0.0
            },
            "combined_candidate_mask": None,
            "veg_loss_mask": None,
            "new_burned_mask": None,
            "new_smoke_mask": None,
            "candidate_regions": [],
            "method":      "TEMPORAL_BURNED_AREA_CHANGE",
            "model_label": self.MODEL_LABEL,
            "data_source": self.DATA_SOURCE,
            "thermal_available": False,
        }
