"""LunarCalendar wrapper: Chinese Lunar Calendar converter."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_LUNARCALENDAR = False
try:
    from lunarcalendar import Converter, Solar, Lunar
    HAS_LUNARCALENDAR = True
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
class LunarCalendarWrapper(SymbolicSystemWrapper):
    """Chinese Lunar Calendar using LunarCalendar library."""
    SYSTEM_ID = "lunarcalendar"
    LIBRARY_BACKEND = "lunarcalendar"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_LUNARCALENDAR:
            try:
                solar = Solar(dt.year, dt.month, dt.day)
                lunar = Converter.Solar2Lunar(solar)

                symbolic_state = {
                    "lunar_year": lunar.year,
                    "lunar_month": lunar.month,
                    "lunar_day": lunar.day,
                    "is_leap": lunar.isleap() if callable(lunar.isleap) else lunar.isleap,
                    "gregorian": f"{dt.year}-{dt.month:02d}-{dt.day:02d}",
                    "raw": str(lunar),
                }

                numeric_projection = [
                    lunar.year % 100,
                    lunar.month % 12,
                    lunar.day % 30,
                    1 if (lunar.isleap() if callable(lunar.isleap) else lunar.isleap) else 0,
                    hash(str(lunar)) % 60,
                    dt.hour % 24,
                    dt.minute % 60,
                ]

                structural_features = {
                    "has_lunar_date": True,
                    "has_leap_flag": True,
                    "time_precision": "day",
                    "backend": "lunarcalendar",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    params=params,
                )
            except Exception as e:
                logger.warning("lunarcalendar compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {"lunar_year": 0, "lunar_month": 0, "lunar_day": 0, "backend": "lunarcalendar_fallback"}
        numeric_projection = [dt.year % 100, dt.month % 12, dt.day % 30, 0, seed % 60, dt.hour % 24, dt.minute % 60]
        structural_features = {"has_lunar_date": False, "time_precision": "day", "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
