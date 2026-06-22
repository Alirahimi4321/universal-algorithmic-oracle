"""Chinese Meihua (Plum Blossom) divination wrapper using meihua-yi."""
import time
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from meihua_yi import qigua_time, qigua_coin, compute_hexagrams, get_gua_name, BAGUA, GUA_NAMES
    MEIHUA_AVAILABLE = True
except ImportError:
    MEIHUA_AVAILABLE = False


def _extract_datetime(entropy_packet: dict) -> datetime:
    ts = entropy_packet.get("timestamp", time.time())
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(tz=timezone.utc)


@register_system
class MeihuaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "meihua_yishu"
    LIBRARY_BACKEND = "meihua-yi"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)
        seed = entropy_packet.get("seed", 0)

        ben_gua = []
        bian_gua = []
        moving_yao = []
        gua_names = ("", "")

        if MEIHUA_AVAILABLE:
            try:
                yao_list, moving = qigua_time(dt)
                ben_gua = yao_list
                moving_yao = moving
                if len(yao_list) >= 6:
                    lower = yao_list[:3]
                    upper = yao_list[3:6]
                    gua_names = (
                        get_gua_name(tuple(lower)),
                        get_gua_name(tuple(upper))
                    )
                    # Compute changed hexagram
                    bian_gua = list(yao_list)
                    for idx in moving_yao:
                        if idx < len(bian_gua):
                            bian_gua[idx] = 1 - bian_gua[idx]
            except Exception:
                pass

        symbolic_state = {
            "solar_date": dt.strftime("%Y-%m-%d %H:%M"),
            "ben_gua": ben_gua,
            "bian_gua": bian_gua,
            "moving_yao": moving_yao,
            "ben_gua_names": gua_names,
            "yao_count": len(ben_gua),
            "moving_count": len(moving_yao),
        }
        numeric_projection = (
            [int(y) for y in ben_gua] +
            [int(y) for y in bian_gua] +
            moving_yao +
            [len(ben_gua), len(moving_yao), seed % 1000]
        )
        # Pad to at least 10
        while len(numeric_projection) < 10:
            numeric_projection.append(0)
        structural_features = {
            "has_moving_yao": bool(moving_yao),
            "gua_changed": ben_gua != bian_gua,
            "ben_gua_name": gua_names[0],
            "bian_gua_name": gua_names[1],
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection[:20],
            structural_features=structural_features,
            params=params,
        )
