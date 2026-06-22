"""ZiWei Stars wrapper — Zi Wei Dou Shu (紫微斗數) star calculations."""
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_ZIWEI = False
try:
    from ziwei.star import get_major_stars, get_minor_stars, solar_to_lunar, get_brightness, get_changsheng12, get_mutagen
    from ziwei.palace import get_palace_names, get_soul_and_body, get_stems_and_branches, HEAVENLY_STEMS, EARTHLY_BRANCHES
    HAS_ZIWEI = True
except ImportError:
    pass


@register_system
class ZiWeiStarsWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "ziwei_stars"
    LIBRARY_BACKEND = "ziwei_cli"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not HAS_ZIWEI:
            return self._build_output({}, [], {"error": "ziwei not installed"})

        year = int(entropy_packet.get("year", 1990))
        month = int(entropy_packet.get("month", 1))
        day = int(entropy_packet.get("day", 1))
        time_index = int((params or {}).get("time_index", 1))
        gender = (params or {}).get("gender", "male")

        lunar_date = solar_to_lunar(f"{year:04d}-{month:02d}-{day:02d}")
        sb = get_soul_and_body(f"{year:04d}-{month:02d}-{day:02d}", time_index)
        sb_list = list(sb.values())
        stems_branches = get_stems_and_branches(f"{year:04d}-{month:02d}-{day:02d}", time_index)
        palace_names = get_palace_names(sb["soul_index"])

        major_stars = []
        try:
            major_stars = get_major_stars(f"{year:04d}-{month:02d}-{day:02d}", time_index, gender)
        except Exception:
            pass

        minor_stars = []
        try:
            minor_stars = get_minor_stars(f"{year:04d}-{month:02d}-{day:02d}", time_index)
        except Exception:
            pass

        numeric = [
            sb.get("soul_index", 0),
            sb.get("body_index", 0),
            lunar_date.get("year", 0),
            lunar_date.get("month", 0),
            lunar_date.get("day", 0),
            *[ord(s) for s in sb_list if isinstance(s, str) and len(s) == 1][:6],
        ]

        return self._build_output(
            symbolic_state={
                "lunar_date": lunar_date,
                "soul_body": sb,
                "palace_names": palace_names,
                "major_stars": major_stars if isinstance(major_stars, list) else list(major_stars),
                "minor_stars": minor_stars[:10] if isinstance(minor_stars, list) else [],
                "stems_branches": {k: str(v) for k, v in stems_branches.items()} if isinstance(stems_branches, dict) else {},
            },
            numeric_projection=numeric,
            structural_features={
                "soul_index": sb.get("soul_index", 0),
                "body_index": sb.get("body_index", 0),
                "num_palaces": len(palace_names),
                "num_major_stars": len(major_stars) if isinstance(major_stars, list) else 0,
                "num_minor_stars": len(minor_stars) if isinstance(minor_stars, list) else 0,
            },
        )
