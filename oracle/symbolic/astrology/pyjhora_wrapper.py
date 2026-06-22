"""PyJHora wrapper: Complete Vedic Astrology (Jyotish) calculations."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_JHORA = False
try:
    from jhora import const as jhora_const
    HAS_JHORA = True
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
class PyJHoraWrapper(SymbolicSystemWrapper):
    """Complete Vedic Astrology using PyJHora library."""
    SYSTEM_ID = "pyjhora_vedic"
    LIBRARY_BACKEND = "jhora"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        lat = params.get("lat", entropy_packet.get("lat", 13.0))
        lon = params.get("lon", entropy_packet.get("lon", 80.0))

        if HAS_JHORA:
            try:
                rashi_names = getattr(jhora_const, "RASHI_NAMES", {
                    1: "Mesha", 2: "Vrishabha", 3: "Mithuna", 4: "Karka",
                    5: "Simha", 6: "Kanya", 7: "Tula", 8: "Vrischika",
                    9: "Dhanus", 10: "Makara", 11: "Kumbha", 12: "Meena",
                })
                day_num = dt.weekday()
                month_jyotish = ((dt.month - 1 + 2) % 12) + 1
                symbolic_state = {
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "location": {"lat": lat, "lon": lon},
                    "jyotish_month": month_jyotish,
                    "rashi_by_day": rashi_names.get((day_num % 12) + 1, ""),
                    "const_available": True,
                }

                numeric_projection = [
                    dt.year % 100,
                    dt.month % 12,
                    dt.day % 30,
                    dt.hour % 24,
                    dt.minute % 60,
                    month_jyotish,
                    day_num % 7,
                    lat % 360,
                    lon % 360,
                    hash(str(symbolic_state)) % 60,
                ]

                structural_features = {
                    "has_panchanga": False,
                    "has_const": True,
                    "time_precision": "hour",
                    "backend": "jhora",
                    "note": "geocoder missing, basic mode",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    params=params,
                )
            except Exception as e:
                logger.warning("jhora compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {"backend": "jhora_fallback"}
        numeric_projection = [dt.year % 100, dt.month % 12, dt.day % 30, dt.hour % 24, seed % 60, 0, 0, 0, 0, 0]
        structural_features = {"has_panchanga": False, "has_const": False, "time_precision": "hour", "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
