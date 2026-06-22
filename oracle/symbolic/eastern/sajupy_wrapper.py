"""Korean Saju (Four Pillars) wrapper using sajupy."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from sajupy import SajuCalculator
    SAJUPY_AVAILABLE = True
except ImportError:
    SAJUPY_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class SajuPyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "korean_saju_py"
    LIBRARY_BACKEND = "sajupy"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)
        city = params.get("city", "Seoul")

        result = {}
        if SAJUPY_AVAILABLE:
            try:
                sc = SajuCalculator()
                result = sc.calculate_saju_from_datetime(dt, city=city)
            except Exception:
                pass

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d %H:%M"),
            "city": city,
            "result": result if isinstance(result, dict) else {},
        }
        # Extract pillars from result
        year_pillar = result.get("year_pillar", "") if isinstance(result, dict) else ""
        month_pillar = result.get("month_pillar", "") if isinstance(result, dict) else ""
        day_pillar = result.get("day_pillar", "") if isinstance(result, dict) else ""
        hour_pillar = result.get("hour_pillar", "") if isinstance(result, dict) else ""

        symbolic_state.update({
            "year_pillar": str(year_pillar),
            "month_pillar": str(month_pillar),
            "day_pillar": str(day_pillar),
            "hour_pillar": str(hour_pillar),
        })
        numeric_projection = [
            dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
            hash(str(year_pillar)) % 10,
            hash(str(month_pillar)) % 12,
            hash(str(day_pillar)) % 10,
            hash(str(hour_pillar)) % 12,
            seed % 1000,
        ]
        structural_features = {
            "has_year_pillar": bool(year_pillar),
            "has_month_pillar": bool(month_pillar),
            "has_day_pillar": bool(day_pillar),
            "has_hour_pillar": bool(hour_pillar),
            "city": city,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
