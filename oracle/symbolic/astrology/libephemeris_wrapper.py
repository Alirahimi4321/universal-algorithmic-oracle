"""Libephemeris wrapper - Swiss Ephemeris planetary position calculations.

Uses libephemeris.planets.calc_ut() for precise astronomical calculations.
Downloads ~38MB ephemeris data on first use, then cached.
"""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import libephemeris.planets as le_planets
    import libephemeris as le
    HAS_LIBEPHEMERIS = True
except ImportError:
    HAS_LIBEPHEMERIS = False
    logger.info("libephemeris not available")

PLANET_MAP = {
    "Sun": "SUN", "Moon": "MOON", "Mercury": "MERCURY",
    "Venus": "VENUS", "Mars": "MARS", "Jupiter": "JUPITER",
    "Saturn": "SATURN", "Uranus": "URANUS", "Neptune": "NEPTUNE",
    "Pluto": "PLUTO",
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


@register_system
class LibephemerisWrapper(SymbolicSystemWrapper):
    """Wrapper for libephemeris planetary calculations."""
    SYSTEM_ID = "libephemeris_astrology"
    LIBRARY_BACKEND = "libephemeris"

    def __init__(self) -> None:
        self.available: bool = HAS_LIBEPHEMERIS

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "libephemeris not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            jd = 2451545.0 + (hash_val % 40000)

            planets = {}
            numeric = []
            for name, const_name in PLANET_MAP.items():
                try:
                    planet_id = getattr(le_planets, const_name)
                    pos, flags = le_planets.calc_ut(jd, planet_id)
                    lon = pos[0]
                    lat = pos[1]
                    dist = pos[2]
                    sign_idx = int(lon / 30) % 12
                    degree = lon % 30
                    planets[name] = {
                        "longitude": float(lon),
                        "latitude": float(lat),
                        "distance": float(dist),
                        "sign": SIGN_NAMES[sign_idx],
                        "degree": float(degree),
                    }
                    numeric.append(lon / 360.0)
                except Exception as e:
                    logger.debug("libephemeris calc failed for %s: %s", name, e)
                    planets[name] = {"longitude": 0.0, "latitude": 0.0,
                                      "distance": 0.0, "sign": "Unknown", "degree": 0.0}
                    numeric.append(0.0)

            aspects = []
            aspect_defs = [(0, "Conjunction", 8), (60, "Sextile", 6),
                            (90, "Square", 8), (120, "Trine", 8), (180, "Opposition", 8)]
            names = list(planets.keys())
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    lon1 = planets[names[i]].get("longitude", 0)
                    lon2 = planets[names[j]].get("longitude", 0)
                    diff = abs(lon1 - lon2)
                    if diff > 180:
                        diff = 360 - diff
                    for angle, aname, orb in aspect_defs:
                        if abs(diff - angle) < orb:
                            aspects.append({"planet1": names[i], "planet2": names[j],
                                            "aspect": aname, "angle": float(diff)})

            return self._build_output(
                symbolic_state={"planets": planets, "aspects": aspects},
                numeric_projection=numeric,
                structural_features={
                    "num_planets": len(planets),
                    "num_aspects": len(aspects),
                    "julian_day": jd,
                },
                raw_output={"jd": jd, "seed": seed},
                params=params,
            )
        except Exception as e:
            logger.warning("libephemeris computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
