"""
FloodEvidenceCollector — Orchestrates all flood evidence collection.

Pipeline:
    Image(s)
        ↓ WaterAnalyzer (SpectralWaterDetector) → water masks + regions
        ↓ Building segmentation (VisualGroundingService) → building bboxes
        ↓ Spatial overlap analysis → affected buildings
        ↓ VLM verification (SingleImageAnalysisAgent) → text confirmation
        ↓ Affected region summarization
"""

import re
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("satquery.flood.evidence_collector")

# ── Keep local copy of spatial utils ──────────────────────────────────────────
from app.utils.spatial_analysis import calculate_bbox_overlap
from app.services.visual_grounding_service import VisualGroundingService
from app.agents.single_image_analysis_agent import SingleImageAnalysisAgent
from app.services.flood_detection.water_analyzer import WaterAnalyzer
from app.services.flood_detection.spectral_water_detector import _load_as_pil


# ── Negation-aware VLM text filter ─────────────────────────────────────────────
def is_present_without_negation(keywords: List[str], text: str) -> bool:
    """
    Returns True ONLY if at least one keyword appears in the text without
    a negation term in the same clause.
    """
    clauses = re.split(r'[.;:]', text.lower())
    negation_terms = r'\b(no|not|neither|none|without|never|zero|clear of|low risk|free of|unlikely|absence of|disprove|lack of)\b'
    for clause in clauses:
        for kw in keywords:
            for match in re.finditer(r'\b' + re.escape(kw) + r'\b', clause):
                preceding = clause[:match.start()]
                if re.search(negation_terms, preceding):
                    continue
                return True
    return False


# ── Infrastructure placeholder ─────────────────────────────────────────────────
class InfrastructureImpactAnalyzer:
    """Placeholder for future road/bridge/railway infrastructure analysis."""
    @staticmethod
    def analyze() -> str:
        return "NOT_AVAILABLE"


# ── Main collector ─────────────────────────────────────────────────────────────
class FloodEvidenceCollector:
    """
    Coordinates gathering water detection, building segmentation,
    spatial overlap analysis, and VLM verification evidence.
    """

    def __init__(
        self,
        water_analyzer: Optional[WaterAnalyzer] = None,
        grounding_service: Optional[VisualGroundingService] = None,
        vla_agent: Optional[SingleImageAnalysisAgent] = None
    ) -> None:
        self.water_analyzer = water_analyzer or WaterAnalyzer()
        self.grounding_service = grounding_service or VisualGroundingService()
        self.vla_agent = vla_agent or SingleImageAnalysisAgent()

    def collect_evidence(
        self,
        image: Any,
        before_image: Optional[Any] = None,
        after_image: Optional[Any] = None,
        query: str = "",
        request_id: str = "temp"
    ) -> Dict[str, Any]:
        """
        Collects all flood-related evidence metrics.

        Multi-temporal path: before_image + after_image
        Single-image path:   image
        """
        evidence: Dict[str, Any] = {}

        # ── 1. Water Analysis ──────────────────────────────────────────────────
        if before_image is not None and after_image is not None:
            logger.info("[%s] Running multi-temporal water analysis...", request_id)
            temporal = self.water_analyzer.compare_temporal(before_image, after_image, request_id)

            before_water = temporal["before_analysis"]
            after_water  = temporal["after_analysis"]
            comparison   = temporal["comparison"]

            evidence["water_analysis"]  = after_water
            evidence["water_comparison"] = comparison
            target_image = after_image   # use after image for building analysis + VLM

        else:
            logger.info("[%s] Running single-image water analysis...", request_id)
            water_info = self.water_analyzer.analyze_water(image, request_id=request_id)
            evidence["water_analysis"]   = water_info
            evidence["water_comparison"] = None
            target_image = image

        water_regions = evidence["water_analysis"].get("water_regions", [])
        logger.info(
            "[%s] Water regions for building overlap: %d",
            request_id, len(water_regions)
        )

        # ── 2. Load target image as PIL (safe re-open) ─────────────────────────
        # We need a raw bytes version for grounding service and VLM
        try:
            pil_target = _load_as_pil(target_image)
            buf = io.BytesIO()
            pil_target.save(buf, format="PNG")
            target_bytes = buf.getvalue()
        except Exception as e:
            logger.warning("[%s] Could not convert target image to bytes: %s", request_id, e)
            target_bytes = None
            pil_target = None

        # ── 3. Building Segmentation ───────────────────────────────────────────
        potentially_affected = []
        building_detections = []
        buildings_detected = False

        if target_bytes is not None:
            logger.info("[%s] Running building segmentation...", request_id)
            try:
                building_info = self.grounding_service.process_grounding(
                    target_bytes, "buildings", request_id
                )
                buildings_detected = building_info.get("status") == "SUCCESS"
                building_detections = building_info.get("detections", [])
                logger.info(
                    "[%s] Buildings found: %d (status=%s)",
                    request_id, len(building_detections), building_info.get("status")
                )
            except Exception as e:
                logger.warning("[%s] Building segmentation failed: %s", request_id, e)

        # ── 4. Spatial Overlap: Water ∩ Buildings ──────────────────────────────
        for b in building_detections:
            b_box = b.get("bbox", [])
            if not b_box:
                continue
            max_overlap = 0.0
            for w in water_regions:
                w_box = w.get("bbox", [])
                if w_box:
                    overlap = calculate_bbox_overlap(b_box, w_box)
                    if overlap > max_overlap:
                        max_overlap = overlap

            if max_overlap > 0.0:
                overlap_pct = round(max_overlap * 100.0, 1)
                risk_level = "LOW"
                if overlap_pct >= 50.0:
                    risk_level = "HIGH"
                elif overlap_pct >= 15.0:
                    risk_level = "MODERATE"

                potentially_affected.append({
                    "id": b.get("id"),
                    "bbox": b_box,
                    "overlap_percentage": overlap_pct,
                    "risk": risk_level
                })

        logger.info("[%s] Potentially affected buildings: %d", request_id, len(potentially_affected))

        evidence["potentially_affected_buildings"] = potentially_affected
        evidence["buildings_detected"] = buildings_detected
        evidence["building_detections"] = building_detections

        # ── 5. VLM Verification ────────────────────────────────────────────────
        vlm_analysis = None
        vlm_indicated = False

        if target_bytes is not None:
            logger.info("[%s] Running VLM flood verification...", request_id)
            try:
                vla_query = (
                    "Analyze this satellite image specifically for possible flooding. Identify: "
                    "1. Large areas covered by water. 2. Water surrounding buildings. "
                    "3. Water crossing roads. 4. Possible submerged infrastructure. "
                    "5. Whether visible water appears normal or unusual."
                )
                vla_res = self.vla_agent.execute(target_bytes, vla_query)
                if vla_res.status == "SUCCESS" and vla_res.result:
                    ans_text = vla_res.result.answer
                    vlm_analysis = ans_text
                    vlm_indicated = is_present_without_negation(
                        ["flood", "flooded", "flooding", "inundated", "submerged",
                         "water expansion", "overflow", "inundation"],
                        ans_text
                    )
                    logger.info(
                        "[%s] VLM analysis complete: vlm_indicated=%s",
                        request_id, vlm_indicated
                    )
            except Exception as e:
                logger.warning("[%s] VLM verification failed (non-fatal): %s", request_id, e)

        evidence["vlm_text_report"] = vlm_analysis
        evidence["vlm_indicated"]   = vlm_indicated

        # ── 6. Infrastructure Analysis ────────────────────────────────────────
        evidence["infrastructure_analysis"] = InfrastructureImpactAnalyzer.analyze()

        # ── 7. Affected Region Summarization ──────────────────────────────────
        affected_regions = []

        # Prefer new water expansion regions (multi-temporal), fall back to all water regions
        water_comparison = evidence.get("water_comparison") or {}
        region_source = water_comparison.get("new_water_regions") or water_regions

        if pil_target is not None:
            orig_w, orig_h = pil_target.size
        else:
            orig_w = orig_h = 512

        third_w = orig_w / 3.0
        third_h = orig_h / 3.0

        for idx, wr in enumerate(region_source, 1):
            bbox = wr.get("bbox", [])
            if not bbox or len(bbox) < 4:
                continue

            ymin, xmin, ymax, xmax = bbox[:4]
            cx = (xmin + xmax) / 2.0
            cy = (ymin + ymax) / 2.0

            # Spatial location label
            y_loc = "north" if cy < third_h else ("south" if cy > 2 * third_h else "center")
            x_loc = "west" if cx < third_w else ("east" if cx > 2 * third_w else "center")
            if y_loc == "center" and x_loc == "center":
                location = "center"
            elif y_loc == "center":
                location = x_loc
            elif x_loc == "center":
                location = y_loc
            else:
                location = f"{y_loc}{x_loc}"

            # Building overlap sum for severity
            overlap_sum = 0.0
            overlap_count = 0
            for b in building_detections:
                b_box = b.get("bbox", [])
                if b_box:
                    ov = calculate_bbox_overlap(b_box, bbox)
                    if ov > 0.0:
                        overlap_sum += ov
                        overlap_count += 1

            avg_overlap = (overlap_sum / overlap_count * 100.0) if overlap_count > 0 else 0.0
            expansion_pct = water_comparison.get("water_expansion_percentage", 0.0)

            if avg_overlap >= 50.0 or expansion_pct >= 80.0:
                severity = "HIGH"
            elif avg_overlap >= 15.0 or expansion_pct >= 30.0:
                severity = "MODERATE"
            else:
                severity = "LOW"

            affected_regions.append({
                "region_id": idx,
                "bbox": bbox,
                "location": location,
                "severity": severity,
                "water_overlap_percentage": round(avg_overlap if overlap_count > 0 else wr.get("area_percentage", 0.0), 1)
            })

        evidence["affected_regions"] = affected_regions
        logger.info("[%s] Evidence collection complete. Regions=%d", request_id, len(affected_regions))

        return evidence
