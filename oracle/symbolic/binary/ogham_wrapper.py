"""Ogham alphabet wrapper - Celtic/Ogham script encoding and decoding."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import ogham
    HAS_OGHAM = True
except ImportError:
    HAS_OGHAM = False
    logger.info("ogham not available")


@register_system
class OghamWrapper(SymbolicSystemWrapper):
    """Wrapper for Ogham alphabet encoding/decoding."""
    SYSTEM_ID = "ogham"
    LIBRARY_BACKEND = "ogham"

    def __init__(self) -> None:
        self.available: bool = HAS_OGHAM

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "ogham not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            question = entropy_packet.get("question", "") if isinstance(entropy_packet, dict) else ""
            text = question if question else f"oracle-{seed}"

            encoded = ogham.letters_to_ogham(text.lower())
            decoded = ogham.ogham_to_letters(encoded)

            numeric = [
                len(encoded) / 100.0,
                hash(encoded) % 1000 / 1000.0,
                len(text) / 100.0,
                hash(decoded) % 1000 / 1000.0,
            ]

            char_values = []
            for ch in text.lower():
                val = ord(ch) - ord('a') + 1 if ch.isalpha() else 0
                char_values.append(val / 26.0)

            return self._build_output(
                symbolic_state={
                    "input_text": text[:200],
                    "ogham_text": encoded,
                    "decoded_text": decoded,
                    "ogham_length": len(encoded),
                    "char_values": char_values[:20],
                },
                numeric_projection=numeric + char_values[:10],
                structural_features={
                    "input_length": len(text),
                    "ogham_length": len(encoded),
                    "roundtrip_match": text.lower() == decoded,
                },
                raw_output={"encoded": encoded, "decoded": decoded},
                params=params,
            )
        except Exception as e:
            logger.warning("ogham computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
