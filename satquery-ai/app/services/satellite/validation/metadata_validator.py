import uuid
from typing import Dict, Any, List

class MetadataValidator:
    """Verifies physical compatibility of radar satellite passes."""
    
    def validate(self, before: Dict[str, Any], after: Dict[str, Any], bbox: List[float]) -> List[str]:
        errors = []
        
        b_sat = before.get("satellite", "")
        a_sat = after.get("satellite", "")
        if "Sentinel-1" not in b_sat or "Sentinel-1" not in a_sat:
            errors.append(f"Invalid platform: Requires Sentinel-1 SAR. Got {b_sat} and {a_sat}.")
            
        b_orbit = before.get("orbit_direction")
        a_orbit = after.get("orbit_direction")
        if b_orbit and a_orbit and b_orbit != a_orbit:
            errors.append(f"Incompatible viewing geometry (Orbit). Baseline is {b_orbit}, Target is {a_orbit}.")
            
        b_pol = before.get("polarization")
        a_pol = after.get("polarization")
        if b_pol and a_pol and b_pol != a_pol:
            errors.append(f"Incompatible polarization filters. Baseline {b_pol} vs Target {a_pol}.")
            
        return errors
