import httpx
import json
import io
from PIL import Image

url = "http://localhost:8000/analyze-image"

# Generate random pattern image to ensure it's not detected as blank
import logging
import random
img = Image.new("RGB", (300, 300))
for x in range(300):
   for y in range(300):
      img.putpixel((x, y), (random.randint(0,255), random.randint(0,255), random.randint(0,255)))

buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)

try:
    print("Testing backend api /analyze-image...")
    response = httpx.post(
        url,
        data={"query": "Describe the main color of this image."},
        files={"image": ("test.png", buf, "image/png")},
        timeout=60.0
    )
    print("STATUS:", response.status_code)
    try:
        data = response.json()
        print("JSON API SUCCESS:", data.get("status"))
        print("ANSWER:", data.get("result", {}).get("answer", data.get("message")))
    except:
        print("RESPONSE:", response.text)
except Exception as e:
    print("FAILED TO CONNECT TO LOCAL API:", e)
