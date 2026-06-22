"""Stellium astrology wrapper - structured chart generation with bazi integration."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from stellium import ChartBuilder, ChartDateTime, ChartLocation
    import swisseph as swe
    HAS_STELLIUM = True
except ImportError:
    HAS_STELLIUM = False
    logger.info("stellium not available")

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


@register_system
class StelliumWrapper(SymbolicSystemWrapper):
    """Wrapper for stellium astrology chart generation."""
    SYSTEM_ID = "stellium_astrology"
    LIBRARY_BACKEND = "stellium"

    def __init__(self) -> None:
        self.available: bool = HAS_STELLIUM

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "stellium not available"}, params)

        try:
            import hashlib
            from datetime import datetime, timezone
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            jd = 2451545.0 + (hash_val % 40000)
            year = 2000 + (hash_val % 50)
            month = 1 + (hash_val % 12)
            day = 1 + (hash_val % 28)
            hour = hash_val % 24

            dt = datetime(year, month, day, hour, 0, tzinfo=timezone.utc)
            jd_calc = swe.julday(dt.year, dt.month, dt.day, dt.hour)
            cdt = ChartDateTime(utc_datetime=dt, julian_day=jd_calc)

            lat = ((hash_val >> 8) % 1800) / 10.0 - 90.0
            lon = ((hash_val >> 16) % 3600) / 10.0 - 180.0
            loc = ChartLocation(lat, lon, name="computed")

            chart = ChartBuilder(cdt, loc).calculate()

            planets = {}
            numeric = []
            for p in chart.get_planets():
                name = p.name if hasattr(p, 'name') else str(p)
                lon_val = p.longitude if hasattr(p, 'longitude') else 0.0
                sign_idx = int(lon_val / 30) % 12
                planets[name.lower()] = {
                    "longitude": float(lon_val),
                    "sign": SIGN_NAMES[sign_idx],
                    "degree": float(lon_val % 30),
                }
                numeric.append(lon_val / 360.0)

            aspects = []
            for a in chart.aspects:
                aspects.append({
                    "planet1": str(getattr(a, 'planet1', '')),
                    "planet2": str(getattr(a, 'planet2', '')),
                    "aspect": str(getattr(a, 'aspect', '')),
                    "angle": float(getattr(a, 'angle', 0)),
                })

            return self._build_output(
                symbolic_state={"planets": planets, "aspects": aspects[:20]},
                numeric_projection=numeric,
                structural_features={"num_planets": len(planets), "num_aspects": len(aspects)},
                raw_output={"jd": jd_calc, "lat": lat, "lon": lon},
                params=params,
            )
        except Exception as e:
            logger.warning("stellium computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
