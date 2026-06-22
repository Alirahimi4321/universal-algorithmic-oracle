"""PyVO wrapper: Virtual Observatory access for astronomical data."""
import time
import logging
from datetime import datetime, timezone
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_PYVO = False
try:
    import pyvo
    HAS_PYVO = True
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
class PyVOWrapper(SymbolicSystemWrapper):
    """Astronomical data access via Virtual Observatory."""
    SYSTEM_ID = "pyvo_astro"
    LIBRARY_BACKEND = "pyvo"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        dt = _extract_datetime(entropy_packet)

        if HAS_PYVO:
            try:
                services = pyvo.regsearch()
                service_list = [
                    {"title": getattr(s, "title", ""), "ivoid": getattr(s, "ivoid", "")}
                    for s in services[:20]
                ]

                symbolic_state = {
                    "service_count": len(service_list),
                    "services": service_list[:10],
                    "available_queries": ["conesearch", "sia", "ssa", "tap"],
                    "query_date": dt.isoformat(),
                }

                numeric_projection = [
                    len(service_list) % 100,
                    hash(str(service_list[:5])) % 1000,
                    dt.year % 100,
                    dt.month % 12,
                    dt.day % 30,
                ]

                structural_features = {
                    "service_count": len(service_list),
                    "has_services": bool(service_list),
                    "time_precision": "day",
                    "backend": "pyvo",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    params=params,
                )
            except Exception as e:
                logger.warning("pyvo compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params, dt)

    def _compute_fallback(self, entropy_packet, params, dt):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {"service_count": 0, "services": [], "backend": "pyvo_fallback"}
        numeric_projection = [0, seed % 1000, dt.year % 100, dt.month % 12, dt.day % 30]
        structural_features = {"service_count": 0, "has_services": False, "time_precision": "day", "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
