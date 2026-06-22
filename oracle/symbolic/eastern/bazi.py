"""BaZi (Four Pillars of Destiny) wrapper using iztro_py + cnlunar."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import iztro_py
    IZTRO_AVAILABLE = True
except ImportError:
    try:
        import iztro
        iztro_py = iztro
        IZTRO_AVAILABLE = True
    except ImportError:
        IZTRO_AVAILABLE = False

try:
    import cnlunar
    CNLUNAR_AVAILABLE = True
except ImportError:
    CNLUNAR_AVAILABLE = False

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
FIVE_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
STEM_ELEMENTS = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
BRANCH_ELEMENTS = ["Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]
YIN_YANG = ["Yang", "Yin"]
ANIMAL_YEARS = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]


@register_system
class BaZiWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "bazi"
    LIBRARY_BACKEND = "iztro-py" if IZTRO_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})

        if IZTRO_AVAILABLE:
            try:
                return self._compute_with_iztro(entropy_packet, params)
            except Exception:
                pass
        if CNLUNAR_AVAILABLE:
            try:
                return self._compute_with_cnlunar(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_iztro(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)

        time_index = min(hour // 2, 12)
        solar_date = f"{year:04d}-{month:02d}-{day:02d}"
        chart = iztro_py.by_solar(solar_date, time_index, '男')

        chinese_date = chart.chinese_date
        parts = chinese_date.split()
        pillar_names = ["year", "month", "day", "hour"]
        pillars = []
        for i, part in enumerate(parts[:4]):
            stem = part[0] if len(part) > 0 else "甲"
            branch = part[1] if len(part) > 1 else "子"
            pillars.append({
                "stem": stem,
                "branch": branch,
                "element": FIVE_ELEMENTS[HEAVENLY_STEMS.index(stem) % 5] if stem in HEAVENLY_STEMS else "Unknown",
            })

        animal_idx = (year - 4) % 12
        animal = ANIMAL_YEARS[animal_idx]

        symbolic_state = {
            "pillars": pillars,
            "year_pillar": pillars[0],
            "month_pillar": pillars[1],
            "day_pillar": pillars[2],
            "hour_pillar": pillars[3],
            "animal_year": animal,
            "chinese_date": chinese_date,
            "lunar_date": chart.lunar_date,
            "five_elements_class": chart.five_elements_class,
        }

        stem_indices = [HEAVENLY_STEMS.index(p["stem"]) % 10 if p["stem"] in HEAVENLY_STEMS else 0 for p in pillars]
        branch_indices = [EARTHLY_BRANCHES.index(p["branch"]) % 12 if p["branch"] in EARTHLY_BRANCHES else 0 for p in pillars]

        numeric_projection = [
            stem_indices[0], branch_indices[0],
            stem_indices[1], branch_indices[1],
            stem_indices[2], branch_indices[2],
            stem_indices[3], branch_indices[3],
            sum(stem_indices) % 10,
            sum(branch_indices) % 12,
            (year - 4) % 12,
            seed % 1000,
        ]

        element_counts = {e: 0 for e in FIVE_ELEMENTS}
        for p in pillars:
            if p["element"] in element_counts:
                element_counts[p["element"]] += 1

        structural_features = {
            "element_balance": max(element_counts.values()) / max(sum(element_counts.values()), 1),
            "stem_element_diversity": len(set(STEM_ELEMENTS[i] for i in stem_indices)) / 5,
            "branch_element_diversity": len(set(BRANCH_ELEMENTS[i] for i in branch_indices)) / 5,
            "yin_yang_ratio": sum(YIN_YANG[i % 2] == "Yang" for i in stem_indices) / 4,
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
        from datetime import datetime
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)

        dt = datetime(year, month, day, hour)
        lunar = cnlunar.Lunar(dt)

        symbolic_state = {
            "lunar_year": lunar.lunarYear,
            "lunar_month": lunar.lunarMonthCn,
            "lunar_day": lunar.lunarDayCn,
            "year_gan_zhi": lunar.year8Char[:2] if lunar.year8Char else "",
            "month_gan_zhi": lunar.month8Char[:2] if lunar.month8Char else "",
            "day_gan_zhi": lunar.day8Char[:2] if lunar.day8Char else "",
            "hour_gan_zhi": lunar.hour8Char[:2] if lunar.hour8Char else "",
        }

        seed = entropy_packet.get("seed", 0)
        numeric_projection = [
            hash(symbolic_state.get("year_gan_zhi", "")) % 10,
            hash(symbolic_state.get("month_gan_zhi", "")) % 12,
            hash(symbolic_state.get("day_gan_zhi", "")) % 10,
            hash(symbolic_state.get("hour_gan_zhi", "")) % 12,
            lunar.lunarYear % 10,
            lunar.lunarMonth % 12,
            lunar.lunarDay % 30,
            hour % 12,
            (lunar.lunarYear - 4) % 12,
            (lunar.lunarYear + lunar.lunarMonth) % 10,
            (lunar.lunarDay + hour) % 12,
            seed % 1000,
        ]

        structural_features = {
            "stem_element_diversity": 0.5,
            "branch_element_diversity": 0.5,
            "yin_yang_ratio": 0.5,
            "element_balance": 0.2,
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
        h = hashlib.sha256(str(seed).encode()).digest()

        pillars = []
        for i in range(4):
            stem_idx = h[i * 2] % 10
            branch_idx = h[i * 2 + 1] % 12
            pillars.append({
                "stem": HEAVENLY_STEMS[stem_idx],
                "branch": EARTHLY_BRANCHES[branch_idx],
                "element": FIVE_ELEMENTS[stem_idx % 5],
                "yin_yang": YIN_YANG[stem_idx % 2],
            })

        year_idx = (h[0] % 12)
        animal = ANIMAL_YEARS[year_idx]

        symbolic_state = {
            "pillars": pillars,
            "year_pillar": pillars[0],
            "month_pillar": pillars[1],
            "day_pillar": pillars[2],
            "hour_pillar": pillars[3],
            "animal_year": animal,
        }

        stem_indices = [HEAVENLY_STEMS.index(p["stem"]) for p in pillars]
        branch_indices = [EARTHLY_BRANCHES.index(p["branch"]) for p in pillars]

        numeric_projection = [
            stem_indices[0], branch_indices[0],
            stem_indices[1], branch_indices[1],
            stem_indices[2], branch_indices[2],
            stem_indices[3], branch_indices[3],
            sum(stem_indices) % 10,
            sum(branch_indices) % 12,
            year_idx,
            seed % 1000,
        ]

        element_counts = {e: 0 for e in FIVE_ELEMENTS}
        for p in pillars:
            if p["element"] in element_counts:
                element_counts[p["element"]] += 1

        structural_features = {
            "element_balance": max(element_counts.values()) / max(sum(element_counts.values()), 1),
            "stem_element_diversity": len(set(STEM_ELEMENTS[i] for i in stem_indices)) / 5,
            "branch_element_diversity": len(set(BRANCH_ELEMENTS[i] for i in branch_indices)) / 5,
            "yin_yang_ratio": sum(YIN_YANG[i % 2] == "Yang" for i in stem_indices) / 4,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
