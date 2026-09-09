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

providers = [":featherless-ai", ":together", ":lepton", ":novita", ""]
models = [
    "Qwen/Qwen2.5-VL-3B-Instruct",
    "Qwen/Qwen2.5-VL-7B-Instruct",
    "meta-llama/Llama-3.2-11B-Vision-Instruct",
    "microsoft/Phi-3.5-vision-instruct"
]

for model in models:
    for prov in providers:
        full_model = model + prov
        try:
            print(f"Testing {full_model} ...", end=" ", flush=True)
            completion = client.chat.completions.create(
                model=full_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "one word"},
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                        ],
                    }
                ],
                max_tokens=5
            )
            print(f"SUCCESS! -> {completion.choices[0].message.content.strip()}")
        except Exception as e:
            err_msg = str(e)
            if "not valid" in err_msg:
                print("invalid provider")
            elif "not supported by any provider" in err_msg:
                print("no provider enabled")
            else:
                print(f"FAILED: {type(e).__name__}: {err_msg[:100]}")
