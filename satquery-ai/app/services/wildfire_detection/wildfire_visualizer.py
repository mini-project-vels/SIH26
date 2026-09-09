"""
WildfireVisualizer
==================
Generates annotated satellite image overlays for wildfire analysis results.

Overlay colour scheme:
  RED/ORANGE     — high-confidence active fire indicator / burned area
  DARK RED fill  — burned-area pixel mask
  YELLOW         — moderate-confidence change / smoke candidate
  GREY tint      — smoke candidate region
"""

import io
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("satquery.wildfire.visualizer")

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
    raise TypeError(f"Cannot load from {type(src)}")


class WildfireVisualizer:

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def draw_visualization(
        self,
        image_source: Any,
        evidence: Dict[str, Any],
        request_id: str,
    ) -> Optional[str]:
        """
        Generate annotated wildfire overlay image.

        Returns relative path (e.g. "outputs/wildfire_abc123.png") or None.
        """
        try:
            pil = _load_as_pil(image_source)
        except Exception as exc:
            logger.error("[%s] Visualizer load failure: %s", request_id, exc)
            return None

        orig_w, orig_h = pil.size
        img_rgba = pil.convert("RGBA")
        overlay  = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
        draw_ov  = ImageDraw.Draw(overlay)

        # ── Pixel-level burned-area mask ──────────────────────────────────
        burned_mask = evidence.get("burned_mask_array")
        if burned_mask is None:
            # Try combined mask from temporal analysis
            burned_mask = evidence.get("combined_candidate_mask")

        if burned_mask is not None and isinstance(burned_mask, np.ndarray):
            m = Image.fromarray((burned_mask * 255).astype(np.uint8), "L")
            m = m.resize((orig_w, orig_h), Image.Resampling.NEAREST)
            m_arr = np.array(m) > 0

            burn_layer = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            burn_layer[m_arr] = [180, 30, 10, 90]     # dark red, ~35% opacity
            overlay = Image.alpha_composite(overlay, Image.fromarray(burn_layer, "RGBA"))
            draw_ov = ImageDraw.Draw(overlay)

        # ── Smoke mask ────────────────────────────────────────────────────
        smoke_mask = evidence.get("smoke_mask_array")
        if smoke_mask is not None and isinstance(smoke_mask, np.ndarray):
            sm = Image.fromarray((smoke_mask * 255).astype(np.uint8), "L")
            sm = sm.resize((orig_w, orig_h), Image.Resampling.NEAREST)
            sm_arr = np.array(sm) > 0

            smoke_layer = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            smoke_layer[sm_arr] = [180, 180, 180, 50]  # grey, subtle
            overlay = Image.alpha_composite(overlay, Image.fromarray(smoke_layer, "RGBA"))
            draw_ov = ImageDraw.Draw(overlay)

        # ── Fire indicator (bright warm pixels) ───────────────────────────
        fire_mask = evidence.get("fire_mask_array")
        if fire_mask is not None and isinstance(fire_mask, np.ndarray):
            fm = Image.fromarray((fire_mask * 255).astype(np.uint8), "L")
            fm = fm.resize((orig_w, orig_h), Image.Resampling.NEAREST)
            fm_arr = np.array(fm) > 0

            fire_layer = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
            fire_layer[fm_arr] = [255, 80, 0, 120]     # bright orange-red
            overlay = Image.alpha_composite(overlay, Image.fromarray(fire_layer, "RGBA"))
            draw_ov = ImageDraw.Draw(overlay)

        # ── Load font ─────────────────────────────────────────────────────
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # ── Candidate bounding boxes ───────────────────────────────────────
        scale_x = orig_w / 512.0
        scale_y = orig_h / 512.0
        candidate_regions: List[Dict] = evidence.get("candidate_regions", [])

        for region in candidate_regions:
            bbox = region.get("bbox", [])
            if len(bbox) < 4:
                continue
            ymin, xmin, ymax, xmax = bbox
            xs0, ys0 = int(xmin * scale_x), int(ymin * scale_y)
            xs1, ys1 = int(xmax * scale_x), int(ymax * scale_y)
            conf = region.get("confidence", 0.5)
            rid  = region.get("id", 1)

            # Determine type label
            region_label_raw = region.get("label", "wildfire_candidate")
            if "smoke" in region_label_raw:
                box_col  = (200, 200, 200, 200)
                fill_col = (200, 200, 200,  40)
                bg_col   = (150, 150, 150)
                lbl_text = f"Smoke Candidate #{rid}"
            elif conf >= 0.72:
                box_col  = (240, 60,  20, 210)
                fill_col = (240, 60,  20,  55)
                bg_col   = (220, 50,  10)
                lbl_text = f"Active Fire Candidate #{rid}"
            else:
                box_col  = (240, 200, 30, 210)
                fill_col = (240, 200, 30,  45)
                bg_col   = (210, 160, 20)
                lbl_text = f"Burned Area #{rid}"

            if conf < 0.65:
                lbl_text += " — Requires Verification"

            draw_ov.rectangle([xs0, ys0, xs1, ys1], outline=box_col, width=3, fill=fill_col)

            try:
                tb  = draw_ov.textbbox((xs0+4, ys0-22), lbl_text, font=font)
                lbg = [tb[0]-4, tb[1]-2, tb[2]+4, tb[3]+2]
            except Exception:
                lbg = [xs0, max(0, ys0-18), xs0 + len(lbl_text)*6 + 8, ys0]

            if lbg[1] < 0:
                dy = -lbg[1]; lbg[1] += dy; lbg[3] += dy

            draw_ov.rectangle(lbg, fill=bg_col + (220,))
            draw_ov.text((lbg[0]+4, lbg[1]+2), lbl_text, fill=(255,255,255,255), font=font)

        img_rgba = Image.alpha_composite(img_rgba, overlay)

        # ── Legend card ────────────────────────────────────────────────────
        card_h  = 120
        card_x1, card_x2 = 12, 340
        card_y1 = max(0, orig_h - card_h - 12)
        card_y2 = orig_h - 12

        leg = Image.new("RGBA", img_rgba.size, (0,0,0,0))
        leg_d = ImageDraw.Draw(leg)
        leg_d.rectangle([card_x1, card_y1, card_x2, card_y2],
                        fill=(0,0,0,185), outline=(255,255,255,200), width=1)
        img_rgba = Image.alpha_composite(img_rgba, leg)

        d = ImageDraw.Draw(img_rgba)
        d.text((card_x1+10, card_y1+6),  "SatQuery Wildfire Analysis",   fill=(255,255,255), font=font)
        d.text((card_x1+10, card_y1+26), "Red/Orange = Fire Candidate",   fill=(240, 90, 30), font=font)
        d.text((card_x1+10, card_y1+46), "Dark Red   = Burned Area",      fill=(180, 40, 20), font=font)
        d.text((card_x1+10, card_y1+66), "Grey Tint  = Smoke Candidate",  fill=(190,190,190), font=font)
        d.text((card_x1+10, card_y1+86), "AI-assisted — thermal verify needed", fill=(160,160,160), font=font)

        # ── Stats ──────────────────────────────────────────────────────────
        wildfire_ass = evidence.get("wildfire_assessment", {})
        burn_pct  = wildfire_ass.get("burned_percentage", 0.0)
        risk_sc   = evidence.get("risk_score", 0)
        stats     = f"Burned: {burn_pct:.1f}% | Risk: {risk_sc}/100"
        d.text((max(orig_w - 260, 10), 10), stats, fill=(220, 180, 130), font=font)

        # ── Save ───────────────────────────────────────────────────────────
        fname    = f"wildfire_analysis_{request_id}.png"
        out_path = os.path.join(self.output_dir, fname)
        img_rgba.convert("RGB").save(out_path, "PNG")
        logger.info("[%s] Wildfire analysis map saved: %s", request_id, out_path)
        return f"outputs/{fname}"
