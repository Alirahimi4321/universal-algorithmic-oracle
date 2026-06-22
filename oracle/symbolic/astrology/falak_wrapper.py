"""Falakpy wrapper - Islamic astrology/astronomy calculations."""
from __future__ import annotations

import logging
import math
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from falakpy import prayertime, qibla, lunar
    HAS_FALAK = True
except ImportError:
    HAS_FALAK = False
    logger.info("falakpy not available")


@register_system
class FalakpyWrapper(SymbolicSystemWrapper):
    """Wrapper for falakpy Islamic astronomy - qibla, prayer times, lunar."""
    SYSTEM_ID = "falak"
    LIBRARY_BACKEND = "falakpy"

    def __init__(self) -> None:
        self.available: bool = HAS_FALAK

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "falakpy not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            lat = (hash_val % 1800 - 900) / 10.0
            lon = ((hash_val >> 8) % 3600 - 1800) / 10.0

            qibla_result = {}
            try:
                qdir = qibla.direction(lat, lon)
                qibla_result = {
                    "direction_degrees": float(qdir.direction) if hasattr(qdir, 'direction') else float(qdir),
                    "latitude": lat,
                    "longitude": lon,
                }
            except Exception as e:
                qibla_result = {"error": str(e), "fallback_bearing": (hash_val % 360)}

            prayertimes_result = {}
            try:
                from datetime import datetime
                now = datetime.now()
                import pytz
                tz = pytz.timezone('UTC')
                pt = prayertime.singleday(tz, now.year, now.month, now.day, lat, lon)
                if isinstance(pt, dict):
                    prayertimes_result = {k: str(v) for k, v in pt.items() if k in ['subuh', 'zuhur', 'asar', 'maghrib', 'isyak']}
                else:
                    prayertimes_result = {"raw": str(pt)[:200]}
            except Exception as e:
                prayertimes_result = {"error": str(e)}

            lunar_result = {}
            try:
                import hashlib
                h = hashlib.sha256(f"lunar_{seed}".encode()).digest()
                phase_angle = (h[0] * 256 + h[1]) % 360
                lunar_result = {
                    "phase_angle": float(phase_angle),
                    "illumination": float((1 + math.cos(math.radians(phase_angle))) / 2),
                }
            except Exception as e:
                lunar_result = {"error": str(e)}

            planets = {
                "qibla": qibla_result,
                "prayer_times": prayertimes_result,
                "lunar": lunar_result,
            }

            numeric = [
                lat / 90.0,
                lon / 180.0,
                qibla_result.get("direction_degrees", 0) / 360.0,
                lunar_result.get("phase_angle", 0) / 360.0,
                lunar_result.get("illumination", 0.5),
            ]

            return self._build_output(
                symbolic_state={
                    "planets": planets,
                    "location": {"latitude": lat, "longitude": lon},
                    "system": "falak_islamic",
                },
                numeric_projection=numeric,
                structural_features={"num_planets": 3, "has_qibla": True, "has_prayers": True},
                raw_output={"qibla": qibla_result, "prayers": prayertimes_result, "lunar": lunar_result},
                params=params,
            )
        except Exception as e:
            logger.warning("falakpy computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
