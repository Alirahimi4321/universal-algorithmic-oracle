"""Purple Star (Ziwei Doushu) astrology wrapper using purplestar library."""
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
    import purplestar
    HAS_PURPLESTAR = True
except ImportError:
    HAS_PURPLESTAR = False
    logger.info("purplestar not available")


@register_system
class PurpleStarWrapper(SymbolicSystemWrapper):
    """Wrapper for Purple Star (Ziwei Doushu) Chinese astrology."""
    SYSTEM_ID = "purplestar"
    LIBRARY_BACKEND = "purplestar"

    def __init__(self) -> None:
        self.available: bool = HAS_PURPLESTAR

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": "purplestar not available"},
            )

        seed = entropy_packet.get("seed", 42)
        rng = random.Random(seed)

        solar_date = entropy_packet.get("solar_date", "2000-01-01")
        gender = entropy_packet.get("gender", "male")
        time_str = entropy_packet.get("time", "12:00")
        timezone = entropy_packet.get("timezone", "UTC")
        place = entropy_packet.get("place", "Unknown")

        try:
            chart = purplestar.generate_chart(
                gender=gender,
                solar_date=solar_date,
                time=time_str,
                timezone=timezone,
                place=place,
            )

            palaces = chart.get("chart", {}).get("palaces", [])
            profile = chart.get("chart", {}).get("profile", {})
            birth_data = chart.get("birth_data", {})

            palace_names = [p.get("palace", "unknown") for p in palaces]
            star_codes = []
            for p in palaces:
                for s in p.get("stars", []):
                    star_codes.append(s.get("code", "unknown"))

            all_values = []
            for i, name in enumerate(palace_names):
                h = int(hashlib.md5(name.encode()).hexdigest()[:4], 16)
                all_values.append(h)
            for i, code in enumerate(star_codes):
                h = int(hashlib.md5(code.encode()).hexdigest()[:4], 16)
                all_values.append(h)

            numeric_projection = []
            for i in range(min(10, max(len(all_values), 1))):
                if i < len(all_values):
                    numeric_projection.append((all_values[i] % 10000) / 10000.0)
                else:
                    numeric_projection.append(rng.random())

            symbolic_state = {
                "chart_type": chart.get("chart_type", "unknown"),
                "life_master": profile.get("life_master", "unknown"),
                "body_master": profile.get("body_master", "unknown"),
                "five_element": profile.get("five_element_bureau", {}).get("key", "unknown"),
                "yin_yang": profile.get("yin_yang", "unknown"),
                "palace_count": len(palaces),
                "star_count": len(star_codes),
                "palaces": palace_names[:12],
                "stars": star_codes[:20],
            }

            structural_features = {
                "palace_density": len(palaces) / 12.0,
                "star_density": len(star_codes) / max(len(palaces), 1),
                "complexity": len(set(star_codes)) / max(len(star_codes), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output=chart,
                params=params,
            )
        except Exception as e:
            logger.warning(f"purplestar computation failed: {e}")
            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend=self.LIBRARY_BACKEND,
                raw_output={"error": str(e)},
            )
