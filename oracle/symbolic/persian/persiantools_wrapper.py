"""Persian/Jalali calendar wrapper using persiantools."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from persiantools.jdatetime import JalaliDate
    PERSIANTOOLS_AVAILABLE = True
except ImportError:
    PERSIANTOOLS_AVAILABLE = False

try:
    from persiantools import digits
    DIGITS_AVAILABLE = True
except ImportError:
    DIGITS_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class PersianToolsWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "persian_calendar"
    LIBRARY_BACKEND = "persiantools"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)

        jalali_year = dt.year
        jalali_month = dt.month
        jalali_day = dt.day
        jalali_str = ""
        persian_digits = ""

        if PERSIANTOOLS_AVAILABLE:
            try:
                jd = JalaliDate(dt)
                jalali_year = jd.year
                jalali_month = jd.month
                jalali_day = jd.day
                jalali_str = str(jd)
            except Exception:
                pass

        if DIGITS_AVAILABLE:
            try:
                persian_digits = digits.to_arabic_number(str(dt.year))
            except Exception:
                pass

        month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                       "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        month_name = month_names[jalali_month - 1] if 1 <= jalali_month <= 12 else ""

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d"),
            "jalali_str": jalali_str,
            "jalali_year": jalali_year,
            "jalali_month": jalali_month,
            "jalali_day": jalali_day,
            "jalali_month_name": month_name,
            "persian_digits": persian_digits,
        }
        numeric_projection = [
            jalali_year % 10, jalali_month, jalali_day,
            seed % 1000,
        ]
        structural_features = {
            "year_offset": jalali_year - dt.year,
            "day_of_year": (jalali_month - 1) * 31 + jalali_day,
            "is_leap_year": jalali_year % 4 == 3,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
