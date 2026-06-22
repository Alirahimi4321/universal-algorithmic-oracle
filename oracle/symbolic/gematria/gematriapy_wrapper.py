"""Hebrew Gematria wrapper using gematriapy."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from gematriapy import gematria, to_hebrew, to_number
    GEMATRIAPY_AVAILABLE = True
except ImportError:
    GEMATRIAPY_AVAILABLE = False


@register_system
class GematriapyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "gematriapy"
    LIBRARY_BACKEND = "gematriapy"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)

        gematria_val = 0
        if GEMATRIAPY_AVAILABLE:
            try:
                gematria_val = gematria(text)
            except Exception:
                pass

        digit_sum = sum(int(d) for d in str(abs(gematria_val))) if gematria_val else 0
        reduced = gematria_val
        while reduced >= 10 and reduced > 0:
            reduced = sum(int(d) for d in str(reduced))

        symbolic_state = {
            "text": text,
            "gematria_value": gematria_val,
            "digit_sum": digit_sum,
            "reduced_value": reduced,
        }
        numeric_projection = [gematria_val, digit_sum, reduced, len(text), seed % 1000]
        structural_features = {
            "total_value": gematria_val,
            "value_entropy": gematria_val / max(len(text), 1),
            "letter_diversity": len(set(text)) / max(len(text), 1),
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
