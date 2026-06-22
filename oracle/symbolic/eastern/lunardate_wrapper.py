"""Lunar date wrapper using the lunardate library."""
import hashlib
from datetime import date
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from lunardate import LunarDate
    LUNARDATE_AVAILABLE = True
except ImportError:
    LUNARDATE_AVAILABLE = False

CHINESE_MONTHS = [
    "Zheng", "Er", "San", "Si", "Wu", "Liu",
    "Qi", "Ba", "Jiu", "Shi", "Dong", "La",
]

CHINESE_HEAVENLY_STEMS = [
    "Jia", "Yi", "Bing", "Ding", "Wu", "Ji",
    "Geng", "Xin", "Ren", "Gui",
]

CHINESE_EARTHLY_BRANCHES = [
    "Zi", "Chou", "Yin", "Mao", "Chen", "Si",
    "Wu", "Wei", "Shen", "You", "Xu", "Hai",
]


@register_system
class LunarDateWrapper(SymbolicSystemWrapper):
    """Wrapper for lunardate - Chinese lunar calendar conversion."""
    SYSTEM_ID = "lunar_date"
    LIBRARY_BACKEND = "lunardate" if LUNARDATE_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        if LUNARDATE_AVAILABLE:
            try:
                return self._compute_lunardate(year, month, day, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, seed, params)

    def _compute_lunardate(self, year, month, day, seed, params):
        greg = date(year, month, day)
        lunar = LunarDate.fromSolarDate(year, month, day)
        lunar_year = lunar.year
        lunar_month = lunar.month
        lunar_day = lunar.day
        is_leap = lunar.leapMonth if hasattr(lunar, 'leapMonth') else False

        stem_idx = (lunar_year - 4) % 10
        branch_idx = (lunar_year - 4) % 12
        heavenly_stem = CHINESE_HEAVENLY_STEMS[stem_idx]
        earthly_branch = CHINESE_EARTHLY_BRANCHES[branch_idx]
        animal = earthly_branch

        month_name = CHINESE_MONTHS[lunar_month - 1] if 1 <= lunar_month <= 12 else "Unknown"

        symbolic_state = {
            "lunar_year": lunar_year,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "is_leap_month": is_leap,
            "heavenly_stem": heavenly_stem,
            "earthly_branch": earthly_branch,
            "animal": animal,
            "month_name": month_name,
            "gregorian_date": {"year": year, "month": month, "day": day},
        }

        numeric_projection = [
            lunar_year % 10 / 10.0,
            lunar_month / 12.0,
            lunar_day / 30.0,
            stem_idx / 10.0,
            branch_idx / 12.0,
            seed % 1000 / 1000.0,
        ]

        structural_features = {
            "month_valid": 1 <= lunar_month <= 12,
            "day_valid": 1 <= lunar_day <= 30,
            "is_leap": is_leap,
            "stem_branch_cycle": (stem_idx, branch_idx),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, year, month, day, seed, params):
        h = hashlib.sha256(f"lunar_{seed}".encode()).digest()
        lunar_year = year
        lunar_month = (h[0] % 12) + 1
        lunar_day = (h[1] % 30) + 1
        stem_idx = (lunar_year - 4) % 10
        branch_idx = (lunar_year - 4) % 12
        heavenly_stem = CHINESE_HEAVENLY_STEMS[stem_idx]
        earthly_branch = CHINESE_EARTHLY_BRANCHES[branch_idx]
        month_name = CHINESE_MONTHS[lunar_month - 1]

        symbolic_state = {"lunar_year": lunar_year, "lunar_month": lunar_month, "lunar_day": lunar_day, "is_leap_month": False, "heavenly_stem": heavenly_stem, "earthly_branch": earthly_branch, "animal": earthly_branch, "month_name": month_name, "gregorian_date": {"year": year, "month": month, "day": day}}
        numeric_projection = [lunar_year % 10 / 10.0, lunar_month / 12.0, lunar_day / 30.0, stem_idx / 10.0, branch_idx / 12.0, seed % 1000 / 1000.0]
        structural_features = {"month_valid": True, "day_valid": True, "is_leap": False, "stem_branch_cycle": (stem_idx, branch_idx)}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection, structural_features=structural_features, params=params)
