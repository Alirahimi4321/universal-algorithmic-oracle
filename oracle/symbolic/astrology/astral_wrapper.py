"""Astral library wrapper - solar/lunar calculations and twilight times."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from astral import LocationInfo
    from astral.sun import sun, dawn, dusk, golden_hour, blue_hour
    HAS_ASTRAL = True
except ImportError:
    HAS_ASTRAL = False
    logger.info("astral not available")


@register_system
class AstralWrapper:
    """Wrapper for astral solar/lunar calculations."""
    SYSTEM_ID = "astral"

    def __init__(self) -> None:
        self.available: bool = HAS_ASTRAL

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="astral", raw_output={"error": "astral not available"})

        import hashlib, random
        seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
        rng = random.Random(seed)

        from datetime import datetime
        try:
            loc = LocationInfo(
                name="Oracle",
                region="World",
                timezone="UTC",
                latitude=rng.uniform(-90, 90),
                longitude=rng.uniform(-180, 180),
            )
            s = sun(loc.observer, date=datetime.now(), tzinfo=None)

            result = {}
            for key, val in s.items():
                if hasattr(val, 'timestamp'):
                    result[key] = val.timestamp()
                else:
                    result[key] = float(val)

            result["latitude"] = loc.latitude
            result["longitude"] = loc.longitude

            numeric = [
                result.get("sunrise", 0) / 86400.0,
                result.get("sunset", 0) / 86400.0,
                result.get("noon", 0) / 86400.0,
                loc.latitude / 90.0,
                loc.longitude / 180.0,
            ]

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="astral",
                symbolic_state=result,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"astral computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="astral", raw_output={"error": str(e)})
