import os
import uuid
from typing import Dict, Any, List

from app.services.satellite.validation.metadata_validator import MetadataValidator
from app.services.satellite.alignment.image_alignment import ImageAlignmentService
from app.services.satellite.preprocessing.sar_pipeline import SARPipeline

class SentinelPreprocessingSpecialist:
    """
    Main orchestrator for Sentinel-1 real/mock processing.
    """
    
    def __init__(self):
        self.validator = MetadataValidator()
        self.alignment = ImageAlignmentService()
        
        # Switch provider depending on system deployment (MOCK vs SNAP vs LOCAL)
        provider = os.getenv("SATELLITE_PROVIDER", "MOCK")
        self.pipeline = SARPipeline(mode=provider)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())
        
        before_acq = payload.get("before_acquisition", {})
        after_acq = payload.get("after_acquisition", {})
        bbox = payload.get("bounding_box", [])
        
        # Step 1: Validate
        errors = self.validator.validate(before_acq, after_acq, bbox)
        if errors:
            return {
                "status": "FAILED",
                "request_id": req_id,
                "reason": "Metadata incompatibilities detected.",
                "errors": errors
            }
            
        # Step 3 & 4 & 6: Process (SAR Generation)
        before_processed = self.pipeline.process_acquisition(before_acq, phase="before", req_id=req_id)
        after_processed = self.pipeline.process_acquisition(after_acq, phase="after", req_id=req_id)
        
        # Step 5: Align
        alignment_report = self.alignment.align(before_processed, after_processed)
        
        if not alignment_report.get("comparison_ready"):
            return {
                "status": "FAILED",
                "request_id": req_id,
                "reason": "Image alignment failed. Scenes do not overlay accurately."
            }
            
        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "data_source": "REAL" if os.getenv("SATELLITE_PROVIDER") == "REAL" else "MOCK",
            "before_image": {
                "path_or_url": before_processed.pop("path_or_url"),
                "metadata": before_processed
            },
            "after_image": {
                "path_or_url": after_processed.pop("path_or_url"),
                "metadata": after_processed
            },
            "alignment": alignment_report,
            "processing": {
                "backend": self.pipeline.mode,
                "steps_completed": before_processed.get("processing_steps", [])
            },
            "ready_for_change_detection": True
        }
