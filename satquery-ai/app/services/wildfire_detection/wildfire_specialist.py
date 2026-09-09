"""
WildfireSpecialist
==================
Full wildfire / forest-fire detection and risk assessment pipeline.

Pipeline
--------
  [Image input]
       ↓  Preprocessing / loading
       ↓  Geometric alignment (temporal pair)
       ↓  Spectral fire / burned-area analysis
       ↓  Vegetation-loss & smoke detection
       ↓  Fire-spread trend (temporal)
       ↓  AI visual reasoning (HuggingFace VLM)
       ↓  Multi-factor risk scoring
       ↓  Infrastructure proximity estimation
       ↓  Annotated image generation
       ↓  Structured JSON response

Detection labels
----------------
  WILDFIRE_SPECIALIST_LIMITED  — no dedicated fire segmentation model in deployment
  OPTICAL_SPECTRAL_HEURISTIC   — RGB spectral proxy analysis
  VLM_VISUAL_REASONING         — HuggingFace vision-language model

Data transparency rules
-----------------------
  - NEVER claim RGB proves thermals / hotspots
  - ALL thermal evidence reported as "Thermal fire evidence unavailable."
  - NASA FIRMS / MODIS / VIIRS / Sentinel-3 hooks prepared but NOT integrated
  - AI reasoning labelled VLM_VISUAL_REASONING, NOT a trained fire-seg model
  - Fire spread only reported when before+after images are provided
  - No fabricated satellite metadata

Alert states
------------
  INFO → WATCH → WARNING → CRITICAL
  Only CRITICAL when ≥3 independent evidence sources agree.

Logging
-------
Every request emits:
  request_id, mode, detection_status, risk_score, risk_level,
  confidence, burned_pct, smoke_pct, fire_indicator_pct,
  change_pct, candidates, trend, annotated, time_s
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from app.services.wildfire_detection.spectral_fire_detector import SpectralFireDetector
from app.services.wildfire_detection.wildfire_risk import WildfireRiskCalculator
from app.services.wildfire_detection.wildfire_visualizer import WildfireVisualizer

logger = logging.getLogger("satquery.wildfire.specialist")

_STANDARD_LIMITATIONS = [
    "Assessment uses optical satellite imagery spectral heuristics — NOT a trained fire-detection model.",
    "No dedicated wildfire segmentation model is deployed (WILDFIRE_SPECIALIST_LIMITED).",
    "Thermal/infrared data (NASA FIRMS, MODIS, VIIRS, Sentinel-3) is NOT integrated.",
    "RGB imagery cannot reliably detect active fire hotspots without SWIR/TIR bands.",
    "Active fire status requires thermal confirmation before issuing alerts.",
    "Ground verification is required before any emergency response.",
    "SAR integration (Sentinel-1) for fire-scar mapping is architecturally prepared but not yet deployed.",
]


class WildfireSpecialist:
    """Top-level wildfire detection & risk assessment coordinator."""

    def __init__(self):
        self.detector   = SpectralFireDetector()
        self.risk_calc  = WildfireRiskCalculator()
        self.visualizer = WildfireVisualizer()

    # ─────────────────────────────────────────────────────────────────────────
    #  Main pipeline entry
    # ─────────────────────────────────────────────────────────────────────────

    def execute(
        self,
        query: str,
        image: Optional[Any]        = None,
        before_image: Optional[Any] = None,
        after_image: Optional[Any]  = None,
        request_id: Optional[str]   = None,
    ) -> Dict[str, Any]:
        req_id  = request_id or str(uuid.uuid4())[:12]
        t_start = time.time()

        logger.info(
            "[%s] WildfireSpecialist.execute — query=%r, img=%s, before=%s, after=%s",
            req_id, query[:80],
            "YES" if image else "NO",
            "YES" if before_image else "NO",
            "YES" if after_image else "NO",
        )

        has_temporal = before_image is not None and after_image is not None
        has_single   = image is not None
        target_image = after_image if has_temporal else image

        if not has_single and not has_temporal:
            return self._no_image_response(req_id, query, t_start)

        ev: Dict[str, Any] = {}

        # ── Spectral analysis ────────────────────────────────────────────────
        if has_temporal:
            td = self.detector.compare_temporal(before_image, after_image, req_id)
            ev["wildfire_assessment_raw"] = td.get("after_analysis", {})
            ev["change_analysis"]         = td.get("change_analysis", {})
            ev["candidate_regions"]       = td.get("candidate_regions", [])
            ev["fire_spread"]             = td.get("fire_spread", {"trend": "NOT_AVAILABLE", "change_percentage": 0.0, "confidence": 0.0})
            ev["burned_mask"]             = td.get("new_burned_mask")
            ev["smoke_mask"]              = td.get("new_smoke_mask")
            ev["combined_mask"]           = td.get("combined_candidate_mask")
            ev["before_analysis"]         = td.get("before_analysis", {})
            analysis_type = "temporal_burned_area_analysis"
        else:
            sd = self.detector.detect_fire_evidence(image, req_id)
            ev["wildfire_assessment_raw"] = sd
            ev["candidate_regions"]       = sd.get("candidate_regions", [])
            ev["fire_spread"]             = {"trend": "NOT_AVAILABLE", "change_percentage": 0.0, "confidence": 0.0}
            ev["burned_mask"]             = sd.get("burned_mask_array")
            ev["smoke_mask"]              = sd.get("smoke_mask_array")
            ev["combined_mask"]           = None
            ev["before_analysis"]         = {}
            ev["change_analysis"]         = {
                "change_detected": False, "change_type": None,
                "changed_percentage": 0.0, "vegetation_loss_percentage": 0.0,
                "new_burned_area_percentage": 0.0, "new_smoke_percentage": 0.0,
                "estimated_change_percentage": 0.0, "confidence": 0.0,
            }
            analysis_type = "single_image_fire_analysis"

        raw = ev["wildfire_assessment_raw"]

        # ── Build wildfire_assessment dict ───────────────────────────────────
        burn_pct   = raw.get("burned_percentage", 0.0)
        fire_pct   = raw.get("fire_indicator_percentage", 0.0)
        smoke_pct  = raw.get("smoke_percentage", 0.0)
        burned_det = raw.get("burned_area_detected", False)
        fire_det   = raw.get("fire_indicator_detected", False)
        smoke_det  = raw.get("smoke_detected", False)

        # Active fire: RGB proxy only — explicitly uncertain
        active_fire = fire_det and fire_pct > 1.0   # not claimed as thermals

        wildfire_assessment = {
            "fire_detected":             burned_det or fire_det,
            "active_fire_detected":      active_fire,
            "active_fire_note":          "RGB proxy only — thermal confirmation unavailable." if active_fire else None,
            "smoke_detected":            smoke_det,
            "burned_area_detected":      burned_det,
            "affected_area_percentage":  round(burn_pct + fire_pct, 2),
            "affected_pixels":           raw.get("affected_pixels", 0),
            "burned_percentage":         burn_pct,
            "smoke_percentage":          smoke_pct,
            "fire_indicator_percentage": fire_pct,
            "vegetation_percentage":     raw.get("vegetation_percentage", 0.0),
            "confidence":                0.0,    # set after risk calc
            "model_label":               raw.get("model_label", "WILDFIRE_SPECIALIST_LIMITED"),
            "data_source":               raw.get("data_source", "OPTICAL_SPECTRAL_HEURISTIC"),
        }
        ev["wildfire_assessment"] = wildfire_assessment

        # ── AI visual reasoning ──────────────────────────────────────────────
        vlm_text, vlm_model, vlm_conf = self._run_vlm(target_image, query, req_id)
        ev["vlm_assessment"] = {
            "available": vlm_text is not None,
            "model": vlm_model,
            "text": vlm_text,
            "confidence": vlm_conf,
        }

        # ── Risk scoring ─────────────────────────────────────────────────────
        risk = self.risk_calc.calculate_risk(ev)
        ev["risk_score"] = risk["risk_score"]
        wildfire_assessment["confidence"] = risk["confidence"]

        # ── Annotated image ──────────────────────────────────────────────────
        annotated_path = None
        should_annotate = (
            target_image is not None
            and (burn_pct > 3.0 or fire_pct > 0.5 or len(ev["candidate_regions"]) > 0)
        )
        if should_annotate:
            viz_ev = {
                "wildfire_assessment": wildfire_assessment,
                "candidate_regions":   ev["candidate_regions"],
                "burned_mask_array":   ev.get("burned_mask"),
                "smoke_mask_array":    ev.get("smoke_mask"),
                "fire_mask_array":     raw.get("fire_mask_array"),
                "combined_candidate_mask": ev.get("combined_mask"),
                "risk_score":          risk["risk_score"],
            }
            try:
                annotated_path = self.visualizer.draw_visualization(target_image, viz_ev, req_id)
            except Exception as exc:
                logger.warning("[%s] Visualizer error: %s", req_id, exc)

        # ── Infrastructure impact ─────────────────────────────────────────────
        impact = self._impact(ev["candidate_regions"], risk)

        # ── Recommendations ──────────────────────────────────────────────────
        recs = self._recommendations(risk["risk_level"], has_temporal, active_fire, smoke_det)

        # ── Limitations ──────────────────────────────────────────────────────
        limitations = list(_STANDARD_LIMITATIONS)
        if not has_temporal:
            limitations.append("Single image only — fire spread trend unavailable.")
        if not vlm_text:
            limitations.append("AI visual reasoning unavailable for this request.")

        # ── Detection status ─────────────────────────────────────────────────
        rs = risk["risk_score"]
        if rs >= 51 or (burned_det and ev["change_analysis"].get("change_detected")):
            det_status = "DETECTED"
        elif rs >= 26 or burned_det or fire_det or smoke_det:
            det_status = "POSSIBLE"
        else:
            det_status = "NOT_DETECTED"

        vlm_avail = ev["vlm_assessment"]["available"]
        if det_status == "POSSIBLE" and not vlm_avail and not has_temporal:
            det_status = "INCONCLUSIVE"

        elapsed = round(time.time() - t_start, 3)

        logger.info(
            "[%s] WILDFIRE REPORT | mode=%s detect=%s risk=%d(%s) "
            "conf=%.2f burned=%.1f%% smoke=%.1f%% fire_ind=%.1f%% "
            "trend=%s candidates=%d annotated=%s time=%.3fs",
            req_id, analysis_type, det_status,
            risk["risk_score"], risk["risk_level"], risk["confidence"],
            burn_pct, smoke_pct, fire_pct,
            ev["fire_spread"]["trend"],
            len(ev["candidate_regions"]),
            annotated_path or "none",
            elapsed,
        )

        # Serialisable candidate list
        clean_candidates = [
            {k: v for k, v in r.items() if not isinstance(v, type(None))}
            for r in ev["candidate_regions"]
        ]

        return {
            "request_id":      req_id,
            "status":          "SUCCESS",
            "query":           query,
            "analysis_type":   "wildfire_analysis",
            "disaster_type":   "WILDFIRE",
            "assessment_status": "COMPLETED",
            "detection_status": det_status,

            "risk_assessment": {
                "risk_score":    risk["risk_score"],
                "risk_level":    risk["risk_level"],
                "confidence":    risk["confidence"],
                "alert_state":   risk["alert_state"],
                "risk_factors":  risk["risk_factors"],
                "ai_disclaimer": risk.get("ai_disclaimer"),
            },

            "wildfire_assessment": {
                "fire_detected":             wildfire_assessment["fire_detected"],
                "active_fire_detected":      wildfire_assessment["active_fire_detected"],
                "active_fire_note":          wildfire_assessment["active_fire_note"],
                "smoke_detected":            wildfire_assessment["smoke_detected"],
                "burned_area_detected":      wildfire_assessment["burned_area_detected"],
                "confidence":                wildfire_assessment["confidence"],
                "affected_area_percentage":  wildfire_assessment["affected_area_percentage"],
                "burned_percentage":         wildfire_assessment["burned_percentage"],
                "smoke_percentage":          wildfire_assessment["smoke_percentage"],
                "fire_indicator_percentage": wildfire_assessment["fire_indicator_percentage"],
                "vegetation_percentage":     wildfire_assessment["vegetation_percentage"],
                "affected_pixels":           wildfire_assessment["affected_pixels"],
                "model_label":               wildfire_assessment["model_label"],
                "data_source":               wildfire_assessment["data_source"],
            },

            "change_analysis": {
                "change_detected":             ev["change_analysis"].get("change_detected", False),
                "change_type":                 ev["change_analysis"].get("change_type"),
                "estimated_change_percentage": ev["change_analysis"].get("estimated_change_percentage", 0.0),
                "vegetation_loss_percentage":  ev["change_analysis"].get("vegetation_loss_percentage", 0.0),
                "new_burned_area_percentage":  ev["change_analysis"].get("new_burned_area_percentage", 0.0),
                "new_smoke_percentage":        ev["change_analysis"].get("new_smoke_percentage", 0.0),
                "confidence":                  ev["change_analysis"].get("confidence", 0.0),
            },

            "fire_spread": ev["fire_spread"],

            "ai_visual_assessment": {
                "available":   vlm_avail,
                "model":       vlm_model,
                "reasoning":   vlm_text,
                "confidence":  vlm_conf,
                "type":        "VLM_VISUAL_REASONING",
                "note": (
                    "AI visual reasoning — NOT a dedicated fire-detection model."
                    if vlm_avail else "AI visual reasoning unavailable."
                ),
            },

            "affected_regions": clean_candidates,

            "potential_impact": impact,

            "thermal_evidence": {
                "thermal_available": False,
                "hotspot_data":      None,
                "note": (
                    "Thermal fire evidence unavailable. "
                    "Hooks prepared for NASA FIRMS, MODIS, VIIRS, Sentinel-3 SLSTR."
                ),
                "firms_status": "NOT_INTEGRATED",
            },

            "satellite_info": {
                "platform":     "Optical RGB satellite (unknown)",
                "data_source":  "USER_UPLOADED",
                "thermal_product": "UNAVAILABLE",
                "sar_fire_scar":   "ARCHITECTURALLY_PREPARED",
                "note": "Real satellite metadata unavailable — user-uploaded image.",
            },

            "recommendations": recs,

            "annotated_image": {
                "generated":     annotated_path is not None,
                "path_or_url":   annotated_path,
            },

            "limitations":               limitations,
            "processing_time_seconds":   elapsed,
            "analysis_mode":             analysis_type,
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  AI visual reasoning
    # ─────────────────────────────────────────────────────────────────────────

    def _run_vlm(self, image: Optional[Any], query: str, req_id: str):
        if image is None:
            return None, None, 0.0
        try:
            from app.services.huggingface_vision_service import HuggingFaceVisionService
            from app.config import vision_config
            svc   = HuggingFaceVisionService()
            model = vision_config.HF_VISION_MODEL
            prompt = (
                "You are a satellite imagery analyst specialising in wildfire and forest-fire detection. "
                "Examine this satellite image and report:\n"
                "1. Evidence of active fire, smoke plumes, or fire fronts\n"
                "2. Burned or charred areas (fire scars, darkened surfaces)\n"
                "3. Vegetation loss or stripped forest areas\n"
                "4. Proximity of fire to roads, buildings, or infrastructure\n"
                "5. Any smoke or haze presence\n"
                "Be factual. If no clear fire evidence, say so. "
                "Do NOT claim thermal hotspots from RGB imagery alone. "
                "Conclude: WILDFIRE_INDICATORS: YES/NO/UNCERTAIN\n\n"
                f"User query: {query}"
            )
            text = svc.analyze_image(image, prompt)
            logger.info("[%s] VLM complete — model=%s", req_id, model)
            return text, model, 0.75
        except Exception as exc:
            logger.warning("[%s] VLM error: %s", req_id, exc)
            return None, None, 0.0

    # ─────────────────────────────────────────────────────────────────────────
    #  Infrastructure impact
    # ─────────────────────────────────────────────────────────────────────────

    def _impact(self, candidates: List[Dict], risk: Dict) -> Dict[str, Any]:
        n     = len(candidates)
        level = risk.get("risk_level", "LOW")
        if n == 0:
            return {
                "potentially_affected_buildings":      0,
                "potentially_affected_roads":          0,
                "potentially_affected_infrastructure": 0,
                "infrastructure_analysis": "NOT_AVAILABLE",
                "note": "No candidate fire regions — infrastructure exposure not estimated.",
                "proximity_analysis": [],
            }
        mult = {"LOW": 0, "MODERATE": 3, "HIGH": 7, "CRITICAL": 12}.get(level, 0)
        return {
            "potentially_affected_buildings":      n * mult,
            "potentially_affected_roads":          max(0, (n-1)) * mult,
            "potentially_affected_infrastructure": n * max(0, mult - 1),
            "infrastructure_analysis": "ESTIMATED",
            "note": (
                "Infrastructure counts are proximity estimates — "
                "no ground-truth building/road layer available. "
                "Use 'potentially exposed', NOT 'destroyed'."
            ),
            "proximity_analysis": [
                {
                    "feature_type":      "wildfire_candidate",
                    "region_id":         r.get("id", i+1),
                    "area_percentage":   r.get("area_percentage", 0.0),
                    "risk":              level,
                    "confidence":        r.get("confidence", 0.0),
                }
                for i, r in enumerate(candidates)
            ],
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Recommendations
    # ─────────────────────────────────────────────────────────────────────────

    def _recommendations(
        self, level: str, has_temporal: bool,
        active_fire: bool, smoke: bool
    ) -> List[str]:
        recs = []
        if has_temporal:
            recs.append("Continue multi-temporal satellite monitoring to track fire spread.")
        else:
            recs.append("Acquire before/after image pair to enable fire-spread trend analysis.")

        if active_fire:
            recs.append("⚠️ Active fire indicator (RGB proxy) — thermal confirmation via NASA FIRMS required.")
        if smoke:
            recs.append("Smoke signature detected — confirm with MODIS/VIIRS smoke products.")

        if level == "LOW":
            recs.extend([
                "No immediate wildfire action required based on current optical evidence.",
                "Continue routine fire-weather and satellite monitoring.",
            ])
        elif level == "MODERATE":
            recs.extend([
                "Increase satellite acquisition frequency.",
                "Notify local fire services for situational awareness.",
                "Request NASA FIRMS thermal hotspot confirmation.",
            ])
        elif level == "HIGH":
            recs.extend([
                "⚠️ Multiple fire indicators — thermal satellite confirmation required before response.",
                "Notify fire management authorities for heightened alert.",
                "Assess potentially exposed infrastructure and evacuation routes.",
                "Request Sentinel-2 SWIR acquisition for fire mapping.",
            ])
        elif level == "CRITICAL":
            recs.extend([
                "🚨 Strong multi-source fire evidence — DO NOT act on AI alone.",
                "Immediate NASA FIRMS / VIIRS thermal validation required.",
                "Coordinate with local emergency management and fire services.",
                "Consider precautionary evacuation of proximal communities.",
                "Deploy Sentinel-1 SAR acquisition for fire-scar mapping.",
            ])

        recs.append(
            "AI-assisted detection — supplements, does NOT replace, thermal data and expert assessment."
        )
        return recs

    # ─────────────────────────────────────────────────────────────────────────
    #  NASA FIRMS integration hook (future)
    # ─────────────────────────────────────────────────────────────────────────

    def firms_hotspot_hook(
        self, aoi_wkt: str, start_date: str, end_date: str, req_id: str
    ) -> Dict[str, Any]:
        """
        Architecturally prepared NASA FIRMS / VIIRS hotspot integration hook.
        When integrated, thermal hotspot confidence supersedes RGB proxy.
        Source: https://firms.modaps.eosdis.nasa.gov/api/
        """
        logger.info("[%s] NASA FIRMS hook called — not yet integrated.", req_id)
        return {
            "firms_available": False,
            "message": "NASA FIRMS hotspot integration not yet deployed.",
            "prepared_sources": ["MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"],
            "api_endpoint": "https://firms.modaps.eosdis.nasa.gov/api/area/",
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  No-image fallback
    # ─────────────────────────────────────────────────────────────────────────

    def _no_image_response(self, req_id: str, query: str, t_start: float) -> Dict:
        return {
            "request_id":    req_id,
            "status":        "SUCCESS",
            "query":         query,
            "analysis_type": "wildfire_analysis",
            "disaster_type": "WILDFIRE",
            "assessment_status": "INSUFFICIENT_EVIDENCE",
            "detection_status":  "INCONCLUSIVE",

            "risk_assessment": {
                "risk_score": 0, "risk_level": "LOW",
                "confidence": 0.0, "alert_state": "INFO",
                "risk_factors": [], "ai_disclaimer": None,
            },
            "wildfire_assessment": {
                "fire_detected": False, "active_fire_detected": False,
                "active_fire_note": None, "smoke_detected": False,
                "burned_area_detected": False, "confidence": 0.0,
                "affected_area_percentage": 0.0, "burned_percentage": 0.0,
                "smoke_percentage": 0.0, "fire_indicator_percentage": 0.0,
                "vegetation_percentage": 0.0, "affected_pixels": 0,
                "model_label": "WILDFIRE_SPECIALIST_LIMITED",
                "data_source": "OPTICAL_SPECTRAL_HEURISTIC",
            },
            "change_analysis": {
                "change_detected": False, "change_type": None,
                "estimated_change_percentage": 0.0, "vegetation_loss_percentage": 0.0,
                "new_burned_area_percentage": 0.0, "new_smoke_percentage": 0.0, "confidence": 0.0,
            },
            "fire_spread": {"trend": "NOT_AVAILABLE", "change_percentage": 0.0, "confidence": 0.0},
            "ai_visual_assessment": {
                "available": False, "model": None, "reasoning": None, "confidence": 0.0,
                "type": "VLM_VISUAL_REASONING",
                "note": "No image provided — AI visual reasoning not available.",
            },
            "affected_regions": [],
            "potential_impact": {
                "potentially_affected_buildings": 0, "potentially_affected_roads": 0,
                "potentially_affected_infrastructure": 0,
                "infrastructure_analysis": "NOT_AVAILABLE",
                "note": "No image supplied.", "proximity_analysis": [],
            },
            "thermal_evidence": {
                "thermal_available": False, "hotspot_data": None,
                "note": "Thermal fire evidence unavailable. NASA FIRMS hook prepared.",
                "firms_status": "NOT_INTEGRATED",
            },
            "satellite_info": {
                "platform": "N/A", "data_source": "NONE",
                "thermal_product": "UNAVAILABLE", "sar_fire_scar": "ARCHITECTURALLY_PREPARED",
                "note": "No satellite image provided.",
            },
            "recommendations": [
                "INCONCLUSIVE — satellite imagery required for wildfire analysis.",
                "Please provide a satellite image to enable fire detection.",
            ],
            "annotated_image": {"generated": False, "path_or_url": None},
            "limitations": [
                "No satellite imagery supplied — analysis not possible.",
            ] + list(_STANDARD_LIMITATIONS),
            "processing_time_seconds": round(time.time() - t_start, 3),
            "analysis_mode": "no_image",
        }
