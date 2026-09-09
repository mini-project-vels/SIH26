import io
import json
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from main import app

# Initialize the TestClient
client = TestClient(app)

def create_mock_satellite_image(color=(0, 150, 20)):
    # 500x500 mock image
    img = Image.new("RGB", (500, 500), color=color)
    draw = ImageDraw.Draw(img)
    
    # Draw a few rect structures as building rooftops
    draw.rectangle([40, 40, 120, 120], fill=(120, 120, 120))
    draw.rectangle([210, 200, 310, 310], fill=(120, 120, 120))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def run_disaster_verification():
    print("======================================================================")
    print("🚀 SatQuery AI - Disaster Intelligence & Management Engine Verification")
    print("======================================================================")
    
    # Generate mock images
    image_bytes = create_mock_satellite_image()
    before_bytes = create_mock_satellite_image(color=(0, 150, 20))
    after_bytes = create_mock_satellite_image(color=(20, 100, 150)) # changed to blue/flooded
    
    overall_results = {}
    
    # --- Test 1: General disaster query ---
    print("\n[TEST 1] Query: 'Analyze this image for disaster risk'")
    resp1 = client.post(
        "/disaster-analysis",
        data={"query": "Analyze this image for disaster risk"},
        files={"image": ("image.png", image_bytes, "image/png")}
    )
    print(f"Status Code: {resp1.status_code}")
    print(json.dumps(resp1.json(), indent=2))
    overall_results["test_1_general_disaster"] = resp1.json()
    
    # --- Test 2: Flood risk query ---
    print("\n[TEST 2] Query: 'Is there a flood risk?'")
    resp2 = client.post(
        "/disaster-analysis",
        data={"query": "Is there a flood risk?"},
        files={"image": ("image.png", image_bytes, "image/png")}
    )
    print(f"Status Code: {resp2.status_code}")
    print(json.dumps(resp2.json(), indent=2))
    overall_results["test_2_flood_risk"] = resp2.json()
    
    # --- Test 3: Region disaster monitoring ---
    print("\n[TEST 3] Query: 'Check this region for possible disaster activity'")
    resp3 = client.post(
        "/disaster-analysis",
        data={"query": "Check this region for possible disaster activity"},
        files={"image": ("image.png", image_bytes, "image/png")}
    )
    print(f"Status Code: {resp3.status_code}")
    print(json.dumps(resp3.json(), indent=2))
    overall_results["test_3_region_activity"] = resp3.json()
    
    # --- Test 4: Two-image Temporal comparison ---
    print("\n[TEST 4] Query: 'Compare these images and identify possible disaster-related changes'")
    resp4 = client.post(
        "/disaster-analysis",
        data={"query": "Compare these images and identify possible disaster-related changes"},
        files={
            "before_image": ("before.png", before_bytes, "image/png"),
            "after_image": ("after.png", after_bytes, "image/png")
        }
    )
    print(f"Status Code: {resp4.status_code}")
    print(json.dumps(resp4.json(), indent=2))
    overall_results["test_4_temporal_comparison"] = resp4.json()
    
    # Write aggregated outcomes
    with open("response_disaster.json", "w") as f:
        json.dump(overall_results, f, indent=2)
        
    print("\nSuccessfully compiled verification results to response_disaster.json")

if __name__ == "__main__":
    run_disaster_verification()
