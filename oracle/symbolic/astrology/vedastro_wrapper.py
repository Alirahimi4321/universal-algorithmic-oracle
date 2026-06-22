"""VedAstro wrapper - Vedic astrology calculations."""
from __future__ import annotations

import logging
import hashlib
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from vedastro import Calculate, GeoLocation, Time
    HAS_VEDASTRO = True
except ImportError:
    HAS_VEDASTRO = False
    logger.info("VedAstro not available")


@register_system
class VedAstroWrapper(SymbolicSystemWrapper):
    """Wrapper for VedAstro Vedic astrology - planetary positions, nakshatra, tithi."""
    SYSTEM_ID = "vedastro"
    LIBRARY_BACKEND = "vedastro"

    def __init__(self) -> None:
        self.available: bool = HAS_VEDASTRO

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "VedAstro not available"}, params)

        try:
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            lat = (hash_val % 1800 - 900) / 10.0
            lon = ((hash_val >> 8) % 3600 - 1800) / 10.0

            try:
                geoloc = GeoLocation(f"Loc_{seed}", lat, lon)
            except Exception:
                geoloc = GeoLocation("Default", 28.6139, 77.2090)

            from datetime import datetime
            now = datetime.now()
            try:
                time_obj = Time(f"{now.year}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}")
            except Exception:
                time_obj = Time("2024-01-01 12:00")

            planets = {}
            numeric = []
            planet_names = [
                ("Sun", "sun"), ("Moon", "moon"), ("Mercury", "mercury"),
                ("Venus", "venus"), ("Mars", "mars"), ("Jupiter", "jupiter"),
                ("Saturn", "saturn"), ("Rahu", "rahu"), ("Ketu", "ketu"),
            ]

            for ved_name, key in planet_names:
                try:
                    longitude = Calculate.PlanetNirayanaLongitude(time_obj, geoloc, ved_name)
                    sign = Calculate.PlanetRasiSign(time_obj, geoloc, ved_name)
                    constellation = Calculate.PlanetConstellation(time_obj, geoloc, ved_name)
                    planets[key] = {
                        "longitude": float(longitude) if longitude else 0.0,
                        "sign": str(sign) if sign else "unknown",
                        "constellation": str(constellation) if constellation else "unknown",
                    }
                    numeric.append(float(longitude) / 360.0 if longitude else 0.0)
                except Exception as e:
                    planets[key] = {"error": str(e)}
                    numeric.append(0.0)

            try:
                lagna = Calculate.LagnaSignName(time_obj, geoloc)
                planets["lagna"] = {"sign": str(lagna) if lagna else "unknown"}
            except Exception:
                planets["lagna"] = {"sign": "unknown"}

            try:
                moon_sign = Calculate.MoonSignName(time_obj, geoloc)
                planets["moon_sign"] = {"sign": str(moon_sign) if moon_sign else "unknown"}
            except Exception:
                planets["moon_sign"] = {"sign": "unknown"}

            try:
                tithi = Calculate.LunarDay(time_obj, geoloc)
                planets["tithi"] = {"value": str(tithi) if tithi else "unknown"}
            except Exception:
                planets["tithi"] = {"value": "unknown"}

            return self._build_output(
                symbolic_state={
                    "planets": planets,
                    "system": "vedic_astrology",
                    "location": {"latitude": lat, "longitude": lon},
                },
                numeric_projection=numeric,
                structural_features={"num_planets": len(planets), "has_lagna": True},
                raw_output={"time": str(now), "location": {"lat": lat, "lon": lon}},
                params=params,
            )
        except Exception as e:
            logger.warning("VedAstro computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
