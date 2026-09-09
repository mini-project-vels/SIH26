import re
from typing import Dict, Any, Optional
from app.config.grounding_config import TARGET_EXTRACTION_KEYWORDS

class TargetExtractionService:
    """
    Target Extraction Service.
    Determines what specific feature or object type (e.g., water_body, forest)
    the user wants to localize in the image based on their query text.
    """

    def __init__(self) -> None:
        # Precompile regexes for common target extraction patterns
        self.action_patterns = [
            re.compile(r"\b(?:locate|highlight|find|show|mark|where is|where are|localize|draw a bounding box around)\s+(?:me\s+)?(?:the|a|an|all|any)?\s*([a-zA-Z0-9_\s\-]{2,})", re.IGNORECASE),
            re.compile(r"([a-zA-Z0-9_\s\-]{2,})\s+(?:detection|localization|segmentation|mask|highlight|extraction)\b", re.IGNORECASE)
        ]
        
        # Words to strip out of the extracted target
        self.stop_words = ["region", "regions", "area", "areas", "zone", "zones", "located", "in the image", "in this image", "on the image", "portions", "portion"]

    def extract_target(self, query: str) -> Dict[str, Any]:
        """
        Extracts the target concept and returns intent and target.
        """
        normalized_query = query.strip().lower()
        
        # 1. Match against known target keywords directly
        matched_category = None
        for category, keywords in TARGET_EXTRACTION_KEYWORDS.items():
            for kw in keywords:
                # Require word borders to prevent partial matches like "water" inside "watermelon"
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, normalized_query):
                    matched_category = category
                    break
            if matched_category:
                break
                
        if matched_category:
            return {
                "intent": "visual_localization",
                "target": matched_category
            }

        # 2. Extract using action regex patterns if direct lookup fails
        extracted_text = None
        for pattern in self.action_patterns:
            match = pattern.search(normalized_query)
            if match:
                extracted_text = match.group(1).strip()
                break
                
        if extracted_text:
            # Clean stop words out
            for stop in self.stop_words:
                extracted_text = re.sub(r"\b" + re.escape(stop) + r"\b", "", extracted_text).strip()
            # Collapse multiple spaces and replace remaining with underscores
            extracted_text = re.sub(r"\s+", "_", extracted_text)
            
            if extracted_text:
                return {
                    "intent": "visual_localization",
                    "target": extracted_text
                }

        # 3. Default fallback to a generic search term or "unknown"
        # Let's see if we can find any noun, or just return the last 1-2 words
        words = [w for w in normalized_query.split() if w not in ["the", "a", "an", "is", "where"]]
        fallback_target = words[-1] if words else "object"
        
        return {
            "intent": "visual_localization",
            "target": fallback_target
        }
