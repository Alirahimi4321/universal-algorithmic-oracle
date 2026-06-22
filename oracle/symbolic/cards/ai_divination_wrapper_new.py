"""AI Divination Skills wrapper - additional divination capabilities."""
import hashlib
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from ai_divination_skills import tarot, iching, xiaoliuren
    HAS_AI_DIVINATION = True
except ImportError:
    HAS_AI_DIVINATION = False
    logger.info("ai-divination-skills not available")


def _seed_from_entropy(entropy_packet: dict) -> int:
    seed = entropy_packet.get("seed", 0)
    bit_stream = entropy_packet.get("bit_stream", [])
    h = hashlib.sha256(str(seed).encode()).digest()
    val = 0
    for i, b in enumerate(bit_stream[:32]):
        val = (val << 1) | (b & 1)
        val ^= h[i % len(h)]
    return val if val else seed


@register_system
class AIDivinationCombinedWrapper(SymbolicSystemWrapper):
    """Combined AI Divination wrapper for tarot + iching + xiaoliuren."""
    SYSTEM_ID = "ai_divination"
    LIBRARY_BACKEND = "ai-divination-skills"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = _seed_from_entropy(entropy_packet)

        tarot_result = {}
        iching_result = {}
        xlr_result = {}

        if HAS_AI_DIVINATION:
            try:
                tarot_result = tarot.draw(deck_name="major", spread_name="three-card", reversals=True, seed=str(seed))
            except Exception as e:
                tarot_result = {"error": str(e)}

            try:
                iching_result = iching.cast(method="coins", seed=str(seed), manual_lines=None)
            except Exception as e:
                iching_result = {"error": str(e)}

            try:
                xlr_result = xiaoliuren.cast_time(seed=seed)
            except Exception as e:
                xlr_result = {"error": str(e)}
        else:
            h = hashlib.sha256(f"combined_{seed}".encode()).digest()
            tarot_result = {"cards": [{"name": f"Card_{h[i] % 78}", "orientation": "upright" if h[i] % 2 == 0 else "reversed"} for i in range(3)]}
            iching_result = {"hexagram": h[0] % 64 + 1, "changing_lines": [h[i] % 6 + 1 for i in range(3)]}
            xlr_result = {"palace": h[0] % 12 + 1, "lot": h[1] % 6 + 1}

        cards = tarot_result.get("cards", [])
        hex_num = iching_result.get("primary_hexagram", {}).get("number", 0) or iching_result.get("hexagram", 0)

        symbolic_state = {
            "tarot": {"cards": [c.get("name", "?") for c in cards], "spread": "three-card"},
            "iching": {"hexagram": hex_num, "lines": iching_result.get("lines", [])},
            "xiaoliuren": xlr_result,
            "system": "ai_divination_combined",
        }

        numeric_projection = [
            seed % 1000,
            len(cards),
            hex_num % 64 if hex_num else 0,
            hash(str(xlr_result)) % 100,
            seed % 78,
        ]

        structural_features = {
            "tarot_cards": len(cards),
            "has_iching": bool(hex_num),
            "has_xlr": bool(xlr_result),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"tarot": tarot_result, "iching": iching_result, "xiaoliuren": xlr_result},
            params=params,
        )
