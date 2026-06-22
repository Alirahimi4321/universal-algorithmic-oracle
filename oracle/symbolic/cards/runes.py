"""Runes and Ogham symbolic wrapper using riimut library."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import riimut.elder_futhark as riimut_elder
    import riimut.futhorc as riimut_futhorc
    RIIMUT_AVAILABLE = True
except ImportError:
    RIIMUT_AVAILABLE = False

ELDER_FUTHARK = [
    "Fehu", "Uruz", "Thurisaz", "Ansuz", "Raidho", "Kenaz",
    "Gebo", "Wunjo", "Hagalaz", "Nauthiz", "Isa", "Jera",
    "Eihwaz", "Perthro", "Algiz", "Sowilo", "Tiwaz", "Berkano",
    "Ehwaz", "Mannaz", "Laguz", "Ingwaz", "Dagaz", "Othala",
]

OGHAM_LETTERS = [
    "Beith", "Luis", "Fearn", "Saille", "Nion", "Uath",
    "Dair", "Tinne", "Coll", "Ceirt", "Muin", "Gort",
    "nGeadhadh", "Ruis", "Ailm", "Onn", "Ur", "Edhadh",
    "Iadha", "Beire", "Oir", "Uilleann", "Ifin", "Emancholl",
]


@register_system
class RunesWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "runes"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        alphabet = params.get("alphabet", "futhark")
        bit_stream = entropy_packet.get("bit_stream", [])
        seed = entropy_packet.get("seed", 0)
        input_text = params.get("text", entropy_packet.get("question_text", "oracle"))

        if alphabet == "ogham":
            symbols = OGHAM_LETTERS
        else:
            symbols = ELDER_FUTHARK

        riimut_mapping = None
        if RIIMUT_AVAILABLE:
            try:
                if alphabet == "futhorc":
                    riimut_mapping = riimut_futhorc.get_rune_mapping()
                else:
                    riimut_mapping = riimut_elder.get_rune_mapping()
            except Exception:
                pass

        rune_count = min(8, len(symbols))
        runes = self._draw_runes(bit_stream, seed, rune_count, len(symbols))

        rune_names = [symbols[r] for r in runes]

        converted_text = None
        if riimut_mapping and input_text:
            try:
                if alphabet == "futhorc":
                    converted_text = riimut_futhorc.letters_to_runes(input_text.lower())
                else:
                    converted_text = riimut_elder.letters_to_runes(input_text.lower())
            except Exception:
                pass

        symbolic_state = {
            "alphabet": alphabet,
            "runes": rune_names,
            "rune_ids": runes,
            "rune_count": rune_count,
            "riimut_available": RIIMUT_AVAILABLE,
            "converted_text": converted_text,
            "input_text": input_text,
        }

        numeric_projection = runes + [seed % 1000, len(runes), sum(runes)]

        structural_features = {
            "rune_diversity": len(set(runes)) / max(len(runes), 1),
            "alphabet_size": len(symbols),
            "sequence_entropy": sum(runes) / max(len(runes) * len(symbols), 1),
            "has_riimut_mapping": 1 if riimut_mapping else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _draw_runes(self, bit_stream: list[int], seed: int, count: int, max_val: int) -> list[int]:
        h = hashlib.sha256(str(seed).encode()).digest()
        runes = []
        used = set()

        for i in range(count):
            val = 0
            start_bit = i * 8
            for j in range(8):
                if start_bit + j < len(bit_stream):
                    val = (val << 1) | bit_stream[start_bit + j]
                else:
                    val = (val << 1) | ((h[i % len(h)] >> (j % 8)) & 1)

            rune_id = val % max_val
            attempts = 0
            while rune_id in used and attempts < max_val:
                rune_id = (rune_id + 1) % max_val
                attempts += 1
            runes.append(rune_id)
            used.add(rune_id)

        return runes
