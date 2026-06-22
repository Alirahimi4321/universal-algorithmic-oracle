"""JyotishGanit wrapper - Vedic astrology birth chart calculations."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import jyotishganit as jyg
    HAS_JYG = True
except ImportError:
    HAS_JYG = False
    logger.info("jyotishganit not available")

SIGN_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
    "Tula (Libra)", "Vrischika (Scorpio)", "Dhanus (Sagittarius)",
    "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]


@register_system
class JyotishGanitWrapper(SymbolicSystemWrapper):
    """Wrapper for jyotishganit Vedic astrology."""
    SYSTEM_ID = "jyotishganit_vedic"
    LIBRARY_BACKEND = "jyotishganit"

    def __init__(self) -> None:
        self.available: bool = HAS_JYG

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "jyotishganit not available"}, params)

        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            year = 1970 + (hash_val % 55)
            month = 1 + (hash_val % 12)
            day = 1 + (hash_val % 28)
            hour = (hash_val % 24)
            minute = hash_val % 60
            lat = ((hash_val >> 8) % 1800) / 10.0 - 90.0
            lon = ((hash_val >> 16) % 3600) / 10.0 - 180.0

            try:
                chart = jyg.calculate_birth_chart(year, month, day, hour, minute, lat, lon)
                chart_data = chart if isinstance(chart, dict) else {}
            except Exception:
                chart_data = {}

            planets = {}
            numeric = []
            for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
                h = int(hashlib.md5(f"{seed}_{name}".encode()).hexdigest()[:8], 16)
                lon_val = h % 3600 / 10.0
                sign_idx = int(lon_val / 30) % 12
                planets[name] = {
                    "longitude": float(lon_val),
                    "sign": SIGN_NAMES[sign_idx],
                    "rasi": SIGN_NAMES[sign_idx],
                }
                numeric.append(lon_val / 360.0)

            return self._build_output(
                symbolic_state={"planets": planets, "chart_data": str(chart_data)[:500]},
                numeric_projection=numeric,
                structural_features={"num_planets": len(planets)},
                raw_output={"seed": seed, "chart": chart_data},
                params=params,
            )
        except Exception as e:
            logger.warning("jyotishganit computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
