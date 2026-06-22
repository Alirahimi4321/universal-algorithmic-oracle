"""Astronomy wrapper using ketu - pure NumPy astronomical calculations."""
from __future__ import annotations

import logging
from typing import Any, Optional

try:
    import numpy as np
    from numpy.typing import ArrayLike
except ImportError:
    np = None
    ArrayLike = None
    logger.info("numpy not available")

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from ketu.ephemeris import calculate_all_positions, find_all_aspects
    HAS_KETU = True
except ImportError:
    HAS_KETU = False
    logger.info("ketu not available")


@register_system
class KetuAstronomyWrapper(SymbolicSystemWrapper):
    """Wrapper for ketu astronomical calculations."""
    SYSTEM_ID = "ketu_astronomy"
    LIBRARY_BACKEND = "ketu"

    ASPECTS = {
        0: "conjunction", 60: "sextile", 90: "square",
        120: "trine", 180: "opposition",
    }

    def __init__(self) -> None:
        self.available: bool = HAS_KETU

    def compute_positions(self, jd: float) -> dict[str, Any]:
        if not HAS_KETU:
            return {"error": "ketu not available"}
        try:
            positions = calculate_all_positions(jd)
            result = {}
            for name, pos in positions.items():
                result[name.lower()] = {
                    "longitude": float(pos[0]),
                    "latitude": float(pos[1]),
                    "distance": float(pos[2]),
                }
            return result
        except Exception as e:
            logger.warning(f"ketu position computation failed: {e}")
            return {"error": str(e)}

    def compute_aspects(self, jd: float, orb_threshold: float = 8.0) -> list[dict[str, Any]]:
        if not HAS_KETU:
            return []
        try:
            results = []
            body_pairs = [
                (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
                (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            ]
            for b1, b2 in body_pairs:
                aspects = find_all_aspects(jd, jd + 365, b1, b2)
                for jd_asp, angle in aspects:
                    if angle > 180:
                        angle = 360 - angle
                    aspect_name = self.ASPECTS.get(round(angle / 30) * 30, "unknown")
                    if aspect_name != "unknown":
                        results.append({
                            "planet1": str(b1),
                            "planet2": str(b2),
                            "aspect": aspect_name,
                            "angle": float(angle),
                        })
            return results[:20]
        except Exception as e:
            logger.warning(f"ketu aspect computation failed: {e}")
            return []

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        try:
            result = self.compute_from_entropy(entropy_packet)
            positions = result.get("positions", {})
            numeric = self.get_numeric_projection(positions)
            return self._build_output(
                symbolic_state=result,
                numeric_projection=numeric,
                structural_features={"has_aspects": len(result.get("aspects", [])) > 0},
                raw_output=result,
                params=params,
            )
        except Exception as e:
            logger.warning("ketu compute failed: %s", e)
            return {"error": str(e)}

    def compute_from_entropy(self, entropy_packet: dict) -> dict[str, Any]:
        try:
            import hashlib
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)
            jd = 2451545.0 + (hash_val % 40000)
            positions = self.compute_positions(jd)
            aspects = self.compute_aspects(jd)
            return {"julian_day": jd, "positions": positions, "aspects": aspects}
        except Exception as e:
            logger.warning("ketu entropy computation failed: %s", e)
            return {"error": str(e)}

    def get_numeric_projection(self, positions: dict[str, Any]) -> list[float]:
        projection = []
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            if name in positions:
                lon = positions[name].get("longitude", 0)
                projection.append(lon / 360.0)
            else:
                projection.append(0.0)
        return projection
