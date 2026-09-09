import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
import io
from PIL import Image

load_dotenv(override=True)

api_key = os.getenv("HF_TOKEN")
base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")

# Create a test image
img = Image.new("RGB", (300, 300), color="blue")
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=80)
raw_bytes = buf.getvalue()

b64 = base64.b64encode(raw_bytes).decode("utf-8")
image_data_url = f"data:image/jpeg;base64,{b64}"

client = OpenAI(base_url=base_url, api_key=api_key)

try:
    print("Testing microsoft/Phi-3.5-vision-instruct:featherless-ai")
    response = client.chat.completions.create(
        model="microsoft/Phi-3.5-vision-instruct:featherless-ai",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": "What color is this image?"},
                ],
            }
        ]
    )
    print("PHI RESPONSE:")
    print(response.choices[0].message.content)
except Exception as e:
    print("PHI FAILED:", e)

try:
    print("Testing Qwen/Qwen2.5-VL-7B-Instruct:featherless-ai")
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-7B-Instruct:featherless-ai",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": "What color is this image?"},
                ],
            }
        ]
    )
    print("QWEN7B RESPONSE:")
    print(response.choices[0].message.content)
except Exception as e:
    print("QWEN7B FAILED:", e)

try:
    print("Testing Llama-3.2-11B-Vision-Instruct:featherless-ai")
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct:featherless-ai",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": "What color is this image?"},
                ],
            }
        ]
    )
    print("LLAMA RESPONSE:")
    print(response.choices[0].message.content)
except Exception as e:
    print("LLAMA FAILED:", e)

