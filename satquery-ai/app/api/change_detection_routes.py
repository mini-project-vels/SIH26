from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional
import os
import uuid

from app.models.change_detection_schemas import ChangeDetectionResponse
from app.services.change_detection.engine import AutomatedChangeDetectionEngine

router = APIRouter()
_cd_engine = AutomatedChangeDetectionEngine()

@router.post(
    "/analyze",
    response_model=ChangeDetectionResponse,
    summary="Automated Remote Sensing Image Change Detection Engine",
    description="Processes BEFORE and AFTER satellite imagery via multi-method arrays (Abs Diff, SSIM, Thresholds, connected components), generates overlay maps, and exports statistically filtered geographical evidence."
)
def automated_change_detection(
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
    analysis_target: str = Form("general")
):
    try:
        # Save uploads temporarily to process via arrays
        tmp_dir = "outputs/temp"
        os.makedirs(tmp_dir, exist_ok=True)
        
        b_ext = before_image.filename.split(".")[-1]
        a_ext = after_image.filename.split(".")[-1]
        
        b_path = os.path.join(tmp_dir, f"tmp_bef_{uuid.uuid4().hex[:8]}.{b_ext}")
        a_path = os.path.join(tmp_dir, f"tmp_aft_{uuid.uuid4().hex[:8]}.{a_ext}")
        
        with open(b_path, "wb") as fb:
            fb.write(before_image.file.read())
        with open(a_path, "wb") as fa:
            fa.write(after_image.file.read())
            
        # Execute Engine
        res = _cd_engine.analyze(b_path, a_path, analysis_target)
        
        if res.get("status") == "FAILED":
            raise HTTPException(status_code=400, detail=res.get("reason"))
            
        return res
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change Detection Pipeline Failed: {str(e)}")
