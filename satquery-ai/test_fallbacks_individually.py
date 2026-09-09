import os
import io
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")
base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")

client = OpenAI(base_url=base_url, api_key=token, timeout=60.0)

# Generate a tiny PNG image
img = Image.new("RGB", (10, 10), color="blue")
buf = io.BytesIO()
img.save(buf, format="PNG")
png_bytes = buf.getvalue()
import base64
image_data_url = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"

models_to_test = [
    "Qwen/Qwen2.5-VL-7B-Instruct:nebius",
    "Qwen/Qwen2.5-VL-3B-Instruct",
    "Qwen/Qwen2.5-VL-7B-Instruct",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "microsoft/Phi-3.5-vision-instruct"
]

for model in models_to_test:
    print(f"Testing model: {model} ...")
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in one sentence."},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
        )
        print(f"  SUCCESS! Response: {completion.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
