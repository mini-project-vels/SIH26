import os
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List, Dict, Any, Optional
from app.config.grounding_config import MASK_COLOR_MAP, BORDER_COLOR_MAP, OUTPUT_DIR

EMOJI_MAP = {
    "water_body": "🌊 Water Body",
    "forest": "🌲 Forest",
    "buildings": "🏢 Buildings",
    "agricultural_land": "🌾 Agricultural Land",
    "glacier": "🏔️ Glacier",
    "roads": "🛣️ Roads"
}

class ImageAnnotationService:
    """
    Image Annotation Service.
    Annotates the satellite image with segmentation masks, contours,
    bounding boxes, and label boxes depending on the detection visualization type.
    """

    def __init__(self, output_dir: str = OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_label_text(self, label: str) -> str:
        return EMOJI_MAP.get(label, f"🔍 {label.replace('_', ' ').title()}")

    def annotate(
        self,
        image_source: Any,
        detections: List[Dict[str, Any]],
        mask_image: Optional[Image.Image] = None,
        request_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Draws annotations on a new copy of the source image and saves it.
        
        Args:
            image_source: Path string, bytes, or PIL Image.
            detections: List of detection items containing bounds, labels, etc.
            mask_image: High-res binary mask (same dimensions as image_source)
            request_id: Optional string to generate unique filename.
            
        Returns:
            Optional[str]: Relative path to the saved annotated image.
        """
        if not request_id:
            request_id = str(uuid.uuid4())[:8]

        try:
            # 1. Open the image source
            if isinstance(image_source, Image.Image):
                img = image_source.copy()
            elif isinstance(image_source, str):
                img = Image.open(image_source)
            elif isinstance(image_source, bytes):
                import io
                img = Image.open(io.BytesIO(image_source))
            elif hasattr(image_source, "file"):
                # FastAPI UploadFile
                image_source.file.seek(0)
                img = Image.open(image_source.file)
            else:
                raise TypeError(f"Unsupported image type for annotation: {type(image_source)}")

            # Convert to RGBA for blending and overlays
            img_rgba = img.convert("RGBA")
            width, height = img_rgba.size

            # 2. Draw segmentation masks if available
            if mask_image and any(d.get("visualization_type") == "segmentation_mask" for d in detections):
                mask_l = mask_image.convert("L")
                
                # We can have different targets in the same query potentially,
                # but let's assume we use the first detection's label to determine the mask color.
                primary_label = detections[0]["label"] if detections else "water_body"
                fill_color = MASK_COLOR_MAP.get(primary_label, (255, 255, 0, 102))  # alpha=102 (~40% opacity)
                border_color = BORDER_COLOR_MAP.get(primary_label, (255, 255, 0))

                # Create semi-transparent overlay
                overlay = Image.new("RGBA", img_rgba.size, fill_color)
                
                # Blend/Composite overlay only on mask areas
                img_rgba = Image.composite(overlay, img_rgba, mask_l)

                # Generate edge/contour mask to draw outline
                try:
                    # FIND_EDGES creates a boundary mask
                    edge_mask = mask_l.filter(ImageFilter.FIND_EDGES)
                    # Blow it up slightly to make the outline bolder/visible
                    edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))
                    
                    outline_layer = Image.new("RGBA", img_rgba.size, border_color + (255,))
                    img_rgba = Image.composite(outline_layer, img_rgba, edge_mask)
                except Exception:
                    # Fallback if filter fails
                    pass

            # 3. Draw fallback bounding boxes & labels
            draw = ImageDraw.Draw(img_rgba)
            
            # Load default font
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            for det in detections:
                label = det["label"]
                bbox = det.get("bbox")  # [ymin, xmin, ymax, xmax]
                viz_type = det.get("visualization_type", "segmentation_mask")
                
                if not bbox:
                    continue
                
                ymin, xmin, ymax, xmax = bbox
                
                # Ensure values are within image dimensions
                ymin = max(0, min(ymin, height - 1))
                xmin = max(0, min(xmin, width - 1))
                ymax = max(0, min(ymax, height - 1))
                xmax = max(0, min(xmax, width - 1))
                
                border_color = BORDER_COLOR_MAP.get(label, (255, 255, 0))

                # Draw bounding box only if it's a fallback or explicitly requested
                if viz_type == "bounding_box":
                    # Draw a rectangle box outline (3px width)
                    draw.rectangle([xmin, ymin, xmax, ymax], outline=border_color, width=3)

                # Draw label card only if the region's relative area is sufficient to avoid clutter (Problem 3)
                from app.config.grounding_config import SHOW_LABEL_MIN_AREA_PERCENT
                relative_area = det.get("relative_area", 1.0)
                
                if relative_area >= SHOW_LABEL_MIN_AREA_PERCENT:
                    label_text = self._get_label_text(label)
                    # Custom prefix naming for major/minor regions: Major Water Body, Small Water Region (or simply Class Name)
                    importance = det.get("importance", "minor_region")
                    if label in ["building", "buildings"]:
                        if importance == "major_region":
                            label_name = f"Building {det.get('id', 1)}"
                        else:
                            # Skip drawing labels for minor buildings to keep the image clean
                            continue
                    elif label == "water_body":
                        label_name = "Major Water Body" if importance == "major_region" else "Small Water Region"
                        if det.get("id"):
                            label_name = f"{label_name} #{det['id']}"
                    else:
                        label_name = f"Major {label.replace('_', ' ').title()}" if importance == "major_region" else f"Small {label.replace('_', ' ').title()}"
                        if det.get("id"):
                            label_name = f"{label_name} #{det['id']}"

                    # Calculate text dimensions using textbbox (Pillow 10+)
                    try:
                        text_bbox = draw.textbbox((xmin + 4, ymin - 20), label_name, font=font)
                        # Add some padding to label background
                        card_bbox = [text_bbox[0] - 4, text_bbox[1] - 2, text_bbox[2] + 4, text_bbox[3] + 2]
                    except Exception:
                        # Fallback text box approximation
                        text_w = len(label_name) * 6
                        text_h = 12
                        card_bbox = [xmin, ymin - text_h - 6, xmin + text_w + 8, ymin]

                    # Ensure label box doesn't go off original image top/left
                    if card_bbox[1] < 0:
                        offset_y = -card_bbox[1]
                        card_bbox[1] += offset_y
                        card_bbox[3] += offset_y
                    if card_bbox[0] < 0:
                        offset_x = -card_bbox[0]
                        card_bbox[0] += offset_x
                        card_bbox[2] += offset_x

                    # Draw solid label background card
                    draw.rectangle(card_bbox, fill=border_color)
                    # Draw white/black text over card (contrast colors)
                    text_color = (255, 255, 255, 255)
                    # If background color is very bright, use black text
                    if sum(border_color) > 550:
                        text_color = (0, 0, 0, 255)
                        
                    draw.text((card_bbox[0] + 4, card_bbox[1] + 2), label_name, fill=text_color, font=font)

            # Convert back to RGB for saving (JPEG doesn't support RGBA)
            final_img = img_rgba.convert("RGB")
            
            # Save annotated image
            out_filename = f"annotated_{request_id}.png"
            out_path = os.path.join(self.output_dir, out_filename)
            final_img.save(out_path, format="PNG")
            
            # Return relative path for exposure
            relative_path = f"outputs/{out_filename}"
            return relative_path
            
        except Exception as e:
            # Return None to handle error gracefully
            return None
