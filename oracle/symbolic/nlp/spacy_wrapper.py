"""spaCy NER and text analysis wrapper."""
from __future__ import annotations

import hashlib
import logging
import math
import random
from collections import Counter

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logger.info("spacy not available")


@register_system
class SpacyWrapper(SymbolicSystemWrapper):
    """Wrapper for spaCy NER, noun chunks, POS tags, and sentence analysis."""
    SYSTEM_ID = "spacy_nlp"
    LIBRARY_BACKEND = "spacy"

    def __init__(self) -> None:
        self.available: bool = HAS_SPACY
        self._nlp = None
        self._model_name: str = "en_core_web_sm"

    def _get_nlp(self):
        if self._nlp is None and self.available:
            try:
                self._nlp = spacy.load(self._model_name)
            except OSError:
                try:
                    logger.info(
                        "spaCy model '%s' not found locally, attempting download...",
                        self._model_name,
                    )
                    from spacy.cli import download
                    download(self._model_name)
                    self._nlp = spacy.load(self._model_name)
                except Exception as e:
                    logger.warning(
                        "Failed to load/download spaCy model '%s': %s. "
                        "Download manually with: python -m spacy download %s",
                        self._model_name, e, self._model_name,
                    )
                    self.available = False
        return self._nlp

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "spacy not available"},
            )

        if params and "model_name" in params:
            self._model_name = params["model_name"]

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)
        text = entropy_packet.get("text", entropy_packet.get("question", ""))

        if not text:
            text = f"oracle_{seed}_query"

        nlp = self._get_nlp()
        if nlp is None:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "spacy model not loaded"},
            )

        try:
            doc = nlp(text)

            entities = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
            noun_chunks = [chunk.text for chunk in doc.noun_chunks]
            sentence_count = len(list(doc.sents))
            pos_tags = [(token.text, token.pos_) for token in doc]
            pos_counter = Counter(token.pos_ for token in doc)

            hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)

            numeric_projection = [
                len(entities) / max(len(doc), 1),
                len(noun_chunks) / max(len(doc), 1),
                sentence_count / max(len(list(doc.sents)), 1),
                len(pos_counter) / max(len(doc), 1),
                (hash_val % 1000) / 1000.0,
                len(text) / 1000.0,
                rng.random(),
            ]

            symbolic_state = {
                "input_text": text[:100],
                "token_count": len(doc),
                "entities": entities[:20],
                "entity_labels": list(pos_counter.keys())[:10],
                "noun_chunks": noun_chunks[:20],
                "sentence_count": sentence_count,
                "pos_tags": pos_tags[:30],
                "unique_pos": len(pos_counter),
            }

            structural_features = {
                "entity_density": len(entities) / max(len(doc), 1),
                "noun_chunk_density": len(noun_chunks) / max(len(doc), 1),
                "pos_variety": len(pos_counter) / max(len(doc), 1),
                "avg_token_length": sum(len(t.text) for t in doc) / max(len(doc), 1),
                "sentence_density": sentence_count / max(len(doc), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"entities": entities, "pos_tags": pos_tags},
                params=params,
            )
        except Exception as e:
            logger.warning(f"spacy computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
