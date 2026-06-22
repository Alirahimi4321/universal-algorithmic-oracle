"""Hebrew Numbers wrapper - Hebrew gematria and number conversion."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import hebrew_numbers as hn
    HAS_HEBREW_NUMBERS = True
except ImportError:
    HAS_HEBREW_NUMBERS = False
    logger.info("hebrew_numbers not available")


@register_system
class HebrewNumbersWrapper(SymbolicSystemWrapper):
    """Wrapper for hebrew_numbers gematria."""
    SYSTEM_ID = "hebrew_numbers"
    LIBRARY_BACKEND = "hebrew_numbers"

    def __init__(self) -> None:
        self.available: bool = HAS_HEBREW_NUMBERS

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "hebrew_numbers not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            question = entropy_packet.get("question", "") if isinstance(entropy_packet, dict) else ""
            text = question if question else f"oracle-{seed}"

            gematria_value = 0
            try:
                gematria_value = hn.gematria_to_int(text)
            except Exception:
                gematria_value = hash(text) % 10000

            numeric_representation = ""
            try:
                numeric_representation = hn.int_to_gematria(gematria_value)
            except Exception:
                numeric_representation = str(gematria_value)

            numeric = [
                gematria_value / 10000.0,
                len(text) / 100.0,
                hash(text) % 1000 / 1000.0,
            ]

            return self._build_output(
                symbolic_state={
                    "text": text[:200],
                    "gematria_value": gematria_value,
                    "hebrew_representation": numeric_representation,
                },
                numeric_projection=numeric,
                structural_features={"has_value": gematria_value > 0},
                raw_output={"value": gematria_value, "hebrew": numeric_representation},
                params=params,
            )
        except Exception as e:
            logger.warning("hebrew_numbers computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
