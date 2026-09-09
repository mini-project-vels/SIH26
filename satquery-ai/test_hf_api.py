import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
print("HF Token loaded:", bool(os.getenv("HF_TOKEN")))
print("Model:", os.getenv("HF_VISION_MODEL"))
print("Starting API request...")

client = OpenAI(
    base_url=os.getenv(
        "HF_BASE_URL",
        "https://router.huggingface.co/v1"
    ),
    api_key=os.getenv("HF_TOKEN"),
)

completion = client.chat.completions.create(
    model=os.getenv(
        "HF_VISION_MODEL",
        "Qwen/Qwen2.5-VL-3B-Instruct:featherless-ai"
    ),
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in one sentence."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
                    },
                },
            ],
        }
    ],
)

print("\n--- AI RESPONSE ---\n")
print(completion.choices[0].message.content)