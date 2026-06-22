"""Korean Zi Wei Dou Shu (紫微斗數) wrapper using iztro_py."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from iztro_py import by_solar as iztro_solar
    from iztro_py.astro import get_sign_by_solar_date, get_zodiac_by_solar_date
    IZTRO_AVAILABLE = True
except ImportError:
    IZTRO_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class IztroWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "iztro_ziwei"
    LIBRARY_BACKEND = "iztro_py"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)
        gender = params.get("gender", "male")

        palaces = {}
        main_star = ""
        life_palace = ""
        body_palace = ""

        if IZTRO_AVAILABLE:
            try:
                chart = iztro_solar(
                    dt.year, dt.month, dt.day,
                    hour=dt.hour, gender=gender
                )
                if hasattr(chart, "palaces"):
                    for p in chart.palaces:
                        name = getattr(p, "name", str(p))
                        palaces[name] = str(p)
                main_star = str(getattr(chart, "main_star", ""))
                life_palace = str(getattr(chart, "life_palace", ""))
                body_palace = str(getattr(chart, "body_palace", ""))
            except Exception:
                pass

        sign = ""
        zodiac = ""
        if IZTRO_AVAILABLE:
            try:
                sign = get_sign_by_solar_date(dt.month, dt.day)
            except Exception:
                pass
            try:
                zodiac = get_zodiac_by_solar_date(dt.month, dt.day)
            except Exception:
                pass

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d"),
            "gender": gender,
            "sign": str(sign),
            "zodiac": str(zodiac),
            "palaces": palaces,
            "main_star": main_star,
            "life_palace": life_palace,
            "body_palace": body_palace,
        }
        numeric_projection = [
            dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
            len(palaces), hash(main_star) % 50, hash(life_palace) % 12,
            seed % 1000,
        ]
        structural_features = {
            "palace_count": len(palaces),
            "has_main_star": bool(main_star),
            "has_life_palace": bool(life_palace),
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
