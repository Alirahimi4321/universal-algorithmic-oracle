"""MayaCalendar library wrapper - Mayan calendar calculations."""
from __future__ import annotations

import hashlib
import logging
import math
import random
from datetime import datetime
from typing import Optional

from ..base import SymbolicOutput, SymbolicSystemWrapper
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import mayacalendar
    HAS_MAYACALENDAR = True
except ImportError:
    HAS_MAYACALENDAR = False
    logger.info("mayacalendar not available")


@register_system
class MayaCalendarWrapper(SymbolicSystemWrapper):
    """Wrapper for MayaCalendar library - Mayan date calculations."""
    SYSTEM_ID = "mayacalendar_ext"
    LIBRARY_BACKEND = "mayacalendar"

    def __init__(self) -> None:
        self.available: bool = HAS_MAYACALENDAR

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "mayacalendar not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        try:
            now = datetime.now()
            maya_date = mayacalendar.MayaDate(now)

            long_count = mayacalendar.MayaDate.long_count_now()
            tzolkin = mayacalendar.MayaDate.tzolkin_now()
            haab = mayacalendar.MayaDate.haab_now()

            hash_val = int(hashlib.sha256(str(long_count).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                (hash_val % 1000) / 1000.0,
                (long_count.baktun % 20) / 20.0 if hasattr(long_count, 'baktun') else rng.random(),
                (long_count.katun % 20) / 20.0 if hasattr(long_count, 'katun') else rng.random(),
                (long_count.tun % 20) / 20.0 if hasattr(long_count, 'tun') else rng.random(),
                rng.random(),
            ]

            symbolic_state = {
                "long_count": str(long_count),
                "tzolkin": str(tzolkin),
                "haab": str(haab),
                "baktun": getattr(long_count, 'baktun', None),
                "katun": getattr(long_count, 'katun', None),
                "tun": getattr(long_count, 'tun', None),
                "uinal": getattr(long_count, 'uinal', None),
                "kin": getattr(long_count, 'kin', None),
            }

            structural_features = {
                "calendar_depth": 5,
                "cycle_position": rng.random(),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"long_count": str(long_count), "tzolkin": str(tzolkin), "haab": str(haab)},
                params=params,
            )
        except Exception as e:
            logger.warning(f"mayacalendar computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
