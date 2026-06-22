"""Gematria / Abjad wrapper using abnum + numerology."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from abnum import Abnum
    ABNUM_AVAILABLE = True
except ImportError:
    ABNUM_AVAILABLE = False

try:
    import numerology as numlib
    NUMEROLOGY_AVAILABLE = True
except ImportError:
    NUMEROLOGY_AVAILABLE = False

ARABIC_ABJAD = {
    "ا": 1, "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7,
    "ح": 8, "ط": 9, "ي": 10, "ک": 11, "ل": 12, "م": 13, "ن": 14,
    "س": 15, "ع": 16, "ف": 17, "ص": 18, "ق": 19, "ر": 20, "ش": 21,
    "ت": 22, "ث": 23, "خ": 24, "ذ": 25, "ض": 26, "ظ": 27, "غ": 28,
}

HEBREW_GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7,
    "ח": 8, "ט": 9, "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50,
    "ס": 60, "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200, "ש": 300,
    "ת": 400,
}

ENGLISH_GEMATRIA = {chr(i): (i - 96) if 97 <= i <= 122 else 0 for i in range(123)}


@register_system
class GematriaWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "gematria"
    LIBRARY_BACKEND = "abnum" if ABNUM_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)
        modulus = params.get("modulus", 22)

        abjad_val = self._abjad_value(text)
        hebrew_val = self._hebrew_value(text)
        english_val = self._english_value(text)

        if ABNUM_AVAILABLE:
            try:
                abnum_obj = Abnum()
                abjad_val = abnum_obj.abjad(text)
            except Exception:
                pass

        if NUMEROLOGY_AVAILABLE:
            try:
                num_result = numlib.numerology(text)
                english_val = num_result.get("numerology", english_val)
            except Exception:
                pass

        digit_sum = self._digit_sum(abjad_val)
        modular_residue = abjad_val % modulus if modulus > 0 else 0
        letter_positions = [self._letter_position(c) for c in text[:30]]

        symbolic_state = {
            "text": text,
            "systems": {
                "abjad": abjad_val,
                "hebrew_gematria": hebrew_val,
                "english_gematria": english_val,
            },
            "digit_features": {
                "digit_sum": digit_sum,
                "reduced_value": self._reduce_to_single(abjad_val),
            },
            "modular_features": {"modulus": modulus, "residue": modular_residue},
        }

        numeric_projection = [
            abjad_val, hebrew_val, english_val, digit_sum,
            modular_residue, len(text), seed % 1000,
        ]

        structural_features = {
            "total_value": abjad_val,
            "value_entropy": abjad_val / max(len(text), 1),
            "letter_diversity": len(set(text)) / max(len(text), 1),
            "modular_state": modular_residue % 7,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _abjad_value(self, text: str) -> int:
        return sum(ARABIC_ABJAD.get(c, 0) for c in text)

    def _hebrew_value(self, text: str) -> int:
        return sum(HEBREW_GEMATRIA.get(c, 0) for c in text)

    def _english_value(self, text: str) -> int:
        return sum(ENGLISH_GEMATRIA.get(c.lower(), 0) for c in text if c.isalpha())

    def _digit_sum(self, n: int) -> int:
        return sum(int(d) for d in str(abs(n)))

    def _reduce_to_single(self, n: int) -> int:
        while n >= 10:
            n = self._digit_sum(n)
        return n

    def _letter_position(self, char: str) -> int:
        if char in ARABIC_ABJAD:
            return ARABIC_ABJAD[char]
        elif char.isalpha():
            return ord(char.lower()) - 96
        return 0
