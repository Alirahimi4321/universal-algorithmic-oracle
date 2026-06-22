"""Lunar-Python wrapper: Chinese Lunar Calendar with BaZi, WuXing, and ShenSha."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_LUNAR = False
try:
    from lunar_python import Lunar, Solar
    HAS_LUNAR = True
except ImportError:
    pass


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class LunarPythonWrapper(SymbolicSystemWrapper):
    """Chinese Lunar Calendar using lunar-python library."""
    SYSTEM_ID = "lunar_python"
    LIBRARY_BACKEND = "lunar_python"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_LUNAR:
            try:
                solar = Solar.fromYmdHms(
                    dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second
                )
                lunar = solar.getLunar()

                bazi = lunar.getBaZi()
                wuxing = lunar.getBaZiWuXing()
                animal = lunar.getAnimal()
                nayin = lunar.getBaZiNaYin()

                symbolic_state = {
                    "lunar_year": lunar.getYear(),
                    "lunar_month": lunar.getMonth(),
                    "lunar_day": lunar.getDay(),
                    "lunar_year_cn": lunar.getYearInChinese(),
                    "lunar_month_cn": lunar.getMonthInChinese(),
                    "lunar_day_cn": lunar.getDayInChinese(),
                    "bazi": bazi,
                    "wuxing": wuxing,
                    "animal": animal,
                    "nayin": nayin,
                    "chong": lunar.getChong(),
                    "chong_desc": lunar.getChongDesc(),
                    "sha": lunar.getSha(),
                    "xi_n_shen": getattr(lunar, "getXiNShen", lambda: "")(),
                    "cai_n_shen": getattr(lunar, "getCaiNShen", lambda: "")(),
                    "yang_gui_shen": str(getattr(lunar, "getYangGuiShen", lambda: "")()),
                    "yin_gui_shen": str(getattr(lunar, "getYinGuiShen", lambda: "")()),
                    "fu_shen": str(getattr(lunar, "getFuShen", lambda: "")()),
                    "tai_sui": lunar.getYear(),
                    "day_gan": lunar.getDayGan(),
                    "day_zhi": lunar.getDayZhi(),
                    "month_gan": lunar.getMonthGan(),
                    "month_zhi": lunar.getMonthZhi(),
                    "raw": str(lunar),
                }

                bazi_hash = hash(str(bazi))
                wuxing_str = str(wuxing)
                element_counts = {}
                for e in wuxing:
                    for c in e:
                        element_counts[c] = element_counts.get(c, 0) + 1

                numeric_projection = [
                    lunar.getYear() % 10,
                    lunar.getMonth() % 12,
                    lunar.getDay() % 30,
                    bazi_hash % 60,
                    hash(animal) % 12,
                    hash(str(nayin)) % 60,
                    element_counts.get("金", 0),
                    element_counts.get("木", 0),
                    element_counts.get("水", 0),
                    element_counts.get("火", 0),
                    element_counts.get("土", 0),
                ]

                structural_features = {
                    "bazi_count": len(bazi),
                    "wuxing_count": len(wuxing),
                    "element_distribution": element_counts,
                    "has_nayin": bool(nayin),
                    "time_precision": "hour",
                    "backend": "lunar_python",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"lunar_str": str(lunar)},
                    params=params,
                )
            except Exception as e:
                logger.warning("lunar_python compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "lunar_year": dt.year,
            "lunar_month": dt.month,
            "lunar_day": dt.day,
            "bazi": [],
            "wuxing": [],
            "animal": "",
            "nayin": [],
            "backend": "lunar_python_fallback",
        }
        numeric_projection = [
            dt.year % 10, dt.month % 12, dt.day % 30, seed % 60, 0, 0, 0, 0, 0, 0, 0
        ]
        structural_features = {
            "bazi_count": 0,
            "wuxing_count": 0,
            "element_distribution": {},
            "has_nayin": False,
            "time_precision": "hour",
            "backend": "fallback",
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
