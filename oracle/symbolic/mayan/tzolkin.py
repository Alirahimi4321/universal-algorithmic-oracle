"""Mayan Tzolkin calendar wrapper using tzolkin-calendar."""
import hashlib
from datetime import date
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import tzolkin_calendar as tzc
    TZOLKIN_CALENDAR_AVAILABLE = True
except ImportError:
    TZOLKIN_CALENDAR_AVAILABLE = False

DAY_SIGNS = [
    "Imix", "Ik", "Akbal", "Kan", "Chicchan", "Cimi", "Manik", "Lamat", "Muluc", "Oc",
    "Chuen", "Eb", "Ben", "Ix", "Men", "Cib", "Caban", "Etz'nab", "Cauac", "Ahau",
]

TONES = ["Imix", "Ik", "Akbal", "Kan", "Chicchan", "Cimi", "Manik", "Lamat", "Muluc", "Oc",
         "Chuen", "Eb", "Ben", "Ix", "Men", "Cib", "Caban", "Etz'nab", "Cauac", "Ahau"]

TONE_NAMES = ["1-Imix", "2-Ik", "3-Akbal", "4-Kan", "5-Chicchan", "6-Cimi", "7-Manik",
              "8-Lamat", "9-Muluc", "10-Oc", "11-Chuen", "12-Eb", "13-Ben", "1-Ix",
              "2-Men", "3-Cib", "4-Caban", "5-Etz'nab", "6-Cauac", "7-Ahau"]


@register_system
class TzolkinWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tzolkin"
    LIBRARY_BACKEND = "tzolkin-calendar" if TZOLKIN_CALENDAR_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        if TZOLKIN_CALENDAR_AVAILABLE:
            try:
                return self._compute_with_tzolkin(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_tzolkin(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        dt = date(year, month, day)
        tz_date = tzc.get_tzolkin_date(dt)

        day_sign = tz_date.day_sign if hasattr(tz_date, 'day_sign') else DAY_SIGNS[seed % 20]
        tone = tz_date.tone if hasattr(tz_date, 'tone') else (seed % 13) + 1
        long_count = tz_date.long_count if hasattr(tz_date, 'long_count') else None

        lc_baktun = long_count.baktun if long_count and hasattr(long_count, 'baktun') else 13
        lc_katun = long_count.katun if long_count and hasattr(long_count, 'katun') else 0
        lc_tun = long_count.tun if long_count and hasattr(long_count, 'tun') else 0
        lc_winal = long_count.winal if long_count and hasattr(long_count, 'winal') else 0
        lc_kin = long_count.kin if long_count and hasattr(long_count, 'kin') else 0

        symbolic_state = {
            "day_sign": day_sign,
            "tone": tone,
            "tzolkin_date": f"{tone}-{day_sign}",
            "long_count": {
                "baktun": lc_baktun,
                "katun": lc_katun,
                "tun": lc_tun,
                "winal": lc_winal,
                "kin": lc_kin,
            },
            "kin_of_long_count": lc_baktun * 144000 + lc_katun * 7200 + lc_tun * 360 + lc_winal * 20 + lc_kin,
            "day_sign_idx": DAY_SIGNS.index(day_sign) % 20 if day_sign in DAY_SIGNS else 0,
            "tone_idx": (tone - 1) % 13,
            "birth_data": {"year": year, "month": month, "day": day},
        }

        day_sign_idx = DAY_SIGNS.index(day_sign) % 20 if day_sign in DAY_SIGNS else 0

        numeric_projection = [
            day_sign_idx,
            (tone - 1) % 13,
            lc_baktun,
            lc_katun,
            lc_tun,
            lc_winal,
            lc_kin,
            (day_sign_idx + tone) % 20,
            (day_sign_idx * tone) % 13,
            symbolic_state["kin_of_long_count"] % 260,
            seed % 1000,
            year % 10,
        ]

        structural_features = {
            "day_sign_diversity": 1 / 20,
            "tone_distribution": tone / 13,
            "long_count_depth": sum([lc_baktun, lc_katun, lc_tun, lc_winal, lc_kin]),
            "galactic_signature": (day_sign_idx * tone) % 260,
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

        h = hashlib.sha256(f"{seed}_tzolkin".encode()).digest()

        day_sign_idx = (h[0] + day) % 20
        tone = (h[1] % 13) + 1
        day_sign = DAY_SIGNS[day_sign_idx]

        days_since_baktun_start = (year - 2012) * 365 + month * 30 + day
        lc_baktun = 13
        lc_katun = days_since_baktun_start // 7200
        lc_tun = (days_since_baktun_start % 7200) // 360
        lc_winal = (days_since_baktun_start % 360) // 20
        lc_kin = days_since_baktun_start % 20

        kin_of_long_count = lc_baktun * 144000 + lc_katun * 7200 + lc_tun * 360 + lc_winal * 20 + lc_kin

        symbolic_state = {
            "day_sign": day_sign,
            "tone": tone,
            "tzolkin_date": f"{tone}-{day_sign}",
            "long_count": {
                "baktun": lc_baktun,
                "katun": lc_katun,
                "tun": lc_tun,
                "winal": lc_winal,
                "kin": lc_kin,
            },
            "kin_of_long_count": kin_of_long_count,
            "day_sign_idx": day_sign_idx,
            "tone_idx": (tone - 1) % 13,
        }

        numeric_projection = [
            day_sign_idx,
            (tone - 1) % 13,
            lc_baktun,
            lc_katun,
            lc_tun,
            lc_winal,
            lc_kin,
            (day_sign_idx + tone) % 20,
            (day_sign_idx * tone) % 13,
            kin_of_long_count % 260,
            seed % 1000,
            year % 10,
        ]

        structural_features = {
            "day_sign_diversity": 1 / 20,
            "tone_distribution": tone / 13,
            "long_count_depth": sum([lc_baktun, lc_katun, lc_tun, lc_winal, lc_kin]),
            "galactic_signature": (day_sign_idx * tone) % 260,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
