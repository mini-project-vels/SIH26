import os
from dotenv import load_dotenv

# Load environment configs
load_dotenv()

# Grounding output directory
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Default confidence mappings
DEFAULT_CONFIDENCE = 0.88

# --- Configurable Filtering Parameters ---
MIN_REGION_AREA_PIXELS = int(os.getenv("MIN_REGION_AREA_PIXELS", "150"))
MIN_REGION_AREA_PERCENT = float(os.getenv("MIN_REGION_AREA_PERCENT", "0.002"))  # 0.2% of image total area
MAX_DETECTIONS_PER_TARGET = int(os.getenv("MAX_DETECTIONS_PER_TARGET", "10"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.4"))

# --- Prioritization Configuration ---
MAJOR_REGION_THRES_PERCENT = float(os.getenv("MAJOR_REGION_THRES_PERCENT", "0.02"))  # 2.0% of image area makes it major

# --- Configurable Annotation Design ---
OVERLAY_ALPHA = float(os.getenv("OVERLAY_ALPHA", "0.40"))  # alpha transparency between 0.35 and 0.50

# --- Configurable Label Clutter Parameter ---
SHOW_LABEL_MIN_AREA_PERCENT = float(os.getenv("SHOW_LABEL_MIN_AREA_PERCENT", "0.01"))  # 1% of image area to show text labels

# --- Dedicated Building Segmentation Configs (Problem 8 & Phase 5 Improvement) ---
MIN_BUILDING_AREA_PIXELS = int(os.getenv("MIN_BUILDING_AREA_PIXELS", "100"))
MAX_BUILDING_AREA_PIXELS = int(os.getenv("MAX_BUILDING_AREA_PIXELS", "50000"))
MIN_BUILDING_AREA_PERCENT = float(os.getenv("MIN_BUILDING_AREA_PERCENT", "0.001")) # 0.1% minimum
MAX_BUILDING_DETECTIONS = int(os.getenv("MAX_BUILDING_DETECTIONS", "50"))
MAX_BUILDING_ASPECT_RATIO = float(os.getenv("MAX_BUILDING_ASPECT_RATIO", "3.0"))  # Aspect ratio threshold
MIN_BUILDING_COMPACTNESS = float(os.getenv("MIN_BUILDING_COMPACTNESS", "0.35"))    # Extent threshold (area / bbox_area)

# Tiling configurations
TILE_SIZE = int(os.getenv("TILE_SIZE", "512"))
TILE_OVERLAP = int(os.getenv("TILE_OVERLAP", "64"))

# Morphology configurations (Step 4)
ENABLE_MORPHOLOGY = True
OPENING_KERNEL = 3
CLOSING_KERNEL = 3
DILATION_KERNEL = 0

# Reusable target visualization configuration color mapping
COLOR_PALETTE = {
    "water_body": (0, 100, 255),       # Blue
    "forest": (0, 200, 50),            # Green
    "vegetation": (0, 200, 50),        # Green
    "buildings": (255, 120, 0),        # Orange / Amber
    "building": (255, 120, 0),         # Orange / Amber
    "roads": (255, 220, 0),            # Yellow
    "road": (255, 220, 0),             # Yellow
    "glacier": (0, 220, 220),          # Cyan
    "fire/burned_area": (255, 50, 0),  # Red/Orange
    "agricultural_land": (200, 200, 50), # Olive/Yellow
    "urban_area": (255, 120, 0)
}

# Derived mask overlay (with opacity) and border color mappings
MASK_COLOR_MAP = {k: v + (int(255 * OVERLAY_ALPHA),) for k, v in COLOR_PALETTE.items()}
BORDER_COLOR_MAP = COLOR_PALETTE

# --- Remote Sensing Specialist Model Registry ---
SPECIALIST_REGISTRY = {
    "building": {
        "specialist_id": "building_segmentation",
        "service_class": "BuildingSegmentationService",
        "model_type": "remote_sensing_segmentation",
        "reason": "Building footprint extraction requires remote-sensing-specific segmentation.",
        "confidence": 0.95,
        "is_available": True  # Enable it now, so building agent executes BuildingSegmentationService!
    },
    "buildings": {
        "specialist_id": "building_segmentation",
        "service_class": "BuildingSegmentationService",
        "model_type": "remote_sensing_segmentation",
        "reason": "Building footprint extraction requires remote-sensing-specific segment extraction.",
        "confidence": 0.95,
        "is_available": True
    },
    "water_body": {
        "specialist_id": "water_segmentation",
        "service_class": "WaterSegmentationService",
        "model_type": "spectral_water_index_analysis",
        "reason": "Water body mapping utilizes localized spectral reflection thresholds.",
        "confidence": 0.92,
        "is_available": True
    },
    "road": {
        "specialist_id": "road_segmentation",
        "service_class": "RoadSegmentationService",
        "model_type": "road_network_extraction",
        "reason": "Road network extraction uses linear shape trace segmenters.",
        "confidence": 0.89,
        "is_available": True
    },
    "roads": {
        "specialist_id": "road_segmentation",
        "service_class": "RoadSegmentationService",
        "model_type": "road_network_extraction",
        "reason": "Road network extraction uses linear shape trace segmenters.",
        "confidence": 0.89,
        "is_available": True
    },
    "forest": {
        "specialist_id": "land_cover_segmentation",
        "service_class": "LandCoverSegmentationService",
        "model_type": "vegetation_canopy_classification",
        "reason": "Forest and crop detection uses canopy/vegetation-index specialists.",
        "confidence": 0.91,
        "is_available": True
    },
    "vegetation": {
        "specialist_id": "land_cover_segmentation",
        "service_class": "LandCoverSegmentationService",
        "model_type": "vegetation_canopy_classification",
        "reason": "Forest and crop detection uses canopy/vegetation-index specialists.",
        "confidence": 0.91,
        "is_available": True
    },
    "agricultural_land": {
        "specialist_id": "land_cover_segmentation",
        "service_class": "LandCoverSegmentationService",
        "model_type": "agricultural_field_mapping",
        "reason": "Forest and crop detection uses canopy/vegetation-index specialists.",
        "confidence": 0.90,
        "is_available": True
    },
    "urban_area": {
        "specialist_id": "land_cover_segmentation",
        "service_class": "LandCoverSegmentationService",
        "model_type": "urban_agglomeration_mapping",
        "reason": "built-up urban layouts match land classification frameworks.",
        "confidence": 0.88,
        "is_available": True
    },
    "glacier": {
        "specialist_id": "land_cover_segmentation",
        "service_class": "LandCoverSegmentationService",
        "model_type": "snow_ice_classification",
        "reason": "glacial flow targets are resolved via land-cover surface ice classification.",
        "confidence": 0.93,
        "is_available": True
    }
}

# Target Extractor keyword lookup to normalize queries
TARGET_EXTRACTION_KEYWORDS = {
    "water_body": ["water body", "water bodies", "lake", "lakes", "river", "rivers", "water", "sea", "ocean", "pond", "ponds", "glacier lake"],
    "forest": ["forest", "forests", "forest area", "forest areas", "wood", "woods", "tree", "trees", "vegetation", "forested"],
    "buildings": ["building", "buildings", "urban", "house", "houses", "structure", "structures", "roof", "roofs", "settlement", "settlements"],
    "agricultural_land": ["agricultural", "agricultural land", "agriculture", "field", "fields", "farm", "farmland", "farmlands", "crop", "crops"],
    "glacier": ["glacier", "glaciers", "snow", "ice"],
    "roads": ["road", "roads", "highway", "highways", "path", "paths", "street", "streets"]
}

# Image classification spectral range thresholds (normalized coordinates in RGB)
def is_water(r: int, g: int, b: int) -> bool:
    if r == 0 and g == 0 and b > 200:
        return True
    avg = (r + g + b) / 3.0
    return (avg < 80 and b > r - 5 and b > g - 5) or (b > r + 15 and b > g + 5 and avg < 150)

def is_forest(r: int, g: int, b: int) -> bool:
    if r == 0 and g > 100 and b == 0:
        return True
    return g > r + 15 and g > b + 15 and g > 30

def is_buildings(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3.0
    is_very_bright = r > 180 and g > 180 and b > 180
    if is_very_bright:
        return False
    is_grey = abs(r - g) < 15 and abs(g - b) < 15 and avg > 90 and avg < 185
    is_rooftop_red = r > g + 20 and r > b + 20 and r > 80
    return is_grey or is_rooftop_red

def is_agricultural_land(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3.0
    is_light_green = g > b + 10 and g > r and avg > 70 and avg < 200
    is_field_yellow = g > b + 15 and r > b + 15 and abs(r - g) < 25 and avg > 80
    return is_light_green or is_field_yellow

def is_glacier(r: int, g: int, b: int) -> bool:
    return r > 190 and g > 200 and b > 210

def is_roads(r: int, g: int, b: int) -> bool:
    avg = (r + g + b) / 3.0
    return abs(r - g) < 10 and abs(g - b) < 10 and avg > 60 and avg < 140

PIXEL_CLASSIFIERS = {
    "water_body": is_water,
    "forest": is_forest,
    "building": is_buildings,
    "buildings": is_buildings,
    "agricultural_land": is_agricultural_land,
    "glacier": is_glacier,
    "road": is_roads,
    "roads": is_roads
}
