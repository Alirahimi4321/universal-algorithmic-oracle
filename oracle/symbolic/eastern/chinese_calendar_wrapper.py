"""Chinese Calendar holidays and solar terms wrapper."""
import time
from datetime import datetime, date, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import chinese_calendar as cc
    CC_AVAILABLE = True
except ImportError:
    CC_AVAILABLE = False


def _extract_date(entropy_packet: dict) -> date:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts.date()
    if isinstance(ts, date):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).date()
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc).date()


@register_system
class ChineseCalendarWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "chinese_calendar"
    LIBRARY_BACKEND = "chinese_calendar"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        d = _extract_date(entropy_packet)
        seed = entropy_packet.get("seed", 0)

        is_holiday = False
        is_workday = False
        holidays = []
        workdays = []
        solar_term = ""

        if CC_AVAILABLE:
            try:
                is_holiday = cc.is_holiday(d)
            except Exception:
                pass
            try:
                is_workday = cc.is_workday(d)
            except Exception:
                pass
            try:
                holiday_dates = cc.get_holidays(d.year)
                holidays = [str(h) for h in holiday_dates if h.month == d.month][:5]
            except Exception:
                pass
            try:
                workday_dates = cc.get_workdays(d.year)
                workdays = [str(w) for w in workday_dates if w.month == d.month][:5]
            except Exception:
                pass
            try:
                terms = cc.get_solar_terms(d.year)
                for term_date, term_name in terms:
                    if term_date.month == d.month and term_date.day == d.day:
                        solar_term = term_name
            except Exception:
                pass

        symbolic_state = {
            "date": str(d),
            "is_holiday": is_holiday,
            "is_workday": is_workday,
            "holiday_count_this_month": len(holidays),
            "workday_count_this_month": len(workdays),
            "solar_term": solar_term,
        }
        numeric_projection = [
            d.month, d.day, int(is_holiday), int(is_workday),
            len(holidays), len(workdays), seed % 1000,
        ]
        structural_features = {
            "is_weekend": d.weekday() >= 5,
            "has_solar_term": bool(solar_term),
            "day_of_year": d.timetuple().tm_yday,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
