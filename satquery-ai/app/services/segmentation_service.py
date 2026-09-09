from PIL import Image
from typing import List, Tuple, Optional

class SegmentationService:
    """
    Segmentation Service.
    Creates high-resolution binary segmentation masks from low-resolution pixel coordinates.
    """

    def generate_mask(
        self,
        original_size: Tuple[int, int],
        regions: List[List[Tuple[int, int]]]
    ) -> Optional[Image.Image]:
        """
        Creates a binary mask (mode 'L') matching the original image size.
        
        Args:
            original_size (Tuple[int, int]): Dimensions of original image (width, height)
            regions (List[List[Tuple[int, int]]]): List of connected component pixels in 128x128 grid
            
        Returns:
            Optional[Image.Image]: Binary PIL image (0 or 255)
        """
        if not regions:
            return None

        try:
            # Create low-res mask
            mask_low = Image.new("L", (128, 128), 0)
            
            for region in regions:
                for x, y in region:
                    if 0 <= x < 128 and 0 <= y < 128:
                        mask_low.putpixel((x, y), 255)
                        
            # Upscale using nearest neighbor to keep hard visual boundaries
            mask_high = mask_low.resize(original_size, Image.Resampling.NEAREST)
            return mask_high
        except Exception:
            # Fall back to None on error (signals fallback to bounding box only)
            return None
