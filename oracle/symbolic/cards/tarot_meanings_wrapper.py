"""Tarot Card Meanings wrapper - structured tarot card data."""
from __future__ import annotations

import logging
import random
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import tarot_card_meanings as tcm
    HAS_TCM = True
except ImportError:
    HAS_TCM = False
    logger.info("tarot_card_meanings not available")


@register_system
class TarotCardMeaningsWrapper(SymbolicSystemWrapper):
    """Wrapper for tarot_card_meanings structured data."""
    SYSTEM_ID = "tarot_card_meanings"
    LIBRARY_BACKEND = "tarot_card_meanings"

    def __init__(self) -> None:
        self.available: bool = HAS_TCM

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "tarot_card_meanings not available"}, params)

        try:
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            rng = random.Random(seed)

            all_cards_raw = tcm.get_all_cards() if hasattr(tcm, 'get_all_cards') else {}
            all_cards = list(all_cards_raw.keys()) if isinstance(all_cards_raw, dict) else list(all_cards_raw)
            num_cards = min(10, len(all_cards))
            drawn = rng.sample(all_cards, num_cards) if all_cards else []

            cards_data = []
            numeric = []
            for card_key in drawn:
                card_obj = all_cards_raw.get(card_key, card_key) if isinstance(all_cards_raw, dict) else card_key
                card_info = {
                    "name": getattr(card_obj, 'name', str(card_key)),
                    "type": getattr(card_obj, 'type', "unknown"),
                }
                if hasattr(card_obj, 'meaning_upright'):
                    card_info["meaning_upright"] = str(card_obj.meaning_upright)[:100]
                if hasattr(card_obj, 'meaning_reversed'):
                    card_info["meaning_reversed"] = str(card_obj.meaning_reversed)[:100]
                cards_data.append(card_info)
                numeric.append(hash(str(card_key)) % 1000 / 1000.0)

            suits = list(tcm.SUITS.keys()) if isinstance(tcm.SUITS, dict) else list(tcm.SUITS) if hasattr(tcm, 'SUITS') else []
            majors = list(tcm.MAJOR_ARCANA.keys()) if isinstance(tcm.MAJOR_ARCANA, dict) else list(tcm.MAJOR_ARCANA) if hasattr(tcm, 'MAJOR_ARCANA') else []

            return self._build_output(
                symbolic_state={
                    "drawn_cards": cards_data,
                    "total_cards": len(all_cards),
                    "num_suits": len(suits),
                    "num_majors": len(majors),
                },
                numeric_projection=numeric,
                structural_features={"num_drawn": num_cards, "total_available": len(all_cards)},
                raw_output={"cards": cards_data},
                params=params,
            )
        except Exception as e:
            logger.warning("tarot_card_meanings computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
