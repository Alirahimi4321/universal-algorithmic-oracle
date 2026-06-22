"""Hebrew Gematria wrapper — gematria from the `hebrew` library."""
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_HEBREW = False
try:
    from hebrew import Hebrew
    HAS_HEBREW = True
except ImportError:
    pass


@register_system
class HebrewGematriaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "hebrew_gematria"
    LIBRARY_BACKEND = "hebrew"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not HAS_HEBREW:
            return self._build_output({}, [], {"error": "hebrew not installed"})

        text = (params or {}).get("text", entropy_packet.get("text", "שלום עולם"))
        try:
            h = Hebrew(text)
            gem_val = h.gematria()
            word_count = len(h.words())
            letter_count = h.length
            no_niqqud = h.no_niqqud()
            no_maqaf = h.no_maqaf()
            normalized = h.normalize()
        except Exception as e:
            return self._build_output({}, [], {"error": str(e)})

        numeric = [
            float(gem_val),
            float(word_count),
            float(letter_count),
            float(gem_val % 9 + 1),
            float(sum(ord(c) for c in text) % 22),
        ]

        return self._build_output(
            symbolic_state={
                "text": text,
                "gematria_value": gem_val,
                "word_count": word_count,
                "letter_count": letter_count,
                "no_niqqud": no_niqqud,
                "no_maqaf": no_maqaf,
                "normalized": normalized,
                "digital_root": gem_val % 9 + 1,
            },
            numeric_projection=numeric,
            structural_features={
                "gematria_value": gem_val,
                "word_count": word_count,
                "digital_root": gem_val % 9 + 1,
            },
        )
