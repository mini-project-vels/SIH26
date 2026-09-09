import os
from dotenv import load_dotenv

# Load environment variables from .env and force override OS vars
load_dotenv(override=True)

# Hugging Face Vision APIs configuration
HF_TOKEN = os.getenv("HF_TOKEN")
HF_VISION_MODEL = "meta-llama/Llama-3.2-11B-Vision-Instruct:featherless-ai"
HF_BASE_URL = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")

# Ordered list of fallback vision models tried when the primary is unavailable.
# All use :featherless-ai provider suffix — confirmed the only provider enabled
# on this HF account that supports these vision models.
HF_FALLBACK_MODELS = [
    HF_VISION_MODEL,                                       # primary (from .env)
    "Qwen/Qwen2.5-VL-3B-Instruct:featherless-ai",         # specifies featherless-ai
    "Qwen/Qwen2.5-VL-7B-Instruct:featherless-ai",         # specifies featherless-ai
    "meta-llama/Llama-3.2-11B-Vision-Instruct:featherless-ai",
    "microsoft/Phi-3.5-vision-instruct:featherless-ai",
]

# Remove duplicates while preserving order
seen = set()
HF_FALLBACK_MODELS = [
    m for m in HF_FALLBACK_MODELS
    if not (m in seen or seen.add(m))
]

# Error strings that mean "this model/provider is overloaded or unavailable —
# try the next fallback" (case-insensitive match).
SKIPPABLE_ERROR_KEYWORDS = [
    "capacity_exhausted",
    "temporarily at capacity",
    "overloaded",
    "model_not_supported",
    "not valid",
    "provider",
    "503",
    "529",
]

# Keep the old name as an alias so existing code doesn't break
CAPACITY_ERROR_KEYWORDS = SKIPPABLE_ERROR_KEYWORDS
