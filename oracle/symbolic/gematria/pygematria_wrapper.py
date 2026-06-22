"""PyGematria wrapper — multi-system gematria (Hebrew, Greek, Agrippa, English Qaballa)."""
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_PYGEMATRIA = False
try:
    from pygematria import conv
    HAS_PYGEMATRIA = True
except ImportError:
    pass


@register_system
class PyGematriaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "pygematria"
    LIBRARY_BACKEND = "pygematria"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not HAS_PYGEMATRIA:
            return self._build_output({}, [], {"error": "pygematria not installed"})

        text = (params or {}).get("text", entropy_packet.get("text", "hello"))
        system = (params or {}).get("system", "hebrew")

        dicts = {
            "hebrew": "hebrew",
            "greek": "greek",
            "agrippa": "agrippa",
            "english_qaballa": "english_qaballa",
            "rudolff": "rudolff",
        }

        results = {}
        for sys_name, dict_name in dicts.items():
            try:
                vals = conv.string_values(text, dict_name)
                results[sys_name] = sum(vals) if vals else 0
            except Exception:
                try:
                    nums = conv.string_to_nums(text, dict_name)
                    results[sys_name] = sum(int(n) for n in nums if str(n).isdigit()) if nums else 0
                except Exception:
                    results[sys_name] = 0

        primary = results.get(system, 0)
        numeric = [float(v) for v in results.values()] + [float(primary)]

        return self._build_output(
            symbolic_state={
                "text": text,
                "system": system,
                "results": results,
                "primary_value": primary,
                "reduced": primary % 9 + 1 if primary else 1,
            },
            numeric_projection=numeric,
            structural_features={
                "primary_value": primary,
                "num_systems": len(results),
                "systems_used": list(results.keys()),
            },
        )
