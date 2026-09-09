import re
from typing import Tuple, Optional
from app.services.classifier_interface import QueryClassifierInterface
from app.config.intents import (
    Intents,
    HazardTypes,
    INTENT_CONFIGS,
    HAZARD_CONFIGS,
    INTENT_PATTERNS,
    CONVERSATIONAL_KEYWORDS,
    AMBIGUOUS_KEYWORDS
)

class RuleBasedClassifier(QueryClassifierInterface):
    """
    Implements a hybrid rule-based intent classifier using keyword scoring,
    query normalization, and regex pattern matching.
    """

    def __init__(self) -> None:
        # Precompile regular expressions for efficiency
        self.intent_regexes = []
        for item in INTENT_PATTERNS:
            compiled_patterns = []
            for pat in item["patterns"]:
                if isinstance(pat, tuple):
                    # For disaster patterns with specific hazard mapping
                    pattern_str, hazard = pat
                    compiled_patterns.append((re.compile(pattern_str, re.IGNORECASE), hazard))
                else:
                    compiled_patterns.append(re.compile(pat, re.IGNORECASE))
            self.intent_regexes.append({
                "intent": item["intent"],
                "patterns": compiled_patterns
            })

        self.conversational_regexes = [
            re.compile(pat, re.IGNORECASE) for pat in CONVERSATIONAL_KEYWORDS
        ]
        self.ambiguous_regexes = [
            re.compile(pat, re.IGNORECASE) for pat in AMBIGUOUS_KEYWORDS
        ]

    def _normalize_query(self, query: str) -> str:
        """
        Normalizes the input query by converting to lowercase,
        removing extra spaces, and basic cleanup.
        """
        normalized = query.strip().lower()
        # Remove trailing question marks or exclamation marks
        normalized = re.sub(r'[?!.,;:]+$', '', normalized)
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def classify(self, query: str) -> Tuple[str, float, Optional[str]]:
        """
        Classifies the query using pre-compiled regex matching and scoring.
        """
        normalized_query = self._normalize_query(query)

        # 1. Handle empty queries
        if not normalized_query:
            return Intents.UNKNOWN, 0.90, None

        # 2. Check for conversational queries
        for regex in self.conversational_regexes:
            if regex.search(normalized_query):
                return Intents.UNKNOWN, 0.90, None

        # 3. Check for ambiguous/too-generic queries
        for regex in self.ambiguous_regexes:
            if regex.match(normalized_query):
                return Intents.UNKNOWN, 0.90, None

        # 4. Check for matches across the intents and calculate scores
        scores = {}
        hazard_type = None

        for item in self.intent_regexes:
            intent = item["intent"]
            patterns = item["patterns"]
            match_count = 0

            if intent == Intents.DISASTER_HAZARD_ANALYSIS:
                # Disaster has special nested tuples (regex, hazard_type)
                for regex, haz in patterns:
                    if regex.search(normalized_query):
                        match_count += 1
                        # If a specific hazard is matched, save it (prioritize non-unknown)
                        if haz != HazardTypes.UNKNOWN or not hazard_type:
                            hazard_type = haz
            else:
                for regex in patterns:
                    if regex.search(normalized_query):
                        match_count += 1

            if match_count > 0:
                # Get the default confidence of the intent as baseline
                baseline_conf = INTENT_CONFIGS[intent]["default_confidence"]
                # Give a small boost if multiple pattern matches occurred
                boost = min(0.05, (match_count - 1) * 0.02)
                scores[intent] = min(0.99, baseline_conf + boost)

        # 5. Determine the highest scoring intent
        if scores:
            best_intent = max(scores, key=lambda k: scores[k])
            confidence = scores[best_intent]

            # If the classified intent is not DISASTER_HAZARD_ANALYSIS, hazard_type must be None
            if best_intent != Intents.DISASTER_HAZARD_ANALYSIS:
                hazard_type = None

            return best_intent, confidence, hazard_type

        # 6. Fallback if no patterns matched
        return Intents.UNKNOWN, 0.50, None
