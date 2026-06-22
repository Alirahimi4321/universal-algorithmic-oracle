"""Tarot card divination wrapper using pytarot library."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import pytarot
    PYTAROT_AVAILABLE = True
except ImportError:
    PYTAROT_AVAILABLE = False

MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
]

SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
MINOR_RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]


@register_system
class TarotWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tarot"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        deck_size = params.get("deck_size", 78)
        bit_stream = entropy_packet.get("bit_stream", [])
        seed = entropy_packet.get("seed", 0)

        pytarot_data = None
        if PYTAROT_AVAILABLE:
            try:
                pytarot_data = {
                    "lucky_day": pytarot.get_lucky_day(),
                    "true_lover": pytarot.get_true_lover(),
                    "positive_action": pytarot.get_positive_action(),
                    "answers_of_wisdom": pytarot.get_answers_of_wisdom(),
                }
            except Exception:
                pass

        spread_size = min(5, deck_size)
        cards = self._draw_cards(bit_stream, seed, spread_size, deck_size)

        card_data = []
        for card_id in cards:
            if card_id < 22:
                card_data.append({
                    "id": card_id,
                    "type": "major_arcana",
                    "name": MAJOR_ARCANA[card_id] if card_id < len(MAJOR_ARCANA) else f"Major_{card_id}",
                    "orientation": "upright" if card_id % 2 == 0 else "reversed",
                })
            else:
                minor_id = card_id - 22
                suit_idx = minor_id // 14
                rank_idx = minor_id % 14
                card_data.append({
                    "id": card_id,
                    "type": "minor_arcana",
                    "suit": SUITS[suit_idx % 4] if suit_idx < len(SUITS) else "Unknown",
                    "rank": MINOR_RANKS[rank_idx % 14] if rank_idx < len(MINOR_RANKS) else "Unknown",
                    "orientation": "upright" if minor_id % 2 == 0 else "reversed",
                })

        upright_count = sum(1 for c in card_data if c["orientation"] == "upright")
        major_count = sum(1 for c in card_data if c["type"] == "major_arcana")

        symbolic_state = {
            "cards": card_data,
            "spread_size": spread_size,
            "deck_size": deck_size,
            "card_ids": cards,
            "pytarot_available": PYTAROT_AVAILABLE,
            "pytarot_data": pytarot_data,
        }

        numeric_projection = [
            cards[0] if cards else 0,
            len(cards),
            upright_count,
            major_count,
            sum(cards) % 78,
            seed % 1000,
            len([c for c in card_data if c.get("suit") == "Cups"]),
            len([c for c in card_data if c.get("suit") == "Swords"]),
        ]

        structural_features = {
            "upright_ratio": upright_count / max(len(cards), 1),
            "major_ratio": major_count / max(len(cards), 1),
            "suit_diversity": len(set(c.get("suit", "") for c in card_data if c["type"] == "minor_arcana")) / 4,
            "card_entropy": len(set(cards)) / max(len(cards), 1),
            "has_pytarot": 1 if pytarot_data else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _draw_cards(self, bit_stream: list[int], seed: int, count: int, deck_size: int) -> list[int]:
        h = hashlib.sha256(str(seed).encode()).digest()
        cards = []
        used = set()

        for i in range(count):
            val = 0
            start_bit = i * 8
            for j in range(8):
                if start_bit + j < len(bit_stream):
                    val = (val << 1) | bit_stream[start_bit + j]
                else:
                    val = (val << 1) | ((h[i % len(h)] >> (j % 8)) & 1)

            card_id = val % deck_size
            attempts = 0
            while card_id in used and attempts < deck_size:
                card_id = (card_id + 1) % deck_size
                attempts += 1
            cards.append(card_id)
            used.add(card_id)

        return cards
