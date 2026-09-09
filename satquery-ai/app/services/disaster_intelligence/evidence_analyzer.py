from typing import Dict, Any, List, Optional
from app.models.disaster_models import NormalizedEvidence
from app.utils.spatial_analysis import calculate_bbox_overlap

class EvidenceAnalyzer:
    """
    Parses and normalizes outputs from various remote sensing specialist agents 
    into standard Evidentiary objects for the Disaster Engine.
    """
    
    def parse_change_detection(self, cd_res: Optional[Dict[str, Any]]) -> NormalizedEvidence:
        """
        Parses outputs from ChangeDetectionAgent.
        """
        if not cd_res or cd_res.get("status") != "SUCCESS":
            return NormalizedEvidence(
                source="change_detection",
                evidence_type="surface_change",
                available=False,
                confidence=0.0
            )
            
        metrics = {}
        # Try to pull change metrics
        if "summary" in cd_res:
            metrics["changed_area_pixels"] = cd_res["summary"].get("changed_pixels", 0)
            metrics["changed_area_percentage"] = cd_res["summary"].get("change_ratio", 0.0) * 100.0
        else:
            metrics["changed_area_pixels"] = cd_res.get("changed_pixels", 0)
            metrics["changed_area_percentage"] = cd_res.get("change_ratio", 0.0) * 100.0
            
        # Draw a generic bounding box & location if present
        detections = cd_res.get("detections", [])
        affected_region = None
        if detections:
            first = detections[0]
            affected_region = {
                "location": first.get("location", "center"),
                "bbox": first.get("bbox")
            }
            
        return NormalizedEvidence(
            source="change_detection",
            evidence_type="surface_change",
            available=True,
            confidence=cd_res.get("confidence", 0.85),
            affected_region=affected_region,
            metrics=metrics
        )

    def parse_building_segmentation(self, bg_res: Optional[Dict[str, Any]]) -> NormalizedEvidence:
        """
        Parses building footprint detections.
        """
        # Make sure this has building detections
        if not bg_res or bg_res.get("status") != "SUCCESS":
            return NormalizedEvidence(
                source="building_segmentation",
                evidence_type="building_detection",
                available=False,
                confidence=0.0
            )
            
        target = bg_res.get("target", "")
        if "building" not in target.lower():
            return NormalizedEvidence(
                source="building_segmentation",
                evidence_type="building_detection",
                available=False,
                confidence=0.0
            )
            
        detections = bg_res.get("detections", [])
        metrics = {
            "building_count": len(detections),
            "total_building_area_pixels": sum(d.get("area_pixels", 0) for d in detections if d.get("area_pixels"))
        }
        
        # Pull affected region from main building detection
        affected_region = None
        if detections:
            first = len(detections) // 2 # center building proxy
            affected_region = {
                "location": detections[first].get("location", "center"),
                "bbox": detections[first].get("bbox")
            }
            
        return NormalizedEvidence(
            source="building_segmentation",
            evidence_type="building_detection",
            available=True,
            confidence=0.95,
            affected_region=affected_region,
            metrics=metrics
        )

    def parse_water_detection(self, water_res: Optional[Dict[str, Any]]) -> NormalizedEvidence:
        """
        Parses water boundary detections from the visual grounding pipeline.
        """
        if not water_res or water_res.get("status") != "SUCCESS":
            return NormalizedEvidence(
                source="water_detection",
                evidence_type="water_boundary",
                available=False,
                confidence=0.0
            )
            
        target = water_res.get("target", "")
        if "water" not in target.lower():
            return NormalizedEvidence(
                source="water_detection",
                evidence_type="water_boundary",
                available=False,
                confidence=0.0
            )
            
        detections = water_res.get("detections", [])
        metrics = {
            "water_bodies_detected": len(detections),
            "total_water_area_pixels": sum(d.get("area_pixels", 0) for d in detections if d.get("area_pixels"))
        }
        
        affected_region = None
        if detections:
            first = detections[0]
            affected_region = {
                "location": first.get("location", "center"),
                "bbox": first.get("bbox")
            }
            
        return NormalizedEvidence(
            source="water_detection",
            evidence_type="water_boundary",
            available=True,
            confidence=0.92,
            affected_region=affected_region,
            metrics=metrics
        )

    def parse_vision_language_analysis(self, vla_res: Optional[Dict[str, Any]]) -> NormalizedEvidence:
        """
        Parses high level VLM QA response texts for mentions of flooding, water expansion, or fire.
        """
        if not vla_res or not vla_res.get("answer"):
            return NormalizedEvidence(
                source="vision_language_analysis",
                evidence_type="vlm_indicators",
                available=False,
                confidence=0.0
            )
            
        ans = vla_res.get("answer", "").lower()
        import re

        def is_present_without_negation(keywords: list, text: str) -> bool:
            # Split text by common clause / sentence delimiters
            clauses = re.split(r'[.;:]', text.lower())
            negation_terms = r'\b(no|not|neither|none|without|never|zero|clear of|low risk|free of|unlikely|absence of|disprove|lack of)\b'
            
            for clause in clauses:
                for kw in keywords:
                    for match in re.finditer(r'\b' + re.escape(kw) + r'\b', clause):
                        # Scan all text preceding the matched word inside the same clause
                        preceding = clause[:match.start()]
                        if re.search(negation_terms, preceding):
                            continue
                        return True
            return False
        
        # Smart rule checks for keywords
        water_indicated = is_present_without_negation(
            ["water", "island", "flood", "flooded", "flooding", "inundated", "river overflow", "submerged"], 
            ans
        )
        fire_indicated = is_present_without_negation(
            ["fire", "burn", "smoke", "wildfire", "charred", "blaze"], 
            ans
        )
        landslide_indicated = is_present_without_negation(
            ["landslide", "debris", "mudslide", "rockfall", "slope failure"], 
            ans
        )
        
        metrics = {
            "vlm_text_report": vla_res.get("answer"),
            "water_indicated": water_indicated,
            "fire_indicated": fire_indicated,
            "landslide_indicated": landslide_indicated
        }
        
        return NormalizedEvidence(
            source="vision_language_analysis",
            evidence_type="vlm_indicators",
            available=True,
            confidence=0.88,
            metrics=metrics
        )
