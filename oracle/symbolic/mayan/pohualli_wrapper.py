"""Maya/Aztec calendar wrapper using pohualli (Tzolkin, Haab, Long Count)."""
from datetime import date
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from pohualli import compute_composite
    POHUALLI_AVAILABLE = True
except ImportError:
    POHUALLI_AVAILABLE = False

DAY_SIGNS = [
    "Imix", "Ik", "Akbal", "Kan", "Chicchan", "Cimi", "Manik", "Lamat", "Muluc", "Oc",
    "Chuen", "Eb", "Ben", "Ix", "Men", "Cib", "Caban", "Etz'nab", "Cauac", "Ahau",
]

MONTHS_HAAB = [
    "Pop", "Wo", "Sip", "Sotz", "Sek", "Xul", "Yaxk'in", "Mol", "Ch'en", "Yax",
    "Sak", "Keh", "Mak", "K'ank'in", "Muwan", "Pax", "K'ayab", "Kumk'u", "Wayeb",
]

YEAR_BEARRERS = ["Ik", "Manik", "Lamat", "Eb"]


def _date_to_julian_day_number(dt: date) -> int:
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    return dt.day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


@register_system
class PohualliWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "pohualli_calendar"
    LIBRARY_BACKEND = "pohualli" if POHUALLI_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        if POHUALLI_AVAILABLE:
            try:
                return self._compute_with_pohualli(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _compute_with_pohualli(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        dt = date(year, month, day)
        jdn = _date_to_julian_day_number(dt)

        composite = compute_composite(jdn)

        tzolkin_day = getattr(composite, "tzolkin_day", DAY_SIGNS[seed % 20])
        tzolkin_tone = getattr(composite, "tzolkin_tone", (seed % 13) + 1)
        haab_month = getattr(composite, "haab_month", MONTHS_HAAB[seed % 19])
        haab_day = getattr(composite, "haab_day", seed % 20)
        lc_baktun = getattr(composite, "lc_baktun", 13)
        lc_katun = getattr(composite, "lc_katun", 0)
        lc_tun = getattr(composite, "lc_tun", 0)
        lc_winal = getattr(composite, "lc_winal", 0)
        lc_kin = getattr(composite, "lc_kin", 0)

        day_sign_idx = DAY_SIGNS.index(tzolkin_day) if tzolkin_day in DAY_SIGNS else seed % 20
        haab_month_idx = MONTHS_HAAB.index(haab_month) if haab_month in MONTHS_HAAB else seed % 19
        year_bearer = YEAR_BEARRERS[day_sign_idx % 4]
        kin_of_long_count = lc_baktun * 144000 + lc_katun * 7200 + lc_tun * 360 + lc_winal * 20 + lc_kin

        symbolic_state = {
            "tzolkin_date": f"{tzolkin_tone}-{tzolkin_day}",
            "tzolkin_day": tzolkin_day,
            "tzolkin_tone": tzolkin_tone,
            "haab_date": f"{haab_day} {haab_month}",
            "haab_month": haab_month,
            "haab_day": haab_day,
            "long_count": {
                "baktun": lc_baktun,
                "katun": lc_katun,
                "tun": lc_tun,
                "winal": lc_winal,
                "kin": lc_kin,
            },
            "kin_of_long_count": kin_of_long_count,
        }

        numeric_projection = [
            day_sign_idx,
            (tzolkin_tone - 1) % 13,
            haab_month_idx,
            haab_day,
            lc_baktun,
            lc_katun,
            lc_tun,
            lc_winal,
            lc_kin,
            kin_of_long_count % 260,
            seed % 1000,
        ]

        structural_features = {
            "day_sign_diversity": 1 / 20,
            "tone_distribution": tzolkin_tone / 13,
            "haab_month_position": haab_month_idx / 19,
            "year_bearer": year_bearer,
            "year_bearer_idx": YEAR_BEARRERS.index(year_bearer),
            "long_count_depth": sum([lc_baktun, lc_katun, lc_tun, lc_winal, lc_kin]),
            "galactic_signature": (day_sign_idx * tzolkin_tone) % 260,
            "tzolkin_cycle_position": kin_of_long_count % 260,
            "haab_cycle_position": kin_of_long_count % 365,
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

        dt = date(year, month, day)
        jdn = _date_to_julian_day_number(dt)

        day_sign_idx = (jdn + seed) % 20
        tzolkin_tone = (jdn + seed) % 13 + 1
        tzolkin_day = DAY_SIGNS[day_sign_idx]

        days_in_haab_cycle = (jdn + seed) % 365
        haab_month_idx = 0
        accumulated = 0
        month_lengths = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 5]
        for i, ml in enumerate(month_lengths):
            if accumulated + ml > days_in_haab_cycle:
                haab_month_idx = i
                break
            accumulated += ml
        haab_day = days_in_haab_cycle - accumulated
        haab_month = MONTHS_HAAB[haab_month_idx]

        days_since_baktun_start = (year - 2012) * 365 + month * 30 + day
        lc_baktun = 13
        lc_katun = days_since_baktun_start // 7200
        lc_tun = (days_since_baktun_start % 7200) // 360
        lc_winal = (days_since_baktun_start % 360) // 20
        lc_kin = days_since_baktun_start % 20

        year_bearer = YEAR_BEARRERS[day_sign_idx % 4]
        kin_of_long_count = lc_baktun * 144000 + lc_katun * 7200 + lc_tun * 360 + lc_winal * 20 + lc_kin

        symbolic_state = {
            "tzolkin_date": f"{tzolkin_tone}-{tzolkin_day}",
            "tzolkin_day": tzolkin_day,
            "tzolkin_tone": tzolkin_tone,
            "haab_date": f"{haab_day} {haab_month}",
            "haab_month": haab_month,
            "haab_day": haab_day,
            "long_count": {
                "baktun": lc_baktun,
                "katun": lc_katun,
                "tun": lc_tun,
                "winal": lc_winal,
                "kin": lc_kin,
            },
            "kin_of_long_count": kin_of_long_count,
        }

        numeric_projection = [
            day_sign_idx,
            (tzolkin_tone - 1) % 13,
            haab_month_idx,
            haab_day,
            lc_baktun,
            lc_katun,
            lc_tun,
            lc_winal,
            lc_kin,
            kin_of_long_count % 260,
            seed % 1000,
        ]

        structural_features = {
            "day_sign_diversity": 1 / 20,
            "tone_distribution": tzolkin_tone / 13,
            "haab_month_position": haab_month_idx / 19,
            "year_bearer": year_bearer,
            "year_bearer_idx": YEAR_BEARRERS.index(year_bearer),
            "long_count_depth": sum([lc_baktun, lc_katun, lc_tun, lc_winal, lc_kin]),
            "galactic_signature": (day_sign_idx * tzolkin_tone) % 260,
            "tzolkin_cycle_position": kin_of_long_count % 260,
            "haab_cycle_position": kin_of_long_count % 365,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
