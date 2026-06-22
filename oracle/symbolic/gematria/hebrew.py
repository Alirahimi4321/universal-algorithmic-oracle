"""Hebrew Gematria numerology wrapper."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

HEBREW_GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7,
    "ח": 8, "ט": 9, "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50,
    "ס": 60, "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200, "ש": 300,
    "ת": 400, "ך": 20, "ם": 40, "ן": 50, "ף": 80, "ץ": 90,
}

@register_system
class HebrewGematriaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "hebrew_gematria"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)
        modulus = params.get("modulus", 22)

        gematria_val = sum(HEBREW_GEMATRIA.get(c, 0) for c in text)
        digit_sum = sum(int(d) for d in str(abs(gematria_val)))
        reduced = gematria_val
        while reduced >= 10:
            reduced = sum(int(d) for d in str(reduced))
        modular_residue = gematria_val % modulus if modulus > 0 else 0

        symbolic_state = {
            "text": text, "gematria_value": gematria_val,
            "digit_sum": digit_sum, "reduced_value": reduced,
            "modulus": modulus, "modular_residue": modular_residue,
        }
        numeric_projection = [gematria_val, digit_sum, reduced, modular_residue, len(text), seed % 1000]
        structural_features = {
            "total_value": gematria_val,
            "value_entropy": gematria_val / max(len(text), 1),
            "letter_diversity": len(set(text)) / max(len(text), 1),
            "modular_state": modular_residue % 7,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
