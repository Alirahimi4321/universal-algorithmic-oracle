"""Hafez divination wrapper - Persian poetry divination (Fal-e Hafez)."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import hafez
    HAS_HAFEZ = True
except ImportError:
    HAS_HAFEZ = False
    logger.info("hafez not available")


@register_system
class HafezWrapper:
    """Wrapper for Hafez poetry divination."""
    SYSTEM_ID = "hafez"

    def __init__(self) -> None:
        self.available: bool = HAS_HAFEZ

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="hafez", raw_output={"error": "hafez not available"})

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="hafez", raw_output={"error": str(e)})

        try:
            poem = hafez.fal()
            title = poem.get("title", "")
            poem_text = poem.get("poem", "")
            interpretation = poem.get("interpretation", "")
            meter = poem.get("meter", "")
            bayt = poem.get("bayt", "")

            numeric = [
                hash(title) % 1000 / 1000.0,
                hash(meter) % 1000 / 1000.0,
                rng.random(),
                rng.random(),
            ]

            symbolic_state = {
                "title": title,
                "poem": poem_text[:200],
                "interpretation": interpretation[:200],
                "meter": meter,
                "bayt": bayt,
            }

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="hafez",
                symbolic_state=symbolic_state,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"hafez computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="hafez", raw_output={"error": str(e)})
