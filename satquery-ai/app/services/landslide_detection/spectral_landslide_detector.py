"""
SpectralLandslideDetector
=========================
Pixel-level spectral analysis for landslide candidate detection from optical
satellite imagery (RGB / RGBA).

Methodology
-----------
A dedicated deep-learning landslide segmentation model is NOT available in
this deployment.  Instead we use physically-motivated spectral heuristics:

  1. Bare-soil / disturbed-terrain index  — high Red, low Green/Blue, low NDVI proxy
  2. Vegetation-loss proxy (Green-channel suppression on steep-colour regions)
  3. Surface-texture change between before/after images (pixel-difference method)
  4. Morphological candidate generation (connected-component analysis)

These heuristics are well-documented in the remote-sensing literature as first-
order proxies for landslide evidence in optical imagery.  They are NOT a
substitute for a validated segmentation model.

DEM / Elevation
---------------
Slope analysis requires a Digital Elevation Model.  If no DEM is supplied the
detector sets  ``dem_available = False``  and skips slope-based scoring.
Future integration with Copernicus DEM 30m or SRTM 1-arc-second is
architecturally prepared via ``integrate_dem()``.

Data source transparency
------------------------
All outputs explicitly declare the data source and methodology so that no
result is misrepresented as coming from a dedicated ML model.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger("satquery.landslide.detector")

# ─────────────────────────────────────────────────────────────────────────────
# Resolution used for analysis (keeps it manageable)
ANALYSIS_RESOLUTION = (512, 512)

# Threshold parameters (documented, tunable)
BARE_SOIL_RED_MIN = 0.38       # Normalised red threshold for bare-soil proxy
VEGETATION_GREEN_MIN = 0.35    # Normalised green threshold for vegetation proxy
CHANGE_DIFF_THRESHOLD = 0.12  # Normalised per-pixel diff to flag as changed


def _load_as_pil(src: Any) -> Image.Image:
    """
    Load an UploadFile / (name, bytes) tuple / path string / PIL.Image
    into a PIL.Image (RGB).
    """
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
    raise TypeError(f"Unsupported image source type: {type(src)}")


def _resize(img: Image.Image, size: Tuple[int, int] = ANALYSIS_RESOLUTION) -> Image.Image:
    return img.resize(size, Image.Resampling.LANCZOS)


def _to_float_array(img: Image.Image) -> np.ndarray:
    """Return H×W×3 float32 array in [0, 1]."""
    return np.array(img, dtype=np.float32) / 255.0


# ─────────────────────────────────────────────────────────────────────────────

class SpectralLandslideDetector:
    """
    Spectral heuristic landslide detector.

    Detection approach (clearly disclosed):
      - SPECTRAL_HEURISTIC: physically motivated band ratios, NOT a trained
        deep-learning segmentation model.
      - Change detection uses per-pixel absolute difference between aligned
        before/after images.
    """

    DATA_SOURCE = "OPTICAL_SPECTRAL_HEURISTIC"
    MODEL_LABEL = "LANDSLIDE_SPECIALIST_LIMITED"   # no dedicated seg model
    dem_available: bool = False  # DEM not integrated — explicitly signalled

    # ------------------------------------------------------------------
    #  Single-image bare-soil / disturbance analysis
    # ------------------------------------------------------------------

    def detect_disturbance(
        self,
        image_src: Any,
        request_id: str = "N/A",
        mode: str = "single"
    ) -> Dict[str, Any]:
        """
        Analyse a single image for landslide disturbance indicators.

        Returns:
            dict with keys:
              disturbance_detected, bare_soil_percentage, vegetation_loss_pct,
              disturbance_mask_array, candidate_regions, method, model_label
        """
        try:
            pil = _resize(_load_as_pil(image_src))
        except Exception as exc:
            logger.error("[%s] Failed to load image: %s", request_id, exc)
            return self._empty_disturbance_result()

        arr = _to_float_array(pil)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # ── Bare-soil proxy ──────────────────────────────────────────────
        # Bare/disturbed soil: high red, moderate-low green, low blue,
        # and notably lower than vegetation green-dominance threshold.
        bare_soil_mask = (
            (r > BARE_SOIL_RED_MIN) &
            (r > g * 1.05) &          # red dominates over green
            (g < VEGETATION_GREEN_MIN + 0.10) &
            (b < 0.45)
        )

        # ── Vegetation proxy (suppress: bright green pixels) ─────────────
        vegetation_mask = (g > VEGETATION_GREEN_MIN) & (g > r) & (g > b)

        # ── Disturbance = bare soil NOT covered by healthy vegetation ────
        disturbance_mask = bare_soil_mask & ~vegetation_mask

        total_px = arr.shape[0] * arr.shape[1]
        bare_px = int(bare_soil_mask.sum())
        veg_px = int(vegetation_mask.sum())
        dist_px = int(disturbance_mask.sum())

        bare_pct = round(bare_px / total_px * 100, 2)
        dist_pct = round(dist_px / total_px * 100, 2)
        veg_pct = round(veg_px / total_px * 100, 2)

        # ── Candidate regions (simple bounding boxes for hotspots) ───────
        candidate_regions = self._extract_candidate_regions(disturbance_mask, arr.shape)

        detected = dist_pct > 3.0  # at least 3% disturbed pixels required

        logger.info(
            "[%s] Disturbance analysis: bare=%.1f%%, veg=%.1f%%, disturbed=%.1f%%, detected=%s",
            request_id, bare_pct, veg_pct, dist_pct, detected
        )

        return {
            "disturbance_detected": detected,
            "bare_soil_percentage": bare_pct,
            "vegetation_percentage": veg_pct,
            "disturbance_percentage": dist_pct,
            "disturbance_pixels": dist_px,
            "disturbance_mask_array": disturbance_mask,
            "candidate_regions": candidate_regions,
            "method": "SPECTRAL_BARE_SOIL_INDEX",
            "model_label": self.MODEL_LABEL,
            "data_source": self.DATA_SOURCE,
            "dem_available": self.dem_available,
            "terrain_evidence": "Terrain elevation evidence unavailable." if not self.dem_available else "DEM integrated.",
        }

    # ------------------------------------------------------------------
    #  Temporal before/after change detection
    # ------------------------------------------------------------------

    def compare_temporal(
        self,
        before_src: Any,
        after_src: Any,
        request_id: str = "N/A"
    ) -> Dict[str, Any]:
        """
        Pixel-level surface change detection between two image acquisitions.

        Workflow:
          1. Geometric alignment (resize both to same resolution)
          2. Per-channel absolute difference
          3. Threshold → change mask
          4. Vegetation-loss layer (green reduction)
          5. Bare-soil gain layer (new bare-soil in after not in before)
          6. Candidate region extraction

        Returns a dict containing both single-image analyses PLUS change data.
        """
        try:
            before_pil = _resize(_load_as_pil(before_src))
            after_pil  = _resize(_load_as_pil(after_src))
        except Exception as exc:
            logger.error("[%s] Temporal compare load failure: %s", request_id, exc)
            return self._empty_change_result()

        b_arr = _to_float_array(before_pil)
        a_arr = _to_float_array(after_pil)

        # ── Per-pixel difference (all 3 channels averaged) ─────────────
        diff = np.abs(a_arr - b_arr).mean(axis=2)   # H×W
        change_mask = diff > CHANGE_DIFF_THRESHOLD

        # ── Vegetation-loss layer ────────────────────────────────────────
        # Pixels that were green before but lost green dominance after
        b_veg = (b_arr[:, :, 1] > VEGETATION_GREEN_MIN) & (b_arr[:, :, 1] > b_arr[:, :, 0])
        a_veg = (a_arr[:, :, 1] > VEGETATION_GREEN_MIN) & (a_arr[:, :, 1] > a_arr[:, :, 0])
        veg_loss_mask = b_veg & ~a_veg & change_mask

        # ── New bare-soil exposure ────────────────────────────────────────
        r_a, g_a, b_ = a_arr[:, :, 0], a_arr[:, :, 1], a_arr[:, :, 2]
        r_b, g_b     = b_arr[:, :, 0], b_arr[:, :, 1]
        new_bare_mask = (
            (r_a > BARE_SOIL_RED_MIN) & (r_a > g_a * 1.05) &
            (r_b < BARE_SOIL_RED_MIN) &     # was NOT bare before
            change_mask
        )

        total_px = diff.size
        changed_px = int(change_mask.sum())
        veg_loss_px = int(veg_loss_mask.sum())
        new_bare_px = int(new_bare_mask.sum())

        changed_pct  = round(changed_px / total_px * 100, 2)
        veg_loss_pct = round(veg_loss_px / total_px * 100, 2)
        new_bare_pct = round(new_bare_px / total_px * 100, 2)

        change_detected = changed_pct > 2.0   # >2% change is significant

        # Combined landslide candidate mask = change + (veg loss OR new bare)
        combined_mask = change_mask & (veg_loss_mask | new_bare_mask)
        candidate_regions = self._extract_candidate_regions(combined_mask, a_arr.shape)

        # Single-image breakdowns
        before_analysis = self.detect_disturbance(before_src, request_id + "_before")
        after_analysis  = self.detect_disturbance(after_src,  request_id + "_after")

        # Determine change type
        if veg_loss_pct > 5.0 and new_bare_pct > 3.0:
            change_type = "VEGETATION_LOSS_BARE_SOIL_EXPOSURE"
        elif veg_loss_pct > 5.0:
            change_type = "VEGETATION_LOSS"
        elif new_bare_pct > 3.0:
            change_type = "NEW_BARE_SOIL_EXPOSURE"
        elif change_detected:
            change_type = "SURFACE_DISTURBANCE"
        else:
            change_type = None

        logger.info(
            "[%s] Temporal change: changed=%.1f%%, veg_loss=%.1f%%, new_bare=%.1f%%, type=%s",
            request_id, changed_pct, veg_loss_pct, new_bare_pct, change_type
        )

        return {
            "before_analysis": before_analysis,
            "after_analysis":  after_analysis,
            "change_analysis": {
                "change_detected": change_detected,
                "change_type": change_type,
                "changed_pixels": changed_px,
                "changed_percentage": changed_pct,
                "vegetation_loss_percentage": veg_loss_pct,
                "new_bare_soil_percentage": new_bare_pct,
                "estimated_change_percentage": changed_pct,
                "confidence": 0.82 if change_detected else 0.70,
            },
            "combined_candidate_mask": combined_mask,
            "veg_loss_mask": veg_loss_mask,
            "new_bare_mask": new_bare_mask,
            "candidate_regions": candidate_regions,
            "method": "TEMPORAL_PIXEL_DIFFERENCE",
            "model_label": self.MODEL_LABEL,
            "data_source": self.DATA_SOURCE,
            "dem_available": self.dem_available,
            "terrain_evidence": "Terrain elevation evidence unavailable." if not self.dem_available else "DEM integrated.",
        }

    # ------------------------------------------------------------------
    #  Candidate region extraction (simple connected-component proxy)
    # ------------------------------------------------------------------

    def _extract_candidate_regions(
        self, mask: np.ndarray, shape: Tuple[int, int, int]
    ) -> List[Dict[str, Any]]:
        """
        Extract up to 5 meaningful rectangular candidate bounding boxes from a
        binary mask using a grid-cell approach (no scipy dependency required).
        """
        H, W = mask.shape[:2]
        candidates = []
        grid_rows, grid_cols = 4, 4
        row_h, col_w = H // grid_rows, W // grid_cols

        for ri in range(grid_rows):
            for ci in range(grid_cols):
                y0, y1 = ri * row_h, (ri + 1) * row_h
                x0, x1 = ci * col_w, (ci + 1) * col_w
                cell = mask[y0:y1, x0:x1]
                cell_pct = float(cell.sum()) / max(1, cell.size)
                if cell_pct > 0.08:    # >8% of cell is disturbed
                    candidates.append({
                        "bbox": [y0, x0, y1, x1],   # [ymin xmin ymax xmax]
                        "area_percentage": round(cell_pct * 100, 1),
                        "confidence": round(min(0.95, 0.5 + cell_pct * 2.5), 2),
                        "label": "landslide_candidate",
                    })

        # Sort by confidence descending, cap at 5
        candidates.sort(key=lambda c: c["confidence"], reverse=True)
        for i, c in enumerate(candidates[:5]):
            c["id"] = i + 1
        return candidates[:5]

    # ------------------------------------------------------------------
    #  DEM integration hook (future)
    # ------------------------------------------------------------------

    def integrate_dem(self, dem_source: Any) -> None:
        """
        Hook for future Copernicus DEM / SRTM integration.
        When a valid DEM is supplied, slope-aspect analysis supplements
        the spectral indicators.
        """
        logger.info("DEM integration hook called — not yet implemented.")
        # TODO: load DEM, compute slope/aspect, set self.dem_available = True

    # ------------------------------------------------------------------
    #  Empty result helpers
    # ------------------------------------------------------------------

    def _empty_disturbance_result(self) -> Dict[str, Any]:
        return {
            "disturbance_detected": False,
            "bare_soil_percentage": 0.0,
            "vegetation_percentage": 0.0,
            "disturbance_percentage": 0.0,
            "disturbance_pixels": 0,
            "disturbance_mask_array": None,
            "candidate_regions": [],
            "method": "SPECTRAL_BARE_SOIL_INDEX",
            "model_label": self.MODEL_LABEL,
            "data_source": self.DATA_SOURCE,
            "dem_available": False,
            "terrain_evidence": "Terrain elevation evidence unavailable.",
        }

    def _empty_change_result(self) -> Dict[str, Any]:
        return {
            "before_analysis": self._empty_disturbance_result(),
            "after_analysis":  self._empty_disturbance_result(),
            "change_analysis": {
                "change_detected": False,
                "change_type": None,
                "changed_pixels": 0,
                "changed_percentage": 0.0,
                "vegetation_loss_percentage": 0.0,
                "new_bare_soil_percentage": 0.0,
                "estimated_change_percentage": 0.0,
                "confidence": 0.0,
            },
            "combined_candidate_mask": None,
            "veg_loss_mask": None,
            "new_bare_mask": None,
            "candidate_regions": [],
            "method": "TEMPORAL_PIXEL_DIFFERENCE",
            "model_label": self.MODEL_LABEL,
            "data_source": self.DATA_SOURCE,
            "dem_available": False,
            "terrain_evidence": "Terrain elevation evidence unavailable.",
        }
