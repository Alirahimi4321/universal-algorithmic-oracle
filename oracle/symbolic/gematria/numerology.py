"""Numerology system wrapper."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system


@register_system
class NumerologyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "numerology"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)
        reduction_base = params.get("reduction_base", 9)

        life_path = self._calculate_life_path(text)
        name_number = self._calculate_name_number(text)
        compound = self._compound_number(life_path)
        reduced = self._reduce_to_base(life_path, reduction_base)
        cyclic = self._cyclic_reduction(life_path)

        digit_freq = self._digit_frequency(text)

        symbolic_state = {
            "text": text,
            "life_path": life_path,
            "name_number": name_number,
            "compound_number": compound,
            "reduced_value": reduced,
            "cyclic_reduction": cyclic,
            "digit_frequency": digit_freq,
            "reduction_base": reduction_base,
        }

        numeric_projection = [
            life_path,
            name_number,
            compound,
            reduced,
            cyclic,
            seed % 1000,
            len(text),
            sum(ord(c) for c in text[:20]),
        ]

        structural_features = {
            "life_path_mod_9": life_path % 9,
            "name_number_mod_9": name_number % 9,
            "master_number": 1 if life_path in [11, 22, 33] else 0,
            "numerological_balance": abs(life_path - name_number) / max(life_path, name_number, 1),
            "digit_diversity": len(digit_freq) / 10,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _calculate_life_path(self, text: str) -> int:
        total = sum(ord(c) for c in text if c.isalpha())
        return self._reduce_to_single(total)

    def _calculate_name_number(self, text: str) -> int:
        vowels = sum(1 for c in text if c in "aeiou")
        consonants = sum(1 for c in text if c.isalpha() and c not in "aeiou")
        return self._reduce_to_single(vowels * 7 + consonants * 3)

    def _compound_number(self, n: int) -> int:
        return sum(int(d) for d in str(n))

    def _reduce_to_single(self, n: int) -> int:
        while n >= 10:
            n = sum(int(d) for d in str(n))
        return n

    def _reduce_to_base(self, n: int, base: int) -> int:
        while n >= base:
            n = sum(int(d) for d in str(n))
        return n

    def _cyclic_reduction(self, n: int) -> int:
        return (n * 7 + 3) % 12

    def _digit_frequency(self, text: str) -> dict:
        freq = {}
        for c in text:
            if c.isdigit():
                freq[c] = freq.get(c, 0) + 1
        return freq
