from PIL import Image
from typing import List, Dict, Any, Tuple

def split_image(image: Image.Image, tile_size: int = 512, overlap: int = 64) -> List[Dict[str, Any]]:
    """
    Splits an image into overlapping tiles.
    Each tile is represented as a dictionary containing layout offsets and sub-image.
    """
    width, height = image.size
    
    # Handle case where the image fits entirely into one single tile
    if width <= tile_size and height <= tile_size:
        return [{
            "x_offset": 0,
            "y_offset": 0,
            "width": width,
            "height": height,
            "tile_image": image
        }]
        
    stride = tile_size - overlap
    if stride <= 0:
        stride = tile_size
        
    tiles = []
    y = 0
    while y < height:
        # Determine actual tile height
        h = min(tile_size, height - y)
        # Shift back to align boundary if we're at the bottom edge to avoid tiny slivers
        y_pos = y
        if y_pos + h > height:
            y_pos = max(0, height - tile_size)
            h = min(tile_size, height - y_pos)

        x = 0
        while x < width:
            w = min(tile_size, width - x)
            # Shift back to align boundary if we're at the right edge
            x_pos = x
            if x_pos + w > width:
                x_pos = max(0, width - tile_size)
                w = min(tile_size, width - x_pos)
                
            tile_box = (x_pos, y_pos, x_pos + w, y_pos + h)
            tile_img = image.crop(tile_box)
            
            tiles.append({
                "x_offset": x_pos,
                "y_offset": y_pos,
                "width": w,
                "height": h,
                "tile_image": tile_img
            })
            
            if x + w >= width:
                break
            x += stride
            
        if y + h >= height:
            break
        y += stride
        
    return tiles

def merge_tile_masks(tile_masks: List[Tuple[Dict[str, Any], Image.Image]], original_width: int, original_height: int) -> Image.Image:
    """
    Merges tile-based segmentation masks back into one high-resolution binary mask.
    Handles overlap by taking the maximum/union of overlapping pixel values.
    """
    # Create empty high-res L-mode mask
    merged_mask = Image.new("L", (original_width, original_height), 0)
    
    for tile, mask in tile_masks:
        # Ensure mask is L-mode and matches tile dimensions
        mask_l = mask.convert("L")
        # In case of overlapping tiles, crop/paste blends them correctly
        merged_mask.paste(mask_l, (tile["x_offset"], tile["y_offset"]), mask_l)
        
    return merged_mask
