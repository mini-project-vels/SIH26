import sys
from app.services.huggingface_vision_service import _is_capacity_error
from app.config import vision_config

err = "Error code: 400 - {'error': {'message': \"the provider or policy you attempted to specify 'nebius' is not valid.\", 'type': 'invalid_request_error', 'param': 'model', 'code': 'model_not_supported'}}"

print("CAPACITY_ERROR_KEYWORDS:", vision_config.CAPACITY_ERROR_KEYWORDS)
print("Is capacity error:", _is_capacity_error(err))
