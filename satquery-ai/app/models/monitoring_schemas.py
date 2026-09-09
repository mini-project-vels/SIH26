from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class StartMonitoringRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float
    monitoring_type: str = "general" # flood, glacier, general
    frequency: str = "daily"

class MonitoringAlert(BaseModel):
    event_id: str
    event_type: str
    status: str
    confidence: int
    risk_level: str
    location: Dict[str, float]
    satellite_source: str
    acquisition_time: str
    message: str
