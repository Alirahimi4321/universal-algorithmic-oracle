"""I Ching library wrapper - additional I Ching calculations."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import iching
    HAS_ICHING = True
except ImportError:
    HAS_ICHING = False
    logger.info("iching not available")


@register_system
class IChingLibWrapper:
    """Wrapper for iching library (complements ichingpy)."""
    SYSTEM_ID = "iching_lib"

    def __init__(self) -> None:
        self.available: bool = HAS_ICHING

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="iching", raw_output={"error": "iching not available"})

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="iching", raw_output={"error": str(e)})

        try:
            from iching import iching as iching_mod
            yao_list = iching_mod.sixYao()

            numeric = [
                yao / 9.0 for yao in yao_list
            ]

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="iching",
                symbolic_state={"yao_list": yao_list},
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"iching computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="iching", raw_output={"error": str(e)})
