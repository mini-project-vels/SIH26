"""
WaterAnalyzer — Satellite water body analysis coordinator.

Wraps SpectralWaterDetector to provide a uniform interface for the
FloodEvidenceCollector. Handles all image formats, logs diagnostics,
and never silently returns placeholder results.
"""

import logging
from typing import Any, Dict, Optional

from app.services.flood_detection.spectral_water_detector import SpectralWaterDetector

logger = logging.getLogger("satquery.flood.water_analyzer")


class WaterAnalyzer:
    """
    Analyzes a satellite image to detect water bodies and quantify coverage.

    Uses SpectralWaterDetector for real pixel-level analysis — no VLM,
    no placeholder values.
    """

    def __init__(self, detector: Optional[SpectralWaterDetector] = None) -> None:
        self.detector = detector or SpectralWaterDetector()
        logger.info("WaterAnalyzer initialized with SpectralWaterDetector")

    def analyze_water(
        self,
        image: Any,
        request_id: str = "temp",
        label: str = ""
    ) -> Dict[str, Any]:
        """
        Run water segmentation on a single image.

        Args:
            image: PIL.Image, bytes, UploadFile, file path, or (filename, bytes) tuple
            request_id: Trace ID for logging and file naming
            label: 'before' | 'after' | '' — used in mask filenames

        Returns:
            {
              water_detected:            bool
              water_regions:             list[{id, bbox, area_pixels, area_percentage, confidence}]
              total_water_area_pixels:   int
              total_water_percentage:    float
              water_mask_array:          np.ndarray or None
              image_size:                (width, height)
              mask_path:                 str or None
            }
        """
        logger.info("[%s] WaterAnalyzer.analyze_water() called (label=%s)", request_id, label or "single")

        result = self.detector.analyze(
            image=image,
            request_id=request_id,
            save_mask=True,
            mask_label=label
        )

        if result.get("error"):
            logger.error("[%s] Water analysis error: %s", request_id, result["error"])
        else:
            logger.info(
                "[%s] Water analysis complete: detected=%s, regions=%d, coverage=%.2f%%",
                request_id,
                result.get("water_detected"),
                len(result.get("water_regions", [])),
                result.get("total_water_percentage", 0.0)
            )

        return result

    def compare_temporal(
        self,
        before_image: Any,
        after_image: Any,
        request_id: str = "temp"
    ) -> Dict[str, Any]:
        """
        Full two-image temporal water comparison.

        Analyzes both images with SpectralWaterDetector, then computes
        pixel-level new water expansion using binary mask arithmetic.

        Returns:
            {
              before_analysis:             {...}   (full analyze result)
              after_analysis:              {...}   (full analyze result)
              comparison: {
                previous_water_percentage: float
                current_water_percentage:  float
                water_expansion_percentage:float
                water_area_difference_pixels: int
                new_water_regions:         list[{id, bbox, area_pixels}]
                water_expansion_mask_path: str or None
              }
            }
        """
        logger.info("[%s] Starting temporal water comparison...", request_id)

        before_result = self.analyze_water(before_image, request_id=request_id, label="before")
        after_result  = self.analyze_water(after_image,  request_id=request_id, label="after")

        logger.info(
            "[%s] Before: water=%.2f%% | After: water=%.2f%%",
            request_id,
            before_result.get("total_water_percentage", 0.0),
            after_result.get("total_water_percentage", 0.0)
        )

        comparison = self.detector.compare(
            before_result=before_result,
            after_result=after_result,
            request_id=request_id,
            save_expansion_mask=True
        )

        logger.info(
            "[%s] Expansion: %.1f%%, new_regions=%d",
            request_id,
            comparison.get("water_expansion_percentage", 0.0),
            len(comparison.get("new_water_regions", []))
        )

        return {
            "before_analysis": before_result,
            "after_analysis":  after_result,
            "comparison":      comparison
        }
