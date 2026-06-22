"""Zi Wei Dou Shu (Purple Star Astrology) wrapper using iztro_py."""
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

STAR_NAMES = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁",
    "七杀", "破军",
]

PALACE_NAMES = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母",
]


@register_system
class ZiWeiWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "ziwei"
    LIBRARY_BACKEND = "iztro-py" if IZTRO_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        if IZTRO_AVAILABLE:
            try:
                return self._compute_with_iztro(entropy_packet, params)
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
        gender_str = params.get("gender", "male")
        gender_char = '男' if gender_str in ('male', 'm', 'man') else '女'

        time_index = min(hour // 2, 12)
        solar_date = f"{year:04d}-{month:02d}-{day:02d}"
        chart = iztro_py.by_solar(solar_date, time_index, gender_char)

        palaces = {}
        star_list = []
        if hasattr(chart, 'horoscope'):
            try:
                h = chart.horoscope()
                if hasattr(h, 'palaces'):
                    for palace_data in h.palaces:
                        pname = palace_data.palaceName if hasattr(palace_data, 'palaceName') else str(palace_data)
                        stars_in_palace = [s.starName for s in palace_data.stars] if hasattr(palace_data, 'stars') else []
                        palaces[pname] = {"stars": stars_in_palace}
                        star_list.extend(stars_in_palace)
            except Exception:
                pass

        symbolic_state = {
            "palaces": palaces,
            "palace_names": list(palaces.keys()),
            "all_stars": star_list,
            "unique_stars": list(set(star_list)),
            "star_count": len(star_list),
            "palace_count": len(palaces),
            "gender": gender_str,
            "chinese_date": chart.chinese_date,
            "lunar_date": chart.lunar_date,
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        star_indices = [STAR_NAMES.index(s) % 14 for s in star_list if s in STAR_NAMES]
        palace_indices = [i for i, pn in enumerate(PALACE_NAMES) if pn in palaces]

        numeric_projection = [
            star_indices[0] if star_indices else 0,
            star_indices[1] if len(star_indices) > 1 else 0,
            star_indices[2] if len(star_indices) > 2 else 0,
            len(star_list),
            len(set(star_list)),
            len(palaces),
            sum(star_indices) % 14 if star_indices else 0,
            seed % 1000,
            len(palace_indices),
            hash(gender_str) % 2,
            (year - 1911) % 60,
            len(palaces) * 2,
        ]

        structural_features = {
            "star_density": len(star_list) / max(len(palaces), 1),
            "unique_star_ratio": len(set(star_list)) / max(len(star_list), 1),
            "palace_coverage": len(palaces) / 12,
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
        gender = params.get("gender", "male")

        h = hashlib.sha256(f"{seed}_ziwei".encode()).digest()

        palaces = {}
        all_stars = []
        for i, pname in enumerate(PALACE_NAMES):
            star_count = (h[i] % 4) + 1
            stars = [STAR_NAMES[(h[i + j + 1]) % len(STAR_NAMES)] for j in range(star_count)]
            palaces[pname] = {"stars": stars, "sian_idx": (h[i + 13] % 120) + 1}
            all_stars.extend(stars)

        life_span = (h[0] % 100) + 20

        symbolic_state = {
            "palaces": palaces,
            "palace_names": PALACE_NAMES,
            "all_stars": all_stars,
            "unique_stars": list(set(all_stars)),
            "life_span": life_span,
            "star_count": len(all_stars),
            "palace_count": len(palaces),
            "gender": gender,
        }

        star_indices = [STAR_NAMES.index(s) % 14 for s in all_stars if s in STAR_NAMES]

        numeric_projection = [
            star_indices[0] if star_indices else 0,
            star_indices[1] if len(star_indices) > 1 else 0,
            star_indices[2] if len(star_indices) > 2 else 0,
            len(all_stars),
            len(set(all_stars)),
            len(palaces),
            life_span,
            seed % 1000,
            sum(star_indices) % 14 if star_indices else 0,
            len(PALACE_NAMES),
            hash(gender) % 2,
            (year - 1911) % 60,
        ]

        structural_features = {
            "star_density": len(all_stars) / max(len(palaces), 1),
            "unique_star_ratio": len(set(all_stars)) / max(len(all_stars), 1),
            "palace_coverage": len(palaces) / 12,
            "life_span_normalized": life_span / 120,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
