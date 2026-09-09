import io
import json
import os
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from main import app

# Initialize FastAPI TestClient
client = TestClient(app)

def create_mock_scene(water_color=None, building_color=None):
    # Base green vegetation (0, 150, 20)
    img = Image.new("RGB", (500, 500), color=(0, 150, 20))
    draw = ImageDraw.Draw(img)
    
    # If water_color is specified, draw a water body (RGB format: blue-ish)
    if water_color:
        draw.rectangle([120, 120, 380, 380], fill=water_color)
        
    # If building_color is specified, draw building rooftops (Grey)
    if building_color:
        # Building inside the water region overlap (150, 150, 220, 220)
        draw.rectangle([150, 150, 220, 220], fill=building_color)
        # Building partially overlapping water boundaries (350, 350, 420, 420)
        draw.rectangle([350, 350, 420, 420], fill=building_color)
        # Building outside water
        draw.rectangle([30, 30, 90, 90], fill=building_color)
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def run_flood_verification():
    print("======================================================================")
    print("🌊 SatQuery AI - Flood Detection & Flood Risk Specialist Verification")
    print("======================================================================")
    
    # Save the mock before and after images to verify locally
    before_bytes = create_mock_scene(water_color=(0, 80, 180), building_color=(120, 120, 120)) # Small water body
    after_bytes = create_mock_scene(water_color=(0, 10, 240), building_color=(120, 120, 120)) # Expanded water body
    
    # Save files to disk for reference
    with open("temp_before_satellite.png", "wb") as f:
        f.write(before_bytes)
    with open("temp_after_satellite.png", "wb") as f:
        f.write(after_bytes)
        
    print("Created mock scenario satellite assets: 'temp_before_satellite.png' & 'temp_after_satellite.png'.")
    
    # Post query
    query = "Compare these images and check whether flooding increased, showing affected buildings."
    print(f"\nAnalyzing Query: '{query}'")
    
    response = client.post(
        "/disaster-analysis",
        data={"query": query},
        files={
            "before_image": ("before.png", before_bytes, "image/png"),
            "after_image": ("after.png", after_bytes, "image/png")
        }
    )
    
    print(f"Status Code: {response.status_code}")
    res_json = response.json()
    print("\nREPORT DETAILS:")
    print(f"Query Intent Classified: {res_json.get('analysis_type')} -> {res_json.get('disaster_type')}")
    print(f"Assessment Status: {res_json.get('assessment_status')}")
    
    flood_assessment = res_json.get("flood_assessment", {})
    print(f"Flood Risk Level: {flood_assessment.get('risk_level')} (Score: {flood_assessment.get('risk_score')}/100)")
    
    water_analysis = res_json.get("water_analysis", {})
    print(f"Water Detected: {water_analysis.get('water_detected')}")
    print(f"Water Expansion Detected: {water_analysis.get('water_expansion_detected')} (Percentage: {water_analysis.get('water_expansion_percentage')}%)")
    
    potential_impact = res_json.get("potential_impact", {})
    print(f"Potentially Affected Buildings: {potential_impact.get('potentially_affected_buildings')}")
    
    print("\nRisk Factors:")
    for rf in res_json.get("risk_factors", []):
        print(f" - {rf.get('factor')} [+{rf.get('contribution')} pts]")
        
    print("\nAffected Regions:")
    for ar in res_json.get("affected_regions", []):
        print(f" - Region ID {ar.get('region_id')} ({ar.get('location')}): Severity {ar.get('severity')}, Overlap {ar.get('water_overlap_percentage')}%")
        
    print("\nRecommendations:")
    for rec in res_json.get("recommendations", []):
        print(f" - {rec}")
        
    annotated = res_json.get("annotated_image", {})
    print(f"\nAnnotated Map Details: Generated={annotated.get('generated')}, URL={annotated.get('path_or_url')}")
    
    # Save the output report JSON to disk
    with open("response_flood.json", "w") as f:
        json.dump(res_json, f, indent=2)
    print("\nSaved full structured report to response_flood.json")
    
    # Clean up temporary test files
    try:
        os.remove("run_tb.py")
        os.remove("test_err.log")
        os.remove("err.txt")
    except Exception:
        pass

if __name__ == "__main__":
    run_flood_verification()
