import os
import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
model_id = "Abhatta7/building-footprint-segmentation"
api_url = f"https://api-inference.huggingface.co/models/{model_id}"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Create a small dummy 100x100 PNG image bytes to send
from PIL import Image
import io
img = Image.new("RGB", (100, 100), color=(100, 100, 100))
buf = io.BytesIO()
img.save(buf, format="PNG")
img_bytes = buf.getvalue()

print(f"URL: {api_url}")
try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(api_url, headers=headers, content=img_bytes)
        print(f"Status Code: {response.status_code}")
        print("Response Content:")
        print(response.text[:1000])
except Exception as e:
    print(f"Error calling HF Inference API: {e}")
