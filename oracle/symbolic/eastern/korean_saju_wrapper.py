"""Korean Saju (Four Pillars) wrapper using korean_saju."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from korean_saju import Saju, SajuAnalysis, load_bundled_data
    KOREAN_SAJU_AVAILABLE = True
except ImportError:
    KOREAN_SAJU_AVAILABLE = False

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
FIVE_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
STEM_ELEMENTS = [
    "Wood", "Wood", "Fire", "Fire", "Earth",
    "Earth", "Metal", "Metal", "Water", "Water",
]
BRANCH_ELEMENTS = [
    "Water", "Earth", "Wood", "Wood", "Earth",
    "Fire", "Fire", "Earth", "Metal", "Metal",
    "Earth", "Water",
]
YIN_YANG = ["Yang", "Yin"]
ANIMAL_YEARS = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]

TEN_GODS = [
    "比肩", "劫财", "食神", "傷官", "偏財",
    "正財", "七殺", "正官", "偏印", "正印",
]


@register_system
class KoreanSajuWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "korean_saju"
    LIBRARY_BACKEND = "korean-saju" if KOREAN_SAJU_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        if KOREAN_SAJU_AVAILABLE:
            try:
                return self._compute_with_library(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_library(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})

        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)
        minute = cal_ctx.get("minute", 0)

        load_bundled_data()
        saju_chart = Saju.from_birth(year, month, day, hour, minute)
        analysis = SajuAnalysis(saju_chart)

        four_pillars = getattr(saju_chart, "four_pillars", None)
        pillars_list = []
        pillar_names = ["year", "month", "day", "hour"]
        for name in pillar_names:
            if four_pillars is not None:
                pillar = getattr(four_pillars, name, None)
                if pillar is not None:
                    stem = getattr(pillar, "heavenly_stem", getattr(pillar, "stem", ""))
                    branch = getattr(pillar, "earthly_branch", getattr(pillar, "branch", ""))
                    element = STEM_ELEMENTS[HEAVENLY_STEMS.index(stem) % 5] if stem in HEAVENLY_STEMS else "Unknown"
                    pillars_list.append({
                        "stem": stem,
                        "branch": branch,
                        "element": element,
                        "yin_yang": YIN_YANG[HEAVENLY_STEMS.index(stem) % 2] if stem in HEAVENLY_STEMS else "Yang",
                    })

        if not pillars_list:
            for i in range(4):
                pillars_list.append({
                    "stem": HEAVENLY_STEMS[i % 10],
                    "branch": EARTHLY_BRANCHES[i % 12],
                    "element": FIVE_ELEMENTS[i % 5],
                    "yin_yang": YIN_YANG[i % 2],
                })

        ten_gods = getattr(analysis, "ten_gods", None)
        ten_gods_list = []
        if ten_gods is not None:
            for name in pillar_names:
                tg = getattr(ten_gods, name, None)
                if tg is not None:
                    ten_gods_list.append(str(tg))
                else:
                    ten_gods_list.append("")
        else:
            ten_gods_list = [""] * 4

        dominant_element = getattr(analysis, "dominant_element", None)
        favorable_elements = getattr(analysis, "favorable_elements", [])
        strength = getattr(analysis, "strength", None)

        symbolic_state = {
            "pillars": pillars_list,
            "year_pillar": pillars_list[0] if len(pillars_list) > 0 else {},
            "month_pillar": pillars_list[1] if len(pillars_list) > 1 else {},
            "day_pillar": pillars_list[2] if len(pillars_list) > 2 else {},
            "hour_pillar": pillars_list[3] if len(pillars_list) > 3 else {},
            "ten_gods": ten_gods_list,
            "dominant_element": str(dominant_element) if dominant_element else "Unknown",
            "favorable_elements": list(favorable_elements) if favorable_elements else [],
            "animal_year": ANIMAL_YEARS[(year - 4) % 12],
        }

        stem_indices = [
            HEAVENLY_STEMS.index(p["stem"]) % 10
            if p["stem"] in HEAVENLY_STEMS else 0
            for p in pillars_list
        ]
        branch_indices = [
            EARTHLY_BRANCHES.index(p["branch"]) % 12
            if p["branch"] in EARTHLY_BRANCHES else 0
            for p in pillars_list
        ]

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
        for p in pillars_list:
            if p["element"] in element_counts:
                element_counts[p["element"]] += 1

        structural_features = {
            "element_balance": max(element_counts.values()) / max(sum(element_counts.values()), 1),
            "stem_element_diversity": len(set(STEM_ELEMENTS[i] for i in stem_indices)) / 5,
            "branch_element_diversity": len(set(BRANCH_ELEMENTS[i] for i in branch_indices)) / 5,
            "yin_yang_ratio": sum(YIN_YANG[i % 2] == "Yang" for i in stem_indices) / 4,
            "strength": float(strength) if strength is not None else 0.0,
            "favorable_elements": list(favorable_elements) if favorable_elements else [],
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

        year_idx = h[0] % 12
        animal = ANIMAL_YEARS[year_idx]

        stem_indices = [HEAVENLY_STEMS.index(p["stem"]) for p in pillars]
        branch_indices = [EARTHLY_BRANCHES.index(p["branch"]) for p in pillars]

        element_counts = {e: 0 for e in FIVE_ELEMENTS}
        for p in pillars:
            if p["element"] in element_counts:
                element_counts[p["element"]] += 1

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

        symbolic_state = {
            "pillars": pillars,
            "year_pillar": pillars[0],
            "month_pillar": pillars[1],
            "day_pillar": pillars[2],
            "hour_pillar": pillars[3],
            "ten_gods": [TEN_GODS[i % 10] for i in stem_indices],
            "dominant_element": max(element_counts, key=element_counts.get),
            "favorable_elements": [],
            "animal_year": animal,
        }

        structural_features = {
            "element_balance": max(element_counts.values()) / max(sum(element_counts.values()), 1),
            "stem_element_diversity": len(set(STEM_ELEMENTS[i] for i in stem_indices)) / 5,
            "branch_element_diversity": len(set(BRANCH_ELEMENTS[i] for i in branch_indices)) / 5,
            "yin_yang_ratio": sum(YIN_YANG[i % 2] == "Yang" for i in stem_indices) / 4,
            "strength": 0.0,
            "favorable_elements": [],
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
