"""Lenormand cartomancy wrapper."""
import hashlib
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

LENORMAND_CARDS = [
    {"id": 1, "name": "Rider", "keywords": ["news", "arrival", "movement", "visit"]},
    {"id": 2, "name": "Clover", "keywords": ["luck", "chance", "temporary", "small"]},
    {"id": 3, "name": "Ship", "keywords": ["journey", "travel", "trade", "distance"]},
    {"id": 4, "name": "House", "keywords": ["home", "family", "safety", "property"]},
    {"id": 5, "name": "Tree", "keywords": ["health", "growth", "longevity", "roots"]},
    {"id": 6, "name": "Clouds", "keywords": ["confusion", "worry", "delay", "uncertainty"]},
    {"id": 7, "name": "Snake", "keywords": ["deception", "temptation", "danger", "wisdom"]},
    {"id": 8, "name": "Coffin", "keywords": ["ending", "transformation", "loss", "letting go"]},
    {"id": 9, "name": "Bouquet", "keywords": ["gift", "beauty", "gratitude", "celebration"]},
    {"id": 10, "name": "Scythe", "keywords": ["danger", "sudden", "cut", "separation"]},
    {"id": 11, "name": "Whip", "keywords": ["conflict", "passion", "repetition", "argument"]},
    {"id": 12, "name": "Birds", "keywords": ["communication", "gossip", "couple", "social"]},
    {"id": 13, "name": "Child", "keywords": ["new", "innocent", "small", "beginning"]},
    {"id": 14, "name": "Fox", "keywords": ["cunning", "clever", "suspicion", "work"]},
    {"id": 15, "name": "Bear", "keywords": ["strength", "protection", "wealth", "mother"]},
    {"id": 16, "name": "Stars", "keywords": ["hope", "inspiration", "destiny", "guidance"]},
    {"id": 17, "name": "Stork", "keywords": ["change", "home", "family", "new"]},
    {"id": 18, "name": "Dog", "keywords": ["loyalty", "friendship", "faithful", "companion"]},
    {"id": 19, "name": "Tower", "keywords": ["authority", "isolation", "ambition", "government"]},
    {"id": 20, "name": "Garden", "keywords": ["social", "community", "network", "public"]},
    {"id": 21, "name": "Mountain", "keywords": ["obstacle", "challenge", "strength", "patience"]},
    {"id": 22, "name": "Crossroads", "keywords": ["choice", "direction", "path", "decision"]},
    {"id": 23, "name": "Mice", "keywords": ["loss", "worry", "trouble", "sickness"]},
    {"id": 24, "name": "Heart", "keywords": ["love", "emotion", "passion", "relationship"]},
    {"id": 25, "name": "Ring", "keywords": ["commitment", "partnership", "cycle", "contract"]},
    {"id": 26, "name": "Book", "keywords": ["secret", "knowledge", "study", "hidden"]},
    {"id": 27, "name": "Letter", "keywords": ["document", "message", "official", "news"]},
    {"id": 28, "name": "Man", "keywords": ["male", "self", "masculine", "husband"]},
    {"id": 29, "name": "Woman", "keywords": ["female", "feminine", "wife", "partner"]},
    {"id": 30, "name": "Lily", "keywords": ["peace", "harmony", "pure", "mature"]},
    {"id": 31, "name": "Sun", "keywords": ["success", "vitality", "warmth", "joy"]},
    {"id": 32, "name": "Moon", "keywords": ["emotion", "intuition", "dreams", "subconscious"]},
    {"id": 33, "name": "Key", "keywords": ["solution", "answer", "unlock", "importance"]},
    {"id": 34, "name": "Fish", "keywords": ["wealth", "abundance", "business", "independent"]},
    {"id": 35, "name": "Anchor", "keywords": ["stability", "grounding", "security", "steady"]},
    {"id": 36, "name": "Cross", "keywords": ["burden", "sacrifice", "karma", "faith"]},
]


@register_system
class LenormandWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "lenormand"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        spread_size = params.get("spread_size", 5)

        drawn_cards = self._draw_cards(seed, spread_size)

        card_data = []
        for pos, card_id in enumerate(drawn_cards):
            card = LENORMAND_CARDS[card_id - 1]
            card_data.append({
                "position": pos + 1,
                "id": card["id"],
                "name": card["name"],
                "keywords": card["keywords"],
            })

        all_keywords = []
        for c in card_data:
            all_keywords.extend(c["keywords"])

        keyword_freq = {}
        for kw in all_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

        significator_card = params.get("significator", 28)
        significator = LENORMAND_CARDS[(significator_card - 1) % 36]

        grand_tableau = self._generate_grand_tableau(seed)

        houses = {}
        for i, card in enumerate(grand_tableau[:36]):
            houses[i + 1] = card

        symbolic_state = {
            "drawn_cards": card_data,
            "significator": significator,
            "keyword_frequency": keyword_freq,
            "total_keywords": len(all_keywords),
            "unique_keywords": len(set(all_keywords)),
            "grand_tableau_size": len(grand_tableau),
            "houses": {k: v["name"] for k, v in houses.items()},
            "spread_size": spread_size,
        }

        card_ids = [c["id"] for c in card_data]

        numeric_projection = [
            card_ids[0] if card_ids else 0,
            card_ids[1] if len(card_ids) > 1 else 0,
            card_ids[2] if len(card_ids) > 2 else 0,
            card_ids[3] if len(card_ids) > 3 else 0,
            card_ids[4] if len(card_ids) > 4 else 0,
            significator["id"],
            len(card_data),
            sum(card_ids) % 36,
            seed % 1000,
            len(set(card_ids)),
            len(all_keywords),
            len(set(all_keywords)),
        ]

        keyword_diversity = len(set(all_keywords)) / max(len(all_keywords), 1)
        card_diversity = len(set(card_ids)) / max(len(card_ids), 1)

        structural_features = {
            "keyword_diversity": keyword_diversity,
            "card_diversity": card_diversity,
            "significator_position": significator_card,
            "keyword_density": len(all_keywords) / max(spread_size, 1),
            "house_coverage": len(houses) / 36,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _draw_cards(self, seed: int, count: int) -> list[int]:
        h = hashlib.sha256(str(seed).encode()).digest()
        cards = []
        used = set()
        for i in range(count):
            card_id = (h[i % len(h)] + i * 7) % 36 + 1
            attempts = 0
            while card_id in used and attempts < 36:
                card_id = card_id % 36 + 1
                attempts += 1
            cards.append(card_id)
            used.add(card_id)
        return cards

    def _generate_grand_tableau(self, seed: int) -> list[dict]:
        h = hashlib.sha256(f"{seed}_grand_tableau".encode()).digest()
        tableau = []
        used = set()
        for i in range(36):
            idx = (h[i % len(h)] + i * 13) % 36
            attempts = 0
            while idx in used and attempts < 36:
                idx = (idx + 1) % 36
                attempts += 1
            used.add(idx)
            card = LENORMAND_CARDS[idx]
            tableau.append({"id": card["id"], "name": card["name"], "keywords": card["keywords"]})
        return tableau
