"""SXTWL wrapper - Chinese calendar/lunar calculations."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import sxtwl
    HAS_SXTWL = True
except ImportError:
    HAS_SXTWL = False
    logger.info("sxtwl not available")


@register_system
class SxtwlWrapper:
    """Wrapper for sxtwl Chinese calendar calculations."""
    SYSTEM_ID = "sxtwl"

    def __init__(self) -> None:
        self.available: bool = HAS_SXTWL

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="sxtwl", raw_output={"error": "sxtwl not available"})

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="sxtwl", raw_output={"error": str(e)})

        try:
            from datetime import datetime
            today = datetime.now()
            day = sxtwl.fromSolar(today.year, today.month, today.day)

            gz = day.getYearGZ()
            heavenly_stem = gz.tg
            earthly_branch = gz.dz

            numeric = [
                heavenly_stem / 10.0,
                earthly_branch / 12.0,
                day.getLunarMonth() / 12.0,
                day.getLunarDay() / 30.0,
                rng.random(),
            ]

            symbolic_state = {
                "heavenly_stem": heavenly_stem,
                "earthly_branch": earthly_branch,
                "lunar_month": day.getLunarMonth(),
                "lunar_day": day.getLunarDay(),
                "is_leap": day.isLunarLeap(),
            }

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="sxtwl",
                symbolic_state=symbolic_state,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"sxtwl computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="sxtwl", raw_output={"error": str(e)})
