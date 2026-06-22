"""Khayyam wrapper: Persian/Jalali Calendar with timezone support."""
import time
import logging
from datetime import datetime, timezone, date
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_KHAYYAM = False
try:
    from khayyam import JalaliDate, JalaliDatetime
    HAS_KHAYYAM = True
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
class KhayyamWrapper(SymbolicSystemWrapper):
    """Persian Jalali Calendar using Khayyam library."""
    SYSTEM_ID = "khayyam_jalali"
    LIBRARY_BACKEND = "khayyam"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_KHAYYAM:
            try:
                jdate = JalaliDate(dt.year, dt.month, dt.day)
                jdt = JalaliDatetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

                day_of_year = jdate.dayofyear() if callable(jdate.dayofyear) else jdate.dayofyear
                symbolic_state = {
                    "jalali_year": jdate.year,
                    "jalali_month": jdate.month,
                    "jalali_day": jdate.day,
                    "weekday": jdate.weekday(),
                    "day_of_year": day_of_year,
                    "gregorian_date": date(dt.year, dt.month, dt.day).isoformat(),
                    "raw": str(jdate),
                }

                weekday_names = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
                symbolic_state["weekday_name"] = weekday_names[jdate.weekday()]

                numeric_projection = [
                    jdate.year % 100,
                    jdate.month % 12,
                    jdate.day % 30,
                    jdate.weekday(),
                    day_of_year % 366,
                    hash(str(jdate)) % 60,
                    dt.hour % 24,
                ]

                structural_features = {
                    "has_jalali_date": True,
                    "has_weekday": True,
                    "time_precision": "day",
                    "backend": "khayyam",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    params=params,
                )
            except Exception as e:
                logger.warning("khayyam compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {"jalali_year": 0, "jalali_month": 0, "jalali_day": 0, "backend": "khayyam_fallback"}
        numeric_projection = [dt.year % 100, dt.month % 12, dt.day % 30, 0, 0, seed % 60, dt.hour % 24]
        structural_features = {"has_jalali_date": False, "time_precision": "day", "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
