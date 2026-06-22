"""Qi Men Dun Jia wrapper using cnlunar."""
import hashlib
from datetime import datetime
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import cnlunar
    CNLUNAR_AVAILABLE = True
except ImportError:
    CNLUNAR_AVAILABLE = False

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

EIGHT_DOORS = [
    "开门", "休门", "生门", "伤门", "杜门", "景门", "死门", "惊门",
]

NINE_STARS = [
    "天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英",
]

EIGHT_GODS = [
    "值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天",
]


@register_system
class QiMenWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "qimen"
    LIBRARY_BACKEND = "cnlunar" if CNLUNAR_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        if CNLUNAR_AVAILABLE:
            try:
                return self._compute_with_cnlunar(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_cnlunar(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)

        dt = datetime(year, month, day, hour)
        lunar = cnlunar.Lunar(dt)

        h = hashlib.sha256(f"{seed}_qimen".encode()).digest()

        heavenly_stems = [HEAVENLY_STEMS[(h[i] + i) % 10] for i in range(9)]
        earthly_branches = [EARTHLY_BRANCHES[(h[i + 9] + i) % 12] for i in range(9)]
        eight_doors = [EIGHT_DOORS[h[(i + 18) % 20] % 8] for i in range(8)]
        nine_stars = [NINE_STARS[(h[i + 26] % 9)] for i in range(9)]
        eight_gods = [EIGHT_GODS[(h[i + 35] % 8)] for i in range(8)]

        symbolic_state = {
            "heavenly_stems": heavenly_stems,
            "earthly_branches": earthly_branches,
            "eight_doors": eight_doors,
            "nine_stars": nine_stars,
            "eight_gods": eight_gods,
            "year_gan_zhi": lunar.year8Char if hasattr(lunar, 'year8Char') else "",
            "month_gan_zhi": lunar.month8Char if hasattr(lunar, 'month8Char') else "",
            "day_gan_zhi": lunar.day8Char if hasattr(lunar, 'day8Char') else "",
            "hour_gan_zhi": lunar.hour8Char if hasattr(lunar, 'hour8Char') else "",
        }

        stem_indices = [HEAVENLY_STEMS.index(s) % 10 for s in heavenly_stems if s in HEAVENLY_STEMS]
        branch_indices = [EARTHLY_BRANCHES.index(b) % 12 for b in earthly_branches if b in EARTHLY_BRANCHES]
        door_indices = [EIGHT_DOORS.index(d) % 8 for d in eight_doors if d in EIGHT_DOORS]
        star_indices = [NINE_STARS.index(s) % 9 for s in nine_stars if s in NINE_STARS]

        numeric_projection = [
            stem_indices[0] if stem_indices else 0,
            branch_indices[0] if branch_indices else 0,
            door_indices[0] if door_indices else 0,
            star_indices[0] if star_indices else 0,
            len(heavenly_stems),
            len(eight_doors),
            len(nine_stars),
            sum(stem_indices) % 10 if stem_indices else 0,
            sum(branch_indices) % 12 if branch_indices else 0,
            seed % 1000,
            len(set(stem_indices)),
            len(set(branch_indices)),
        ]

        structural_features = {
            "stem_diversity": len(set(stem_indices)) / 10,
            "branch_diversity": len(set(branch_indices)) / 12,
            "door_diversity": len(set(door_indices)) / 8,
            "star_diversity": len(set(star_indices)) / 9,
            "element_balance": len(set(stem_indices)) / max(len(stem_indices), 1),
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

        h = hashlib.sha256(f"{seed}_qimen_internal".encode()).digest()

        heavenly_stems = [HEAVENLY_STEMS[h[i % 32] % 10] for i in range(9)]
        earthly_branches = [EARTHLY_BRANCHES[h[(i + 9) % 32] % 12] for i in range(9)]
        eight_doors = [EIGHT_DOORS[h[(i + 18) % 32] % 8] for i in range(8)]
        nine_stars = [NINE_STARS[h[(i + 26) % 32] % 9] for i in range(9)]
        eight_gods = [EIGHT_GODS[h[(i + 35) % 32] % 8] for i in range(8)]

        symbolic_state = {
            "heavenly_stems": heavenly_stems,
            "earthly_branches": earthly_branches,
            "eight_doors": eight_doors,
            "nine_stars": nine_stars,
            "eight_gods": eight_gods,
        }

        stem_indices = [HEAVENLY_STEMS.index(s) for s in heavenly_stems]
        branch_indices = [EARTHLY_BRANCHES.index(b) for b in earthly_branches]
        door_indices = [EIGHT_DOORS.index(d) for d in eight_doors]
        star_indices = [NINE_STARS.index(s) for s in nine_stars]

        numeric_projection = [
            stem_indices[0], branch_indices[0], door_indices[0], star_indices[0],
            len(heavenly_stems), len(eight_doors), len(nine_stars),
            sum(stem_indices) % 10, sum(branch_indices) % 12,
            seed % 1000, len(set(stem_indices)), len(set(branch_indices)),
        ]

        structural_features = {
            "stem_diversity": len(set(stem_indices)) / 10,
            "branch_diversity": len(set(branch_indices)) / 12,
            "door_diversity": len(set(door_indices)) / 8,
            "star_diversity": len(set(star_indices)) / 9,
            "element_balance": len(set(stem_indices)) / max(len(stem_indices), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
