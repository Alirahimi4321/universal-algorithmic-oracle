"""Proces library wrapper - Persian text preprocessing and normalization."""
from __future__ import annotations

import hashlib
import logging
import math
from typing import Optional

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from proces import preprocess as proces_preprocess
    HAS_PROCES = True
except ImportError:
    HAS_PROCES = False
    logger.info("proces not available")


@register_system
class ProcesWrapper(SymbolicSystemWrapper):
    """Wrapper for Persian text preprocessing using proces library."""
    SYSTEM_ID = "proces_text"
    LIBRARY_BACKEND = "proces"

    def __init__(self) -> None:
        self.available: bool = HAS_PROCES

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "proces not available"},
            )

        text = entropy_packet.get("text", entropy_packet.get("question", ""))
        if not text:
            seed = entropy_packet.get("seed", 42)
            text = f"oracle_query_{seed}"

        try:
            normalized = proces_preprocess(text)

            char_values = [ord(c) for c in normalized if c.isalpha()]
            word_count = len(normalized.split())
            char_count = len(normalized)

            hash_val = int(hashlib.sha256(normalized.encode()).hexdigest()[:8], 16)
            numeric_projection = [
                (hash_val % 1000) / 1000.0,
                word_count / max(char_count, 1),
                len(set(normalized)) / max(char_count, 1),
                (sum(char_values) % 1000) / 1000.0,
                math.sin(hash_val) * 0.5 + 0.5,
            ]

            symbolic_state = {
                "original_text": text[:200],
                "normalized_text": normalized[:200],
                "char_count": char_count,
                "word_count": word_count,
                "unique_chars": len(set(normalized)),
            }

            structural_features = {
                "text_density": word_count / max(char_count, 1),
                "unique_ratio": len(set(normalized)) / max(char_count, 1),
                "avg_char_value": sum(char_values) / max(len(char_values), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"normalized": normalized},
                params=params,
            )
        except Exception as e:
            logger.warning(f"proces computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
