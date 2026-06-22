"""Tianji library wrappers: BaZi, ZiWei, QiMen, LiuRen."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from tianji.bazi import BaZiChart
    TIANJI_BAZI_AVAILABLE = True
except ImportError:
    TIANJI_BAZI_AVAILABLE = False

try:
    from tianji.ziwei import create_ziwei_chart
    TIANJI_ZIWEI_AVAILABLE = True
except ImportError:
    TIANJI_ZIWEI_AVAILABLE = False

try:
    from tianji.qimen import QiMenChart
    TIANJI_QIMEN_AVAILABLE = True
except ImportError:
    TIANJI_QIMEN_AVAILABLE = False

try:
    from tianji.liuren import LiuRenChart
    TIANJI_LIUREN_AVAILABLE = True
except ImportError:
    TIANJI_LIUREN_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class TianjiBaZiWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tianji_bazi"
    LIBRARY_BACKEND = "tianji"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if TIANJI_BAZI_AVAILABLE:
            try:
                chart = BaZiChart(
                    year=dt.year, month=dt.month, day=dt.day, hour=dt.hour
                )
                chart.compute()
                symbolic_state = {
                    "year_pillar": getattr(chart, "year_pillar", str(getattr(chart, "yearGanZhi", ""))),
                    "month_pillar": getattr(chart, "month_pillar", str(getattr(chart, "monthGanZhi", ""))),
                    "day_pillar": getattr(chart, "day_pillar", str(getattr(chart, "dayGanZhi", ""))),
                    "hour_pillar": getattr(chart, "hour_pillar", str(getattr(chart, "hourGanZhi", ""))),
                    "five_elements": getattr(chart, "five_elements", getattr(chart, "wuXing", {})),
                    "raw": str(chart),
                }
                numeric_projection = [
                    hash(str(symbolic_state.get("year_pillar", ""))) % 10,
                    hash(str(symbolic_state.get("month_pillar", ""))) % 12,
                    hash(str(symbolic_state.get("day_pillar", ""))) % 10,
                    hash(str(symbolic_state.get("hour_pillar", ""))) % 12,
                    dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
                ]
                structural_features = {
                    "element_count": len(symbolic_state.get("five_elements", {})),
                    "time_precision": "hour",
                    "backend": "tianji.bazi",
                }
                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"chart_str": str(chart)},
                    params=params,
                )
            except Exception:
                pass

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "year_pillar": f"{dt.year % 60} cycle",
            "month_pillar": f"{dt.month} cycle",
            "day_pillar": f"{dt.day} cycle",
            "hour_pillar": f"{dt.hour} cycle",
            "five_elements": {},
            "backend": "tianji_bazi_fallback",
        }
        numeric_projection = [dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12, seed % 100]
        structural_features = {"element_count": 0, "time_precision": "hour", "backend": "fallback"}
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )


@register_system
class TianjiZiWeiWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tianji_ziwei"
    LIBRARY_BACKEND = "tianji"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if TIANJI_ZIWEI_AVAILABLE:
            try:
                chart = create_ziwei_chart(
                    year=dt.year, month=dt.month, day=dt.day, hour=dt.hour
                )
                houses = getattr(chart, "houses", getattr(chart, "palaces", {}))
                if callable(houses):
                    houses = {}
                symbolic_state = {
                    "houses": dict(houses) if houses else {},
                    "main_star": getattr(chart, "main_star", getattr(chart, "mingZhu", "")),
                    "life_palace": getattr(chart, "life_palace", getattr(chart, "mingGong", "")),
                    "body_palace": getattr(chart, "body_palace", getattr(chart, "shenGong", "")),
                    "raw": str(chart),
                }
                house_count = len(symbolic_state["houses"])
                numeric_projection = [
                    dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
                    house_count % 100, hash(str(symbolic_state["main_star"])) % 50,
                    hash(str(symbolic_state["life_palace"])) % 12,
                ]
                structural_features = {
                    "house_count": house_count,
                    "has_body_palace": bool(symbolic_state["body_palace"]),
                    "time_precision": "hour",
                    "backend": "tianji.ziwei",
                }
                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"chart_str": str(chart)},
                    params=params,
                )
            except Exception:
                pass

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "houses": {},
            "main_star": "",
            "life_palace": "",
            "body_palace": "",
            "backend": "tianji_ziwei_fallback",
        }
        numeric_projection = [dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12, seed % 100]
        structural_features = {"house_count": 0, "has_body_palace": False, "time_precision": "hour", "backend": "fallback"}
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )


@register_system
class TianjiQiMenWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tianji_qimen"
    LIBRARY_BACKEND = "tianji"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if TIANJI_QIMEN_AVAILABLE:
            try:
                chart = QiMenChart(
                    year=dt.year, month=dt.month, day=dt.day, hour=dt.hour
                )
                chart.compute()
                symbolic_state = {
                    "ju_number": getattr(chart, "ju_number", getattr(chart, "juShu", 0)),
                    "stem": getattr(chart, "stem", getattr(chart, "tianGan", "")),
                    "door": getattr(chart, "door", getattr(chart, "baMen", "")),
                    "deity": getattr(chart, "deity", getattr(chart, "baShen", "")),
                    "nine_palaces": getattr(chart, "nine_palaces", getattr(chart, "jiuGong", [])),
                    "raw": str(chart),
                }
                numeric_projection = [
                    dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
                    hash(str(symbolic_state["stem"])) % 10,
                    hash(str(symbolic_state["door"])) % 8,
                    hash(str(symbolic_state["deity"])) % 8,
                    symbolic_state["ju_number"] % 20 if isinstance(symbolic_state["ju_number"], int) else 0,
                ]
                structural_features = {
                    "palace_count": len(symbolic_state["nine_palaces"]) if isinstance(symbolic_state["nine_palaces"], list) else 0,
                    "time_precision": "hour",
                    "backend": "tianji.qimen",
                }
                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"chart_str": str(chart)},
                    params=params,
                )
            except Exception:
                pass

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "ju_number": 0,
            "stem": "",
            "door": "",
            "deity": "",
            "nine_palaces": [],
            "backend": "tianji_qimen_fallback",
        }
        numeric_projection = [dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12, seed % 100]
        structural_features = {"palace_count": 0, "time_precision": "hour", "backend": "fallback"}
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )


@register_system
class TianjiLiuRenWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tianji_liuren"
    LIBRARY_BACKEND = "tianji"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if TIANJI_LIUREN_AVAILABLE:
            try:
                chart = LiuRenChart(
                    year=dt.year, month=dt.month, day=dt.day, hour=dt.hour
                )
                chart.compute()
                symbolic_state = {
                    "four_displays": getattr(chart, "four_displays", getattr(chart, "siZhu", [])),
                    "twelve_officers": getattr(chart, "twelve_officers", getattr(chart, "shiErShen", [])),
                    "heavenly_plate": getattr(chart, "heavenly_plate", getattr(chart, "tianPan", [])),
                    "earthly_plate": getattr(chart, "earthly_plate", getattr(chart, "diPan", [])),
                    "raw": str(chart),
                }
                numeric_projection = [
                    dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12,
                    len(symbolic_state["four_displays"]) if isinstance(symbolic_state["four_displays"], list) else 0,
                    len(symbolic_state["twelve_officers"]) if isinstance(symbolic_state["twelve_officers"], list) else 0,
                    len(symbolic_state["heavenly_plate"]) if isinstance(symbolic_state["heavenly_plate"], list) else 0,
                    len(symbolic_state["earthly_plate"]) if isinstance(symbolic_state["earthly_plate"], list) else 0,
                ]
                structural_features = {
                    "display_count": len(symbolic_state["four_displays"]) if isinstance(symbolic_state["four_displays"], list) else 0,
                    "time_precision": "hour",
                    "backend": "tianji.liuren",
                }
                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output={"chart_str": str(chart)},
                    params=params,
                )
            except Exception:
                pass

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "four_displays": [],
            "twelve_officers": [],
            "heavenly_plate": [],
            "earthly_plate": [],
            "backend": "tianji_liuren_fallback",
        }
        numeric_projection = [dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12, seed % 100]
        structural_features = {"display_count": 0, "time_precision": "hour", "backend": "fallback"}
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
