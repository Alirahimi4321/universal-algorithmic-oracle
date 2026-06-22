"""Kinliuren wrapper: 大六壬 (Da Liu Ren) - One of the Three Great Chinese Divination Systems."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_KINLIUREN = False
try:
    from kinliuren.kinliuren import Liuren as _Liuren
    HAS_KINLIUREN = True
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


JIEQI_NAMES = [
    "小寒", "大寒", "立春", "雨水", "驚蟄", "春分",
    "清明", "穀雨", "立夏", "小滿", "芒種", "夏至",
    "小暑", "大暑", "立秋", "處暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

GANGZHI = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"


def _get_jieqi_and_month(dt: datetime) -> tuple[str, int]:
    month = dt.month
    day = dt.day
    solar_term_days = [
        (1, 6), (1, 20), (2, 4), (2, 19), (3, 6), (3, 21),
        (4, 5), (4, 20), (5, 6), (5, 21), (6, 6), (6, 21),
        (7, 7), (7, 23), (8, 7), (8, 23), (9, 8), (9, 23),
        (10, 8), (10, 23), (11, 7), (11, 22), (12, 7), (12, 22),
    ]
    cmonth = ((month - 1) * 2) + (1 if day < solar_term_days[(month - 1) * 2][1] else 0)
    cmonth = cmonth % 24
    jieqi_idx = cmonth
    return JIEQI_NAMES[jieqi_idx % 12], ((month - 1) % 12) + 1


def _day_gangzhi(dt: datetime) -> str:
    base = datetime(1900, 1, 31)
    dt_naive = dt.replace(tzinfo=None)
    diff = (dt_naive - base).days
    gan_idx = diff % 10
    zhi_idx = diff % 12
    return GANGZHI[gan_idx] + DIZHI[zhi_idx]


def _hour_gangzhi(dt: datetime, day_gz: str) -> str:
    hour = dt.hour
    zhi_idx = ((hour + 1) // 2) % 12
    day_gan = day_gz[0]
    gan_base = GANGZHI.index(day_gan) % 5
    hour_gan_idx = (gan_base * 2 + zhi_idx) % 10
    return GANGZHI[hour_gan_idx] + DIZHI[zhi_idx]


@register_system
class KinliurenWrapper(SymbolicSystemWrapper):
    """Da Liu Ren (大六壬) divination using kinliuren library."""
    SYSTEM_ID = "kinliuren"
    LIBRARY_BACKEND = "kinliuren"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_KINLIUREN:
            try:
                jieqi, cmonth = _get_jieqi_and_month(dt)
                day_gz = _day_gangzhi(dt)
                hour_gz = _hour_gangzhi(dt, day_gz)

                l = _Liuren(jieqi, cmonth, day_gz, hour_gz)
                result = l.result(0)

                three_pass = result.get("三傳", {})
                four_ke = result.get("四課", {})
                sky_earth = result.get("天地盤", {})
                geju = result.get("格局", [])

                symbolic_state = {
                    "jieqi": jieqi,
                    "cmonth": cmonth,
                    "day_gangzhi": day_gz,
                    "hour_gangzhi": hour_gz,
                    "geju": str(geju),
                    "san_chuan": str(three_pass),
                    "si_ke": str(four_ke),
                    "tian_di_pan": str(sky_earth),
                    "di_zhuan_tian": str(result.get("地轉天盤", {})),
                    "di_zhuan_tian_jiang": str(result.get("地轉天將", {})),
                    "ri_ma": str(result.get("日馬", "")),
                    "raw": str(result),
                }

                chusan = three_pass.get("初傳", ["", "", "", ""])
                zhongchuan = three_pass.get("中傳", ["", "", "", ""])
                mochuan = three_pass.get("末傳", ["", "", "", ""])

                numeric_projection = [
                    hash(jieqi) % 12,
                    cmonth % 12,
                    hash(day_gz) % 60,
                    hash(hour_gz) % 60,
                    hash(str(chusan[0])) % 12 if chusan[0] else 0,
                    hash(str(chusan[2])) % 5 if len(chusan) > 2 else 0,
                    hash(str(zhongchuan[0])) % 12 if zhongchuan[0] else 0,
                    hash(str(mochuan[0])) % 12 if mochuan[0] else 0,
                    len(str(geju)) % 10,
                ]

                structural_features = {
                    "has_three_pass": bool(three_pass),
                    "has_four_ke": bool(four_ke),
                    "has_sky_earth_plate": bool(sky_earth),
                    "geju_count": len(geju) if isinstance(geju, list) else 0,
                    "time_precision": "hour",
                    "backend": "kinliuren",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output=result,
                    params=params,
                )
            except Exception as e:
                logger.warning("kinliuren compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {
            "jieqi": "",
            "cmonth": 0,
            "day_gangzhi": "",
            "hour_gangzhi": "",
            "geju": "",
            "san_chuan": "",
            "si_ke": "",
            "tian_di_pan": "",
            "backend": "kinliuren_fallback",
        }
        numeric_projection = [
            dt.year % 12, dt.month % 12, dt.day % 60, dt.hour % 60,
            seed % 100, 0, 0, 0, 0,
        ]
        structural_features = {
            "has_three_pass": False,
            "has_four_ke": False,
            "has_sky_earth_plate": False,
            "geju_count": 0,
            "time_precision": "hour",
            "backend": "fallback",
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
