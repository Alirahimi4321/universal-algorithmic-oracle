"""Tarot Card Meanings wrapper: Complete 78-card meanings database."""
import time
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_TCM = False
try:
    from tarot_card_meanings import get_all_cards, get_card, get_suit
    HAS_TCM = True
except ImportError:
    pass


@register_system
class TarotCardMeaningsWrapper(SymbolicSystemWrapper):
    """Tarot card meanings database lookup."""
    SYSTEM_ID = "tarot_meanings_db"
    LIBRARY_BACKEND = "tarot-card-meanings"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", int(time.time()))

        if HAS_TCM:
            try:
                all_cards = get_all_cards()
                card_name = params.get("card_name")
                suit = params.get("suit")

                if card_name:
                    card = get_card(card_name)
                    selected = [card] if card else []
                elif suit:
                    selected = get_suit(suit)
                else:
                    idx = seed % len(all_cards)
                    selected = [all_cards[idx]]

                symbolic_state = {
                    "total_cards": len(all_cards),
                    "selected_cards": selected,
                    "card_name": card_name,
                    "suit": suit,
                }

                numeric_projection = [
                    len(all_cards),
                    len(selected),
                    hash(str(selected)) % 78,
                    seed % 78,
                ]

                structural_features = {
                    "total_database_size": len(all_cards),
                    "selected_count": len(selected),
                    "backend": "tarot-card-meanings",
                }

                return self._build_output(
                    symbolic_state=symbolic_state,
                    numeric_projection=numeric_projection,
                    structural_features=structural_features,
                    params=params,
                )
            except Exception as e:
                logger.warning("tarot-card-meanings compute failed: %s", e)

        return self._compute_fallback(entropy_packet, params)

    def _compute_fallback(self, entropy_packet, params):
        seed = entropy_packet.get("seed", 0)
        symbolic_state = {"total_cards": 78, "selected_cards": [], "backend": "tarot_meanings_fallback"}
        numeric_projection = [78, 0, seed % 78, seed % 78]
        structural_features = {"total_database_size": 78, "selected_count": 0, "backend": "fallback"}
        return self._build_output(symbolic_state=symbolic_state, numeric_projection=numeric_projection,
                                  structural_features=structural_features, params=params)
