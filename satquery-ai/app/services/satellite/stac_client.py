import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import json

class STACClient:
    """
    Client for querying official STAC endpoints for Sentinel-1 imagery metadata.
    Defaults to Element84's Earth Search which hosts real Sentinel-1 GRD metadata free of auth limits.
    """
    
    def __init__(self):
        # We use Earth Search v1 for real metadata
        self.base_url = os.getenv("STAC_API_URL", "https://earth-search.aws.element84.com/v1/search")
        self.collection = "sentinel-1-grd"

    def query_acquisitions(
        self, 
        bbox: List[float], 
        target_date: str, 
        days_range: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Query the STAC catalog for acquisitions covering the bbox around the target_date.
        """
        try:
            t_date = datetime.strptime(target_date, "%Y-%m-%d")
            start_date = t_date - timedelta(days=days_range)
            end_date = t_date + timedelta(days=days_range)
            
            datetime_str = f"{start_date.isoformat()}Z/{end_date.isoformat()}Z"
            
            payload = {
                "collections": [self.collection],
                "bbox": bbox,
                "datetime": datetime_str,
                "limit": 10
            }
            
            response = requests.post(self.base_url, json=payload, timeout=15)
            response.raise_for_status()
            
            features = response.json().get("features", [])
            
            # Format the output precisely
            acquisitions = []
            for feat in features:
                props = feat.get("properties", {})
                acq = {
                    "product_id": feat.get("id"),
                    "satellite": props.get("constellation", "Sentinel-1").capitalize(),
                    "acquisition_datetime": props.get("datetime"),
                    "sensor_mode": props.get("s1:instrument_mode", "IW"),
                    "polarization": "+".join(props.get("s1:polarizations", ["VV"])),
                    "orbit_direction": props.get("sat:orbit_state", "DESCENDING").upper(),
                    "relative_orbit": props.get("sat:relative_orbit", 0),
                    "processing_level": props.get("s1:processing_level", "GRD"),
                    "bbox": feat.get("bbox", bbox),
                    "source_catalog": "Earth Search v1"
                }
                acquisitions.append(acq)
                
            # Sort by absolute time proximity to the target_date
            acquisitions.sort(
                key=lambda x: abs((datetime.strptime(x["acquisition_datetime"].split("T")[0], "%Y-%m-%d") - t_date).days)
            )
            
            return acquisitions
        except Exception as e:
            print(f"STAC API Error: {str(e)}")
            return []

    def get_latest_acquisitions(self, bbox: List[float], limit: int = 2) -> List[Dict[str, Any]]:
        """
        Pull the absolute latest acquisitions covering the given bbox seamlessly.
        """
        try:
            payload = {
                "collections": [self.collection],
                "bbox": bbox,
                "limit": limit,
                "sortby": [{"field": "properties.datetime", "direction": "desc"}]
            }
            
            # Diagnostic STAC logging
            print(f"[STAC DEBUG] Endpoint: {self.base_url}/search")
            print(f"[STAC DEBUG] Search Payload: {json.dumps(payload)}")
            
            response = requests.post(self.base_url, json=payload, timeout=15)
            response.raise_for_status()
            
            features = response.json().get("features", [])
            acquisitions = []
            for feat in features:
                props = feat.get("properties", {})
                acq = {
                    "product_id": feat.get("id"),
                    "satellite": props.get("constellation", "Sentinel-1").capitalize(),
                    "acquisition_datetime": props.get("datetime"),
                    "sensor_mode": props.get("s1:instrument_mode", "IW"),
                    "polarization": "+".join(props.get("s1:polarizations", ["VV"])),
                    "orbit_direction": props.get("sat:orbit_state", "DESCENDING").upper(),
                    "relative_orbit": props.get("sat:relative_orbit", 0),
                    "processing_level": props.get("s1:processing_level", "GRD"),
                    "bbox": feat.get("bbox", bbox),
                    "source_catalog": "Earth Search v1 STAC"
                }
                acquisitions.append(acq)
                
            return acquisitions
        except Exception as e:
            print(f"STAC Latest API Error: {str(e)}")
            return []
