"""
run_glacier_test.py
Integration script to test Glacier Detection and GLOF Risk Specialist.
"""

import os
import io
import json
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def create_synthetic_image(glacier_type="none", lake_type="none") -> bytes:
    arr = np.full((256, 256, 3), (60, 50, 40), dtype=np.uint8) # Dark rock background
    
    # Glacier
    if glacier_type == "small":
        # White snow / ice in top-left
        arr[20:100, 20:100] = (250, 250, 255)
    elif glacier_type == "large":
        # Advance / larger glacier
        arr[10:150, 10:150] = (250, 250, 255)
        
    # Glacial lake
    if lake_type == "small":
        # Teal lake next to glacier
        arr[100:130, 80:110] = (30, 150, 160)
    elif lake_type == "large":
        # Expanded lake
        arr[100:180, 80:160] = (30, 150, 160)

    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_test():
    print("\n🧊 SatQuery AI - Glacier Detection & GLOF Specialist Verification")
    print("=================================================================\n")
    
    # 1. Create baseline (Before)
    before_bytes = create_synthetic_image(glacier_type="large", lake_type="small")
    print("✓ Built baseline image (Large glacier, small glacial lake)")
    
    # 2. Create recent (After)
    after_bytes = create_synthetic_image(glacier_type="small", lake_type="large")
    print("✓ Built recent image (Retreated glacier, expanded glacial lake)\n")
    
    # 3. Form multipart request to /analyze/glacier
    files = {
        "before_image": ("before.png", before_bytes, "image/png"),
        "after_image": ("after.png", after_bytes, "image/png"),
    }
    data = {
        "query": "Is there a GLOF risk due to glacier retreat?"
    }
    
    print("Sending API request to POST /analyze/glacier...")
    response = client.post("/analyze/glacier", data=data, files=files)
    
    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return
        
    res_json = response.json()
    
    with open("response_glacier.json", "w") as f:
        json.dump(res_json, f, indent=2)
        
    print(f"✓ Success! Status: {res_json.get('status')}")
    print(f"✓ Saved raw response to response_glacier.json\n")
    
    print("=== ANALYSIS RESULTS ===")
    
    glm = res_json.get("glacier_assessment", {})
    cha = res_json.get("change_analysis", {})
    lka = res_json.get("glacial_lake_analysis", {})
    rsk = res_json.get("risk_assessment", {})
    
    print(f"- Glacier Detected:      {glm.get('glacier_detected')} ({glm.get('glacier_percentage')}% coverage)")
    print(f"- Glacier Changed:       {cha.get('change_detected')} -> {cha.get('change_type')}")
    print(f"- Glacial Lake Detected: {lka.get('lake_detected')}, Expanded: {lka.get('lake_expansion_detected')} ({lka.get('estimated_expansion_percentage')}%)")
    
    print(f"\n- Risk Level:            {rsk.get('risk_level')} (Score: {rsk.get('risk_score')})")
    
    print("\n- Risk Factors:")
    for rf in rsk.get("risk_factors", []):
        print(f"  * {rf['factor']} (+{rf['contribution']} points)")

    annot_path = res_json.get("annotated_image", {}).get("path_or_url")
    print(f"\n- Annotated Execution Map: {annot_path}")
    print("\nVerification Complete.")

if __name__ == "__main__":
    run_test()
