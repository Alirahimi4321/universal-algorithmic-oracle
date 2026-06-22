"""Astronomical calculations wrapper using astropy."""
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HAS_ASTROPY = False
try:
    import astropy
    from astropy import coordinates as coords
    from astropy import units as u
    from astropy.time import Time
    HAS_ASTROPY = True
except ImportError:
    pass


class AstropyAnalyzer:
    """Astronomical calculations using astropy."""

    def __init__(self):
        self.available = HAS_ASTROPY

    def compute_sidereal_time(self, longitude: float = 0.0, timestamp: float = None) -> dict:
        if not self.available:
            return {"error": "astropy not available"}
        try:
            t = Time(timestamp or time.time(), format='unix')
            lst = t.sidereal_time('apparent', longitude * u.deg)
            return {
                "sidereal_time": str(lst),
                "hours": float(lst.hour),
                "longitude": longitude,
            }
        except Exception as e:
            return {"error": str(e)}

    def compute_planet_positions(self, timestamp: float = None) -> dict:
        if not self.available:
            return {"error": "astropy not available"}
        try:
            t = Time(timestamp or time.time(), format='unix')
            earth = coords.get_body("earth", t)
            result = {"time": str(t.iso)}
            for body_name in ["sun", "moon", "mars", "jupiter", "saturn"]:
                try:
                    body = coords.get_body(body_name, t)
                    result[body_name] = {
                        "ra": float(body.ra.deg),
                        "dec": float(body.dec.deg),
                        "alt": float(body.alt.deg) if hasattr(body, 'alt') else 0,
                    }
                except Exception:
                    result[body_name] = {"ra": 0, "dec": 0, "alt": 0}
            return result
        except Exception as e:
            return {"error": str(e)}
