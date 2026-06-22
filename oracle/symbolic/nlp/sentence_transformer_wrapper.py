"""Sentence Transformers embedding wrapper."""
from __future__ import annotations

import hashlib
import logging
import math
import random

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.info("sentence-transformers not available")


@register_system
class SentenceTransformerWrapper(SymbolicSystemWrapper):
    """Wrapper for sentence-transformers embeddings and similarity features."""
    SYSTEM_ID = "sentence_transformers"
    LIBRARY_BACKEND = "sentence-transformers"

    def __init__(self) -> None:
        self.available: bool = HAS_SENTENCE_TRANSFORMERS
        self._model = None
        self._model_name: str = "all-MiniLM-L6-v2"

    def _get_model(self):
        if self._model is None and self.available:
            try:
                self._model = SentenceTransformer(self._model_name)
            except Exception as e:
                logger.warning("Failed to load sentence-transformers model: %s", e)
                self.available = False
        return self._model

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "sentence-transformers not available"},
            )

        if params and "model_name" in params:
            self._model_name = params["model_name"]

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)
        text = entropy_packet.get("text", entropy_packet.get("question", ""))

        if not text:
            text = f"oracle_{seed}_query"

        model = self._get_model()
        if model is None:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "model not loaded"},
            )

        try:
            embedding = model.encode(text, normalize_embeddings=True).tolist()

            mag = math.sqrt(sum(x * x for x in embedding))
            cosine_features = []
            reference_vectors = [
                [rng.random() for _ in range(384)] for _ in range(3)
            ]
            for ref in reference_vectors:
                dot = sum(a * b for a, b in zip(embedding, ref))
                ref_mag = math.sqrt(sum(x * x for x in ref))
                cosine_sim = dot / (mag * ref_mag) if ref_mag > 0 else 0.0
                cosine_features.append(cosine_sim)

            hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)

            numeric_projection = embedding[:32] + [
                mag,
                max(embedding),
                min(embedding),
                sum(embedding) / len(embedding),
                (hash_val % 1000) / 1000.0,
                rng.random(),
            ]

            symbolic_state = {
                "input_text": text[:100],
                "embedding_dim": len(embedding),
                "embedding_magnitude": round(mag, 6),
                "embedding_head": [round(x, 6) for x in embedding[:10]],
                "embedding_tail": [round(x, 6) for x in embedding[-5:]],
                "cosine_similarities": [round(s, 6) for s in cosine_features],
                "mean_value": round(sum(embedding) / len(embedding), 6),
                "std_value": round(
                    math.sqrt(
                        sum((x - sum(embedding) / len(embedding)) ** 2 for x in embedding)
                        / len(embedding)
                    ),
                    6,
                ),
            }

            structural_features = {
                "embedding_norm": round(mag, 6),
                "max_component": round(max(embedding), 6),
                "min_component": round(min(embedding), 6),
                "mean_component": round(sum(embedding) / len(embedding), 6),
                "cosine_mean": round(sum(cosine_features) / len(cosine_features), 6),
                "l2_sparsity": round(
                    sum(1 for x in embedding if abs(x) < 0.01) / len(embedding), 6
                ),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"embedding": embedding},
                params=params,
            )
        except Exception as e:
            logger.warning(f"sentence-transformers computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
