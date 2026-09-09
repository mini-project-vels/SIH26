import base64
import os
import logging
from typing import Any, Optional
from openai import OpenAI
from app.config import vision_config

logger = logging.getLogger(__name__)


def _is_capacity_error(error_text: str) -> bool:
    """Returns True if the error string indicates a capacity / overload issue."""
    lower = error_text.lower()
    return any(kw in lower for kw in vision_config.CAPACITY_ERROR_KEYWORDS)


class HuggingFaceVisionService:
    """
    Communicates with the Hugging Face Router using the OpenAI SDK.

    Handles:
    - Local image → Base64 data URL encoding
    - MIME type validation
    - Primary model call with automatic fallback on capacity errors
    - Controlled error reporting (no secrets exposed)
    """

    SUPPORTED_EXTENSIONS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

    def __init__(self) -> None:
        self.api_key = vision_config.HF_TOKEN
        self.base_url = vision_config.HF_BASE_URL
        self.primary_model = vision_config.HF_VISION_MODEL
        self.fallback_models = vision_config.HF_FALLBACK_MODELS

    # ─────────────────────────── helpers ─────────────────────────────────────

    def _bytes_to_data_url(self, file_content: bytes, filename: str) -> str:
        """Encodes image bytes as a Base64 data URL, validating extension."""
        _, ext = os.path.splitext(filename.lower())
        mime_type = self.SUPPORTED_EXTENSIONS.get(ext)
        if not mime_type:
            raise ValueError(
                f"Unsupported image format '{ext}'. Supported formats: PNG, JPG, JPEG, WEBP."
            )
        b64 = base64.b64encode(file_content).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"

    def _read_image(self, image: Any) -> tuple[bytes, str]:
        """
        Extracts raw bytes and filename from various image input types:
        """
        import io
        from PIL import Image

        def extract_bytes() -> tuple[bytes, str]:
            if hasattr(image, "file"):
                filename = image.filename or "image.png"
                image.file.seek(0)
                content = image.file.read()
                if not content:
                    raise ValueError("Image file is empty or could not be read.")
                return content, filename
            elif isinstance(image, tuple) and len(image) == 2:
                filename, content = image
                return content, filename
            elif isinstance(image, str):
                with open(image, "rb") as f:
                    return f.read(), image
            else:
                raise TypeError(f"Unrecognised image input type: {type(image)}")
        
        raw_bytes, fname = extract_bytes()
        
        # Compress the image heavily to prevent Nginx/vLLM base64 payload drops or hangs
        try:
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                
                # Resize if larger than 448 on any side (matches CLIP/SigLIP typical bounds)
                # This guarantees sub-50KB base64 strings to stop proxy/vLLM timeouts
                max_size = 448
                if pil_img.width > max_size or pil_img.height > max_size:
                    pil_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Re-encode to JPEG bytes with 85 quality to reduce network transit
                out_buf = io.BytesIO()
                pil_img.save(out_buf, format="JPEG", quality=85)
                # Force rename extension so MIME resolves correctly
                fname = os.path.splitext(fname)[0] + ".jpg"
                return out_buf.getvalue(), fname
        except Exception as e:
            logger.warning(f"Image compression failed, falling back to raw bytes: {e}")
            return raw_bytes, fname

    def _call_model(self, client: OpenAI, model: str, image_data_url: str, prompt: str) -> str:
        """Sends a single vision completion request to the given model."""
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=0.2,           # 1. Improves predictability and reduces hallucination
            max_tokens=1024,           # 2. Ensures detailed analysis doesn't get cut off
            top_p=0.9                  # 3. Focuses the model on factual correctness
        )
        if not completion.choices or not completion.choices[0].message.content:
            raise RuntimeError("Empty response received from Hugging Face Vision router.")
        return completion.choices[0].message.content.strip()

    # ────────────────────────── public API ───────────────────────────────────

    def analyze_image(self, image: Any, prompt: str) -> str:
        """
        Sends the image + prompt to the Hugging Face Router.

        Tries the primary model first. On a capacity / overload error it
        automatically falls back through ``HF_FALLBACK_MODELS`` in order.
        Raises ``ValueError`` for config issues, ``RuntimeError`` when all
        models are exhausted.

        Args:
            image: FastAPI UploadFile, (filename, bytes) tuple, or path string.
            prompt: Full remote-sensing prompt including system instructions.

        Returns:
            str: The AI-generated text answer.
        """
        if not self.api_key:
            raise ValueError("Vision service configuration is missing.")

        # Read and encode the image once — reused across all model attempts
        try:
            file_content, filename = self._read_image(image)
        except (TypeError, OSError) as exc:
            raise ValueError(f"Failed to read image source: {exc}") from exc

        image_data_url = self._bytes_to_data_url(file_content, filename)

        client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=120.0)

        last_error: Optional[str] = None

        for model in self.fallback_models:
            try:
                logger.info("Attempting vision analysis with model: %s", model)
                answer = self._call_model(client, model, image_data_url, prompt)
                if model != self.primary_model:
                    logger.info("Fallback model succeeded: %s", model)
                return answer

            except Exception as exc:
                error_str = str(exc)
                last_error = error_str

                if _is_capacity_error(error_str):
                    logger.warning(
                        "Model %s is at capacity — trying next fallback. Error: %s",
                        model, error_str
                    )
                    continue  # try the next model in the list
                else:
                    # Non-capacity error (auth, bad request, etc.) — fail immediately
                    raise RuntimeError(
                        f"Hugging Face Router request failed: {error_str}"
                    ) from exc

        # All models exhausted
        raise RuntimeError(
            "All vision models are currently at capacity. Please try again in a few minutes. "
            f"Last error: {last_error}"
        )
