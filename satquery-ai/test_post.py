import httpx
import io
from PIL import Image

url = "http://127.0.0.1:8000/analyze-image"

# Let's generate a valid PNG bytes first
img = Image.new("RGB", (10, 10), color="blue")
buf = io.BytesIO()
img.save(buf, format="PNG")
png_bytes = buf.getvalue()

files = {
    "image": ("test.png", png_bytes, "image/png")
}

data = {
    "query": "what is present in this image?"
}

try:
    response = httpx.post(url, data=data, files=files, timeout=120.0)
    print("STATUS:", response.status_code)
    print("RESPONSE JSON:", response.json())
except Exception as e:
    print("ERROR:", e)
