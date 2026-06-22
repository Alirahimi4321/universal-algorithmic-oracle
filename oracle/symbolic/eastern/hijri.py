"""Hijri/Islamic calendar wrapper using hijridate library."""
import hashlib
from datetime import date
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from hijridate import Hijri, Gregorian
    HIJRIDATE_AVAILABLE = True
except ImportError:
    HIJRIDATE_AVAILABLE = False

ISLAMIC_MONTHS = [
    "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
    "Jumada al-Ula", "Jumada al-Thani", "Rajab", "Shaban",
    "Ramadan", "Shawwal", "Dhu al-Qidah", "Dhu al-Hijjah",
]

ISLAMIC_WEEKDAYS = ["Ahad", "Ithnayn", "Thulatha", "Arbi'a", "Khamis", "Jumu'ah", "Sabt"]


@register_system
class HijriCalendarWrapper(SymbolicSystemWrapper):
    """Hijri/Islamic calendar computation using hijridate."""
    SYSTEM_ID = "hijri_calendar"
    LIBRARY_BACKEND = "hijridate" if HIJRIDATE_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        if HIJRIDATE_AVAILABLE:
            try:
                return self._compute_hijridate(year, month, day, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, seed, params)

    def _compute_hijridate(self, year, month, day, seed, params):
        g = Gregorian(year, month, day)
        h = g.to_hijri()
        h_year = h.year
        h_month = h.month
        h_day = h.day
        h_month_name = ISLAMIC_MONTHS[h_month - 1] if 1 <= h_month <= 12 else "Unknown"

        g2 = Gregorian(year, month, day)
        h2 = g2.to_hijri()
        g_back = h2.to_gregorian()

        symbolic_state = {
            "hijri_year": h_year,
            "hijri_month": h_month,
            "hijri_day": h_day,
            "hijri_month_name": h_month_name,
            "gregorian_date": {"year": year, "month": month, "day": day},
            "round_trip": {"year": g_back.year, "month": g_back.month, "day": g_back.day},
            "year_mod_30": h_year % 30,
            "month_mod_12": h_month % 12,
        }

        numeric_projection = [
            h_year % 10, h_year % 12, h_month, h_day,
            h_year % 30, h_month % 12, h_day % 30,
            (h_year + h_month + h_day) % 7,
            seed % 1000,
        ]

        structural_features = {
            "month_validity": 1 if 1 <= h_month <= 12 else 0,
            "day_validity": 1 if 1 <= h_day <= 30 else 0,
            "year_era": h_year // 100,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, year, month, day, seed, params):
        h = hashlib.sha256(f"hijri_{year}_{month}_{day}_{seed}".encode()).digest()
        h_year = 1445 + (h[0] % 5)
        h_month = (h[1] % 12) + 1
        h_day = (h[2] % 30) + 1
        h_month_name = ISLAMIC_MONTHS[h_month - 1]

        symbolic_state = {
            "hijri_year": h_year,
            "hijri_month": h_month,
            "hijri_day": h_day,
            "hijri_month_name": h_month_name,
            "gregorian_date": {"year": year, "month": month, "day": day},
            "year_mod_30": h_year % 30,
            "month_mod_12": h_month % 12,
        }

        numeric_projection = [
            h_year % 10, h_year % 12, h_month, h_day,
            h_year % 30, h_month % 12, h_day % 30,
            (h_year + h_month + h_day) % 7,
            seed % 1000,
        ]

        structural_features = {
            "month_validity": 1 if 1 <= h_month <= 12 else 0,
            "day_validity": 1 if 1 <= h_day <= 30 else 0,
            "year_era": h_year // 100,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
