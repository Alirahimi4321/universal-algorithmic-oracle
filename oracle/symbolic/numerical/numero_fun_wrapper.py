"""Numero Fun library wrapper - numerology number calculations."""
from __future__ import annotations

import hashlib
import logging
import math
import random
from typing import Optional

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import numero_fun
    HAS_NUMERO = True
except ImportError:
    HAS_NUMERO = False
    logger.info("numero_fun not available")


@register_system
class NumeroFunWrapper(SymbolicSystemWrapper):
    """Wrapper for Numero Fun numerology calculations."""
    SYSTEM_ID = "numero_fun"
    LIBRARY_BACKEND = "numero_fun"

    def __init__(self) -> None:
        self.available: bool = HAS_NUMERO

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "numero_fun not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)
        text = entropy_packet.get("text", entropy_packet.get("question", ""))

        try:
            letter_values = {}
            if text:
                for char in text.upper():
                    if char.isalpha():
                        val = numero_fun.letter_to_number(char)
                        if val is not None:
                            letter_values[char] = val

            text_number = numero_fun.calculate_number(text) if text else 0
            digit_sum = numero_fun.get_sum(text_number) if text_number else 0

            all_values = list(letter_values.values())
            sum_vals = sum(all_values) if all_values else 0

            hash_val = int(hashlib.sha256(str(text_number).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                (text_number % 100) / 100.0,
                (digit_sum % 100) / 100.0,
                (sum_vals % 1000) / 1000.0,
                (hash_val % 1000) / 1000.0,
                len(letter_values) / max(len(text), 1),
            ]

            symbolic_state = {
                "input_text": text[:100],
                "text_number": text_number,
                "digit_sum": digit_sum,
                "letter_values": letter_values,
                "total_letter_sum": sum_vals,
                "unique_letters": len(set(letter_values.keys())),
            }

            structural_features = {
                "numerical_density": len(letter_values) / max(len(text), 1),
                "value_variance": (sum((v - sum_vals/max(len(all_values), 1))**2 for v in all_values) / max(len(all_values), 1)) if all_values else 0,
                "reduction_depth": len(str(digit_sum)),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"letter_values": letter_values},
                params=params,
            )
        except Exception as e:
            logger.warning(f"numero_fun computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
