"""PyEphem wrapper - high-precision astronomical calculations."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import ephem
    HAS_EPHEM = True
except ImportError:
    HAS_EPHEM = False
    logger.info("ephem not available")


@register_system
class EphemWrapper:
    """Wrapper for PyEphem astronomical calculations."""
    SYSTEM_ID = "ephem"

    BODIES = {
        "sun": "Sun", "moon": "Moon", "mercury": "Mercury",
        "venus": "Venus", "mars": "Mars", "jupiter": "Jupiter",
        "saturn": "Saturn", "uranus": "Uranus", "neptune": "Neptune",
        "pluto": "Pluto",
    }

    def __init__(self) -> None:
        self.available: bool = HAS_EPHEM

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="ephem", raw_output={"error": "ephem not available"})

        try:
            import hashlib, random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)
        except Exception as e:
            logger.warning("random/hashlib initialization failed: %s", e)
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="ephem", raw_output={"error": str(e)})

        try:
            obs = ephem.Observer()
            obs.lat = str(rng.uniform(-90, 90))
            obs.lon = str(rng.uniform(-180, 180))
            obs.date = ephem.now()

            positions = {}
            for name, attr_name in self.BODIES.items():
                try:
                    BodyClass = getattr(ephem, attr_name)
                    body = BodyClass()
                    body.compute(obs)
                    positions[name] = {
                        "longitude": float(body.hlong) * 180.0 / 3.14159,
                        "latitude": float(body.hlat) * 180.0 / 3.14159,
                        "distance": float(body.earth_distance),
                    }
                except Exception as e:
                    logger.warning("ephem body %s computation failed: %s", name, e)
                    positions[name] = {"error": str(e)}

            numeric = []
            for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
                if name in positions and "longitude" in positions[name]:
                    numeric.append(positions[name]["longitude"] / 360.0)
                else:
                    numeric.append(0.0)

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="ephem",
                symbolic_state=positions,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"ephem computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="ephem", raw_output={"error": str(e)})
