"""Divination wrapper for divicast library (Six-Line divination and BaZi)."""
from __future__ import annotations

import logging
from typing import Any, Optional

from .base import SymbolicOutput, SymbolicSystemWrapper
from .registry import register_system

logger = logging.getLogger(__name__)

try:
    from divicast.sixline import DivinatorySymbol, rich_draw_divination, to_standard_format
    HAS_DIVICAST = True
except ImportError:
    HAS_DIVICAST = False
    logger.info("divicast not available")


@register_system
class SixLineWrapper(SymbolicSystemWrapper):
    """Wrapper for Six-Line (Liu Yao) divination via divicast."""
    SYSTEM_ID = "sixline"
    LIBRARY_BACKEND = "divicast"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}

        if not HAS_DIVICAST:
            return self._fallback(entropy_packet, params)

        try:
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            try:
                import random
                rng = random.Random(seed)
            except Exception as e:
                logger.warning("random initialization failed: %s", e)
                return self._fallback(entropy_packet, params)

            d = DivinatorySymbol.create()

            try:
                std = to_standard_format(d)
                raw_data = std.model_dump(exclude_none=True) if hasattr(std, 'model_dump') else {}
            except Exception:
                raw_data = {"description": str(d)}

            numeric_projection = [
                rng.random(),
                rng.random(),
                rng.random(),
                hash(str(raw_data)) % 1000 / 1000.0,
            ]

            symbolic_state = {
                "method": "sixline",
                "source": "divicast",
                "raw": raw_data,
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features={"method": "sixline", "lines": 6},
                raw_output=raw_data,
                params=params,
            )
        except Exception as e:
            logger.warning(f"divicast sixline failed: {e}")
            return self._fallback(entropy_packet, params)

    def _fallback(self, entropy_packet: dict, params: dict) -> SymbolicOutput:
        try:
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            import random
            rng = random.Random(seed)

            lines = [rng.choice([6, 7, 8, 9]) for _ in range(6)]
            yin_yang = [1 if l in (7, 9) else 0 for l in lines]

            numeric_projection = [l / 9.0 for l in lines]
            symbolic_state = {"lines": lines, "yin_yang": yin_yang, "method": "sixline_fallback"}

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features={"method": "sixline_fallback"},
                raw_output={"lines": lines},
                params=params,
            )
        except Exception as e:
            logger.warning("divicast fallback failed: %s", e)
            return {"error": str(e)}
