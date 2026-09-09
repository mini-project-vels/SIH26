import sys
import io
import logging
import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("water_diag")

def make_satellite_test_image():
    """
    Build a synthetic image that looks like a real satellite image —
    dark olive vegetation, dark blueish water, grey buildings.
    This is similar to what real satellite RGB imagery looks like.
    """
    w, h = 512, 512
    arr = np.full((h, w, 3), (55, 110, 35), dtype=np.uint8)  # olive green vegetation

    # Deep lake - dark blueish (NOT pure blue)
    arr[150:380, 80:420] = (28, 52, 88)
    # Shallow water - slightly lighter/greenish-blue  
    arr[200:250, 180:300] = (40, 70, 120)
    
    # Buildings (grey rooftop)
    arr[30:80, 30:80] = (130, 128, 125)
    arr[400:450, 430:490] = (140, 135, 130)

    return Image.fromarray(arr, "RGB")

def diagnose_classifier(img):
    from app.config.grounding_config import is_water

    img_rgb = img.convert("RGB")
    
    print("\n[1] Sampling is_water() on known water pixels (28, 52, 88):")
    for py in range(160, 200, 10):
        for px in range(100, 180, 20):
            r, g, b = img_rgb.getpixel((px, py))
            result = is_water(r, g, b)
            print(f"    Pixel ({px},{py}) = RGB({r},{g},{b}) -> is_water={result}")

    print("\n[2] Sampling is_water() on known vegetation pixels (55, 110, 35):")
    for py in range(5, 50, 10):
        for px in range(5, 50, 10):
            r, g, b = img_rgb.getpixel((px, py))
            result = is_water(r, g, b)
            print(f"    Pixel ({px},{py}) = RGB({r},{g},{b}) -> is_water={result}")

def diagnose_local_grounding(img):
    from app.services.visual_grounding_service import LocalGroundingService
    
    print("\n[3] LocalGroundingService.detect() on PIL Image ->")
    svc = LocalGroundingService(min_region_size=10)
    _, regions = svc.detect(img, "water_body")
    print(f"    Found {len(regions)} region(s)")
    for i, r in enumerate(regions[:3]):
        print(f"    Region {i}: {len(r)} pixels")
    return regions

def diagnose_bytes_path(img):
    from app.services.visual_grounding_service import VisualGroundingService
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()
    
    print(f"\n[4] VisualGroundingService.process_grounding() with bytes (len={len(raw_bytes)}) ->")
    svc = VisualGroundingService()
    res = svc.process_grounding(raw_bytes, "water_body", "diag_001")
    print(f"    status={res.get('status')}, detections={len(res.get('detections', []))}")
    return res

def diagnose_pil_path(img):
    from app.services.visual_grounding_service import VisualGroundingService
    
    print(f"\n[5] VisualGroundingService.process_grounding() with PIL image ->")
    svc = VisualGroundingService()
    # PIL Image is not handled by process_grounding! Check the code path:
    try:
        res = svc.process_grounding(img, "water_body", "diag_002")
        print(f"    status={res.get('status')}, detections={len(res.get('detections', []))}")
        if res.get("status") == "ERROR":
            print(f"    ERROR: {res.get('error_message')}")
        return res
    except Exception as e:
        print(f"    EXCEPTION: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("WATER DETECTION ROOT CAUSE DIAGNOSTIC")
    print("=" * 60)

    img = make_satellite_test_image()
    img.save("diag_test_satellite.png")
    print(f"Saved synthetic satellite test image: diag_test_satellite.png ({img.size})")
    
    diagnose_classifier(img)
    regions = diagnose_local_grounding(img)
    res_bytes = diagnose_bytes_path(img)
    res_pil = diagnose_pil_path(img)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  is_water classifier effective: {'YES' if regions else 'NO - classifier does not detect satellite water colors'}")
    print(f"  bytes path: {res_bytes.get('status')}")
    print(f"  PIL path: {res_pil.get('status') if res_pil else 'EXCEPTION'}")
    print("=" * 60)
