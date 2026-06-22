"""Tarot Oracle library wrapper — comprehensive tarot with multiple spreads."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

SPREAD_LAYOUTS = {
    "single": [[1]],
    "three_card": [[1, 2, 3]],
    "cross": [[1, 2, 3, 4]],
    "celtic_cross": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
    "horseshoe": [[1, 2, 3, 4, 5, 6, 7]],
}

SPREAD_POSITIONS = {
    "three_card": ["Past", "Present", "Future"],
    "cross": ["Current Situation", "Challenge", "Past Influence", "Future Influence"],
    "celtic_cross": [
        "Present", "Challenge", "Past Foundation", "Recent Past",
        "Best Outcome", "Near Future", "Self-Perception", "Environment",
        "Hopes & Fears", "Final Outcome",
    ],
    "horseshoe": [
        "Past", "Present", "Future", "Advice",
        "External Influence", "Inner Voice", "Outcome",
    ],
}


@register_system
class TarotOracleWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "tarot_oracle"
    LIBRARY_BACKEND = "tarot-oracle"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        spread_name = params.get("spread", "three_card")
        seed = entropy_packet.get("seed", 0)
        bit_stream = entropy_packet.get("bit_stream", [])
        allow_reversed = params.get("allow_reversed", True)
        question = params.get("question", "general reading")

        try:
            return self._compute_with_library(
                seed=seed,
                spread_name=spread_name,
                allow_reversed=allow_reversed,
                question=question,
                params=params,
            )
        except ImportError:
            return self._compute_fallback(
                seed=seed,
                bit_stream=bit_stream,
                spread_name=spread_name,
                allow_reversed=allow_reversed,
                params=params,
            )

    def _compute_with_library(
        self,
        seed: int,
        spread_name: str,
        allow_reversed: bool,
        question: str,
        params: dict,
    ) -> SymbolicOutput:
        from tarot_oracle.tarot import TarotDivination

        spread_layout = SPREAD_LAYOUTS.get(spread_name, [[0, 1, 2]])
        spread_size = len(spread_layout[0])

        divination = TarotDivination()
        reading_json = divination.perform_reading_json(
            question=question,
            spread_layout=spread_layout,
            allow_reversed=allow_reversed,
            include_legend=True,
        )

        cards_raw = divination.draw_cards_for_reading(
            seed=seed,
            spread_layout=spread_layout,
            allow_reversed=allow_reversed,
        )

        positions = SPREAD_POSITIONS.get(spread_name, [f"Position_{i}" for i in range(spread_size)])
        legend = reading_json.get("legend", [])

        card_entries = []
        card_names = []
        orientations = []
        major_count = 0
        reversed_count = 0

        for i, card in enumerate(cards_raw):
            card_name = card.name
            is_reversed = card.is_reversed
            card_type = card.card_type
            orientation = "reversed" if is_reversed else "upright"

            card_entries.append({
                "name": card_name,
                "position": positions[i] if i < len(positions) else f"Position_{i}",
                "orientation": orientation,
                "card_type": card_type,
                "suit": card.suit,
                "value": card.value,
                "keywords": card.keywords[:5] if card.keywords else [],
            })

            card_names.append(card_name)
            orientations.append(orientation)
            if card_type == "major":
                major_count += 1
            if is_reversed:
                reversed_count += 1

        minor_count = spread_size - major_count

        symbolic_state = {
            "cards": card_entries,
            "spread": spread_name,
            "spread_size": spread_size,
            "question": question,
            "card_names": card_names,
            "orientations": orientations,
            "reading_display": reading_json.get("spread", []),
            "seed_used": str(reading_json.get("seed", seed)),
        }

        numeric_projection = [
            float(hashlib.sha256(name.encode()).digest()[0]) / 255.0
            for name in card_names
        ] + [
            reversed_count / max(spread_size, 1),
            major_count / max(spread_size, 1),
            seed % 1000 / 1000.0,
        ]

        structural_features = {
            "major_ratio": major_count / max(spread_size, 1),
            "minor_ratio": minor_count / max(spread_size, 1),
            "reversal_ratio": reversed_count / max(spread_size, 1),
            "spread_complexity": spread_size / 10,
            "card_entropy": len(set(card_names)) / max(spread_size, 1),
            "suit_diversity": len(set(c.suit for c in cards_raw if c.suit)) / 4,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"method": "library", "spread": spread_name, "reading_json": reading_json},
            params=params,
        )

    def _compute_fallback(
        self,
        seed: int,
        bit_stream: list[int],
        spread_name: str,
        allow_reversed: bool,
        params: dict,
    ) -> SymbolicOutput:
        spread_layout = SPREAD_LAYOUTS.get(spread_name, [[0, 1, 2]])
        spread_size = len(spread_layout[0])

        rng = hashlib.sha256(str(seed).encode()).digest()

        MAJOR_ARCANA = [
            "The Fool", "The Magician", "The High Priestess", "The Empress",
            "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
            "Strength", "The Hermit", "Wheel of Fortune", "Justice",
            "The Hanged Man", "Death", "Temperance", "The Devil",
            "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
        ]
        SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
        RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]

        card_entries = []
        card_names = []
        orientations = []
        used_indices = set()
        major_count = 0
        reversed_count = 0

        for i in range(spread_size):
            idx = rng[i % len(rng)] % 78
            attempts = 0
            while idx in used_indices and attempts < 78:
                idx = (idx + 1) % 78
                attempts += 1
            used_indices.add(idx)

            is_reversed = allow_reversed and ((rng[i % len(rng)] >> 1 & 1) == 1)
            orientation = "reversed" if is_reversed else "upright"

            if idx < 22:
                card_name = MAJOR_ARCANA[idx]
                card_type = "major"
                suit = None
                value = idx
                major_count += 1
            else:
                minor_id = idx - 22
                suit = SUITS[minor_id // 14 % 4]
                value = RANKS[minor_id % 14]
                card_name = f"{value} of {suit}"
                card_type = "minor"

            if is_reversed:
                reversed_count += 1

            card_entries.append({
                "name": card_name,
                "position": SPREAD_POSITIONS.get(spread_name, [f"Position_{j}" for j in range(spread_size)])[i] if i < len(SPREAD_POSITIONS.get(spread_name, [])) else f"Position_{i}",
                "orientation": orientation,
                "card_type": card_type,
                "suit": suit,
                "value": value,
                "keywords": [],
            })
            card_names.append(card_name)
            orientations.append(orientation)

        minor_count = spread_size - major_count

        symbolic_state = {
            "cards": card_entries,
            "spread": spread_name,
            "spread_size": spread_size,
            "card_names": card_names,
            "orientations": orientations,
        }

        numeric_projection = [
            float(idx) / 78.0 for idx in used_indices
        ] + [
            reversed_count / max(spread_size, 1),
            major_count / max(spread_size, 1),
            seed % 1000 / 1000.0,
        ]

        structural_features = {
            "major_ratio": major_count / max(spread_size, 1),
            "minor_ratio": minor_count / max(spread_size, 1),
            "reversal_ratio": reversed_count / max(spread_size, 1),
            "spread_complexity": spread_size / 10,
            "card_entropy": len(set(card_names)) / max(spread_size, 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output={"method": "fallback", "spread": spread_name},
            params=params,
        )
