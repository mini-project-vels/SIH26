"""
Landslide API Routes
====================
Dedicated REST endpoints for the Landslide Risk Specialist.

Endpoints:
  POST /api/disaster/landslide/analyze
      - Single image, before/after pair, or text-only query
      - Returns full LandslideSpecialist structured report

  POST /api/disaster/landslide/sentinel-sar  (architecturally prepared)
      - AOI-based Sentinel-1 SAR landslide monitoring trigger
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.landslide_detection.landslide_specialist import LandslideSpecialist

logger = logging.getLogger("satquery.api.landslide")

router = APIRouter()
_landslide_specialist = LandslideSpecialist()


@router.post(
    "/analyze",
    summary="Landslide Detection & Risk Assessment",
    description=(
        "Performs satellite-based landslide detection, terrain disturbance analysis, "
        "and multi-factor risk scoring. "
        "Accepts a single image, or a before/after image pair for temporal change detection. "
        "Returns a structured risk report including detection status, risk score, risk factors, "
        "affected regions, potential infrastructure impact, and an annotated image overlay."
    ),
)
def landslide_analyze(
    query: str = Form(
        ...,
        description="Natural language landslide analysis query "
                    "(e.g. 'Detect landslide activity and assess risk in this area')",
    ),
    image: Optional[UploadFile] = File(
        None,
        description="Single-image satellite acquisition for single-temporal analysis",
    ),
    before_image: Optional[UploadFile] = File(
        None,
        description="Baseline (pre-event) satellite image for temporal change detection",
    ),
    after_image: Optional[UploadFile] = File(
        None,
        description="Recent (post-event) satellite image for temporal change detection",
    ),
):
    """
    POST /api/disaster/landslide/analyze

    Modes:
      A) Single image  — provide `image`
      B) Before/after  — provide `before_image` + `after_image`
      C) Text only     — provide `query` only (returns INSUFFICIENT_EVIDENCE)

    Methodology:
      1. Spectral bare-soil / vegetation disturbance analysis
      2. Temporal pixel-level change detection (if before+after supplied)
      3. AI visual reasoning via Hugging Face vision model
      4. Multi-factor risk scoring (false-positive protected)
      5. Annotated image overlay generation

    Data transparency:
      - All results clearly labelled: SPECTRAL_HEURISTIC / VLM_VISUAL_REASONING
      - No dedicated landslide segmentation model (labelled LANDSLIDE_SPECIALIST_LIMITED)
      - DEM/terrain evidence explicitly reported as unavailable
      - SAR evidence explicitly reported as unavailable for this request
    """
    try:
        request_id = str(uuid.uuid4())
        logger.info(
            "[%s] POST /api/disaster/landslide/analyze — "
            "image=%s before=%s after=%s query=%r",
            request_id,
            image.filename if image else "None",
            before_image.filename if before_image else "None",
            after_image.filename if after_image else "None",
            query[:100],
        )

        result = _landslide_specialist.execute(
            query=query,
            image=image,
            before_image=before_image,
            after_image=after_image,
            request_id=request_id,
        )

        return result

    except Exception as exc:
        logger.error("[%s] Landslide analysis failure: %s", request_id, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Landslide Specialist execution failure: {str(exc)}",
        )


@router.post(
    "/sentinel-sar",
    summary="Sentinel-1 SAR — Landslide Monitoring (Architecturally Prepared)",
    description=(
        "Triggers Sentinel-1 SAR-based landslide monitoring for a given Area of Interest. "
        "This endpoint is architecturally prepared for future integration with the "
        "Sentinel-1 STAC pipeline. Currently returns a transparent 'not available' response."
    ),
)
def landslide_sentinel_sar(
    aoi_wkt: str = Form(..., description="Area of Interest in WKT format"),
    start_date: str = Form(..., description="Start date YYYY-MM-DD"),
    end_date:   str = Form(..., description="End date YYYY-MM-DD"),
):
    """
    POST /api/disaster/landslide/sentinel-sar

    Architecturally prepared Sentinel-1 SAR endpoint.
    When integrated:
      - VV / VH / VV-VH ratio backscatter change detection
      - Coherence loss (InSAR proxy) for surface displacement
      - Integration with existing monitoring_routes SAR pipeline
    """
    try:
        request_id = str(uuid.uuid4())
        logger.info(
            "[%s] Sentinel-1 SAR landslide hook — aoi=%s start=%s end=%s",
            request_id, aoi_wkt[:60], start_date, end_date,
        )
        result = _landslide_specialist.sentinel_sar_hook(
            aoi_wkt=aoi_wkt,
            start_date=start_date,
            end_date=end_date,
            req_id=request_id,
        )
        return result

    except Exception as exc:
        logger.error("[%s] SAR hook failure: %s", request_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Sentinel-1 SAR hook failure: {str(exc)}",
        )
