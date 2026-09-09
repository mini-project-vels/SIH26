import os
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageChops
from typing import Dict, Any, Tuple, List
from skimage.metrics import structural_similarity as ssim
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects, disk, binary_opening

class AutomatedChangeDetectionEngine:
    """
    Automated multi-method change detection engine processing raw or SAR-preprocessed imagery.
    Executes multiple algorithms (Abs Diff, SSIM, Configurable Thresholds, Connected Components) 
    and applies morphological noise filtering to determine exact change magnitudes.
    """
    
    def __init__(
        self, 
        output_dir: str = "outputs/change_detection",
        diff_threshold: float = 0.15,
        min_area_pixels: int = 50
    ):
        self.output_dir = output_dir
        self.diff_threshold = diff_threshold
        self.min_area = min_area_pixels
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _validate_inputs(self, before_path: str, after_path: str) -> Tuple[bool, str]:
        if not os.path.exists(before_path):
            return False, f"Before image not found: {before_path}"
        if not os.path.exists(after_path):
            return False, f"After image not found: {after_path}"
        return True, "SUCCESS"

    def _normalize(self, img_path: str) -> np.ndarray:
        """Loads and normalizes an image to generic float bounds 0-1 grayscale."""
        img = Image.open(img_path).convert("L")
        return np.array(img, dtype=np.float32) / 255.0

    def analyze(
        self, 
        before_image_path: str, 
        after_image_path: str, 
        analysis_target: str = "general"
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())[:12]
        target_dir = os.path.join(self.output_dir, req_id)
        os.makedirs(target_dir, exist_ok=True)
        
        # Step 1: Validation
        valid, msg = self._validate_inputs(before_image_path, after_image_path)
        if not valid:
            return {"status": "FAILED", "reason": msg, "comparison_ready": False}
            
        # Step 2: Image Normalization
        try:
            b_array = self._normalize(before_image_path)
            a_array = self._normalize(after_image_path)
        except Exception as e:
            return {"status": "FAILED", "reason": f"Reading error or dimension mismatch: {str(e)}"}
            
        if b_array.shape != a_array.shape:
            # Force resize `a` to match `b` automatically for robustness
            img_b = Image.open(before_image_path)
            img_a = Image.open(after_image_path).resize(img_b.size)
            a_array = np.array(img_a.convert("L"), dtype=np.float32) / 255.0
            
        # Step 3: Multi-Method Registration
        # Method 1: Absolute Difference
        diff_array = np.abs(a_array - b_array)
        
        # Method 2 & 3: Structural Similarity
        # ssim_map represents similarity [-1 to 1], where 1 is identical.
        # Change is roughly 1 - ssim_map
        _, ssim_map = ssim(b_array, a_array, data_range=1.0, full=True)
        ssim_change = 1.0 - np.clip(ssim_map, 0, 1)

        # Method 4: Configurable Baseline Threshold Fusion
        # We combine ABS diff and SSIM logic
        fused_change = (diff_array * 0.7) + (ssim_change * 0.3)
        binary_mask = fused_change > self.diff_threshold
        
        # Step 5: Noise Filtering (Morphological Ops)
        # 1. Remove tiny speckles through morphological opening
        clean_mask = binary_opening(binary_mask, disk(3))
        # 2. Remove isolated disjoint small regions
        clean_mask = remove_small_objects(clean_mask, min_size=self.min_area)
        
        # Step 3 & 4 (Method 5 & Confidence): Region Extraction & CC
        labeled_map = label(clean_mask)
        regions = regionprops(labeled_map)
        
        significant_regions = []
        total_changed_pixels = 0
        total_pixels = clean_mask.size
        
        for idx, region in enumerate(regions):
            area = region.area
            total_changed_pixels += area
            
            # Confidence is bumped slightly based on area density vs the threshold
            bbox = region.bbox # (min_row, min_col, max_row, max_col)
            conf = min(0.99, 0.70 + (area / self.min_area) * 0.05)
            
            r_data = {
                "region_id": idx + 1,
                "bounding_box": [bbox[1], bbox[0], bbox[3], bbox[2]], # [x1, y1, x2, y2]
                "area_pixels": area,
                "change_percentage": round((area / total_pixels) * 100, 4),
                "confidence": round(conf, 2),
                "methods_detected": ["absolute_difference", "ssim", "threshold_analysis", "connected_components"]
            }
            significant_regions.append(r_data)
            
        overall_change = round((total_changed_pixels / total_pixels) * 100, 2)
        change_detected = overall_change > 0.1
        
        if overall_change > 20: intensity = "CRITICAL"
        elif overall_change > 10: intensity = "HIGH"
        elif overall_change > 2: intensity = "MODERATE"
        else: intensity = "LOW"
        
        # Step 6: Visualizations Generation
        out_paths = {}
        
        # 1. Save original copies (for easy UI ref)
        img_b = Image.open(before_image_path).convert("RGB")
        img_a = Image.open(after_image_path).convert("RGB")
        if img_a.size != img_b.size:
            img_a = img_a.resize(img_b.size)
        
        p_bef = os.path.join(target_dir, "before_visualization.png")
        p_aft = os.path.join(target_dir, "after_visualization.png")
        img_b.save(p_bef); out_paths["before"] = p_bef.replace("\\", "/")
        img_a.save(p_aft); out_paths["after"] = p_aft.replace("\\", "/")
        
        # 2. Raw Difference Map (Heatmap styled proxy)
        diff_scaled = (diff_array * 255).astype(np.uint8)
        # Apply pseudo-heat color mapping by dropping it in Red channel
        diff_img = Image.merge("RGB", (Image.fromarray(diff_scaled), Image.fromarray(np.zeros_like(diff_scaled)), Image.fromarray(np.zeros_like(diff_scaled))))
        p_raw = os.path.join(target_dir, "raw_difference.png")
        diff_img.save(p_raw); out_paths["difference_map"] = p_raw.replace("\\", "/")
        
        # 3. Filtered Change Map
        mask_scaled = (clean_mask * 255).astype(np.uint8)
        mask_img = Image.fromarray(mask_scaled)
        p_map = os.path.join(target_dir, "change_map.png")
        mask_img.save(p_map); out_paths["change_map"] = p_map.replace("\\", "/")
        
        # 4. Overlay Visualization
        # Red transparent overlay exactly over identical changed pixels
        red_solid = Image.new("RGB", img_a.size, (255, 0, 0))
        blend_target = Image.blend(img_a, red_solid, 0.5)
        overlay_img = Image.composite(blend_target, img_a, mask_img)
        
        # Draw bounding boxes
        draw = ImageDraw.Draw(overlay_img)
        for r in significant_regions:
            bx = r["bounding_box"]
            draw.rectangle([bx[0], bx[1], bx[2], bx[3]], outline="yellow", width=2)
            
        p_overlay = os.path.join(target_dir, "overlay_visualization.png")
        overlay_img.save(p_overlay); out_paths["overlay"] = p_overlay.replace("\\", "/")
        
        # Returns standard block
        return {
            "request_id": req_id,
            "status": "SUCCESS",
            "analysis_type": "automated_change_detection",
            "change_detected": change_detected,
            "overall_change_percentage": overall_change,
            "change_intensity": intensity,
            "significant_regions": significant_regions,
            "visualizations": out_paths,
            "ready_for_disaster_analysis": True
        }
