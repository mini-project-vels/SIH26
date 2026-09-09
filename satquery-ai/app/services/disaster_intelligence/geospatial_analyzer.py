from typing import Dict, Any, List

class GeospatialImpactAnalyzer:
    """
    Analyzes potential impact regions based on available information.
    Supports Mode A (Image-Relative) and Mode B (Georeferenced).
    """
    
    def analyze(
        self,
        disaster_type: str,
        detected_regions: List[Dict[str, Any]],
        latitude: float = None,
        longitude: float = None
    ) -> Dict[str, Any]:
        has_geo = latitude is not None and longitude is not None
        
        mode = "GEOREFERENCED" if has_geo else "IMAGE_RELATIVE"
        affected_zones = []
        
        if mode == "IMAGE_RELATIVE":
            # For simplicity without real CV orientation, fallback to regions or defaults
            for region in detected_regions:
                # Mock location based on region box if passed, otherwise default
                loc = region.get("location", "center")
                bbox = region.get("bbox", [])
                
                # Simple logic for image-relative quadrants if bbox is provided [x1, y1, x2, y2]
                if bbox and len(bbox) == 4:
                    if bbox[1] > 200: 
                        loc = "southern region"
                    elif bbox[1] < 100:
                        loc = "northern region"
                
                affected_zones.append(f"Potential impact is concentrated toward the {loc} of the analyzed satellite image.")
        else:
            affected_zones.append(f"Georeferenced impact detected near coordinates Lat: {latitude}, Lon: {longitude}")
            
        return {
            "mode": mode,
            "affected_zones": list(set(affected_zones))
        }
