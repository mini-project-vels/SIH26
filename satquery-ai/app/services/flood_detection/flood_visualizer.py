import io
import os
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional

from app.services.flood_detection.spectral_water_detector import _load_as_pil, ANALYSIS_RESOLUTION

logger = logging.getLogger("satquery.flood.visualizer")


class FloodVisualizer:
    """
    Generates annotated flood maps with real pixel-level water overlays.
    Uses the binary water_mask_array from SpectralWaterDetector when available,
    falls back to bounding box rectangles.
    """

    def __init__(self, output_dir: str = "outputs") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def draw_visualization(
        self,
        image_source: Any,
        evidence: Dict[str, Any],
        request_id: str
    ) -> Optional[str]:
        """
        Composite flood annotation on the target image:
          - Semi-transparent blue fill for water pixels (real mask or bbox fallback)
          - Orange fill for potentially affected buildings
          - Red outline for HIGH-severity affected regions
          - Legend card
        """
        try:
            pil_img = _load_as_pil(image_source)
        except Exception as e:
            logger.error("[%s] FloodVisualizer: could not load image: %s", request_id, e)
            return None

        orig_w, orig_h = pil_img.size
        img_rgba = pil_img.convert("RGBA")

        overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        # ── 1. Water mask overlay ───────────────────────────────────────────────
        water_analysis = evidence.get("water_analysis", {})
        water_mask_arr = water_analysis.get("water_mask_array")

        if water_mask_arr is not None and isinstance(water_mask_arr, np.ndarray):
            # Real per-pixel mask — upscale to original image size
            mask_img = Image.fromarray((water_mask_arr * 255).astype(np.uint8), "L")
            mask_upscaled = mask_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)
            mask_arr_up = np.array(mask_upscaled) > 0

            # Paint water pixels semi-transparent blue
            water_overlay = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            water_overlay[mask_arr_up] = [30, 110, 230, 100]   # RGBA — semi-transparent blue
            water_layer = Image.fromarray(water_overlay, "RGBA")
            overlay = Image.alpha_composite(overlay, water_layer)
            draw_overlay = ImageDraw.Draw(overlay)
            logger.info("[%s] Used real pixel-level water mask for visualization", request_id)
        else:
            # Fallback: draw bounding box rectangles from water regions
            water_regions = water_analysis.get("water_regions", [])
            for wr in water_regions:
                ymin, xmin, ymax, xmax = wr["bbox"][:4]
                draw_overlay.rectangle([xmin, ymin, xmax, ymax],
                                       fill=(30, 110, 230, 80),
                                       outline=(30, 110, 230, 255), width=2)
            logger.info("[%s] Used bbox fallback for water visualization (%d regions)",
                        request_id, len(water_regions))

        # ── 2. Affected buildings: orange ─────────────────────────────────────
        building_detections = evidence.get("building_detections", [])
        affected_ids = {b["id"] for b in evidence.get("potentially_affected_buildings", [])}
        for b in building_detections:
            if b.get("id") in affected_ids:
                ymin, xmin, ymax, xmax = b["bbox"][:4]
                draw_overlay.rectangle([xmin, ymin, xmax, ymax],
                                       fill=(255, 120, 0, 80),
                                       outline=(255, 120, 0, 255), width=2)

        # ── 3. High-risk affected regions: red outline ─────────────────────────
        for ar in evidence.get("affected_regions", []):
            if ar.get("severity") == "HIGH":
                bbox = ar.get("bbox", [])
                if bbox and len(bbox) >= 4:
                    ymin, xmin, ymax, xmax = bbox[:4]
                    draw_overlay.rectangle([xmin, ymin, xmax, ymax],
                                           outline=(255, 30, 30, 255), width=4)

        # Composite overlays
        img_rgba = Image.alpha_composite(img_rgba, overlay)

        # ── 4. Legend card ─────────────────────────────────────────────────────
        card_h = 110
        card_x1, card_x2 = 12, 310
        card_y1 = max(0, orig_h - card_h - 12)
        card_y2 = orig_h - 12

        legend_layer = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_legend = ImageDraw.Draw(legend_layer)
        draw_legend.rectangle([card_x1, card_y1, card_x2, card_y2],
                               fill=(0, 0, 0, 175), outline=(255, 255, 255, 220), width=1)
        img_rgba = Image.alpha_composite(img_rgba, legend_layer)

        draw = ImageDraw.Draw(img_rgba)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        draw.text((card_x1 + 10, card_y1 + 6),  "SatQuery Flood Analysis",  fill=(255, 255, 255), font=font)
        draw.text((card_x1 + 10, card_y1 + 26), "Blue  = Water / Flood Evidence",          fill=(100, 180, 255), font=font)
        draw.text((card_x1 + 10, card_y1 + 46), "Orange = Potentially Affected Buildings", fill=(255, 165, 80),  font=font)
        draw.text((card_x1 + 10, card_y1 + 66), "Red    = High-Risk Affected Area",        fill=(255, 100, 100), font=font)

        # Water stats overlay (top-right corner)
        water_pct = water_analysis.get("total_water_percentage", 0.0)
        water_px  = water_analysis.get("total_water_area_pixels", 0)
        stats_text = f"Water: {water_pct:.1f}% ({water_px} px)"
        draw.text((orig_w - 250, 10), stats_text, fill=(200, 230, 255), font=font)

        # ── 5. Save ────────────────────────────────────────────────────────────
        out_filename = f"flood_analysis_{request_id}.png"
        out_path = os.path.join(self.output_dir, out_filename)
        img_rgba.convert("RGB").save(out_path, "PNG")
        logger.info("[%s] Flood analysis map saved: %s", request_id, out_path)
        return f"outputs/{out_filename}"

