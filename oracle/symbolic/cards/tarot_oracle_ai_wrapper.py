"""Tarot Oracle wrapper: AI-powered tarot divination with semantic analysis."""
import time
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_TAROT_ORACLE = False
try:
    from tarot_oracle import TarotDivination
    HAS_TAROT_ORACLE = True
except ImportError:
    pass


@register_system
class TarotOracleNewWrapper(SymbolicSystemWrapper):
    """Tarot divination using tarot-oracle with AI interpretation."""
    SYSTEM_ID = "tarot_oracle_ai"
    LIBRARY_BACKEND = "tarot-oracle"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        question = params.get("question", entropy_packet.get("question", "general reading"))
        spread = params.get("spread", "three_card")
        seed_val = entropy_packet.get("seed", int(time.time()))

        if HAS_TAROT_ORACLE:
            try:
                oracle = TarotDivination()
                spread_map = {
                    "three_card": [[0, 1, 2]],
                    "celtic_cross": [[0], [1, 2, 3, 4], [5, 6, 7, 8, 9]],
                    "single": [[0]],
                }
                layout = spread_map.get(spread, spread_map["three_card"])
                result = oracle.perform_reading_json(
                    question=question,
                    spread_layout=layout,
                    include_legend=True,
                )

                cards_drawn = result.get("legend", [])
                symbolic_state = {
                    "question": question,
                    "spread": spread,
                    "cards": [
                        {
                            "name": c.get("name", ""),
                            "notation": c.get("notation", ""),
                            "type": c.get("type", ""),
                            "keywords": c.get("keywords", ""),
                        }
                        for c in cards_drawn
                    ],
                    "spread_visual": result.get("spread", []),
                    "num_cards": len(cards_drawn),
                }

                numeric_projection = [
                    hash(question) % 100,
                    len(cards_drawn),
                    sum(1 for c in cards_drawn if c.get("is_reversed")),
                    hash(str(cards_drawn)) % 78,
                    seed_val % 78,
                ]

                structural_features = {
                    "card_count": len(cards_drawn),
                    "has_interpretation": bool(result.get("interpretation")),
                    "backend": "tarot-oracle",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    raw_output=result,
                    params=params,
                )
            except Exception as e:
                logger.warning("tarot-oracle compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params)

    def _compute_fallback(self, entropy_packet, params):
        seed = entropy_packet.get("seed", int(time.time()))
        symbolic_state = {"cards": [], "question": params.get("question", ""), "backend": "tarot_oracle_fallback"}
        numeric_projection = [0, 0, 0, seed % 78, seed % 78]
        structural_features = {"card_count": 0, "has_interpretation": False, "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
