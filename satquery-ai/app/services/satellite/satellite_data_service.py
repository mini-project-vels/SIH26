import os
import uuid
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime

from app.services.satellite.stac_client import STACClient

class SatelliteDataService:
    """
    Service for integrating Copernicus Sentinel-1 SAR imagery.
    Coordinates authentication, BBOX gen, search, and retrieval.
    """
    
    def __init__(self):
        # We check for credentials if needed, but Element84 STAC is open.
        self.client_id = os.getenv("COPERNICUS_CLIENT_ID")
        self.stac_client = STACClient()
    
    def generate_bounding_box(self, latitude: float, longitude: float, radius_km: float) -> List[float]:
        """
        Input: latitude, longitude, radius_km
        Convert this into an approximate geographic bounding box.
        """
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Invalid coordinates. Latitude must be -90 to 90, Longitude -180 to 180.")
            
        if radius_km <= 0 or radius_km > 500:
            raise ValueError("Radius must be a reasonable positive value (e.g., 5-100 km).")
            
        # 1 degree of latitude is roughly 111.32 km
        lat_delta = radius_km / 111.32
        # 1 degree of longitude is roughly 111.32 * cos(lat) km
        lon_delta = radius_km / (111.32 * math.cos(math.radians(latitude)))
        
        min_lon = longitude - lon_delta
        min_lat = latitude - lat_delta
        max_lon = longitude + lon_delta
        max_lat = latitude + lat_delta
        
        # [minLon, minLat, maxLon, maxLat]
        return [round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)]
        
    def search_acquisitions(self, bbox: List[float], before_date: str, after_date: str) -> List[Dict[str, Any]]:
        """
        Searches for Sentinel-1 GRD imagery using Copernicus APIs.
        Mocks the result for development without real credentials.
        """
        try:
            b_dt = datetime.strptime(before_date, "%Y-%m-%d")
            a_dt = datetime.strptime(after_date, "%Y-%m-%d")
        except:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
            
        if a_dt < b_dt:
            raise ValueError("after_date cannot be earlier than before_date.")
            
        # Search REAL Sentinel-1 acquisitions using STAC!
        # Find closest match to BEFORE date
        before_results = self.stac_client.query_acquisitions(bbox, before_date, days_range=15)
        after_results = self.stac_client.query_acquisitions(bbox, after_date, days_range=15)
        
        if not before_results or not after_results:
            return [] # No combinations available natively
            
        return [before_results[0], after_results[0]]
        
    def fetch_imagery(self, acquisition_id: str) -> str:
        """
        No-op for metadata phase.
        """
        return ""
