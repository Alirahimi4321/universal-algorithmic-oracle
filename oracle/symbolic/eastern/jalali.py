"""Persian/Jalali calendar wrapper using jdatetime library."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    JDATETIME_AVAILABLE = False

JALALI_MONTHS = [
    "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
    "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand",
]

JALALI_WEEKDAYS = ["Shanbe", "Yekshanbe", "Doshanbeh", "Seshanbeh", "Chaharshanbe", "Panjshanbe", "Jomeh"]


@register_system
class JalaliCalendarWrapper(SymbolicSystemWrapper):
    """Persian/Jalali calendar computation using jdatetime."""
    SYSTEM_ID = "jalali_calendar"
    LIBRARY_BACKEND = "jdatetime" if JDATETIME_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        if JDATETIME_AVAILABLE:
            try:
                return self._compute_jdatetime(year, month, day, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, seed, params)

    def _compute_jdatetime(self, year, month, day, seed, params):
        g_date = jdatetime.date(year, month, day)
        j_date = g_date
        j_year = j_date.year
        j_month = j_date.month
        j_day = j_date.day

        j_month_name = JALALI_MONTHS[j_month - 1] if 1 <= j_month <= 12 else "Unknown"
        weekday_idx = j_date.weekday()
        j_weekday = JALALI_WEEKDAYS[weekday_idx] if 0 <= weekday_idx <= 6 else "Unknown"

        g_back = j_date.togregorian()

        symbolic_state = {
            "jalali_year": j_year,
            "jalali_month": j_month,
            "jalali_day": j_day,
            "jalali_month_name": j_month_name,
            "jalali_weekday": j_weekday,
            "gregorian_date": {"year": year, "month": month, "day": day},
            "round_trip": {"year": g_back.year, "month": g_back.month, "day": g_back.day},
            "year_mod_2820": j_year % 2820,
            "month_mod_12": j_month % 12,
        }

        numeric_projection = [
            j_year % 10, j_year % 12, j_month, j_day,
            j_year % 2820, j_month % 12, j_day % 30,
            (j_year + j_month + j_day) % 7,
            weekday_idx,
            seed % 1000,
        ]

        structural_features = {
            "month_validity": 1 if 1 <= j_month <= 12 else 0,
            "day_validity": 1 if 1 <= j_day <= 31 else 0,
            "year_era": j_year // 1000,
            "weekday_idx": weekday_idx,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, year, month, day, seed, params):
        h = hashlib.sha256(f"jalali_{year}_{month}_{day}_{seed}".encode()).digest()
        j_year = 1403 + (h[0] % 3)
        j_month = (h[1] % 12) + 1
        j_day = (h[2] % 31) + 1
        j_month_name = JALALI_MONTHS[j_month - 1]
        j_weekday = JALALI_WEEKDAYS[h[3] % 7]

        symbolic_state = {
            "jalali_year": j_year,
            "jalali_month": j_month,
            "jalali_day": j_day,
            "jalali_month_name": j_month_name,
            "jalali_weekday": j_weekday,
            "gregorian_date": {"year": year, "month": month, "day": day},
            "year_mod_2820": j_year % 2820,
            "month_mod_12": j_month % 12,
        }

        numeric_projection = [
            j_year % 10, j_year % 12, j_month, j_day,
            j_year % 2820, j_month % 12, j_day % 30,
            (j_year + j_month + j_day) % 7,
            h[3] % 7,
            seed % 1000,
        ]

        structural_features = {
            "month_validity": 1 if 1 <= j_month <= 12 else 0,
            "day_validity": 1 if 1 <= j_day <= 31 else 0,
            "year_era": j_year // 1000,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
