"""
SpectralGlacierDetector — Real satellite glacier/ice detection using spectral analysis.

Glacier and snow/ice in RGB satellite imagery typically exhibit:
  - Very high brightness (all three channels near 200–255)
  - Near-equal R, G, B values (grey-white tone)
  - Slightly bluer tint on ice vs. whiter on fresh snow
  - Shadows at glacier edges: dark with bluish cast

Glacial lakes:
  - Dark to moderate: bluish-grey, turquoise, or dark-teal
  - Appear adjacent to or within glacier boundaries
  
Three spectral classes detected:
  (A) Snow/Ice — very bright, near-neutral
  (B) Blue ice — bright, slightly blue-dominant
  (C) Shadow ice edges — moderately dark, bluish
"""

import io
import os
import logging
import numpy as np
from PIL import Image
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("satquery.glacier.detector")

# ─── Spectral thresholds ───────────────────────────────────────────────────────

# (A) Snow / firn — very bright, near-neutral colour
SNOW_MIN_R = 190
SNOW_MIN_G = 190
SNOW_MIN_B = 190

# (B) Blue ice — bright but with blue > green > red
BLUE_ICE_MIN_AVG    = 150
BLUE_ICE_B_OVER_R   = 10     # b must exceed r by at least this
BLUE_ICE_B_OVER_G   = 5

# (C) Shadow ice — medium-dark, blue-grey
SHADOW_ICE_MIN_AVG  = 60
SHADOW_ICE_MAX_AVG  = 160
SHADOW_ICE_MAX_DIFF = 25    # max channel difference (near-neutral)
SHADOW_ICE_MIN_B    = 90

# Exclusion
CLOUD_MIN_BRIGHTNESS = 230   # Very uniform bright white → probable cloud not ice
VEGETATION_MAX_R    = 120
VEGETATION_MIN_G    = 60    # g > r + 20 and g > b + 10 → vegetation
RED_TERRAIN_R_EXCESS = 30   # r > g + X = dry soil/rock

# Glacial lake thresholds (dark turquoise/grey-blue water adjacent to glacier)
GLACIAL_LAKE_MAX_AVG  = 140
GLACIAL_LAKE_MIN_B    = 60
GLACIAL_LAKE_B_R_RATIO = 1.05

# Analysis / region parameters
ANALYSIS_RESOLUTION = 256
MIN_GLACIER_PIXELS  = 15    # min component pixels at analysis resolution
MIN_LAKE_PIXELS     = 5

# ──────────────────────────────────────────────────────────────────────────────


def _is_glacier_pixel(r: int, g: int, b: int) -> bool:
    """True if the pixel is likely glacier / snow / ice in satellite imagery."""
    avg = (r + g + b) / 3.0

    # Exclude obvious vegetation
    if g > r + 20 and g > b + 10 and avg < 160:
        return False

    # Exclude red/brown terrain
    if r > g + RED_TERRAIN_R_EXCESS and r > b + RED_TERRAIN_R_EXCESS:
        return False

    # (A) Snow / firn
    if r >= SNOW_MIN_R and g >= SNOW_MIN_G and b >= SNOW_MIN_B:
        # Extra: very uniform bright white (possible cloud) — still count as ice/snow
        # We can't reliably distinguish cloud from snow with RGB alone, mark it
        return True

    # (B) Blue ice — bright with strong blue component
    if avg >= BLUE_ICE_MIN_AVG and b > r + BLUE_ICE_B_OVER_R and b > g + BLUE_ICE_B_OVER_G:
        return True

    # (C) Shadow ice / glacier edge
    if (SHADOW_ICE_MIN_AVG < avg < SHADOW_ICE_MAX_AVG and
            abs(r - g) < SHADOW_ICE_MAX_DIFF and
            abs(g - b) < SHADOW_ICE_MAX_DIFF and
            b >= SHADOW_ICE_MIN_B):
        return True

    return False


def _is_glacial_lake_pixel(r: int, g: int, b: int) -> bool:
    """True if the pixel looks like a glacial meltwater lake (dark turquoise/grey-blue)."""
    avg = (r + g + b) / 3.0
    if avg > GLACIAL_LAKE_MAX_AVG:
        return False
    if b < GLACIAL_LAKE_MIN_B:
        return False
    # Exclude vegetation
    if g > r + 20 and g > b + 10:
        return False
    if r > 0 and (b / r) >= GLACIAL_LAKE_B_R_RATIO:
        return True
    # Turquoise meltwater — g and b roughly similar, both > r
    if b >= r and g >= r and avg > 30:
        return True
    return False


def _load_as_pil(image: Any) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image)).convert("RGB")
    if isinstance(image, io.BytesIO):
        image.seek(0)
        return Image.open(image).convert("RGB")
    if isinstance(image, str):
        return Image.open(image).convert("RGB")
    if hasattr(image, "file"):
        image.file.seek(0)
        raw = image.file.read()
        return Image.open(io.BytesIO(raw)).convert("RGB")
    if isinstance(image, tuple) and len(image) >= 2:
        return Image.open(io.BytesIO(image[1])).convert("RGB")
    raise TypeError(f"Unsupported image type: {type(image)}")


def _build_mask(pil_img: Image.Image, classifier, resolution: int) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Downsample + vectorised classification → bool mask."""
    original_size = pil_img.size
    analysis_img = pil_img.resize((resolution, resolution), Image.Resampling.BILINEAR)
    arr = np.array(analysis_img, dtype=np.int32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    avg = (r + g + b) / 3.0

    if classifier == "glacier":
        # Exclude vegetation
        is_veg = (g > r + 20) & (g > b + 10) & (avg < 160)
        is_red_terrain = (r > g + RED_TERRAIN_R_EXCESS) & (r > b + RED_TERRAIN_R_EXCESS)
        excluded = is_veg | is_red_terrain

        tier_a = (~excluded) & (r >= SNOW_MIN_R) & (g >= SNOW_MIN_G) & (b >= SNOW_MIN_B)
        tier_b = (~excluded) & (avg >= BLUE_ICE_MIN_AVG) & (b > r + BLUE_ICE_B_OVER_R) & (b > g + BLUE_ICE_B_OVER_G)
        tier_c = (~excluded) & (avg > SHADOW_ICE_MIN_AVG) & (avg < SHADOW_ICE_MAX_AVG) & \
                 (np.abs(r - g) < SHADOW_ICE_MAX_DIFF) & (np.abs(g - b) < SHADOW_ICE_MAX_DIFF) & (b >= SHADOW_ICE_MIN_B)
        mask = tier_a | tier_b | tier_c

    elif classifier == "lake":
        is_veg = (g > r + 20) & (g > b + 10)
        with np.errstate(divide='ignore', invalid='ignore'):
            b_over_r = np.where(r > 0, b.astype(float) / r.astype(float), 0.0)
        tier_a = (~is_veg) & (avg <= GLACIAL_LAKE_MAX_AVG) & (b >= GLACIAL_LAKE_MIN_B) & (b_over_r >= GLACIAL_LAKE_B_R_RATIO)
        tier_b = (~is_veg) & (b >= r) & (g >= r) & (avg > 30) & (avg <= GLACIAL_LAKE_MAX_AVG)
        mask = tier_a | tier_b
    else:
        mask = np.zeros((resolution, resolution), dtype=bool)

    return mask, original_size


def _find_connected_regions(mask: np.ndarray, min_pixels: int) -> List[List[Tuple[int, int]]]:
    rows, cols = mask.shape
    visited = np.zeros((rows, cols), dtype=bool)
    regions = []
    for row in range(rows):
        for col in range(cols):
            if mask[row, col] and not visited[row, col]:
                component = []
                queue = deque([(col, row)])
                visited[row, col] = True
                while queue:
                    cx, cy = queue.popleft()
                    component.append((cx, cy))
                    for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if mask[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                queue.append((nx, ny))
                if len(component) >= min_pixels:
                    regions.append(component)
    return regions


def _regions_to_dicts(regions: List, orig_w: int, orig_h: int, resolution: int) -> Tuple[List[Dict], int, float]:
    scale_x = orig_w / resolution
    scale_y = orig_h / resolution
    orig_total = orig_w * orig_h
    area_scale = orig_total / (resolution * resolution)

    result = []
    total_pixels = 0
    for i, comp in enumerate(regions):
        comp_xs = [p[0] for p in comp]
        comp_ys = [p[1] for p in comp]
        ymin, ymax = int(min(comp_ys) * scale_y), int(max(comp_ys) * scale_y)
        xmin, xmax = int(min(comp_xs) * scale_x), int(max(comp_xs) * scale_x)
        area_px = int(len(comp) * area_scale)
        total_pixels += area_px
        result.append({
            "id": i + 1,
            "bbox": [ymin, xmin, ymax, xmax],
            "area_pixels": area_px,
            "area_percentage": round((area_px / orig_total) * 100.0, 2)
        })
    total_pct = round((total_pixels / orig_total) * 100.0, 2)
    return result, total_pixels, total_pct


class SpectralGlacierDetector:
    """
    Real pixel-level glacier, ice, and glacial lake detector for satellite imagery.
    Uses pure spectral analysis (numpy vectorised) — no VLM, no placeholder values.
    """

    def __init__(self, resolution: int = ANALYSIS_RESOLUTION, output_dir: str = "outputs"):
        self.resolution = resolution
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("SpectralGlacierDetector initialized (resolution=%d)", resolution)

    def detect_glacier(self, image: Any, request_id: str = "temp", label: str = "") -> Dict[str, Any]:
        """Detect glacier/ice regions in a single image. Returns regions + mask."""
        logger.info("[%s] Detecting glacier/ice (label=%s)...", request_id, label or "single")
        try:
            pil = _load_as_pil(image)
        except Exception as e:
            logger.error("[%s] Image load failed: %s", request_id, e)
            return self._empty_glacier(error=str(e))

        orig_w, orig_h = pil.size
        mask, _ = _build_mask(pil, "glacier", self.resolution)

        raw_px = int(mask.sum())
        raw_pct = (raw_px / (self.resolution * self.resolution)) * 100.0
        logger.info("[%s] Glacier pixels at res: %d (%.1f%%)", request_id, raw_px, raw_pct)

        regions_raw = _find_connected_regions(mask, MIN_GLACIER_PIXELS)
        regions, total_px, total_pct = _regions_to_dicts(regions_raw, orig_w, orig_h, self.resolution)
        detected = len(regions) > 0

        logger.info("[%s] Glacier detected=%s, regions=%d, coverage=%.2f%%",
                    request_id, detected, len(regions), total_pct)

        mask_path = self._save_mask(mask, pil, request_id, label, "glacier")

        return {
            "glacier_detected": detected,
            "glacier_regions": regions,
            "total_glacier_area_pixels": total_px,
            "total_glacier_percentage": total_pct,
            "glacier_mask_array": mask,
            "image_size": (orig_w, orig_h),
            "mask_path": mask_path
        }

    def detect_glacial_lake(self, image: Any, request_id: str = "temp", label: str = "") -> Dict[str, Any]:
        """Detect glacial meltwater lakes in a single image."""
        logger.info("[%s] Detecting glacial lakes (label=%s)...", request_id, label or "single")
        try:
            pil = _load_as_pil(image)
        except Exception as e:
            logger.error("[%s] Image load failed: %s", request_id, e)
            return self._empty_lake(error=str(e))

        orig_w, orig_h = pil.size
        mask, _ = _build_mask(pil, "lake", self.resolution)

        regions_raw = _find_connected_regions(mask, MIN_LAKE_PIXELS)
        regions, total_px, total_pct = _regions_to_dicts(regions_raw, orig_w, orig_h, self.resolution)
        detected = len(regions) > 0

        logger.info("[%s] Glacial lake detected=%s, regions=%d, coverage=%.2f%%",
                    request_id, detected, len(regions), total_pct)

        mask_path = self._save_mask(mask, pil, request_id, label, "lake")

        return {
            "lake_detected": detected,
            "lake_regions": regions,
            "total_lake_area_pixels": total_px,
            "total_lake_percentage": total_pct,
            "lake_mask_array": mask,
            "mask_path": mask_path
        }

    def compare_temporal(
        self,
        before_image: Any,
        after_image: Any,
        request_id: str = "temp"
    ) -> Dict[str, Any]:
        """Full before/after comparison for both glacier and glacial lake."""
        logger.info("[%s] Temporal glacier comparison starting...", request_id)

        before_glacier = self.detect_glacier(before_image, request_id, "before")
        after_glacier  = self.detect_glacier(after_image,  request_id, "after")

        before_lake    = self.detect_glacial_lake(before_image, request_id, "before_lake")
        after_lake     = self.detect_glacial_lake(after_image,  request_id, "after_lake")

        # — Glacier change
        before_pct = before_glacier["total_glacier_percentage"]
        after_pct  = after_glacier["total_glacier_percentage"]
        glacier_diff_pct = round(after_pct - before_pct, 2)

        if abs(glacier_diff_pct) < 0.5:
            change_type = "NO_SIGNIFICANT_CHANGE"
        elif glacier_diff_pct < 0:
            change_type = "GLACIER_RETREAT"
        else:
            change_type = "GLACIER_ADVANCE"

        if before_pct > 0:
            change_percentage = round(abs(glacier_diff_pct) / before_pct * 100.0, 1)
        else:
            change_percentage = 100.0 if abs(glacier_diff_pct) > 0 else 0.0

        change_detected = change_type != "NO_SIGNIFICANT_CHANGE"

        # Pixel-level lost/gained ice
        bm = before_glacier.get("glacier_mask_array")
        am = after_glacier.get("glacier_mask_array")
        new_ice_mask = lost_ice_mask = None
        new_ice_path = lost_ice_path = None

        if bm is not None and am is not None:
            if bm.shape != am.shape:
                bm = np.array(
                    Image.fromarray(bm.astype(np.uint8) * 255)
                    .resize((am.shape[1], am.shape[0]), Image.Resampling.NEAREST)
                ) > 0
            new_ice_mask = am & ~bm
            lost_ice_mask = bm & ~am
            new_ice_path  = self._save_change_mask(new_ice_mask, request_id, "new_ice", [30, 200, 255])
            lost_ice_path = self._save_change_mask(lost_ice_mask, request_id, "lost_ice", [255, 100, 30])

        logger.info("[%s] Glacier: before=%.2f%% after=%.2f%% change_type=%s",
                    request_id, before_pct, after_pct, change_type)

        # — Glacial lake change
        before_lake_pct = before_lake["total_lake_percentage"]
        after_lake_pct  = after_lake["total_lake_percentage"]
        lake_diff = after_lake_pct - before_lake_pct
        lake_expansion_detected = lake_diff > 0.2

        if before_lake_pct > 0:
            lake_expansion_pct = round(lake_diff / before_lake_pct * 100.0, 1)
        else:
            lake_expansion_pct = 100.0 if lake_diff > 0 else 0.0

        logger.info("[%s] Glacial lake: before=%.2f%% after=%.2f%% expansion=%.1f%%",
                    request_id, before_lake_pct, after_lake_pct, lake_expansion_pct)

        return {
            "before_glacier": before_glacier,
            "after_glacier":  after_glacier,
            "before_lake":    before_lake,
            "after_lake":     after_lake,
            "glacier_change": {
                "change_detected": change_detected,
                "change_type": change_type,
                "before_glacier_percentage": before_pct,
                "after_glacier_percentage": after_pct,
                "area_difference_pixels": abs(after_glacier["total_glacier_area_pixels"] - before_glacier["total_glacier_area_pixels"]),
                "estimated_change_percentage": change_percentage,
                "new_ice_mask_path": new_ice_path,
                "lost_ice_mask_path": lost_ice_path
            },
            "lake_change": {
                "before_lake_percentage": before_lake_pct,
                "after_lake_percentage": after_lake_pct,
                "lake_expansion_detected": lake_expansion_detected,
                "estimated_expansion_percentage": max(0.0, lake_expansion_pct)
            }
        }

    def _save_mask(self, mask: np.ndarray, pil: Image.Image, request_id: str, label: str, kind: str) -> Optional[str]:
        try:
            label_str = f"_{label}" if label else ""
            filepath = os.path.join(self.output_dir, f"{kind}_mask{label_str}_{request_id}.png")
            orig_w, orig_h = pil.size
            mask_img = Image.fromarray((mask * 255).astype(np.uint8), "L")
            mask_up = np.array(mask_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)) > 0

            base = np.array(pil.convert("RGBA"))
            if kind == "glacier":
                base[mask_up] = [200, 230, 255, 180]   # icy blue-white
            else:
                base[mask_up] = [30, 180, 200, 180]    # teal (lake)

            Image.fromarray(base, "RGBA").convert("RGB").save(filepath, "PNG")
            logger.info("Saved %s mask: %s", kind, filepath)
            return filepath
        except Exception as e:
            logger.warning("Could not save %s mask: %s", kind, e)
            return None

    def _save_change_mask(self, mask: np.ndarray, request_id: str, label: str, color: List[int]) -> Optional[str]:
        try:
            filepath = os.path.join(self.output_dir, f"{label}_{request_id}.png")
            h, w = mask.shape
            rgb = np.zeros((h, w, 3), dtype=np.uint8)
            rgb[mask] = color
            img = Image.fromarray(rgb, "RGB")
            img = img.resize((w * 3, h * 3), Image.Resampling.NEAREST)
            img.save(filepath, "PNG")
            return filepath
        except Exception as e:
            logger.warning("Could not save change mask %s: %s", label, e)
            return None

    @staticmethod
    def _empty_glacier(error: str = "") -> Dict:
        return {
            "glacier_detected": False, "glacier_regions": [],
            "total_glacier_area_pixels": 0, "total_glacier_percentage": 0.0,
            "glacier_mask_array": None, "image_size": (0, 0),
            "mask_path": None, "error": error
        }

    @staticmethod
    def _empty_lake(error: str = "") -> Dict:
        return {
            "lake_detected": False, "lake_regions": [],
            "total_lake_area_pixels": 0, "total_lake_percentage": 0.0,
            "lake_mask_array": None, "mask_path": None, "error": error
        }
