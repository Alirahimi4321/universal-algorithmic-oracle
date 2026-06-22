"""Rokh library wrapper - Persian/Islamic/Gregorian calendar events."""
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
    import rokh
    from rokh.params import DateSystem
    HAS_ROKH = True
except ImportError:
    HAS_ROKH = False
    logger.info("rokh not available")


@register_system
class RokhWrapper(SymbolicSystemWrapper):
    """Wrapper for Rokh calendar events (Jalali/Hijri/Gregorian)."""
    SYSTEM_ID = "rokh_events"
    LIBRARY_BACKEND = "rokh"

    def __init__(self) -> None:
        self.available: bool = HAS_ROKH

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "rokh not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        day = entropy_packet.get("day", rng.randint(1, 28))
        month = entropy_packet.get("month", rng.randint(1, 12))
        year = entropy_packet.get("year", 1403)
        date_system_str = entropy_packet.get("date_system", "jalali")

        try:
            date_system_map = {
                "jalali": DateSystem.JALALI,
                "hijri": DateSystem.HIJRI,
                "gregorian": DateSystem.GREGORIAN,
            }
            date_system = date_system_map.get(date_system_str, DateSystem.JALALI)

            events = rokh.get_events(
                day=day,
                month=month,
                year=year,
                input_date_system=date_system,
            )

            all_events = []
            for key, val in events.items():
                if isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        if isinstance(sub_val, list):
                            for item in sub_val:
                                if isinstance(item, dict):
                                    all_events.append(item.get("title", str(item)))
                                else:
                                    all_events.append(str(item))
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            all_events.append(item.get("title", str(item)))
                        else:
                            all_events.append(str(item))

            event_hash = int(hashlib.sha256(str(all_events).encode()).hexdigest()[:8], 16)

            numeric_projection = [
                day / 31.0,
                month / 12.0,
                (event_hash % 1000) / 1000.0,
                len(all_events) / 10.0,
                rng.random(),
            ]

            symbolic_state = {
                "date_system": date_system_str,
                "day": day,
                "month": month,
                "year": year,
                "event_count": len(all_events),
                "events": all_events[:10],
            }

            structural_features = {
                "event_density": len(all_events) / 10.0,
                "event多样性": len(set(all_events)) / max(len(all_events), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output=events,
                params=params,
            )
        except Exception as e:
            logger.warning(f"rokh computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
