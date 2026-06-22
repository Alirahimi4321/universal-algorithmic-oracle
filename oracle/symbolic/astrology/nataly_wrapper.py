"""Nataly wrapper: Professional natal chart calculations using Swiss Ephemeris."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_NATALY = False
try:
    from nataly.chart import NatalChart as _NatalChart
    HAS_NATALY = True
except ImportError:
    pass


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class NatalyWrapper(SymbolicSystemWrapper):
    """Natal chart calculation using nataly library with Swiss Ephemeris."""
    SYSTEM_ID = "nataly_natal"
    LIBRARY_BACKEND = "nataly"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        lat = params.get("lat", entropy_packet.get("lat", 40.7128))
        lon = params.get("lon", entropy_packet.get("lon", -74.0060))
        name = params.get("name", "oracle_subject")

        if HAS_NATALY:
            try:
                chart = _NatalChart(
                    person_name=name,
                    dt_utc=dt,
                    lat=float(lat),
                    lon=float(lon),
                )

                planets = chart.get_planets()
                asteroids = chart.get_asteroids()
                axes = chart.get_axes()
                luminaries = chart.get_luminaries()

                planet_data = []
                for p in planets:
                    retro = p.is_retrograde
                    planet_data.append({
                        "name": p.name,
                        "sign": p.sign.name if p.sign else "",
                        "longitude": round(p.longitude, 4),
                        "declination": round(p.declination, 4),
                        "retrograde": retro,
                        "house": p.house,
                        "dignity": p.dignity,
                        "speed": round(p.speed, 4),
                    })

                asteroid_data = []
                for a in asteroids:
                    asteroid_data.append({
                        "name": a.name,
                        "sign": a.sign.name if a.sign else "",
                        "longitude": round(a.longitude, 4),
                        "retrograde": a.is_retrograde,
                    })

                axis_data = []
                for ax in axes:
                    axis_data.append({
                        "name": ax.name,
                        "sign": ax.sign.name if ax.sign else "",
                        "longitude": round(ax.longitude, 4),
                    })

                retro_count = sum(1 for p in planet_data if p["retrograde"])

                symbolic_state = {
                    "planet_count": len(planet_data),
                    "planets": planet_data,
                    "asteroids": asteroid_data,
                    "axes": axis_data,
                    "luminaries": [l.name for l in luminaries],
                    "retrograde_count": retro_count,
                    "sun_sign": planet_data[0]["sign"] if planet_data else "",
                    "moon_sign": planet_data[1]["sign"] if len(planet_data) > 1 else "",
                    "rising_sign": axis_data[0]["sign"] if axis_data else "",
                    "location": {"lat": float(lat), "lon": float(lon)},
                    "utc_time": dt.isoformat(),
                }

                numeric_projection = [
                    hash(planet_data[0]["sign"]) % 12 if planet_data else 0,
                    hash(planet_data[1]["sign"]) % 12 if len(planet_data) > 1 else 0,
                    hash(axis_data[0]["sign"]) % 12 if axis_data else 0,
                    planet_data[0]["longitude"] % 30 if planet_data else 0,
                    planet_data[1]["longitude"] % 30 if len(planet_data) > 1 else 0,
                    retro_count,
                    len(planet_data),
                    len(asteroid_data),
                    dt.year % 100,
                    dt.month % 12,
                    dt.day % 30,
                ]

                structural_features = {
                    "planet_count": len(planet_data),
                    "asteroid_count": len(asteroid_data),
                    "axis_count": len(axis_data),
                    "retrograde_count": retro_count,
                    "has_aspects": hasattr(chart, 'get_aspects'),
                    "time_precision": "minute",
                    "backend": "nataly",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"chart_str": str(chart)},
                    params=params,
                )
            except Exception as e:
                logger.warning("nataly compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "planet_count": 0,
            "planets": [],
            "asteroids": [],
            "axes": [],
            "luminaries": [],
            "retrograde_count": 0,
            "sun_sign": "",
            "moon_sign": "",
            "rising_sign": "",
            "backend": "nataly_fallback",
        }
        numeric_projection = [0, 0, 0, 0, 0, 0, 0, 0, dt.year % 100, dt.month % 12, dt.day % 30]
        structural_features = {
            "planet_count": 0,
            "asteroid_count": 0,
            "axis_count": 0,
            "retrograde_count": 0,
            "has_aspects": False,
            "time_precision": "minute",
            "backend": "fallback",
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
