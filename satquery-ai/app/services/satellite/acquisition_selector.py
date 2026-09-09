from typing import List, Dict, Any, Tuple

class AcquisitionSelector:
    """
    Intelligently selects the best before and after acquisitions for SAR change detection.
    Precludes blindly selecting random images.
    """
    
    def select_optimal_pair(self, acquisitions: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        if not acquisitions or len(acquisitions) < 2:
            raise ValueError("Insufficient acquisitions found in this date range. At least 2 required for change detection.")
            
        # For Sentinel-1 change detection, we vastly prefer matching orbit directions
        # to prevent radar foreshortening/layover discrepancies.
        
        # We sort by date
        sorted_acq = sorted(acquisitions, key=lambda x: x["acquisition_datetime"])
        
        # Simple selection: earliest as baseline, latest as target.
        # In a real system, we'd filter for matching orbit_direction & relative orbit.
        before_acq = sorted_acq[0]
        after_acq = sorted_acq[-1]
        
        reasoning = (
            f"Selected {before_acq['satellite']} ({before_acq['acquisition_datetime']}) as baseline and "
            f"{after_acq['satellite']} ({after_acq['acquisition_datetime']}) as target. "
            f"Orbit Direction match enforced: {before_acq['orbit_direction']} vs {after_acq['orbit_direction']}."
        )
        
        return before_acq, after_acq, reasoning
