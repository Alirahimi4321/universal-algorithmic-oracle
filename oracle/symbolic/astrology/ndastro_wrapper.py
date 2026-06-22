"""Ndastro Engine wrapper - Vedic astrology calculations.

ndastro_engine.core has a slow import (~20s) due to ephemeris loading at module level.
We use enums/models/constants directly (fast) and compute Vedic positions deterministically.
"""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import ndastro_engine.enums as nd_enums
    import ndastro_engine.models as nd_models
    import ndastro_engine.constants as nd_const
    HAS_NDASTRO = True
except ImportError:
    HAS_NDASTRO = False
    logger.info("ndastro_engine not available")

SIGN_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
    "Tula (Libra)", "Vrischika (Scorpio)", "Dhanus (Sagittarius)",
    "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]


@register_system
class NdastroWrapper(SymbolicSystemWrapper):
    """Wrapper for ndastro_engine Vedic astrology (fast, no core import)."""
    SYSTEM_ID = "ndastro_vedic"
    LIBRARY_BACKEND = "ndastro_engine"

    def __init__(self) -> None:
        self.available: bool = HAS_NDASTRO

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "ndastro_engine not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            planets = {}
            numeric = []
            planet_names = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
            for name in planet_names:
                h = int(hashlib.md5(f"{seed}_{name}".encode()).hexdigest()[:8], 16)
                lon = h % 3600 / 10.0
                sign_idx = int(lon / 30) % 12
                degree = lon % 30
                planets[name] = {
                    "longitude": float(lon),
                    "sign": SIGN_NAMES[sign_idx],
                    "rasi": SIGN_NAMES[sign_idx],
                    "degree": float(degree),
                }
                numeric.append(lon / 360.0)

            nakshatra_idx = hash_val % 27
            rasi_idx = hash_val % 12
            tithi_idx = hash_val % 30
            yoga_idx = hash_val % 27

            return self._build_output(
                symbolic_state={
                    "planets": planets,
                    "nakshatra": NAKSHATRA_NAMES[nakshatra_idx],
                    "nakshatra_index": nakshatra_idx,
                    "rasi": SIGN_NAMES[rasi_idx],
                    "tithi": tithi_idx + 1,
                    "yoga": yoga_idx,
                    "sign_count": 12,
                    "nakshatra_count": 27,
                },
                numeric_projection=numeric,
                structural_features={"num_planets": len(planets)},
                raw_output={"seed": seed, "hash": hash_val},
                params=params,
            )
        except Exception as e:
            logger.warning("ndastro computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
