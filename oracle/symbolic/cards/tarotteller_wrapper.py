"""TarotTeller wrapper — full tarot deck with Celtic Cross, Three Card, and more."""
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_TAROTTELLER = False
try:
    from tarotteller import TarotDeck, draw_spread, SPREADS
    HAS_TAROTTELLER = True
except ImportError:
    pass


@register_system
class TarotTellerWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tarotteller"
    LIBRARY_BACKEND = "tarotteller"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not HAS_TAROTTELLER:
            return self._build_output({}, [], {"error": "tarotteller not installed"})

        spread_name = (params or {}).get("spread", "three_card")
        import random as _random
        seed_val = entropy_packet.get("seed", entropy_packet.get("timestamp", 42))
        rng = _random.Random(int(seed_val) if seed_val else None)
        deck = TarotDeck(rng=rng)
        deck.shuffle()

        available = list(SPREADS.keys())
        if spread_name not in available:
            spread_name = available[1] if len(available) > 1 else available[0]

        reading = draw_spread(deck, spread_name)
        placements = []
        numeric = []
        keywords_all = []

        for p in reading.placements:
            drawn = p.card
            card = drawn.card
            placement_info = {
                "position": p.position,
                "card_name": card.name,
                "suit": str(card.suit) if card.suit else "Major",
                "rank": str(card.rank) if card.rank else str(card.arcana),
                "reversed": drawn.is_reversed,
                "meaning": drawn.meaning[:200] if drawn.meaning else "",
                "orientation": drawn.orientation,
            }
            keywords = list(getattr(drawn, 'keywords', []))
            placement_info["keywords"] = keywords
            placements.append(placement_info)

            card_val = hash(card.name) % 78
            sign = -1 if drawn.is_reversed else 1
            numeric.append(float(sign * card_val))
            keywords_all.extend(keywords)

        return self._build_output(
            symbolic_state={
                "spread": spread_name,
                "available_spreads": available,
                "placements": placements,
            },
            numeric_projection=numeric,
            structural_features={
                "num_cards": len(placements),
                "num_keywords": len(keywords_all),
                "unique_keywords": list(set(keywords_all))[:20],
                "reversed_count": sum(1 for p in placements if p["reversed"]),
            },
            raw_output={"text": reading.as_text() if callable(reading.as_text) else str(reading)},
        )
