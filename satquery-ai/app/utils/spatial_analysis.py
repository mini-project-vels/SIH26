from typing import List, Dict, Any, Tuple
from PIL import Image, ImageChops

def calculate_bbox_overlap(boxA: List[int], boxB: List[int]) -> float:
    """
    Calculates the percentage of boxA that overlaps with/is inside boxB.
    Box format: [ymin, xmin, ymax, xmax]
    Returns a float between 0.0 and 1.0.
    """
    yMinA, xMinA, yMaxA, xMaxA = boxA
    yMinB, xMinB, yMaxB, xMaxB = boxB
    
    # Calculate intersection bounds
    xA = max(xMinA, xMinB)
    yA = max(yMinA, yMinB)
    xB = min(xMaxA, xMaxB)
    yB = min(yMaxA, yMaxB)
    
    inter_area = max(0, xB - xA) * max(0, yB - yA)
    boxA_area = max(1, (xMaxA - xMinA) * (yMaxA - yMinA))
    
    return float(inter_area) / float(boxA_area)

def calculate_mask_overlap(maskA: Image.Image, maskB: Image.Image) -> int:
    """
    Calculates the number of overlapping non-zero pixels between two binary masks.
    """
    if maskA.size != maskB.size:
        # Resize to align
        maskB = maskB.resize(maskA.size, Image.Resampling.NEAREST)
        
    maskA_l = maskA.convert("L")
    maskB_l = maskB.convert("L")
    
    intersection = ImageChops.and_(maskA_l, maskB_l)
    
    # Compute intersection sum
    pixels = list(intersection.getdata())
    return sum(1 for p in pixels if p > 0)

def find_affected_objects(disaster_bbox: List[int], building_detections: List[Dict[str, Any]], overlap_threshold: float = 0.10) -> List[Dict[str, Any]]:
    """
    Identifies which building detections reside within a disaster bounding box.
    Returns the list of affected building dictionaries.
    """
    affected = []
    for b in building_detections:
        bbox = b.get("bbox")
        if not bbox:
            continue
        overlap = calculate_bbox_overlap(bbox, disaster_bbox)
        if overlap >= overlap_threshold:
            # Add overlap ratio to building metadata
            b_copy = dict(b)
            b_copy["overlap_ratio"] = round(overlap, 3)
            affected.append(b_copy)
    return affected
