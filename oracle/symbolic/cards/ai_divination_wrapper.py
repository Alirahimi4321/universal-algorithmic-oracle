"""AI Divination Skills wrapper (Tarot, I Ching, Xiao Liu Ren)."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from ai_divination_skills.tarot import draw as tarot_draw
    HAS_TAROT = True
except ImportError:
    HAS_TAROT = False

try:
    from ai_divination_skills.iching import cast as iching_cast
    HAS_ICHING = True
except ImportError:
    HAS_ICHING = False

try:
    from ai_divination_skills.xiaoliuren import cast_numbers as xiaoliuren_cast_numbers
    from ai_divination_skills.xiaoliuren import cast_time as xiaoliuren_cast_time
    HAS_XIAOLIUREN = True
except ImportError:
    HAS_XIAOLIUREN = False


def _seed_from_entropy(entropy_packet: dict) -> int:
    """Derive a deterministic seed from an entropy packet."""
    bit_stream = entropy_packet.get("bit_stream", [])
    seed = entropy_packet.get("seed", 0)
    h = hashlib.sha256(str(seed).encode()).digest()
    val = 0
    for i, b in enumerate(bit_stream[:32]):
        val = (val << 1) | (b & 1)
        val ^= h[i % len(h)]
    return val if val else seed


@register_system
class AIDivinationTarotWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "ai_tarot"
    LIBRARY_BACKEND = "ai-divination-skills"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        if not HAS_TAROT:
            return self._build_output(
                symbolic_state={"error": "ai_divination_skills.tarot not installed"},
                numeric_projection=[],
                structural_features={},
                raw_output={},
                params=params,
            )

        deck_name = params.get("deck_name", "major")
        spread_name = params.get("spread_name", "three-card")
        reversals = params.get("reversals", True)
        result = tarot_draw(deck_name=deck_name, spread_name=spread_name, reversals=reversals, seed=str(seed))

        cards = result.get("cards", [])
        card_names = [c.get("name", "Unknown") for c in cards]
        upright_count = sum(1 for c in cards if c.get("orientation") == "upright")

        symbolic_state = {
            "cards": cards,
            "card_names": card_names,
            "spread_name": spread_name,
        }

        numeric_projection = [
            seed % 1000,
            len(cards),
            upright_count,
            sum(hash(n) % 100 for n in card_names) % 1000,
            seed % 78,
        ]

        structural_features = {
            "upright_ratio": upright_count / max(len(cards), 1),
            "card_diversity": len(set(card_names)) / max(len(cards), 1),
            "spread_factor": len(cards) / 78,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=result,
            params=params,
        )


@register_system
class AIDivinationIChingWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "ai_iching"
    LIBRARY_BACKEND = "ai-divination-skills"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        if not HAS_ICHING:
            return self._build_output(
                symbolic_state={"error": "ai_divination_skills.iching not installed"},
                numeric_projection=[],
                structural_features={},
                raw_output={},
                params=params,
            )

        method = params.get("method", "coins")
        result = iching_cast(method=method, seed=str(seed), manual_lines=None)

        primary = result.get("primary_hexagram", {})
        resulting = result.get("resulting_hexagram", {})
        lines = result.get("lines", [])
        changing_lines = result.get("changing_lines", [])

        hex_number = primary.get("number", 0)
        line_values = [l.get("value", 0) for l in lines] if lines else []
        line_sum = sum(line_values)

        symbolic_state = {
            "primary_hexagram": primary,
            "resulting_hexagram": resulting,
            "lines": line_values,
            "changing_lines": changing_lines,
            "hexagram_name": primary.get("name", "Unknown"),
        }

        numeric_projection = [
            hex_number,
            line_sum,
            len(changing_lines),
            seed % 64,
            seed % 1000,
            sum(line_values) % 49 if line_values else 0,
        ]

        structural_features = {
            "yin_yang_ratio": sum(1 for v in line_values if v % 2 == 0) / max(len(line_values), 1),
            "changing_ratio": len(changing_lines) / max(len(line_values), 1),
            "hexagram_completeness": len(line_values) / 6,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=result,
            params=params,
        )


@register_system
class AIDivinationXiaoLiuRenWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "ai_xiaoliuren"
    LIBRARY_BACKEND = "ai-divination-skills"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        if not HAS_XIAOLIUREN:
            return self._compute_internal(entropy_packet, params)

        try:
            numbers = params.get("numbers")
            if numbers:
                result = xiaoliuren_cast_numbers(numbers)
            else:
                result = xiaoliuren_cast_time(seed=seed)
            return self._parse_result(result, entropy_packet, params)
        except Exception:
            return self._compute_internal(entropy_packet, params)

    def _parse_result(self, result, entropy_packet: dict, params: dict) -> SymbolicOutput:
        seed = entropy_packet.get("seed", 0)

        if isinstance(result, dict):
            symbolic_state = {
                "result": {str(k): str(v)[:200] for k, v in result.items()},
                "library": "ai_divination_skills",
            }

            numeric_projection = [
                hash(str(result)) % 100,
                seed % 1000,
                len(result),
                hash(str(sorted(result.keys()))) % 100 if result else 0,
            ]

            structural_features = {
                "result_completeness": len(result) / 12,
                "has_result": bool(result),
            }

            return self._build_output(
                symbolic_state=symbolic_state,
                numeric_projection=numeric_projection,
                structural_features=structural_features,
                params=params,
            )

        return self._compute_internal(entropy_packet, params)

    def _compute_internal(self, entropy_packet: dict, params: dict) -> SymbolicOutput:
        seed = entropy_packet.get("seed", 0)
        h = hashlib.sha256(f"xiaoliuren_{seed}".encode()).digest()

        palace_num = h[0] % 12 + 1
        lot_num = h[1] % 6 + 1

        symbolic_state = {
            "palace_number": palace_num,
            "lot_number": lot_num,
            "library": "internal",
        }

        numeric_projection = [
            palace_num,
            lot_num,
            seed % 12,
            seed % 1000,
        ]

        structural_features = {
            "palace_validity": 1.0,
            "lot_validity": 1.0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
