"""Roman numeral wrapper using the roman library."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import roman as roman_lib
    ROMAN_AVAILABLE = True
except ImportError:
    ROMAN_AVAILABLE = False


@register_system
class RomanNumeralWrapper(SymbolicSystemWrapper):
    """Wrapper for roman library - Roman numeral conversion."""
    SYSTEM_ID = "roman_numerals"
    LIBRARY_BACKEND = "roman" if ROMAN_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        text = entropy_packet.get("normalized_text", "")

        h = hashlib.sha256(f"roman_{seed}".encode()).digest()
        numbers = [h[i] * 256 + h[i + 1] for i in range(0, min(8, len(h)), 2)]
        numbers = [n % 3999 + 1 for n in numbers]

        roman_numerals = []
        if ROMAN_AVAILABLE:
            for n in numbers:
                try:
                    roman_numerals.append(roman_lib.toRoman(n))
                except Exception:
                    roman_numerals.append(f"R{n}")
        else:
            roman_numerals = [f"R{n}" for n in numbers]

        text_sum = sum(ord(c) for c in text[:20] if c.isalpha()) % 3999 + 1
        if ROMAN_AVAILABLE:
            try:
                text_roman = roman_lib.toRoman(text_sum)
            except Exception:
                text_roman = f"R{text_sum}"
        else:
            text_roman = f"R{text_sum}"

        decoded = []
        if ROMAN_AVAILABLE:
            for rn in roman_numerals[:3]:
                try:
                    decoded.append(roman_lib.fromRoman(rn))
                except Exception:
                    decoded.append(0)
        else:
            decoded = numbers[:3]

        symbolic_state = {
            "roman_numerals": roman_numerals,
            "arabic_numbers": numbers,
            "text_sum": text_sum,
            "text_roman": text_roman,
            "decoded": decoded,
        }

        numeric_projection = [
            numbers[0] / 3999.0 if numbers else 0,
            numbers[1] / 3999.0 if len(numbers) > 1 else 0,
            text_sum / 3999.0,
            len(roman_numerals) / 8.0,
            seed % 1000 / 1000.0,
        ]

        structural_features = {
            "num_conversions": len(roman_numerals),
            "max_value": max(numbers) if numbers else 0,
            "text_derived": text_sum,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
