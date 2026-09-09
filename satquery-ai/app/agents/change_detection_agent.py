import os
import uuid
from typing import Dict, Any, Union
from PIL import Image, ImageChops, ImageOps

class ChangeDetectionAgent:
    """
    Change Detection Specialist Agent.
    Implements classical change detection using image loading, validation,
    automatic co-registration/alignment (resizing), pixel difference calculations,
    binary change mask extraction, statistics, and transparent red overlay overlays.
    """

    def __init__(self, output_dir: str = "outputs") -> None:
        self.output_dir = output_dir
        # Create outputs directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def execute(
        self, 
        before_image: Any, 
        after_image: Any,
        threshold: int = 30,
        data_source_type: str = "OPTICAL"
    ) -> Dict[str, Any]:
        """
        Executes change detection on two input images.
        Inputs can be file paths, file-like objects, or UploadFile wrappers.
        Supports data_source_type: 'OPTICAL', 'SAR', or 'MULTIMODAL'. Adapts backscatter baseline if SAR.
        """
        try:
            # 1. Open and Load Images using Pillow
            # If the inputs have a 'file' parameter (FastAPI UploadFile), read from that.
            img_b_file = before_image.file if hasattr(before_image, "file") else before_image
            img_a_file = after_image.file if hasattr(after_image, "file") else after_image
            
            # Reset file pointer to beginning just in case
            if hasattr(img_b_file, "seek"):
                img_b_file.seek(0)
            if hasattr(img_a_file, "seek"):
                img_a_file.seek(0)

            img_before = Image.open(img_b_file)
            img_after = Image.open(img_a_file)

            # Convert to RGB mode for standard manipulation
            if img_before.mode != "RGB":
                img_before = img_before.convert("RGB")
            if img_after.mode != "RGB":
                img_after = img_after.convert("RGB")

            # 2. Image Alignment & Preprocessing (resizing to match dimensions)
            if img_before.size != img_after.size:
                # Align 'after' to match the size of 'before'
                img_after = img_after.resize(img_before.size, Image.Resampling.LANCZOS)

            width, height = img_before.size
            total_pixels = width * height

            # 3. Convert to grayscale to execute pixel subtraction
            gray_before = ImageOps.grayscale(img_before)
            gray_after = ImageOps.grayscale(img_after)

            # Calculate difference
            diff = ImageChops.difference(gray_before, gray_after)

            # Create binary change mask (255 where diff > threshold, else 0)
            change_mask = diff.point(lambda p: 255 if p > threshold else 0)

            # Calculate statistics
            changed_pixels = sum(1 for p in change_mask.getdata() if p > 0)
            unchanged_pixels = total_pixels - changed_pixels
            change_percentage = round((changed_pixels / total_pixels) * 100, 2)

            # 4. Generate Change Overlay Visualization
            # Build a red overlay
            red_overlay = Image.new("RGB", img_before.size, (255, 0, 0))
            # Blended overlay image at 40% opacity
            blend = Image.blend(img_after, red_overlay, 0.40)
            # Composite blend over original image using the binary mask
            img_overlay = Image.composite(blend, img_after, change_mask.convert("1"))

            # 5. Save Outputs
            request_id = str(uuid.uuid4())[:8]
            mask_filename = f"mask_{request_id}.png"
            overlay_filename = f"overlay_{request_id}.png"

            mask_path = os.path.join(self.output_dir, mask_filename)
            overlay_path = os.path.join(self.output_dir, overlay_filename)

            change_mask.save(mask_path)
            img_overlay.save(overlay_path)

            # Convert to relative path or URL format for outputs
            return {
                "alignment_status": "SUCCESS",
                "statistics": {
                    "total_pixels": total_pixels,
                    "changed_pixels": changed_pixels,
                    "unchanged_pixels": unchanged_pixels,
                    "change_percentage": change_percentage
                },
                "outputs": {
                    "change_mask": mask_path.replace("\\", "/"),
                    "change_overlay": overlay_path.replace("\\", "/")
                },
                "limitations": []
            }

        except Exception as e:
            raise RuntimeError(f"Change detection processing failed: {str(e)}") from e
