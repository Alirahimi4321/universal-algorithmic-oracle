"""Holidays calendar wrapper using the holidays library."""
import hashlib
from datetime import date, timedelta
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import holidays as holidays_lib
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

COUNTRY_CODES = [
    "US", "GB", "FR", "DE", "IT", "ES", "JP", "CN", "KR", "IN",
    "BR", "RU", "CA", "AU", "MX", "TR", "SA", "AE", "IR", "EG",
]


@register_system
class HolidaysWrapper(SymbolicSystemWrapper):
    """Wrapper for holidays library - country-specific holidays."""
    SYSTEM_ID = "holidays_calendar"
    LIBRARY_BACKEND = "holidays" if HOLIDAYS_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        h = hashlib.sha256(f"holidays_{seed}".encode()).digest()
        country_idx = h[0] % len(COUNTRY_CODES)
        country = params.get("country", COUNTRY_CODES[country_idx])

        if HOLIDAYS_AVAILABLE:
            try:
                return self._compute_holidays(year, month, day, seed, country, params)
            except Exception as e:
                pass
        return self._compute_internal(year, month, day, seed, country, params)

    def _compute_holidays(self, year, month, day, seed, country, params):
        try:
            country_holidays = holidays_lib.country_holidays(country, years=year)
        except Exception:
            country_holidays = {}

        today = date(year, month, day)
        is_holiday = today in country_holidays
        holiday_name = country_holidays.get(today, "") if is_holiday else ""

        upcoming = []
        for i in range(1, 31):
            check_date = today + timedelta(days=i)
            if check_date in country_holidays:
                upcoming.append({
                    "date": check_date.isoformat(),
                    "name": country_holidays[check_date],
                })
                if len(upcoming) >= 5:
                    break

        all_holidays_list = sorted(country_holidays.items())

        symbolic_state = {
            "country": country,
            "today": today.isoformat(),
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "upcoming_holidays": upcoming,
            "total_holidays_in_year": len([h for h in all_holidays_list if h[0].year == year]),
        }

        numeric_projection = [
            month / 12.0,
            day / 31.0,
            1.0 if is_holiday else 0.0,
            len(upcoming) / 5.0,
            hash(country) % 100 / 100.0,
            seed % 1000 / 1000.0,
        ]

        structural_features = {
            "has_holiday_today": is_holiday,
            "upcoming_count": len(upcoming),
            "country_code": country,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, year, month, day, seed, country, params):
        h = hashlib.sha256(f"holidays_{seed}_{country}".encode()).digest()
        is_holiday = h[0] % 7 == 0
        symbolic_state = {
            "country": country,
            "today": f"{year}-{month:02d}-{day:02d}",
            "is_holiday": is_holiday,
            "holiday_name": f"Day_{h[1] % 30}" if is_holiday else "",
            "upcoming_holidays": [],
            "total_holidays_in_year": h[2] % 15 + 5,
        }
        numeric_projection = [month / 12.0, day / 31.0, 1.0 if is_holiday else 0.0, 0.0, hash(country) % 100 / 100.0, seed % 1000 / 1000.0]
        structural_features = {"has_holiday_today": is_holiday, "upcoming_count": 0, "country_code": country}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection, structural_features=structural_features, params=params)
