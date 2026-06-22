"""Maya calendar wrappers - mayacal and MayaCalendar."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import mayacal
    HAS_MAYACAL = True
except ImportError:
    HAS_MAYACAL = False
    logger.info("mayacal not available")

try:
    from MayaCalendar import MayanDate
    HAS_MAYACALENDAR = True
except ImportError:
    HAS_MAYACALENDAR = False
    logger.info("MayaCalendar not available")


@register_system
class MayacalWrapper:
    """Wrapper for mayacal Maya calendar calculations."""
    SYSTEM_ID = "mayacal"

    def __init__(self) -> None:
        self.available: bool = HAS_MAYACAL

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="mayacal", raw_output={"error": "mayacal not available"})

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="mayacal", raw_output={"error": str(e)})

        try:
            from datetime import datetime
            today = datetime.now()

            lc = mayacal.kin_to_long_count(1000000)
            md = mayacal.Mayadate(lc)
            cr = md.calendar_round

            numeric = [
                md.get_total_kin() % 13 / 13.0,
                cr.tzolkin.tzolkin_num / 20.0,
                cr.haab.month_number / 19.0,
                cr.haab.haab_num / 20.0,
            ]

            symbolic_state = {
                "total_kin": md.get_total_kin(),
                "tzolkin": f"{cr.tzolkin.day_name} {cr.tzolkin.tzolkin_num}",
                "haab": f"{cr.haab.month_name} {cr.haab.haab_num}",
                "long_count": str(lc) if lc else "",
            }

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="mayacal",
                symbolic_state=symbolic_state,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"mayacal computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="mayacal", raw_output={"error": str(e)})
