"""
Wildfire / Forest-Fire API Routes
===================================
POST /api/disaster/wildfire/analyze      — main analysis endpoint
POST /api/disaster/wildfire/firms-hook   — NASA FIRMS hotspot hook (prepared)
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.wildfire_detection.wildfire_specialist import WildfireSpecialist

logger = logging.getLogger("satquery.api.wildfire")

router = APIRouter()
_wildfire_specialist = WildfireSpecialist()


@router.post(
    "/analyze",
    summary="Wildfire / Forest-Fire Detection & Risk Assessment",
    description=(
        "Performs satellite-based wildfire analysis including: burned-area spectral detection, "
        "smoke signature recognition, vegetation-loss analysis, fire-spread trend estimation "
        "(when before+after images are supplied), AI visual reasoning, multi-factor risk scoring, "
        "and annotated image overlay generation.\n\n"
        "**Data transparency**: All detections clearly labelled as SPECTRAL_HEURISTIC or "
        "VLM_VISUAL_REASONING. Thermal hotspot data (NASA FIRMS/VIIRS) is NOT integrated — "
        "explicitly reported as unavailable.\n\n"
        "**Modes**:\n"
        "- A) Single image — provide `image`\n"
        "- B) Before/after — provide `before_image` + `after_image`\n"
        "- C) Text only   — returns INSUFFICIENT_EVIDENCE"
    ),
)
def wildfire_analyze(
    query: str = Form(
        ...,
        description="Natural language wildfire analysis query "
                    "(e.g. 'Detect wildfire activity, smoke and burned areas')",
    ),
    image: Optional[UploadFile] = File(
        None, description="Single satellite image (single-temporal analysis)"
    ),
    before_image: Optional[UploadFile] = File(
        None, description="Baseline/pre-fire image (temporal change detection)"
    ),
    after_image: Optional[UploadFile] = File(
        None, description="Recent/post-fire image (temporal change detection)"
    ),
):
    """
    POST /api/disaster/wildfire/analyze

    Detection pipeline:
      1. Spectral burned-area / fire-indicator / smoke analysis (RGB heuristics)
      2. Temporal vegetation-loss & burned-area expansion (before+after pair)
      3. AI visual reasoning (HuggingFace VLM — NOT a fire-segmentation model)
      4. Multi-factor risk scoring (false-positive protection built-in)
      5. Infrastructure proximity estimation
      6. Annotated image overlay

    Clearly distinguished detection types:
      ACTIVE_FIRE   — warm RGB proxy + confirmed by multiple factors
      SMOKE         — grey/haze spectral signature
      BURNED_AREA   — dark/charred surface proxy
      FIRE_RISK     — risk score without confirmed active fire

    Thermal/hotspot data:
      NASA FIRMS / MODIS / VIIRS / Sentinel-3 => NOT integrated
      Explicitly reported as "Thermal fire evidence unavailable."
    """
    try:
        request_id = str(uuid.uuid4())
        logger.info(
            "[%s] POST /api/disaster/wildfire/analyze — "
            "img=%s before=%s after=%s query=%r",
            request_id,
            image.filename if image else "None",
            before_image.filename if before_image else "None",
            after_image.filename if after_image else "None",
            query[:100],
        )

        result = _wildfire_specialist.execute(
            query=query,
            image=image,
            before_image=before_image,
            after_image=after_image,
            request_id=request_id,
        )
        return result

    except Exception as exc:
        logger.error("[%s] Wildfire analysis failure: %s", request_id, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Wildfire Specialist execution failure: {str(exc)}",
        )


@router.post(
    "/firms-hook",
    summary="NASA FIRMS Hotspot Integration (Architecturally Prepared)",
    description=(
        "Triggers NASA FIRMS / VIIRS thermal hotspot query for an Area of Interest. "
        "This endpoint is architecturally prepared — currently returns a transparent "
        "'not integrated' response. When activated: MODIS_NRT and VIIRS_SNPP_NRT/NOAA20_NRT "
        "active-fire products will be queried and integrated into the risk assessment."
    ),
)
def wildfire_firms_hook(
    aoi_wkt:    str = Form(..., description="Area of Interest in WKT format"),
    start_date: str = Form(..., description="Start date YYYY-MM-DD"),
    end_date:   str = Form(..., description="End date YYYY-MM-DD"),
):
    """
    POST /api/disaster/wildfire/firms-hook

    When integrated, this will:
      1. Query NASA FIRMS API with AOI + date range
      2. Parse MODIS / VIIRS active-fire point products
      3. Return thermal hotspot confidence alongside spectral evidence
    Source: https://firms.modaps.eosdis.nasa.gov/api/
    """
    try:
        request_id = str(uuid.uuid4())
        result = _wildfire_specialist.firms_hotspot_hook(
            aoi_wkt=aoi_wkt,
            start_date=start_date,
            end_date=end_date,
            req_id=request_id,
        )
        return result
    except Exception as exc:
        logger.error("[%s] FIRMS hook failure: %s", request_id, exc)
        raise HTTPException(status_code=500, detail=f"FIRMS hook failure: {str(exc)}")
