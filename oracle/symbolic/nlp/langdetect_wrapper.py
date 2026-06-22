"""Language detection wrapper using langdetect."""
from __future__ import annotations

import hashlib
import logging
import math
import random

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import langdetect
    from langdetect import detect, detect_langs, DetectorFactory
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    logger.info("langdetect not available")


@register_system
class LangdetectWrapper(SymbolicSystemWrapper):
    """Wrapper for language detection and confidence scoring."""
    SYSTEM_ID = "langdetect_nlp"
    LIBRARY_BACKEND = "langdetect"

    def __init__(self) -> None:
        self.available: bool = HAS_LANGDETECT

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "langdetect not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)
        text = entropy_packet.get("text", entropy_packet.get("question", ""))

        if not text:
            text = f"oracle_{seed}_query"

        try:
            detected_lang = detect(text)
            lang_probs = detect_langs(text)
            prob_dict = {str(lp.lang): round(lp.prob, 6) for lp in lang_probs}

            hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)

            top_probs = sorted(prob_dict.values(), reverse=True)
            numeric_projection = [
                top_probs[0] if top_probs else 0.0,
                top_probs[1] if len(top_probs) > 1 else 0.0,
                top_probs[2] if len(top_probs) > 2 else 0.0,
                len(prob_dict) / 10.0,
                (hash_val % 1000) / 1000.0,
                len(text) / 1000.0,
                rng.random(),
            ]

            symbolic_state = {
                "input_text": text[:100],
                "detected_language": detected_lang,
                "num_candidates": len(prob_dict),
                "language_probabilities": prob_dict,
                "top_language": detected_lang,
                "top_probability": prob_dict.get(detected_lang, 0.0),
                "language_entropy": -sum(
                    p * math.log2(p) for p in prob_dict.values() if p > 0
                ),
            }

            structural_features = {
                "confidence": prob_dict.get(detected_lang, 0.0),
                "language_diversity": len(prob_dict),
                "entropy": -sum(
                    p * math.log2(p) for p in prob_dict.values() if p > 0
                ),
                "max_confidence": max(prob_dict.values()) if prob_dict else 0.0,
                "min_confidence": min(prob_dict.values()) if prob_dict else 0.0,
                "text_length": len(text),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"probabilities": prob_dict},
                params=params,
            )
        except Exception as e:
            logger.warning(f"langdetect computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
