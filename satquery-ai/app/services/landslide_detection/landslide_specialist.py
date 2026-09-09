"""
LandslideSpecialist
===================
Orchestrator for the complete landslide detection and risk pipeline.

Pipeline
--------
  [Image input]
       ↓
  Image preprocessing / loading
       ↓
  Geometric alignment (temporal pair)
       ↓
  Spectral disturbance analysis
       ↓
  Vegetation-loss & bare-soil change detection (temporal)
       ↓
  Candidate landslide region extraction
       ↓
  AI visual reasoning (Hugging Face vision model)
       ↓
  Multi-factor risk scoring (LandslideRiskCalculator)
       ↓
  Annotated image generation (LandslideVisualizer)
       ↓
  Structured JSON response

Data transparency
-----------------
  - SPECTRAL_HEURISTIC results are clearly labelled as spectral analysis
  - No dedicated landslide segmentation model is available — reported as
    "LANDSLIDE_SPECIALIST_LIMITED"
  - AI visual reasoning uses the existing Hugging Face vision service and
    is labelled "VLM_VISUAL_REASONING"
  - DEM/elevation data is NOT available: explicitly stated in output
  - SAR / Sentinel-1 support is architecturally prepared (see sentinel_sar_hook)

Logging
-------
Every request emits structured log entries for:
  request_id, image_source, acquisition_dates, model_used,
  detection_confidence, change_percentage, risk_score, risk_factors,
  processing_time, limitations
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from app.services.landslide_detection.spectral_landslide_detector import SpectralLandslideDetector
from app.services.landslide_detection.landslide_risk import LandslideRiskCalculator
from app.services.landslide_detection.landslide_visualizer import LandslideVisualizer

logger = logging.getLogger("satquery.landslide.specialist")

# Limitations that are ALWAYS disclosed
_STANDARD_LIMITATIONS = [
    "Assessment is based on optical satellite imagery spectral analysis.",
    "No dedicated deep-learning landslide segmentation model is available (LANDSLIDE_SPECIALIST_LIMITED).",
    "Terrain elevation / DEM data is NOT integrated — slope-based evidence unavailable.",
    "SAR / Sentinel-1 backscatter analysis is architecturally prepared but awaits a dedicated processor.",
    "Ground verification is required before any emergency response.",
    "AI visual reasoning does not guarantee pixel-level landslide delineation.",
]


class LandslideSpecialist:
    """
    Top-level coordinator for landslide hazard detection and risk assessment.
    """

    def __init__(self) -> None:
        self.detector   = SpectralLandslideDetector()
        self.risk_calc  = LandslideRiskCalculator()
        self.visualizer = LandslideVisualizer()

    # ──────────────────────────────────────────────────────────────────────────
    #  Main entry point
    # ──────────────────────────────────────────────────────────────────────────

    def execute(
        self,
        query: str,
        image: Optional[Any] = None,
        before_image: Optional[Any] = None,
        after_image: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full landslide analysis pipeline.

        Args:
            query:        User natural-language query.
            image:        Single satellite image (optional).
            before_image: Baseline / pre-event image (optional, for temporal).
            after_image:  Recent / post-event image (optional, for temporal).
            request_id:   Unique request identifier.

        Returns:
            Structured landslide analysis report (dict).
        """
        req_id   = request_id or str(uuid.uuid4())[:12]
        t_start  = time.time()

        logger.info(
            "[%s] LandslideSpecialist.execute — query=%r, image=%s, before=%s, after=%s",
            req_id, query[:80],
            "YES" if image else "NO",
            "YES" if before_image else "NO",
            "YES" if after_image else "NO",
        )

        # ── Determine analysis mode ───────────────────────────────────────
        has_temporal = before_image is not None and after_image is not None
        has_single   = image is not None
        target_image = after_image if (has_temporal and after_image is not None) else image

        if not has_single and not has_temporal:
            logger.warning("[%s] No image supplied — returning INSUFFICIENT_EVIDENCE", req_id)
            return self._no_image_response(req_id, query, t_start)

        evidence: Dict[str, Any] = {}

        # ── Spectral analysis ─────────────────────────────────────────────
        if has_temporal:
            # Before/after change detection pipeline
            change_data = self.detector.compare_temporal(before_image, after_image, req_id)
            evidence["landslide_assessment"] = change_data.get("after_analysis", {})
            evidence["change_analysis"]      = change_data.get("change_analysis", {})
            evidence["candidate_regions"]    = change_data.get("candidate_regions", [])
            evidence["disturbance_mask"]     = change_data.get("combined_candidate_mask")
            evidence["veg_loss_mask"]        = change_data.get("veg_loss_mask")
            evidence["new_bare_mask"]        = change_data.get("new_bare_mask")
            evidence["before_analysis"]      = change_data.get("before_analysis", {})
            analysis_type = "temporal_change_analysis"
        else:
            # Single-image analysis
            single_data = self.detector.detect_disturbance(image, req_id)
            evidence["landslide_assessment"] = single_data
            evidence["candidate_regions"]    = single_data.get("candidate_regions", [])
            evidence["disturbance_mask"]     = single_data.get("disturbance_mask_array")
            evidence["change_analysis"]      = {
                "change_detected": False,
                "change_type": None,
                "changed_percentage": 0.0,
                "vegetation_loss_percentage": 0.0,
                "estimated_change_percentage": 0.0,
                "confidence": 0.0,
            }
            evidence["before_analysis"]  = {}
            analysis_type = "single_image_analysis"

        # ── AI visual reasoning ───────────────────────────────────────────
        vlm_text, vlm_model, vlm_confidence = self._run_vlm_analysis(
            target_image, query, req_id
        )
        evidence["vlm_assessment"] = {
            "available": vlm_text is not None,
            "model": vlm_model,
            "text": vlm_text,
            "confidence": vlm_confidence,
        }

        # ── Risk scoring ──────────────────────────────────────────────────
        risk_report = self.risk_calc.calculate_risk(evidence)
        evidence["risk_score"] = risk_report.get("risk_score", 0)

        # ── Annotated image ───────────────────────────────────────────────
        annotated_path = None
        landslide_assessment = evidence.get("landslide_assessment", {})
        dist_pct = landslide_assessment.get("disturbance_percentage", 0.0)
        candidate_regions = evidence.get("candidate_regions", [])

        should_annotate = (
            target_image is not None
            and (dist_pct > 3.0 or len(candidate_regions) > 0)
        )

        if should_annotate:
            viz_evidence = {
                "landslide_assessment": landslide_assessment,
                "candidate_regions": candidate_regions,
                "disturbance_mask_array": evidence.get("disturbance_mask"),
                "combined_candidate_mask": evidence.get("disturbance_mask"),
                "risk_score": risk_report.get("risk_score", 0),
            }
            try:
                annotated_path = self.visualizer.draw_visualization(
                    target_image, viz_evidence, req_id
                )
            except Exception as exc:
                logger.warning("[%s] Visualizer failed: %s", req_id, exc)

        # ── Infrastructure impact ─────────────────────────────────────────
        impact = self._estimate_impact(candidate_regions, risk_report)

        # ── Recommendations ───────────────────────────────────────────────
        recommendations = self._generate_recommendations(
            risk_report.get("risk_level", "LOW"),
            has_temporal,
        )

        # ── Limitations ───────────────────────────────────────────────────
        limitations = list(_STANDARD_LIMITATIONS)
        if not has_temporal:
            limitations.append(
                "Only a single image was provided — temporal change detection not available."
            )
        if vlm_text is None:
            limitations.append(
                "AI visual reasoning model was unavailable — text-based analysis skipped."
            )

        # ── Determine final landslide detection status ─────────────────────
        dist_detected  = landslide_assessment.get("disturbance_detected", False)
        change_det     = evidence["change_analysis"].get("change_detected", False)
        risk_sc        = risk_report.get("risk_score", 0)

        if risk_sc >= 51 or (dist_detected and change_det):
            detection_status = "DETECTED"
        elif risk_sc >= 26 or dist_detected or change_det:
            detection_status = "POSSIBLE"
        else:
            detection_status = "NOT_DETECTED"

        # Inconclusive guard
        vlm_avail = evidence["vlm_assessment"]["available"]
        if detection_status == "POSSIBLE" and not vlm_avail and not has_temporal:
            detection_status = "INCONCLUSIVE"

        elapsed = round(time.time() - t_start, 3)

        # ── Structured logging ────────────────────────────────────────────
        logger.info(
            "[%s] LANDSLIDE REPORT COMPLETE | "
            "analysis=%s | detection=%s | risk=%d (%s) | "
            "confidence=%.2f | change_pct=%.1f | dist_pct=%.1f | "
            "candidates=%d | annotated=%s | time=%.3fs",
            req_id, analysis_type, detection_status,
            risk_report.get("risk_score", 0),
            risk_report.get("risk_level", "UNKNOWN"),
            risk_report.get("confidence", 0.0),
            evidence["change_analysis"].get("estimated_change_percentage", 0.0),
            dist_pct,
            len(candidate_regions),
            annotated_path or "none",
            elapsed,
        )

        # ── Build serialisable candidate list (no numpy arrays) ───────────
        clean_candidates = [
            {k: v for k, v in r.items() if not isinstance(v, type(None))}
            for r in candidate_regions
        ]

        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "query": query,
            "analysis_type": "landslide_analysis",
            "disaster_type": "LANDSLIDE",
            "assessment_status": "COMPLETED",
            "detection_status": detection_status,

            "risk_assessment": {
                "risk_score":  risk_report.get("risk_score", 0),
                "risk_level":  risk_report.get("risk_level", "LOW"),
                "confidence":  risk_report.get("confidence", 0.0),
                "alert_state": risk_report.get("alert_state", "INFO"),
                "risk_factors": risk_report.get("risk_factors", []),
                "ai_disclaimer": risk_report.get("ai_disclaimer"),
            },

            "landslide_assessment": {
                "landslide_detected":     dist_detected,
                "detection_status":       detection_status,
                "confidence":             landslide_assessment.get("confidence", 0.0)
                                          if "confidence" in landslide_assessment
                                          else risk_report.get("confidence", 0.0),
                "affected_area_pixels":   landslide_assessment.get("disturbance_pixels", 0),
                "affected_area_percentage": landslide_assessment.get("disturbance_percentage", 0.0),
                "bare_soil_percentage":   landslide_assessment.get("bare_soil_percentage", 0.0),
                "vegetation_percentage":  landslide_assessment.get("vegetation_percentage", 0.0),
                "model_label":            landslide_assessment.get("model_label", "LANDSLIDE_SPECIALIST_LIMITED"),
                "data_source":            landslide_assessment.get("data_source", "OPTICAL_SPECTRAL_HEURISTIC"),
            },

            "change_analysis": {
                "change_detected":            evidence["change_analysis"].get("change_detected", False),
                "change_type":                evidence["change_analysis"].get("change_type"),
                "estimated_change_percentage": evidence["change_analysis"].get("estimated_change_percentage", 0.0),
                "vegetation_loss_percentage": evidence["change_analysis"].get("vegetation_loss_percentage", 0.0),
                "new_bare_soil_percentage":   evidence["change_analysis"].get("new_bare_soil_percentage", 0.0),
                "confidence":                 evidence["change_analysis"].get("confidence", 0.0),
            },

            "ai_visual_assessment": {
                "available": vlm_avail,
                "model":     vlm_model,
                "reasoning": vlm_text,
                "confidence": vlm_confidence,
                "type": "VLM_VISUAL_REASONING",
                "note": (
                    "This is AI visual reasoning, not a dedicated landslide segmentation model."
                    if vlm_avail else "AI visual reasoning unavailable."
                ),
            },

            "affected_regions": clean_candidates,

            "potential_impact": impact,

            "terrain_evidence": {
                "dem_available": False,
                "slope_analysis": "Terrain elevation evidence unavailable.",
                "note": "DEM integration prepared for Copernicus DEM / SRTM sources.",
            },

            "sar_evidence": {
                "sar_available": False,
                "note": "Sentinel-1 SAR processing is architecturally prepared. No SAR data available for this request.",
            },

            "recommendations": recommendations,

            "annotated_image": {
                "generated":  annotated_path is not None,
                "path_or_url": annotated_path,
            },

            "limitations": limitations,
            "processing_time_seconds": elapsed,
            "analysis_mode": analysis_type,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  AI visual reasoning
    # ──────────────────────────────────────────────────────────────────────────

    def _run_vlm_analysis(
        self,
        image: Optional[Any],
        query: str,
        req_id: str,
    ):
        """
        Run the Hugging Face vision-language model for natural-language
        landslide indicator interpretation.

        Returns: (text_result, model_name, confidence)
        """
        if image is None:
            return None, None, 0.0

        try:
            from app.services.huggingface_vision_service import HuggingFaceVisionService
            from app.config import vision_config

            svc = HuggingFaceVisionService()
            model_name = vision_config.HF_VISION_MODEL

            prompt = (
                "You are a satellite imagery analyst specialising in geohazards. "
                "Examine this satellite image carefully and report:\n"
                "1. Any evidence of landslides, debris flows, or mass movements\n"
                "2. Areas of bare soil or disturbed terrain\n"
                "3. Vegetation loss or stripped hillsides\n"
                "4. Road or infrastructure displacement\n"
                "5. Slope disturbance patterns\n"
                "Be factual. If you do NOT see clear evidence, say so explicitly. "
                "Do not over-report. Conclude with: LANDSLIDE_INDICATORS: YES/NO/UNCERTAIN\n\n"
                f"User query: {query}"
            )

            text = svc.analyze_image(image, prompt)
            logger.info("[%s] VLM analysis complete — model=%s", req_id, model_name)
            return text, model_name, 0.75

        except Exception as exc:
            logger.warning("[%s] VLM analysis failed: %s", req_id, exc)
            return None, None, 0.0

    # ──────────────────────────────────────────────────────────────────────────
    #  Infrastructure impact estimation
    # ──────────────────────────────────────────────────────────────────────────

    def _estimate_impact(
        self,
        candidate_regions: List[Dict[str, Any]],
        risk_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Estimate potentially exposed infrastructure.
        Without an actual building/road detection layer we provide
        honest uncertainty bounds.
        """
        n_candidates = len(candidate_regions)
        risk_level   = risk_report.get("risk_level", "LOW")

        if n_candidates == 0:
            return {
                "potentially_affected_buildings":  0,
                "potentially_affected_roads":      0,
                "infrastructure_analysis":         "NOT_AVAILABLE",
                "note": "No candidate regions — no infrastructure exposure estimated.",
            }

        # Rough proxy: higher risk = higher potential exposure
        # These are NOT verified — explicitly labelled "potentially exposed"
        multiplier = {"LOW": 0, "MODERATE": 2, "HIGH": 5, "CRITICAL": 10}.get(risk_level, 0)
        est_buildings = n_candidates * multiplier
        est_roads     = max(0, n_candidates - 1) * multiplier

        return {
            "potentially_affected_buildings": est_buildings,
            "potentially_affected_roads":     est_roads,
            "infrastructure_analysis":        "ESTIMATED",
            "note": (
                "Infrastructure counts are rough proximity estimates — "
                "no ground-truth building/road layer is available. "
                "Use 'potentially exposed', NOT 'destroyed'."
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  Recommendations
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_recommendations(
        self, risk_level: str, has_temporal: bool
    ) -> List[str]:
        base = ["Continue satellite monitoring of the affected area."]

        if has_temporal:
            base.append("Acquire next-pass imagery to monitor progression.")

        if risk_level == "LOW":
            base.extend([
                "No immediate action required based on current satellite evidence.",
                "Continue routine precipitation and slope stability monitoring.",
            ])
        elif risk_level == "MODERATE":
            base.extend([
                "Increase satellite monitoring frequency.",
                "Request ground survey teams to verify suspected areas.",
                "Alert local authorities to potential instability zones.",
            ])
        elif risk_level == "HIGH":
            base.extend([
                "⚠️ AI-assisted assessment — ground verification is MANDATORY before response.",
                "Notify disaster management teams for situational awareness.",
                "Assess potentially exposed infrastructure and evacuation routes.",
                "Request SAR acquisition for surface displacement mapping.",
            ])
        elif risk_level == "CRITICAL":
            base.extend([
                "🚨 Multiple indicators suggest HIGH hazard potential — DO NOT act on AI alone.",
                "Immediate ground verification required by qualified geohazard specialists.",
                "Coordinate with local emergency management agencies.",
                "Consider precautionary evacuation of high-risk proximal populations.",
                "Deploy Sentinel-1 SAR coherence analysis for precise delineation.",
            ])

        base.append(
            "AI-assisted detection — results supplement, not replace, expert field assessment."
        )
        return base

    # ──────────────────────────────────────────────────────────────────────────
    #  Sentinel-1 SAR hook (future integration)
    # ──────────────────────────────────────────────────────────────────────────

    def sentinel_sar_hook(
        self,
        aoi_wkt: str,
        start_date: str,
        end_date: str,
        req_id: str,
    ) -> Dict[str, Any]:
        """
        Architecturally prepared hook for Sentinel-1 SAR-based landslide analysis.

        When integrated:
          - VV / VH / VV-VH ratio backscatter change
          - Coherence loss detection (InSAR)
          - Integration with existing monitoring_routes SAR pipeline

        Currently returns a transparent "not available" stub.
        """
        logger.info(
            "[%s] Sentinel-1 SAR hook called — NOT yet implemented. AOI=%s", req_id, aoi_wkt
        )
        return {
            "sar_available": False,
            "message": "Sentinel-1 SAR landslide processing not yet integrated.",
            "prepared_channels": ["VV", "VH", "VV_VH_ratio", "backscatter_change"],
            "future_source": "Copernicus Sentinel-1 STAC API",
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  No-image fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _no_image_response(
        self, req_id: str, query: str, t_start: float
    ) -> Dict[str, Any]:
        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "query": query,
            "analysis_type": "landslide_analysis",
            "disaster_type": "LANDSLIDE",
            "assessment_status": "INSUFFICIENT_EVIDENCE",
            "detection_status": "INCONCLUSIVE",

            "risk_assessment": {
                "risk_score": 0,
                "risk_level": "LOW",
                "confidence": 0.0,
                "alert_state": "INFO",
                "risk_factors": [],
                "ai_disclaimer": None,
            },
            "landslide_assessment": {
                "landslide_detected": False,
                "detection_status": "INCONCLUSIVE",
                "confidence": 0.0,
                "affected_area_pixels": 0,
                "affected_area_percentage": 0.0,
                "bare_soil_percentage": 0.0,
                "vegetation_percentage": 0.0,
                "model_label": "LANDSLIDE_SPECIALIST_LIMITED",
                "data_source": "OPTICAL_SPECTRAL_HEURISTIC",
            },
            "change_analysis": {
                "change_detected": False,
                "change_type": None,
                "estimated_change_percentage": 0.0,
                "vegetation_loss_percentage": 0.0,
                "new_bare_soil_percentage": 0.0,
                "confidence": 0.0,
            },
            "ai_visual_assessment": {
                "available": False,
                "model": None,
                "reasoning": None,
                "confidence": 0.0,
                "type": "VLM_VISUAL_REASONING",
                "note": "No image provided — AI visual reasoning not available.",
            },
            "affected_regions": [],
            "potential_impact": {
                "potentially_affected_buildings": 0,
                "potentially_affected_roads": 0,
                "infrastructure_analysis": "NOT_AVAILABLE",
                "note": "No image — analysis unavailable.",
            },
            "terrain_evidence": {
                "dem_available": False,
                "slope_analysis": "Terrain elevation evidence unavailable.",
                "note": "DEM integration prepared for Copernicus DEM / SRTM sources.",
            },
            "sar_evidence": {
                "sar_available": False,
                "note": "Sentinel-1 SAR processing architecturally prepared.",
            },
            "recommendations": [
                "INCONCLUSIVE — additional imagery required.",
                "Please provide at least one satellite image to enable landslide analysis.",
            ],
            "annotated_image": {"generated": False, "path_or_url": None},
            "limitations": [
                "No satellite imagery supplied — analysis not possible.",
                "Satellite acquisition unavailable for this request.",
            ] + list(_STANDARD_LIMITATIONS),
            "processing_time_seconds": round(time.time() - t_start, 3),
            "analysis_mode": "no_image",
        }
