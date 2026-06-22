"""Flatlib astrology wrapper - Western astrological chart calculations.

flatlib.Chart has a bug with swisseph compatibility, so we use swisseph directly
and flatlib.const for astrological constants.
"""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False
    logger.info("swisseph not available")

try:
    import flatlib.const as flconst
    HAS_FLATLIB = True
except ImportError:
    HAS_FLATLIB = False
    logger.info("flatlib not available")

PLANETS = {
    "Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3,
    "Mars": 4, "Jupiter": 5, "Saturn": 6,
    "Uranus": 7, "Neptune": 8, "Pluto": 9, "Chiron": 15,
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

HOUSE_SYSTEMS = {"placidus": b"P", "koch": b"K", "equal": b"A",
                  "whole_sign": b"W", "porphyrius": b"O"}


@register_system
class FlatlibWrapper(SymbolicSystemWrapper):
    """Wrapper for flatlib/swisseph Western astrology."""
    SYSTEM_ID = "flatlib_astrology"
    LIBRARY_BACKEND = "flatlib+swisseph"

    def __init__(self) -> None:
        self.available: bool = HAS_SWISSEPH

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "swisseph not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            jd = 2451545.0 + (hash_val % 40000)
            lat = ((hash_val >> 8) % 1800) / 10.0 - 90.0
            lon = ((hash_val >> 16) % 3600) / 10.0 - 180.0

            planets = {}
            numeric = []
            for name, pid in PLANETS.items():
                try:
                    pos, _ = swe.calc_ut(jd, pid)
                    lon_val = pos[0]
                    sign_idx = int(lon_val / 30) % 12
                    degree = lon_val % 30
                    planets[name] = {
                        "longitude": float(lon_val),
                        "sign": SIGN_NAMES[sign_idx],
                        "degree": float(degree),
                    }
                    numeric.append(lon_val / 360.0)
                except Exception:
                    planets[name] = {"longitude": 0.0, "sign": "Unknown", "degree": 0.0}
                    numeric.append(0.0)

            house_cusps = {}
            try:
                houses, ascmc = swe.houses(jd, lat, lon, b"P")
                for i, h in enumerate(houses, 1):
                    house_cusps[f"House{i}"] = float(h)
                house_cusps["Ascendant"] = float(ascmc[0])
                house_cusps["MC"] = float(ascmc[1])
                numeric.extend([h / 360.0 for h in houses[:12]])
            except Exception:
                pass

            aspects = self._compute_aspects(planets)

            return self._build_output(
                symbolic_state={"planets": planets, "houses": house_cusps, "aspects": aspects},
                numeric_projection=numeric,
                structural_features={
                    "num_planets": len(planets),
                    "num_houses": len(house_cusps),
                    "num_aspects": len(aspects),
                },
                raw_output={"jd": jd, "lat": lat, "lon": lon},
                params=params,
            )
        except Exception as e:
            logger.warning("flatlib computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)

    def _compute_aspects(self, planets: dict) -> list[dict]:
        aspects = []
        aspect_defs = [(0, "Conjunction", 8), (60, "Sextile", 6), (90, "Square", 8),
                        (120, "Trine", 8), (180, "Opposition", 8)]
        names = list(planets.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                lon1 = planets[names[i]].get("longitude", 0)
                lon2 = planets[names[j]].get("longitude", 0)
                diff = abs(lon1 - lon2)
                if diff > 180:
                    diff = 360 - diff
                for angle, name, orb in aspect_defs:
                    if abs(diff - angle) < orb:
                        aspects.append({"planet1": names[i], "planet2": names[j],
                                        "aspect": name, "angle": float(diff)})
        return aspects
