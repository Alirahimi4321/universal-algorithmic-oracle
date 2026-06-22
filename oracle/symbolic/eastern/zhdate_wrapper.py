"""Chinese zodiac date wrapper using zhdate."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from zhdate import ZhDate
    ZHDATE_AVAILABLE = True
except ImportError:
    ZHDATE_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class ZhDateWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "zhdate"
    LIBRARY_BACKEND = "zhdate"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)

        lunar_str = ""
        lunar_year = dt.year
        lunar_month = dt.month
        lunar_day = dt.day

        if ZHDATE_AVAILABLE:
            try:
                zdate = ZhDate.from_datetime(dt)
                lunar_year = zdate.lunar_year
                lunar_month = zdate.lunar_month
                lunar_day = zdate.lunar_day
                lunar_str = str(zdate)
            except Exception:
                pass

        shengxiao = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
        zodiac_idx = (lunar_year - 4) % 12
        zodiac = shengxiao[zodiac_idx] if 0 <= zodiac_idx < 12 else ""

        stem_branch = ["甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
                       "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
                       "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
                       "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
                       "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
                       "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"]
        ganzhi_idx = (lunar_year - 4) % 60
        ganzhi = stem_branch[ganzhi_idx] if 0 <= ganzhi_idx < 60 else ""

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d"),
            "lunar_str": lunar_str,
            "lunar_year": lunar_year,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "zodiac": zodiac,
            "ganzhi_year": ganzhi,
        }
        numeric_projection = [
            lunar_year % 10, lunar_month % 12, lunar_day % 30,
            zodiac_idx, ganzhi_idx % 10, seed % 1000,
        ]
        structural_features = {
            "zodiac_index": zodiac_idx,
            "cycle_position": ganzhi_idx,
            "lunar_year_offset": lunar_year - dt.year,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
