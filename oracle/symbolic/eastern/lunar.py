"""Lunar calendar wrapper using lunar-python + cnlunar + chinese-calendar + lunarcalendar."""
import hashlib
from datetime import date, datetime
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from lunar_python import Lunar, Solar as LunarSolar
    LUNAR_PYTHON_AVAILABLE = True
except ImportError:
    LUNAR_PYTHON_AVAILABLE = False

try:
    import cnlunar
    CNLUNAR_AVAILABLE = True
except ImportError:
    CNLUNAR_AVAILABLE = False

try:
    import chinese_calendar as cc
    CC_AVAILABLE = True
except ImportError:
    CC_AVAILABLE = False

try:
    from lunarcalendar import Converter, Lunar as LunarCal, Solar as SolarCal
    LUNARCALENDAR_AVAILABLE = True
except ImportError:
    LUNARCALENDAR_AVAILABLE = False

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ANIMAL_YEARS = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]


@register_system
class LunarCalendarWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "lunar_calendar"
    LIBRARY_BACKEND = "lunar-python" if LUNAR_PYTHON_AVAILABLE else ("lunarcalendar" if LUNARCALENDAR_AVAILABLE else "internal")

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        if LUNAR_PYTHON_AVAILABLE:
            try:
                return self._compute_with_lunar_python(entropy_packet, params)
            except Exception:
                pass
        if CNLUNAR_AVAILABLE:
            try:
                return self._compute_with_cnlunar(entropy_packet, params)
            except Exception:
                pass
        if LUNARCALENDAR_AVAILABLE:
            try:
                return self._compute_with_lunarcalendar(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_lunar_python(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        solar = LunarSolar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        stem_idx = (lunar.getYear() - 4) % 10
        branch_idx = (lunar.getYear() - 4) % 12

        holidays = []
        if CC_AVAILABLE:
            try:
                dt = date(year, month, day)
                if cc.is_workday(dt):
                    holidays.append("workday")
                else:
                    holidays.append("holiday")
            except Exception:
                pass

        symbolic_state = {
            "lunar_year": lunar.getYear(),
            "lunar_month": lunar.getMonth(),
            "lunar_day": lunar.getDay(),
            "heavenly_stem": HEAVENLY_STEMS[stem_idx],
            "earthly_branch": EARTHLY_BRANCHES[branch_idx],
            "animal_year": ANIMAL_YEARS[branch_idx],
            "month_name": lunar.getMonthCn(),
            "day_name": lunar.getDayCn(),
            "is_leap_month": lunar.getMonth() < 0,
            "festivals": lunar.getFestivals() if hasattr(lunar, 'getFestivals') else [],
            "holidays": holidays,
            "solar_date": {"year": year, "month": month, "day": day},
        }

        numeric_projection = [
            lunar.getYear() % 10,
            lunar.getYear() % 12,
            abs(lunar.getMonth()) % 12,
            lunar.getDay() % 30,
            stem_idx,
            branch_idx,
            (lunar.getYear() - 4) % 12,
            hash(lunar.getMonthCn()) % 10 if lunar.getMonthCn() else 0,
            hash(lunar.getDayCn()) % 30 if lunar.getDayCn() else 0,
            len(holidays),
            seed % 1000,
            year % 10,
        ]

        structural_features = {
            "stem_element_diversity": len(set([HEAVENLY_STEMS[stem_idx]])) / 10,
            "branch_diversity": 1 / 12,
            "is_leap": 1 if lunar.getMonth() < 0 else 0,
            "holiday_indicator": 1 if holidays and "holiday" in holidays else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_with_cnlunar(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)

        dt = datetime(year, month, day, hour)
        lunar_obj = cnlunar.Lunar(dt)

        symbolic_state = {
            "lunar_year": lunar_obj.lunarYear,
            "lunar_month": lunar_obj.lunarMonth,
            "lunar_day": lunar_obj.lunarDay,
            "heavenly_stem": lunar_obj.year8Char[:1] if lunar_obj.year8Char else "",
            "earthly_branch": lunar_obj.year8Char[1:2] if len(lunar_obj.year8Char) > 1 else "",
            "year_gan_zhi": lunar_obj.year8Char,
            "month_gan_zhi": lunar_obj.month8Char,
            "day_gan_zhi": lunar_obj.day8Char,
            "hour_gan_zhi": lunar_obj.hour8Char,
            "solar_date": {"year": year, "month": month, "day": day},
        }

        numeric_projection = [
            lunar_obj.lunarYear % 10,
            lunar_obj.lunarYear % 12,
            lunar_obj.lunarMonth % 12,
            lunar_obj.lunarDay % 30,
            hash(lunar_obj.year8Char) % 10 if lunar_obj.year8Char else 0,
            hash(lunar_obj.month8Char) % 12 if lunar_obj.month8Char else 0,
            hash(lunar_obj.day8Char) % 30 if lunar_obj.day8Char else 0,
            hash(lunar_obj.hour8Char) % 12 if lunar_obj.hour8Char else 0,
            (lunar_obj.lunarYear - 4) % 12,
            seed % 1000,
            year % 10,
            month % 12,
        ]

        structural_features = {
            "stem_element_diversity": 0.2,
            "branch_diversity": 0.2,
            "is_leap": 0,
            "holiday_indicator": 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_with_lunarcalendar(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        solar = SolarCal(year, month, day)
        lunar = Converter.Solar2Lunar(solar)

        stem_idx = (lunar.year - 4) % 10
        branch_idx = (lunar.year - 4) % 12

        symbolic_state = {
            "lunar_year": lunar.year,
            "lunar_month": lunar.month,
            "lunar_day": lunar.day,
            "heavenly_stem": HEAVENLY_STEMS[stem_idx],
            "earthly_branch": EARTHLY_BRANCHES[branch_idx],
            "animal_year": ANIMAL_YEARS[branch_idx],
            "solar_date": {"year": year, "month": month, "day": day},
            "library": "lunarcalendar",
        }

        numeric_projection = [
            lunar.year % 10, lunar.year % 12, lunar.month % 12, lunar.day % 30,
            stem_idx, branch_idx, branch_idx,
            (stem_idx + branch_idx) % 10,
            (stem_idx * branch_idx) % 12,
            seed % 1000, year % 10, month % 12,
        ]

        structural_features = {
            "stem_element_diversity": 1 / 10,
            "branch_diversity": 1 / 12,
            "is_leap": 0,
            "holiday_indicator": 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        h = hashlib.sha256(f"{seed}_lunar".encode()).digest()

        stem_idx = (year - 4) % 10
        branch_idx = (year - 4) % 12
        lunar_month = h[0] % 12 + 1
        lunar_day = h[1] % 30 + 1

        symbolic_state = {
            "lunar_year": year,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "heavenly_stem": HEAVENLY_STEMS[stem_idx],
            "earthly_branch": EARTHLY_BRANCHES[branch_idx],
            "animal_year": ANIMAL_YEARS[branch_idx],
            "solar_date": {"year": year, "month": month, "day": day},
        }

        numeric_projection = [
            year % 10, year % 12, lunar_month, lunar_day,
            stem_idx, branch_idx, branch_idx,
            (stem_idx + branch_idx) % 10,
            (stem_idx * branch_idx) % 12,
            seed % 1000, year % 100, month % 12,
        ]

        structural_features = {
            "stem_element_diversity": 1 / 10,
            "branch_diversity": 1 / 12,
            "is_leap": 0,
            "holiday_indicator": 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
