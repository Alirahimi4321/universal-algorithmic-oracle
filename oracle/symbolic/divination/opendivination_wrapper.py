"""OpenDivination wrapper - I Ching divination with proper entropy sources.

Uses opendivination.oracles.iching for authentic I Ching readings with
cryptographic entropy sources and provenance tracking.
"""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from opendivination.oracles.iching import draw_iching_sync
    from opendivination.types import ICMethod, LineType
    HAS_OPENDIVINATION = True
except ImportError:
    HAS_OPENDIVINATION = False
    logger.info("opendivination not available")

METHOD_MAP = {
    "three_coin": ICMethod.THREE_COIN if HAS_OPENDIVINATION else None,
    "yarrow": ICMethod.YARROW if HAS_OPENDIVINATION else None,
    "uniform": ICMethod.UNIFORM if HAS_OPENDIVINATION else None,
}


@register_system
class OpenDivinationWrapper(SymbolicSystemWrapper):
    """Wrapper for opendivination I Ching readings."""
    SYSTEM_ID = "opendivination_iching"
    LIBRARY_BACKEND = "opendivination"

    def __init__(self) -> None:
        self.available: bool = HAS_OPENDIVINATION

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "opendivination not available"}, params)

        try:
            method_name = "three_coin"
            if params and "method" in params:
                method_name = params["method"]

            method = METHOD_MAP.get(method_name, ICMethod.THREE_COIN)

            draw = draw_iching_sync(method=method)

            lines = [lt.value for lt in draw.lines]
            changing = list(draw.changing_lines)

            primary = draw.primary
            primary_info = {
                "number": primary.number if hasattr(primary, 'number') else 0,
                "symbol": primary.symbol if hasattr(primary, 'symbol') else "",
                "description": (primary.description[:200] if hasattr(primary, 'description')
                                and primary.description else ""),
            }

            secondary_info = None
            if draw.secondary is not None:
                sec = draw.secondary
                secondary_info = {
                    "number": sec.number if hasattr(sec, 'number') else 0,
                    "symbol": sec.symbol if hasattr(sec, 'symbol') else "",
                }

            numeric = [l / 9.0 for l in lines]
            numeric.extend([len(changing) / 6.0, 1.0 if changing else 0.0])

            return self._build_output(
                symbolic_state={
                    "method": method_name,
                    "primary_hexagram": primary_info,
                    "secondary_hexagram": secondary_info,
                    "lines": lines,
                    "changing_lines": changing,
                    "line_types": [lt.name for lt in draw.lines],
                },
                numeric_projection=numeric,
                structural_features={
                    "num_lines": len(lines),
                    "num_changing": len(changing),
                    "has_secondary": secondary_info is not None,
                    "method": method_name,
                },
                raw_output={"lines": lines, "changing": changing},
                params=params,
            )
        except Exception as e:
            logger.warning("opendivination computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
