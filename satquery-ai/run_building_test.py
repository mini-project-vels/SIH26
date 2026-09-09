import httpx
import io
import json
import os
from PIL import Image, ImageDraw

def create_rich_mock_satellite_image():
    # 500x500 satellite mock: green vegetation (0, 150, 20)
    img = Image.new("RGB", (500, 500), color=(0, 150, 20))
    draw = ImageDraw.Draw(img)
    
    # Draw grey building rectangular rooftops (r=120, g=120, b=120)
    # Building 1 (Northwest)
    draw.rectangle([40, 40, 120, 120], fill=(120, 120, 120))
    # Building 2 (Center)
    draw.rectangle([210, 200, 310, 310], fill=(120, 120, 120))
    # Building 3 (Southeast)
    draw.rectangle([350, 380, 450, 470], fill=(120, 120, 120))
    
    # Draw a linear road (yellow-ish, r=70, g=70, b=70) that crossing the image
    # Note: road pixels are 70, 70, 70, so they don't trigger the building class
    draw.line([(0, 450), (350, 0)], fill=(70, 70, 70), width=15)
    
    # Save raw mock
    img.save("test_satellite_building.png")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_test():
    img_bytes = create_rich_mock_satellite_image()
    url = "http://127.0.0.1:8000/locate-object"
    
    files = {
        "image": ("test_satellite_building.png", img_bytes, "image/png")
    }
    data = {
        "query": "Mark all buildings"
    }
    
    print("Sending POST request to /locate-object...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, data=data, files=files)
            print(f"STATUS CODE: {response.status_code}")
            response_json = response.json()
            print("\nRESPONSE JSON:\n")
            print(json.dumps(response_json, indent=2))
            
            # Save response to a text file for verification
            with open("response_building.json", "w") as f:
                json.dump(response_json, indent=2)
            
            if response_json.get("status") == "SUCCESS":
                annotated_url = response_json["annotated_image"]["url"]
                print(f"\nAnnotated image created at: {annotated_url}")
                # Save the annotated file locally to verify it looks correct
                # The url points to /outputs/annotated_xxxx.png
                relative_path = annotated_url.lstrip("/")
                if os.path.exists(relative_path):
                    print(f"Verified annotated file exists locally at: {relative_path}")
            else:
                print("Failed to locate buildings in the response.")
    except Exception as e:
        print("ERROR executing post request:", e)

if __name__ == "__main__":
    run_test()
