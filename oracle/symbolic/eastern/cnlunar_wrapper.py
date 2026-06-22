"""Chinese Lunar Calendar wrapper using cnlunar."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from cnlunar import Lunar
    CNLUNAR_AVAILABLE = True
except ImportError:
    CNLUNAR_AVAILABLE = False

try:
    from cnlunar import holidays as cnholidays
    CNLUNAR_HOLIDAYS_AVAILABLE = True
except ImportError:
    CNLUNAR_HOLIDAYS_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class CnLunarWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "cnlunar"
    LIBRARY_BACKEND = "cnlunar"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d"),
            "lunar_year": 0, "lunar_month": 0, "lunar_day": 0,
            "ganzhi_year": "", "ganzhi_month": "", "ganzhi_day": "",
            "shengxiao": "", "solar_term": "", "festival": "",
            "is_leap_month": False,
        }

        if CNLUNAR_AVAILABLE:
            try:
                lunar = Lunar(dt)
                symbolic_state.update({
                    "lunar_year": getattr(lunar, "lunarYear", 0),
                    "lunar_month": getattr(lunar, "lunarMonth", 0),
                    "lunar_day": getattr(lunar, "lunarDay", 0),
                    "ganzhi_year": str(getattr(lunar, "year8Char", "")),
                    "ganzhi_month": str(getattr(lunar, "month8Char", "")),
                    "ganzhi_day": str(getattr(lunar, "day8Char", "")),
                    "shengxiao": str(getattr(lunar, "chineseYearZodiac", "")),
                    "solar_term": str(getattr(lunar, "todaySolarTerms", "")),
                    "festival": str(getattr(lunar, "todaySolarTerms", "")),
                    "is_leap_month": bool(getattr(lunar, "isLunarLeapMonth", False)),
                })
            except Exception:
                pass

        numeric_projection = [
            symbolic_state["lunar_year"] % 10,
            symbolic_state["lunar_month"] % 12,
            symbolic_state["lunar_day"] % 30,
            hash(symbolic_state["ganzhi_year"]) % 10,
            hash(symbolic_state["shengxiao"]) % 12,
            seed % 1000,
        ]
        structural_features = {
            "has_ganzhi": bool(symbolic_state["ganzhi_year"]),
            "has_shengxiao": bool(symbolic_state["shengxiao"]),
            "has_solar_term": bool(symbolic_state["solar_term"]),
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
