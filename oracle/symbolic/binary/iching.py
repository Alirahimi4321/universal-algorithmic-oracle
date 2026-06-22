"""I Ching wrapper using ichingpy."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from ichingpy import IChing
    from ichingpy.model.hexagram import Hexagram as IchingHexagram
    ICHINGPY_AVAILABLE = True
except ImportError:
    ICHINGPY_AVAILABLE = False

TRIGRAMS = {
    (0, 0, 0): {"name": "Kun", "element": "Earth", "binary": "000"},
    (0, 0, 1): {"name": "Gen", "element": "Mountain", "binary": "001"},
    (0, 1, 0): {"name": "Kan", "element": "Water", "binary": "010"},
    (0, 1, 1): {"name": "Xun", "element": "Wind", "binary": "011"},
    (1, 0, 0): {"name": "Zhen", "element": "Thunder", "binary": "100"},
    (1, 0, 1): {"name": "Li", "element": "Fire", "binary": "101"},
    (1, 1, 0): {"name": "Dui", "element": "Lake", "binary": "110"},
    (1, 1, 1): {"name": "Qian", "element": "Heaven", "binary": "111"},
}


def lines_to_hexagram(lines: list[int]) -> int:
    val = 0
    for i, line in enumerate(lines[:6]):
        val |= (line & 1) << i
    return val


def hexagram_to_lines(hex_id: int) -> list[int]:
    return [(hex_id >> i) & 1 for i in range(6)]


def get_trigram(lines: list[int]) -> dict:
    key = tuple(lines[:3])
    return TRIGRAMS.get(key, {"name": "Unknown", "element": "Unknown", "binary": "???"})


@register_system
class IChingWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "iching"
    LIBRARY_BACKEND = "ichingpy" if ICHINGPY_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        line_count = params.get("line_count", 6)
        bit_stream = entropy_packet.get("bit_stream", [])
        seed = entropy_packet.get("seed", 0)

        if ICHINGPY_AVAILABLE:
            return self._compute_with_ichingpy(entropy_packet, params)
        return self._compute_internal(entropy_packet, params)

    def _compute_with_ichingpy(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        line_count = params.get("line_count", 6)

        try:
            iching = IChing()
            lines = self._generate_lines(entropy_packet.get("bit_stream", []), seed, line_count)
            hex_id = lines_to_hexagram(lines[:6]) + 1

            hexagram = iching.get_hexagram_by_number(hex_id)
            changing = [i + 1 for i, l in enumerate(lines) if l == 2]

            transition_hex = hex_id
            for pos in changing:
                transition_hex ^= 1 << (pos - 1)

            symbolic_state = {
                "hexagram": hex_id,
                "name": getattr(hexagram, "name", str(hex_id)),
                "lines": lines,
                "changing_lines": changing,
                "transition_hexagram": min(transition_hex, 64),
                "binary_code": "".join(str(l % 2) for l in lines),
                "unicode": getattr(hexagram, "unicode", ""),
            }

            yin_count = sum(1 for l in lines if l % 2 == 0)
            yang_count = len(lines) - yin_count

            numeric_projection = [
                hex_id, len(changing), yin_count, yang_count,
                min(transition_hex, 64), seed % 1000, len(lines), sum(lines),
            ]

            structural_features = {
                "binary_code": symbolic_state["binary_code"],
                "yin_yang_balance": yang_count / max(len(lines), 1),
                "transition_distance": len(changing),
                "line_entropy": sum(1 for l in lines if l == 2) / max(len(lines), 1),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                raw_output={"upper_element": "", "lower_element": ""},
                params=params,
            )
        except Exception:
            return self._compute_internal(entropy_packet, params)

    def _compute_internal(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        line_count = params.get("line_count", 6)
        seed = entropy_packet.get("seed", 0)

        lines = self._generate_lines(entropy_packet.get("bit_stream", []), seed, line_count)
        hexagram_id = lines_to_hexagram(lines[:6])
        upper = get_trigram(lines[:3])
        lower = get_trigram(lines[3:6]) if len(lines) >= 6 else get_trigram(lines[:3])
        changing = [i + 1 for i, l in enumerate(lines) if l == 2]
        transition_hex = self._transition_hexagram(hexagram_id, changing)

        symbolic_state = {
            "hexagram": hexagram_id, "line_count": line_count, "lines": lines,
            "changing_lines": changing, "upper_trigram": upper, "lower_trigram": lower,
            "transition_hexagram": transition_hex,
            "binary_code": "".join(str(l % 2) for l in lines),
        }

        yin_count = sum(1 for l in lines if l % 2 == 0)
        yang_count = len(lines) - yin_count

        numeric_projection = [
            hexagram_id, len(changing), yin_count, yang_count,
            transition_hex, seed % 1000, len(lines), sum(lines),
        ]

        structural_features = {
            "binary_code": symbolic_state["binary_code"],
            "yin_yang_balance": yang_count / max(len(lines), 1),
            "transition_distance": len(changing),
            "line_entropy": sum(1 for l in lines if l == 2) / max(len(lines), 1),
            "elemental_diversity": len(set([upper["element"], lower["element"]])),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"upper_element": upper["element"], "lower_element": lower["element"]},
            params=params,
        )

    def _generate_lines(self, bit_stream: list[int], seed: int, count: int) -> list[int]:
        lines = []
        h = hashlib.sha256(str(seed).encode()).digest()
        byte_idx = 0
        bit_idx = 0
        for i in range(count):
            if bit_idx + 1 < len(bit_stream):
                b1, b2 = bit_stream[bit_idx], bit_stream[bit_idx + 1]
                bit_idx += 2
            elif byte_idx < len(h):
                b1 = (h[byte_idx] >> (7 - bit_idx % 8)) & 1
                b2 = (h[byte_idx] >> (6 - bit_idx % 8)) & 1
                bit_idx += 2
                if bit_idx % 8 == 0:
                    byte_idx += 1
            else:
                val = (seed + i * 1103515245) & 0x7FFFFFFF
                b1, b2 = val & 1, (val >> 1) & 1
            if b1 == 0 and b2 == 0:
                lines.append(0)
            elif b1 == 0 and b2 == 1:
                lines.append(1)
            elif b1 == 1 and b2 == 0:
                lines.append(2)
            else:
                lines.append(3)
        return lines

    def _transition_hexagram(self, hex_id: int, changing: list[int]) -> int:
        trans = hex_id
        for pos in changing:
            trans ^= 1 << (pos - 1)
        return trans
