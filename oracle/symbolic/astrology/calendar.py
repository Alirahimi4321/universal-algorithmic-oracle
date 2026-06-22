"""Multi-calendar system wrapper for temporal entropy."""
import datetime
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + (
        (gy2 + 399) // 400
    ) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def gregorian_to_hijri(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    jd = (
        int((1461 * (gy + 4800 + int((gm - 14) / 12))) / 4)
        + int((367 * (gm - 2 - 12 * int((gm - 14) / 12))) / 12)
        - int((3 * int((gy + 4900 + int((gm - 14) / 12)) / 100)) / 4)
        + gd
        - 32075
    )
    l = jd - 1948440 + 10632
    n = int((l - 1) / 10631)
    l = l - 10631 * n + 354
    j = int((10985 - l) / 5316) * int((50 * l) / 17719) + int(l / 5670) * int(
        (43 * l) / 15238
    )
    l = l - int((30 - j) / 15) * int((17719 * j) / 50) - int(j / 16) * int(
        (15238 * j) / 43
    ) + 29
    hm = int((24 * l) / 709)
    hd = l - int((709 * hm) / 24)
    hy = 30 * n + j - 30
    return hy, hm, hd


@register_system
class CalendarWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "calendar"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        timestamp = float(entropy_packet.get("timestamp", 0))
        cal_ctx = entropy_packet.get("calendar_context", {})

        dt = datetime.datetime.fromtimestamp(timestamp)
        gy, gm, gd = dt.year, dt.month, dt.day

        jy, jm, jd = gregorian_to_jalali(gy, gm, gd)
        hy, hm, hd = gregorian_to_hijri(gy, gm, gd)

        day_of_year = dt.timetuple().tm_yday
        week_of_year = dt.isocalendar()[1]
        days_in_month = (dt.replace(month=dt.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day

        symbolic_state = {
            "gregorian": {"year": gy, "month": gm, "day": gd},
            "jalali": {"year": jy, "month": jm, "day": jd},
            "hijri": {"year": hy, "month": hm, "day": hd},
            "time": {"hour": dt.hour, "minute": dt.minute, "second": dt.second},
            "weekday": dt.weekday(),
            "weekday_name": dt.strftime("%A"),
        }

        numeric_projection = [
            gy,
            gm,
            gd,
            jy,
            jm,
            jd,
            hy,
            hm,
            hd,
            dt.hour,
            dt.minute,
            day_of_year,
            week_of_year,
            dt.weekday(),
            days_in_month,
        ]

        month_cycle = gm / 12.0
        hour_cycle = dt.hour / 24.0
        weekday_polarity = 1.0 if dt.weekday() < 5 else 0.0

        structural_features = {
            "month_cycle_position": month_cycle,
            "hour_cycle_position": hour_cycle,
            "weekday_polarity": weekday_polarity,
            "jalali_modulus_12": jy % 12,
            "hijri_modulus_30": hd,
            "day_of_year_normalized": day_of_year / 365.0,
            "calendar_resonance": (jy % 12 + jm) / 13.0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
