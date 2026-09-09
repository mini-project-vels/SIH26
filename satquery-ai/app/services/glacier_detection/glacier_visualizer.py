import os
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional
from app.services.glacier_detection.spectral_glacier_detector import _load_as_pil

logger = logging.getLogger("satquery.glacier.visualizer")

class GlacierVisualizer:
    """
    Generates annotated maps showing glacier boundaries, retreats, and glacial lakes using real pixel-level masks.
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def draw_visualization(self, image_source: Any, evidence: Dict[str, Any], request_id: str) -> Optional[str]:
        try:
            pil_img = _load_as_pil(image_source)
        except Exception as e:
            logger.error("[%s] GlacierVisualizer could not load image: %s", request_id, e)
            return None

        orig_w, orig_h = pil_img.size
        img_rgba = pil_img.convert("RGBA")
        overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        glacier_obj = evidence.get("glacier_assessment", {})
        lake_obj    = evidence.get("glacial_lake_analysis", {})
        change_obj  = evidence.get("change_analysis", {})

        # ── 1. Glacier mask ──────────────────────────────────────────────────────────
        g_mask = glacier_obj.get("glacier_mask_array")
        if g_mask is not None and isinstance(g_mask, np.ndarray):
            mask_img = Image.fromarray((g_mask * 255).astype(np.uint8), "L").resize((orig_w, orig_h), Image.Resampling.NEAREST)
            g_overlay = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            g_overlay[np.array(mask_img) > 0] = [200, 230, 255, 90]  # Ice blue
            overlay = Image.alpha_composite(overlay, Image.fromarray(g_overlay, "RGBA"))
        
        # ── 2. Glacier Retreat (Lost Ice) ────────────────────────────────────────────
        lost_mask = change_obj.get("lost_ice_mask_array")
        if lost_mask is not None and isinstance(lost_mask, np.ndarray):
            mask_img = Image.fromarray((lost_mask * 255).astype(np.uint8), "L").resize((orig_w, orig_h), Image.Resampling.NEAREST)
            l_overlay = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            l_overlay[np.array(mask_img) > 0] = [255, 100, 30, 150]  # Orange/Red for lost ice
            overlay = Image.alpha_composite(overlay, Image.fromarray(l_overlay, "RGBA"))

        # ── 3. Glacial Lake ────────────────────────────────────────────────────────
        l_mask = lake_obj.get("lake_mask_array")
        if l_mask is not None and isinstance(l_mask, np.ndarray):
            mask_img = Image.fromarray((l_mask * 255).astype(np.uint8), "L").resize((orig_w, orig_h), Image.Resampling.NEAREST)
            lk_overlay = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            lk_overlay[np.array(mask_img) > 0] = [30, 200, 230, 150]  # Teal/cyan for lake
            overlay = Image.alpha_composite(overlay, Image.fromarray(lk_overlay, "RGBA"))

        img_rgba = Image.alpha_composite(img_rgba, overlay)

        # ── 4. Legend card ─────────────────────────────────────────────────────
        card_h = 90
        card_x1, card_x2 = 12, 280
        card_y1 = max(0, orig_h - card_h - 12)
        card_y2 = orig_h - 12

        legend_layer = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_legend = ImageDraw.Draw(legend_layer)
        draw_legend.rectangle([card_x1, card_y1, card_x2, card_y2], fill=(0, 0, 0, 175), outline=(255, 255, 255, 220))
        img_rgba = Image.alpha_composite(img_rgba, legend_layer)

        draw = ImageDraw.Draw(img_rgba)
        try:
            font = ImageFont.load_default()
        except:
            font = None

        draw.text((card_x1 + 10, card_y1 + 6),  "GLACIER LEGEND", fill=(255, 255, 255), font=font)
        draw.text((card_x1 + 10, card_y1 + 26), "White/Blue = Glacier / Ice", fill=(200, 240, 255), font=font)
        draw.text((card_x1 + 10, card_y1 + 46), "Teal           = Glacial Lake", fill=(100, 255, 255), font=font)
        draw.text((card_x1 + 10, card_y1 + 66), "Orange      = Ice Retreat (Loss)", fill=(255, 120, 80), font=font)

        out_filename = f"glacier_analysis_{request_id}.png"
        out_path = os.path.join(self.output_dir, out_filename)
        img_rgba.convert("RGB").save(out_path, "PNG")
        logger.info("[%s] Glacier map saved: %s", request_id, out_path)
        return f"outputs/{out_filename}"
