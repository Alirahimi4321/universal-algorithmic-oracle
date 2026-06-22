"""Arcanite wrapper - Tarot card deck and spread system.

Uses arcanite for 78-card tarot deck with 11 spread layouts.
Provides card drawing, spread positions, and structural features.
(No LLM interpretation - just card data and positions.)
"""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from arcanite.core import load_tarot_deck, load_spread, list_spreads
    HAS_ARCANITE = True
except ImportError:
    HAS_ARCANITE = False
    logger.info("arcanite not available")


@register_system
class ArcaniteWrapper(SymbolicSystemWrapper):
    """Wrapper for arcanite tarot deck and spreads."""
    SYSTEM_ID = "arcanite_tarot"
    LIBRARY_BACKEND = "arcanite"

    def __init__(self) -> None:
        self.available: bool = HAS_ARCANITE
        self._deck = None
        self._spread_names = None

    def _ensure_deck(self):
        if self._deck is None and HAS_ARCANITE:
            try:
                self._deck = load_tarot_deck()
                self._spread_names = list_spreads()
            except Exception as e:
                logger.warning("Failed to load arcanite deck: %s", e)

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "arcanite not available"}, params)

        try:
            import random
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)

            spread_name = "celtic-cross"
            if params and "spread" in params:
                spread_name = params["spread"]

            self._ensure_deck()
            if self._deck is None:
                return self._build_output({}, [], {}, {"error": "deck not loaded"}, params)

            deck = self._deck
            cards_shuffled = list(deck.cards)
            rng.shuffle(cards_shuffled)

            try:
                spread = load_spread(spread_name)
                num_positions = len(spread.positions) if hasattr(spread, 'positions') else 10
                spread_info = {
                    "name": spread_name,
                    "num_positions": num_positions,
                    "positions": [],
                }
                if hasattr(spread, 'positions'):
                    for p in spread.positions:
                        pos_info = {"name": p.name if hasattr(p, 'name') else str(p)}
                        if hasattr(p, 'short_description'):
                            pos_info["description"] = p.short_description[:100]
                        spread_info["positions"].append(pos_info)
            except Exception:
                num_positions = 10
                spread_info = {"name": spread_name, "num_positions": num_positions, "positions": []}

            drawn = cards_shuffled[:min(num_positions, len(cards_shuffled))]
            drawn_cards = []
            for i, card in enumerate(drawn):
                card_info = {
                    "name": card.card_name if hasattr(card, 'card_name') else f"Card {i}",
                    "id": card.card_id if hasattr(card, 'card_id') else f"card_{i}",
                    "suit": card.suit if hasattr(card, 'suit') else "unknown",
                    "number": card.card_number if hasattr(card, 'card_number') else 0,
                }
                drawn_cards.append(card_info)

            suits = [c.get("suit", "unknown") for c in drawn_cards]
            suit_counts = {}
            for s in suits:
                suit_counts[s] = suit_counts.get(s, 0) + 1

            major_arcana = sum(1 for c in drawn_cards
                               if c.get("suit") in ("major", "trumps", "unknown") and c.get("number", 0) > 0)

            numeric = [c.get("number", 0) / 78.0 for c in drawn_cards]
            numeric.extend([len(drawn_cards) / 78.0, major_arcana / 22.0])

            return self._build_output(
                symbolic_state={
                    "spread": spread_info,
                    "drawn_cards": drawn_cards,
                    "total_cards": len(drawn_cards),
                    "suit_distribution": suit_counts,
                    "seed": seed,
                },
                numeric_projection=numeric,
                structural_features={
                    "num_cards": len(drawn_cards),
                    "spread_name": spread_name,
                    "num_spreads_available": len(self._spread_names) if self._spread_names else 0,
                    "major_arcana_count": major_arcana,
                },
                raw_output={"cards": drawn_cards, "spread": spread_info},
                params=params,
            )
        except Exception as e:
            logger.warning("arcanite computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
