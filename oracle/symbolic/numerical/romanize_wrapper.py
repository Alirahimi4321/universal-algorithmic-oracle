"""Romanize3 wrapper - romanization of various scripts."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import romanize3
    HAS_ROMANIZE3 = True
except ImportError:
    HAS_ROMANIZE3 = False
    logger.info("romanize3 not available")


@register_system
class RomanizeWrapper:
    """Wrapper for romanize3 script romanization."""
    SYSTEM_ID = "romanize"

    def __init__(self) -> None:
        self.available: bool = HAS_ROMANIZE3

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="romanize3", raw_output={"error": "romanize3 not available"})

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="romanize3", raw_output={"error": str(e)})

        try:
            text = params.get("text", "سلام دنیا") if params else "سلام دنیا"

            romanized = ""
            try:
                romanized = romanize3.romanize(text)
            except Exception:
                romanized = text

            numeric = [
                len(text) / 100.0,
                hash(romanized) % 1000 / 1000.0,
                rng.random(),
                rng.random(),
            ]

            symbolic_state = {
                "original": text,
                "romanized": romanized,
            }

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="romanize3",
                symbolic_state=symbolic_state,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"romanize3 computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="romanize3", raw_output={"error": str(e)})
