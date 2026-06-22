"""Mayan Long Count calendar wrapper."""
import hashlib
from datetime import date, timedelta
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

LONG_COUNT_EPOCH = date(2012, 12, 21)
BAKTUN_DAYS = 144000
KATUN_DAYS = 7200
TUN_DAYS = 360
WINAL_DAYS = 20


@register_system
class LongCountWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "long_count"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)

        target_date = date(year, month, day)
        days_diff = (target_date - LONG_COUNT_EPOCH).days

        if days_diff < 0:
            abs_days = abs(days_diff)
            baktun = -1 - (abs_days // BAKTUN_DAYS)
            remainder = abs_days % BAKTUN_DAYS
        else:
            baktun = days_diff // BAKTUN_DAYS
            remainder = days_diff % BAKTUN_DAYS

        katun = remainder // KATUN_DAYS
        remainder = remainder % KATUN_DAYS
        tun = remainder // TUN_DAYS
        remainder = remainder % TUN_DAYS
        winal = remainder // WINAL_DAYS
        kin = remainder % WINAL_DAYS

        kin_of_long_count = baktun * BAKTUN_DAYS + katun * KATUN_DAYS + tun * TUN_DAYS + winal * WINAL_DAYS + kin

        h = hashlib.sha256(f"{seed}_longcount_{year}_{month}_{day}".encode()).digest()

        haab_day = (days_diff % 365)
        haab_month = haab_day // 20
        haab_day_in_month = haab_day % 20

        lords_of_night = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]
        lord_of_night = lords_of_night[kin % 9]

        cycle_of_suns = (days_diff % 52) // 4 + 1

        symbolic_state = {
            "baktun": baktun,
            "katun": katun,
            "tun": tun,
            "winal": winal,
            "kin": kin,
            "kin_of_long_count": kin_of_long_count,
            "long_count_string": f"{baktun}.{katun}.{tun}.{winal}.{kin}",
            "haab": {"month": haab_month, "day": haab_day_in_month},
            "lord_of_night": lord_of_night,
            "cycle_of_suns": cycle_of_suns,
            "creation_date": "August 11, 3114 BCE",
            "baktun_13_end": "December 21, 2012",
            "days_from_epoch": days_diff,
        }

        numeric_projection = [
            abs(baktun) % 20,
            katun % 20,
            tun % 20,
            winal % 18,
            kin % 20,
            kin_of_long_count % 260,
            haab_month,
            haab_day_in_month,
            lords_of_night.index(lord_of_night),
            cycle_of_suns,
            seed % 1000,
            (baktun + katun + tun + winal + kin) % 13,
        ]

        structural_features = {
            "baktun_magnitude": abs(baktun) / 20,
            "katun_position": katun / 20,
            "tun_cyclicity": tun / 20,
            "winal_density": winal / 18,
            "kin_urgency": kin / 20,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
