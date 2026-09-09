from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.models.monitoring_schemas import StartMonitoringRequest, MonitoringAlert
from app.services.monitoring.engine import AutomatedMonitoringEngine

router = APIRouter()
_monitor = AutomatedMonitoringEngine()

@router.post("/start", summary="Initiate a near-real-time monitoring job")
async def start_monitoring_job(request: StartMonitoringRequest):
    return await _monitor.start_monitoring(request.latitude, request.longitude, request.radius_km, request.monitoring_type, request.frequency)

@router.post("/stop/{job_id}")
def stop_monitoring_job(job_id: str):
    success = _monitor.stop_monitoring(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "STOPPED"}

@router.post("/{job_id}/check", summary="Manual override to trigger checking tick")
def check_monitoring_job(job_id: str):
    try:
        res = _monitor.trigger_check(job_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = _monitor.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/history/{job_id}")
def get_history(job_id: str):
    return {"history": _monitor.get_job_history(job_id)}

@router.get("/events", response_model=List[MonitoringAlert])
def get_all_events():
    return _monitor.get_all_events()

@router.get("/active")
def get_active_jobs():
    db = _monitor._read_db()
    return list(db["jobs"].values())

@router.get("/debug")
def test_stac_connection(latitude: float = 28.0, longitude: float = 86.9, radius_km: float = 10.0):
    import requests
    import os
    from app.services.satellite.satellite_data_service import SatelliteDataService
    
    stac_url = os.getenv("STAC_API_URL", "https://earth-search.aws.element84.com/v1")
    if "/search" in stac_url:
        stac_url = stac_url.replace("/search", "")
        
    sat = SatelliteDataService()
    bbox = sat.generate_bounding_box(latitude, longitude, radius_km)
    
    debug_res = {
        "stac_endpoint": stac_url,
        "available_collections": [],
        "selected_collection": "sentinel-1-grd",
        "bbox": bbox,
        "datetime_range": "ALL_AVAILABLE",
        "http_status": 0,
        "items_found": 0,
        "latest_item": None,
        "error": None
    }
    
    try:
        colls_res = requests.get(f"{stac_url}/collections", timeout=10)
        if colls_res.status_code == 200:
            all_c = colls_res.json().get("collections", [])
            debug_res["available_collections"] = [c["id"] for c in all_c if "sentinel-1" in c.get("id", "").lower()]
    except Exception as e:
        debug_res["error"] = f"Collection lookup failed: {str(e)}"
        
    payload = {
        "collections": ["sentinel-1-grd"],
        "bbox": bbox,
        "limit": 1,
        "sortby": [{"field": "properties.datetime", "direction": "desc"}]
    }
    
    try:
        search_res = requests.post(f"{stac_url}/search", json=payload, timeout=10)
        debug_res["http_status"] = search_res.status_code
        search_res.raise_for_status()
        
        feats = search_res.json().get("features", [])
        debug_res["items_found"] = len(feats)
        if feats:
            f = feats[0]
            debug_res["latest_item"] = {
                "id": f.get("id"),
                "datetime": f["properties"].get("datetime"),
                "orbit_direction": f["properties"].get("sat:orbit_state", "UNKNOWN").upper(),
                "sensor_mode": f["properties"].get("s1:instrument_mode", "UNKNOWN")
            }
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
             debug_res["error"] = f"STAC API Error {e.response.status_code}: {e.response.text[:200]}"
        else:
             debug_res["error"] = f"Network or timeout error: {str(e)}"
             
    return debug_res
