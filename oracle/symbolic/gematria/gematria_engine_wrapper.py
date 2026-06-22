"""Gematria Engine wrapper - multi-system gematria calculations."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import gematria_engine as ge
    HAS_GEMATRIA_ENGINE = True
except ImportError:
    HAS_GEMATRIA_ENGINE = False
    logger.info("gematria_engine not available")


@register_system
class GematriaEngineWrapper(SymbolicSystemWrapper):
    """Wrapper for gematria_engine multi-system gematria."""
    SYSTEM_ID = "gematria_engine"
    LIBRARY_BACKEND = "gematria_engine"

    def __init__(self) -> None:
        self.available: bool = HAS_GEMATRIA_ENGINE

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "gematria_engine not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            question = entropy_packet.get("question", "") if isinstance(entropy_packet, dict) else ""
            text = question if question else f"oracle-{seed}"

            systems = ge.list_systems() if hasattr(ge, 'list_systems') else []
            results = {}
            numeric = []

            for sys_name in systems:
                try:
                    val = ge.gematria(text, system=sys_name)
                    results[sys_name] = float(val) if val else 0.0
                    numeric.append(float(val) / 10000.0 if val else 0.0)
                except Exception:
                    results[sys_name] = 0.0
                    numeric.append(0.0)

            if not results:
                val = ge.gematria_value(text) if hasattr(ge, 'gematria_value') else hash(text) % 10000
                results["default"] = float(val)
                numeric.append(float(val) / 10000.0)

            breakdown = {}
            if hasattr(ge, 'breakdown'):
                try:
                    breakdown = ge.breakdown(text)
                except Exception:
                    pass

            return self._build_output(
                symbolic_state={"text": text[:200], "systems": results, "breakdown": str(breakdown)[:500]},
                numeric_projection=numeric,
                structural_features={"num_systems": len(results)},
                raw_output={"results": results},
                params=params,
            )
        except Exception as e:
            logger.warning("gematria_engine computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
