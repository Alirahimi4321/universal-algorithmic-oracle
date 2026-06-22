"""English Gematria numerology wrapper."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

ENGLISH_GEMATRIA = {
    "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7,
    "h": 8, "i": 9, "j": 10, "k": 11, "l": 12, "m": 13, "n": 14,
    "o": 15, "p": 16, "q": 17, "r": 18, "s": 19, "t": 20, "u": 21,
    "v": 22, "w": 23, "x": 24, "y": 25, "z": 26,
}

@register_system
class EnglishGematriaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "english_gematria"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)
        modulus = params.get("modulus", 9)

        gematria_val = sum(ENGLISH_GEMATRIA.get(c.lower(), 0) for c in text if c.isalpha())
        digit_sum = sum(int(d) for d in str(abs(gematria_val)))
        reduced = gematria_val
        while reduced >= 10:
            reduced = sum(int(d) for d in str(reduced))
        modular_residue = gematria_val % modulus if modulus > 0 else 0

        word_values = []
        for word in text.split():
            wv = sum(ENGLISH_GEMATRIA.get(c.lower(), 0) for c in word if c.isalpha())
            word_values.append(wv)

        symbolic_state = {
            "text": text, "gematria_value": gematria_val,
            "digit_sum": digit_sum, "reduced_value": reduced,
            "modulus": modulus, "modular_residue": modular_residue,
            "word_values": word_values,
        }
        numeric_projection = [gematria_val, digit_sum, reduced, modular_residue, len(text), len(word_values), seed % 1000]
        structural_features = {
            "total_value": gematria_val,
            "value_entropy": gematria_val / max(len(text), 1),
            "letter_diversity": len(set(c.lower() for c in text if c.isalpha())) / 26,
            "word_count": len(word_values),
            "modular_state": modular_residue % 9,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
