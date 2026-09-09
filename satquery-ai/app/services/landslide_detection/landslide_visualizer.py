"""
LandslideVisualizer
===================
Generates annotated satellite image overlays for landslide analysis results.

Overlay colours (spec-compliant):
  - Orange/red fill      → HIGH-confidence landslide candidate region
  - Yellow semi-transparent → MODERATE-confidence change region
  - Transparent overlay  → original satellite image remains visible

Labels follow the pattern:
  "Landslide Candidate #1", "Landslide Candidate #2", etc.
"""

import io
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("satquery.landslide.visualizer")

OUTPUT_DIR = "outputs"


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


class LandslideVisualizer:
    """
    Composite annotated overlay generator — landslide analysis results.
    """

    def __init__(self, output_dir: str = OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def draw_visualization(
        self,
        image_source: Any,
        evidence: Dict[str, Any],
        request_id: str,
    ) -> Optional[str]:
        """
        Draw landslide candidate overlays on the target image.

        Returns:
            Relative path to saved PNG (e.g. "outputs/landslide_abc123.png"),
            or None on failure.
        """
        try:
            pil_img = _load_as_pil(image_source)
        except Exception as exc:
            logger.error("[%s] LandslideVisualizer: cannot load image — %s", request_id, exc)
            return None

        orig_w, orig_h = pil_img.size
        img_rgba = pil_img.convert("RGBA")

        # ── 1. Draw candidate region overlays ────────────────────────────
        overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)

        candidate_regions: List[Dict[str, Any]] = evidence.get("candidate_regions", [])

        # Also draw raw disturbance mask if available
        dist_mask = evidence.get("disturbance_mask_array")
        if dist_mask is None:
            dist_mask = evidence.get("combined_candidate_mask")

        if dist_mask is not None and isinstance(dist_mask, np.ndarray):
            mask_img = Image.fromarray((dist_mask * 255).astype(np.uint8), "L")
            mask_up = mask_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)
            mask_arr = np.array(mask_up) > 0

            dist_layer = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            # Orange-red semi-transparent fill for disturbed pixels
            dist_layer[mask_arr] = [230, 100, 20, 80]   # RGBA: orange-red, ~31% opacity
            dist_pil = Image.fromarray(dist_layer, "RGBA")
            overlay = Image.alpha_composite(overlay, dist_pil)
            draw_ov = ImageDraw.Draw(overlay)
            logger.info("[%s] Applied pixel-level disturbance mask", request_id)

        # ── 2. Candidate bounding boxes & labels ─────────────────────────
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        analysis_h, analysis_w = 512, 512   # detection resolution
        scale_x = orig_w / analysis_w
        scale_y = orig_h / analysis_h

        for region in candidate_regions:
            bbox = region.get("bbox", [])
            if len(bbox) < 4:
                continue
            ymin, xmin, ymax, xmax = bbox
            # Scale to original image size
            xs0 = int(xmin * scale_x)
            ys0 = int(ymin * scale_y)
            xs1 = int(xmax * scale_x)
            ys1 = int(ymax * scale_y)

            conf = region.get("confidence", 0.5)
            rid  = region.get("id", 1)

            # High confidence → orange-red; lower → yellow
            if conf >= 0.75:
                box_color  = (230, 80, 20, 200)    # orange-red
                fill_color = (230, 80, 20, 50)
                label_bg   = (230, 80, 20)
            else:
                box_color  = (240, 200, 30, 200)   # yellow
                fill_color = (240, 200, 30, 40)
                label_bg   = (200, 160, 20)

            draw_ov.rectangle([xs0, ys0, xs1, ys1], outline=box_color, width=3, fill=fill_color)

            # Label
            label_text = f"Landslide Candidate #{rid}"
            try:
                tb = draw_ov.textbbox((xs0 + 4, ys0 - 22), label_text, font=font)
                lbg = [tb[0] - 4, tb[1] - 2, tb[2] + 4, tb[3] + 2]
            except Exception:
                lw = len(label_text) * 6
                lbg = [xs0, max(0, ys0 - 18), xs0 + lw + 8, ys0]

            # Clamp label card
            if lbg[1] < 0:
                dy = -lbg[1]
                lbg[1] += dy; lbg[3] += dy
            draw_ov.rectangle(lbg, fill=label_bg + (220,))
            draw_ov.text((lbg[0] + 4, lbg[1] + 2), label_text, fill=(255, 255, 255, 255), font=font)

        # Composite overlay
        img_rgba = Image.alpha_composite(img_rgba, overlay)

        # ── 3. Legend card ────────────────────────────────────────────────
        card_h = 120
        card_x1, card_x2 = 12, 320
        card_y1 = max(0, orig_h - card_h - 12)
        card_y2 = orig_h - 12

        legend_layer = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_lg = ImageDraw.Draw(legend_layer)
        draw_lg.rectangle([card_x1, card_y1, card_x2, card_y2],
                          fill=(0, 0, 0, 180), outline=(255, 255, 255, 200), width=1)
        img_rgba = Image.alpha_composite(img_rgba, legend_layer)

        draw_final = ImageDraw.Draw(img_rgba)
        draw_final.text((card_x1 + 10, card_y1 + 6),
                        "SatQuery Landslide Analysis", fill=(255, 255, 255), font=font)
        draw_final.text((card_x1 + 10, card_y1 + 26),
                        "Orange/Red = High-Confidence Candidate", fill=(255, 140, 60), font=font)
        draw_final.text((card_x1 + 10, card_y1 + 46),
                        "Yellow     = Moderate-Confidence Change", fill=(240, 220, 60), font=font)
        draw_final.text((card_x1 + 10, card_y1 + 66),
                        "AI-assisted — ground verification advised", fill=(180, 180, 180), font=font)

        # ── 4. Stats (top-right) ──────────────────────────────────────────
        landslide_ass = evidence.get("landslide_assessment", {})
        dist_pct = landslide_ass.get("disturbance_percentage", 0.0)
        risk_score = evidence.get("risk_score", 0)
        stats_text = f"Disturbed: {dist_pct:.1f}% | Risk: {risk_score}/100"
        draw_final.text((max(orig_w - 300, 10), 10), stats_text,
                        fill=(220, 200, 180), font=font)

        # ── 5. Save ───────────────────────────────────────────────────────
        out_filename = f"landslide_analysis_{request_id}.png"
        out_path = os.path.join(self.output_dir, out_filename)
        img_rgba.convert("RGB").save(out_path, "PNG")
        logger.info("[%s] Landslide analysis map saved: %s", request_id, out_path)
        return f"outputs/{out_filename}"
