from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
from collections import deque

from app.config.grounding_config import (
    PIXEL_CLASSIFIERS, OUTPUT_DIR, MIN_REGION_AREA_PIXELS,
    MIN_REGION_AREA_PERCENT, MAX_DETECTIONS_PER_TARGET, IOU_THRESHOLD,
    MAJOR_REGION_THRES_PERCENT, SPECIALIST_REGISTRY
)
from app.services.segmentation_service import SegmentationService
from app.services.image_annotation_service import ImageAnnotationService
from app.services.grounding_interface import VisualGroundingModelInterface
from app.services.model_router import RemoteSensingModelRouter, SPECIALIST_CLASSES

class LocalGroundingService(VisualGroundingModelInterface):
    """
    Default practical implementation of visual grounding.
    Performs real image analysis on pixel intensities and color channels
    to identify spatial segments matching target categories.
    """
    
    def __init__(self, min_region_size: int = 10) -> None:
        self.min_region_size = min_region_size

    def detect(self, image: Image.Image, target: str) -> Tuple[List[Dict[str, Any]], List[List[Tuple[int, int]]]]:
        img_rgb = image.convert("RGB")
        
        # Determine the resolver classifier
        classifier = PIXEL_CLASSIFIERS.get(target)
        if not classifier:
            return [], []

        # 1. Downsample for fast analysis
        analysis_size = (128, 128)
        img_small = img_rgb.resize(analysis_size, Image.Resampling.BILINEAR)
        pixels = list(img_small.getdata())
        
        # 2. Build boolean grid of matching pixels
        grid = [[False for _ in range(128)] for _ in range(128)]
        for y in range(128):
            for x in range(128):
                idx = y * 128 + x
                r, g, b = pixels[idx]
                grid[y][x] = classifier(r, g, b)

        # 3. Connected Component Analysis (BFS)
        visited = [[False for _ in range(128)] for _ in range(128)]
        regions = []

        for y in range(128):
            for x in range(128):
                if grid[y][x] and not visited[y][x]:
                    component = []
                    queue = deque([(x, y)])
                    visited[y][x] = True
                    
                    while queue:
                        curr_x, curr_y = queue.popleft()
                        component.append((curr_x, curr_y))
                        
                        for nx, ny in [(curr_x + 1, curr_y), (curr_x - 1, curr_y), 
                                       (curr_x, curr_y + 1), (curr_x, curr_y - 1)]:
                            if 0 <= nx < 128 and 0 <= ny < 128:
                                if grid[ny][nx] and not visited[ny][nx]:
                                    visited[ny][nx] = True
                                    queue.append((nx, ny))
                                    
                    if len(component) >= self.min_region_size:
                        regions.append(component)

        # Return raw component coords
        return [], regions


def calculate_iou(boxA: List[int], boxB: List[int]) -> float:
    """
    Calculates Intersection over Union (IoU) of two bounding boxes.
    Format: [ymin, xmin, ymax, xmax]
    """
    yMinA, xMinA, yMaxA, xMaxA = boxA
    yMinB, xMinB, yMaxB, xMaxB = boxB
    
    xA = max(xMinA, xMinB)
    yA = max(yMinA, yMinB)
    xB = min(xMaxA, xMaxB)
    yB = min(yMaxA, yMaxB)
    
    interArea = max(0, xB - xA) * max(0, yB - yA)
    
    boxAArea = (xMaxA - xMinA) * (yMaxA - yMinA)
    boxBArea = (xMaxB - xMinB) * (yMaxB - yMinB)
    
    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea == 0:
        return 0.0
        
    return interArea / unionArea


class VisualGroundingService:
    """
    Visual Grounding Service.
    Coordinates target localization, segmentation, and annotation.
    Implements complex NMS style IoU overlap filtering, minimum area thresholds,
    precise region location categorization, and metadata summary construction.
    """

    def __init__(
        self,
        grounding_model: Optional[VisualGroundingModelInterface] = None,
        segmentation: Optional[SegmentationService] = None,
        annotation: Optional[ImageAnnotationService] = None,
        router: Optional[RemoteSensingModelRouter] = None
    ) -> None:
        self.grounding_model = grounding_model or LocalGroundingService()
        self.segmentation = segmentation or SegmentationService()
        self.annotation = annotation or ImageAnnotationService()
        self.router = router or RemoteSensingModelRouter()

    def _determine_relative_location(self, cx: float, cy: float, width: int, height: int) -> str:
        """
        Maps high-res pixel coordinates to one of the 9 relative layout regions.
        Dividing the image into a 3x3 grid.
        Top = North, Bottom = South, Left = West, Right = East.
        """
        # Partition Y axis
        if cy < height / 3.0:
            y_loc = "north"
        elif cy > 2.0 * height / 3.0:
            y_loc = "south"
        else:
            y_loc = "center"

        # Partition X axis
        if cx < width / 3.0:
            x_loc = "west"
        elif cx > 2.0 * width / 3.0:
            x_loc = "east"
        else:
            x_loc = "center"

        # Combine Y and X
        if y_loc == "center" and x_loc == "center":
            return "center"
        elif y_loc == "center":
            return x_loc
        elif x_loc == "center":
            return y_loc
        else:
            return f"{y_loc}{x_loc}"

    def process_grounding(
        self, 
        image: Any, 
        target: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Main Visual Grounding pipeline incorporating Area filtering, IoU overlapping merges,
        spatial metadata sorting, and drawings.
        """
        # 1. Load source image to PIL
        import time
        start_time = time.time()
        try:
            if hasattr(image, "file"):
                image.file.seek(0)
                pil_img = Image.open(image.file)
            elif isinstance(image, str):
                pil_img = Image.open(image)
            else:
                if isinstance(image, tuple) and len(image) == 2:
                    import io
                    pil_img = Image.open(io.BytesIO(image[1]))
                elif isinstance(image, bytes):
                    import io
                    pil_img = Image.open(io.BytesIO(image))
                else:
                    raise TypeError("Unsupported image format")
        except Exception as e:
            return {
                "status": "ERROR",
                "error_message": f"Invalid image format: {str(e)}",
                "detections": [],
                "annotated_image": None
            }

        # Route request utilizing the Remote Sensing Specialist Model Router (Problem 6)
        router_res = self.router.route_request(target, "REGION_GROUNDING", pil_img)
        
        # Determine model class engine to use
        if router_res["fallback_used"] or router_res["selected_specialist"] == "generic_grounding":
            model_to_use = self.grounding_model
        else:
            spec_info = SPECIALIST_REGISTRY.get(target)
            service_class_name = spec_info.get("service_class")
            cls = SPECIALIST_CLASSES.get(service_class_name)
            model_to_use = cls() if cls else self.grounding_model

        # Assemble diagnostic routing metadata
        exec_mode = "local_or_api"
        fb_used = router_res["fallback_used"]
        model_used = SPECIALIST_REGISTRY.get(target, {}).get("model_type", "generic_grounding")

        if hasattr(model_to_use, "execution_mode"):
            exec_mode = getattr(model_to_use, "execution_mode", exec_mode)
        if hasattr(model_to_use, "fallback_used"):
            fb_used = getattr(model_to_use, "fallback_used", fb_used)
        if hasattr(model_to_use, "model"):
            model_used = getattr(model_to_use, "model", model_used)

        metadata = {
            "specialist_used": router_res["selected_specialist"],
            "model_type": SPECIALIST_REGISTRY.get(target, {}).get("model_type", "generic_grounding"),
            "fallback_used": fb_used,
            "execution_mode": exec_mode,
            "model_used": model_used
        }

        # 2. Run localization model to extract raw component pixel coordinates
        _, regions = model_to_use.detect(pil_img, target)
        
        if not regions:
            return {
                "status": "NOT_FOUND",
                "target": target,
                "detections": [],
                "annotated_image": None,
                "specialist_used": router_res["selected_specialist"],
                "model_used": model_used,
                "execution_mode": exec_mode,
                "fallback_used": fb_used,
                "metadata": metadata
            }

        orig_width, orig_height = pil_img.size
        image_area = orig_width * orig_height
        scale_x = orig_width / 128.0
        scale_y = orig_height / 128.0

        # 3. Process candidate properties: bounding boxes, centroid coordinates, areas
        candidates = []
        for component in regions:
            comp_xs = [p[0] for p in component]
            comp_ys = [p[1] for p in component]
            
            xmin, xmax = min(comp_xs), max(comp_xs)
            ymin, ymax = min(comp_ys), max(comp_ys)
            
            orig_xmin = int(xmin * scale_x)
            orig_xmax = int(xmax * scale_x)
            orig_ymin = int(ymin * scale_y)
            orig_ymax = int(ymax * scale_y)
            
            bbox = [orig_ymin, orig_xmin, orig_ymax, orig_xmax]
            
            pixel_area = len(component) * scale_x * scale_y
            relative_area = pixel_area / image_area
            bounding_box_area = (orig_ymax - orig_ymin) * (orig_xmax - orig_xmin)
            
            # Precise Center 
            center_x = (orig_xmin + orig_xmax) / 2.0
            center_y = (orig_ymin + orig_ymax) / 2.0
            
            location = self._determine_relative_location(center_x, center_y, orig_width, orig_height)

            candidates.append({
                "component": component,
                "bbox": bbox,
                "pixel_area": pixel_area,
                "relative_area": relative_area,
                "bounding_box_area": bounding_box_area,
                "location": location
            })

        # 4. Filters & Post-processing
        # 4A. Remove extremely small regions
        filtered_candidates = []
        for c in candidates:
            if c["pixel_area"] < MIN_REGION_AREA_PIXELS:
                continue
            if c["relative_area"] < MIN_REGION_AREA_PERCENT:
                continue
            filtered_candidates.append(c)

        if not filtered_candidates:
            return {
                "status": "NOT_FOUND",
                "target": target,
                "detections": [],
                "annotated_image": None,
                "metadata": metadata
            }

        # 4B. Sort by area descending (largest region first)
        filtered_candidates.sort(key=lambda x: x["pixel_area"], reverse=True)

        # 4C. Overlap Non-Maximum Suppression (IoU duplicate merging)
        accepted_candidates = []
        for cand in filtered_candidates:
            overlap = False
            for acc in accepted_candidates:
                if calculate_iou(cand["bbox"], acc["bbox"]) > IOU_THRESHOLD:
                    overlap = True
                    break
            if not overlap:
                accepted_candidates.append(cand)

        # 4D. Limit to max permitted detections
        accepted_candidates = accepted_candidates[:MAX_DETECTIONS_PER_TARGET]

        if not accepted_candidates:
            return {
                "status": "NOT_FOUND",
                "target": target,
                "detections": [],
                "annotated_image": None,
                "metadata": metadata
            }

        # 4E. Prioritization Labeling 
        # Classify as major_region or minor_region based on area threshold
        final_detections = []
        final_components = []
        
        for idx, cand in enumerate(accepted_candidates, 1):
            importance = "major_region" if cand["relative_area"] >= MAJOR_REGION_THRES_PERCENT else "minor_region"
            
            final_detections.append({
                "id": idx,
                "label": target,
                "importance": importance,
                "location": cand["location"],
                "visualization_type": "segmentation_mask",
                "bbox": cand["bbox"],
                "relative_area": cand["relative_area"],
                "area_pixels": int(cand["pixel_area"])
            })
            
            final_components.append(cand["component"])

        # 5. Generate high-resolution segmentation mask for accepted regions only
        if hasattr(model_to_use, "high_res_mask") and getattr(model_to_use, "high_res_mask", None) is not None:
            mask_im = getattr(model_to_use, "high_res_mask")
        else:
            mask_im = self.segmentation.generate_mask(pil_img.size, final_components)

        # 6. Generate annotated output image
        annotated_path = self.annotation.annotate(
            image_source=pil_img,
            detections=final_detections,
            mask_image=mask_im,
            request_id=request_id
        )
        
        if annotated_path:
            import shutil
            try:
                shutil.copy(annotated_path, "final_annotated_image.png")
            except Exception:
                pass

        # 7. Formulate summary count dict 
        major_count = sum(1 for d in final_detections if d["importance"] == "major_region")
        minor_count = sum(1 for d in final_detections if d["importance"] == "minor_region")
        
        summary = {
            "major_regions": major_count,
            "minor_regions": minor_count,
            "total_valid_regions": len(final_detections)
        }
        if target in ["building", "buildings"]:
            summary["total_buildings_detected"] = len(final_detections)

        # Format endpoints for Static Access
        web_url = f"/outputs/annotated_{request_id}.png" if annotated_path else None
        
        processing_time = round(time.time() - start_time, 3)
        metadata["processing_time_seconds"] = processing_time

        return {
            "status": "SUCCESS",
            "target": target,
            "summary": summary,
            "detections": final_detections,
            "annotated_image": {
                "generated": annotated_path is not None,
                "url": web_url,
                "path_or_url": annotated_path
            },
            "specialist_used": router_res["selected_specialist"],
            "model_used": model_used,
            "execution_mode": exec_mode,
            "fallback_used": fb_used,
            "processing_time_seconds": processing_time,
            "metadata": metadata
        }
