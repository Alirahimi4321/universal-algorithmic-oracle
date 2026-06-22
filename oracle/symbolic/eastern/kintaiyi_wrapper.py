"""Kintaiyi wrapper: 太乙神數 (Taiyi Shenshu) - One of the Three Great Chinese Divination Systems."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_KINTAIYI = False
try:
    from kintaiyi.kintaiyi import Taiyi as _Taiyi
    HAS_KINTAIYI = True
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
class KintaiyiWrapper(SymbolicSystemWrapper):
    """Taiyi Shenshu (太乙神數) divination using kintaiyi library."""
    SYSTEM_ID = "kintaiyi"
    LIBRARY_BACKEND = "kintaiyi"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_KINTAIYI:
            try:
                t = _Taiyi(dt.year, dt.month, dt.day, dt.hour, dt.minute)
                ji_style = params.get("ji_style", 0)
                acum_style = params.get("acum_style", 0)

                pan_result = t.pan(ji_style, acum_style)
                symbolic_state = {
                    "ji_style": ["年計", "月計", "日計", "時計", "分計"][ji_style],
                    "acum_style": acum_style,
                    "lunar_date": str(pan_result.get("農曆", "")),
                    "ganzhi": str(pan_result.get("干支", "")),
                    "jiyuan": str(pan_result.get("紀元", "")),
                    "taishui": str(pan_result.get("太歲", "")),
                    "ju_shi": str(pan_result.get("局式", "")),
                    "taiyi_palace": str(pan_result.get("太乙落宮", "")),
                    "taiyi_gua": str(pan_result.get("太乙", "")),
                    "tianyi": str(pan_result.get("天乙", "")),
                    "diyi": str(pan_result.get("地乙", "")),
                    "si_shen": str(pan_result.get("四神", "")),
                    "zhifu": str(pan_result.get("直符", "")),
                    "wen_chang": str(pan_result.get("文昌", "")),
                    "shiji": str(pan_result.get("始擊", "")),
                    "zhu_suan": str(pan_result.get("主算", "")),
                    "ke_suan": str(pan_result.get("客算", "")),
                    "ding_suan": str(pan_result.get("定算", "")),
                    "ba_men": str(pan_result.get("八門值事", "")),
                    "wu_fan": str(pan_result.get("陽九", "")),
                    "bai_liu": str(pan_result.get("百六", "")),
                    "raw": str(pan_result),
                }

                zhu_suan = pan_result.get("主算", [0, []])
                ke_suan = pan_result.get("客算", [0, []])
                ding_suan = pan_result.get("定算", [0, []])
                zhu_num = zhu_suan[0] if isinstance(zhu_suan, (list, tuple)) else 0
                ke_num = ke_suan[0] if isinstance(ke_suan, (list, tuple)) else 0
                ding_num = ding_suan[0] if isinstance(ding_suan, (list, tuple)) else 0

                numeric_projection = [
                    ji_style,
                    acum_style,
                    hash(str(symbolic_state["ganzhi"])) % 60,
                    hash(str(symbolic_state["jiyuan"])) % 36,
                    int(zhu_num) % 100,
                    int(ke_num) % 100,
                    int(ding_num) % 100,
                    hash(str(symbolic_state["taiyi_gua"])) % 8,
                    hash(str(symbolic_state["wen_chang"])) % 12,
                    hash(str(symbolic_state["shiji"])) % 12,
                ]

                structural_features = {
                    "ji_style": ji_style,
                    "has_pan_data": True,
                    "computed_fields": len(pan_result),
                    "time_precision": "minute",
                    "backend": "kintaiyi",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output=pan_result,
                    params=params,
                )
            except Exception as e:
                logger.warning("kintaiyi compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "ji_style": "年計",
            "acum_style": 0,
            "lunar_date": "",
            "ganzhi": "",
            "jiyuan": "",
            "taishui": "",
            "ju_shi": "",
            "taiyi_palace": "",
            "taiyi_gua": "",
            "backend": "kintaiyi_fallback",
        }
        numeric_projection = [
            dt.year % 10, dt.month % 12, dt.day % 30, dt.hour % 12, dt.minute % 60,
            seed % 100, 0, 0, 0, 0,
        ]
        structural_features = {
            "ji_style": 0,
            "has_pan_data": False,
            "computed_fields": 0,
            "time_precision": "minute",
            "backend": "fallback",
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
