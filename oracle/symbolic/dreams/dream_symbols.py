"""Dream symbolics wrapper - extracts symbolic features from dream descriptions."""
import hashlib
import re
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

ARCHETYPES = {
    "shadow": ["dark", "night", "shadow", "black", "hidden", "secret", "hidden", "cave", "underground"],
    "anima_animus": ["woman", "man", "stranger", "lover", "partner", "beloved", "feminine", "masculine"],
    "wise_old": ["elder", "old", "wise", "teacher", "sage", "professor", "guru", "mentor"],
    "trickster": ["clown", "jester", "trickster", "thief", "prankster", "joker", "fool"],
    "rebirth": ["baby", "birth", "egg", "seed", "spring", "dawn", "sunrise", "phoenix"],
    "death": ["death", "die", "dead", "grave", "tomb", "corpse", "funeral", "ending"],
    "hero": ["hero", "warrior", "champion", "battle", "fight", "quest", "journey", "adventure"],
    "great_mother": ["mother", "earth", "nurturing", "comfort", "home", "warmth", "safety"],
}

EMOTIONS = {
    "joy": ["happy", "joy", "delight", "laugh", "smile", "pleasure", "bliss", "euphoria", "ecstasy"],
    "fear": ["afraid", "fear", "terror", "horror", "nightmare", "dread", "panic", "scared", "anxiety"],
    "sadness": ["sad", "cry", "tears", "grief", "loss", "mourn", "sorrow", "melancholy", "depressed"],
    "anger": ["angry", "rage", "fury", "mad", "hate", "violent", "destroy", "furious", "outraged"],
    "surprise": ["surprise", "shock", "unexpected", "amaze", "wonder", "astonish", "stun", "astonished"],
    "disgust": ["disgust", "revolt", "nausea", "vomit", "rotten", "filthy", "putrid", "gross"],
    "love": ["love", "affection", "tender", "embrace", "kiss", "romance", "passion", "desire"],
    "peace": ["calm", "peace", "serene", "tranquil", "quiet", "still", "gentle", "harmony"],
}

ENTITY_CATEGORIES = {
    "animal": ["dog", "cat", "bird", "snake", "horse", "fish", "insect", "spider", "bear", "wolf", "lion", "tiger", "elephant", "dragon"],
    "person": ["man", "woman", "child", "baby", "stranger", "friend", "family", "mother", "father", "brother", "sister"],
    "place": ["house", "room", "forest", "ocean", "mountain", "road", "city", "school", "garden", "cave", "temple"],
    "object": ["car", "phone", "book", "key", "sword", "mirror", "clock", "door", "window", "light", "fire", "water"],
    "nature": ["sun", "moon", "star", "rain", "snow", "wind", "storm", "cloud", "river", "lake", "tree", "flower"],
}


@register_system
class DreamSymbolsWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "dream_symbols"
    LIBRARY_BACKEND = "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        dream_text = params.get("dream_text", entropy_packet.get("dream_text", ""))

        tokens = self._tokenize(dream_text)

        archetype_scores = self._score_archetypes(tokens)
        emotion_scores = self._score_emotions(tokens)
        entities = self._extract_entities(tokens)

        dominant_archetype = max(archetype_scores, key=archetype_scores.get) if archetype_scores else "unknown"
        dominant_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else "neutral"
        dominant_entity_type = max(entities, key=lambda k: len(entities[k])) if entities else "none"

        symbolic_state = {
            "dream_text_length": len(dream_text),
            "token_count": len(tokens),
            "archetype_scores": archetype_scores,
            "emotion_scores": emotion_scores,
            "entities": entities,
            "dominant_archetype": dominant_archetype,
            "dominant_emotion": dominant_emotion,
            "dominant_entity_type": dominant_entity_type,
            "unique_tokens": len(set(tokens)),
            "archetype_count": sum(1 for v in archetype_scores.values() if v > 0),
            "emotion_count": sum(1 for v in emotion_scores.values() if v > 0),
        }

        archetype_vals = list(archetype_scores.values())
        emotion_vals = list(emotion_scores.values())

        numeric_projection = [
            archetype_vals[0] if archetype_vals else 0,
            archetype_vals[1] if len(archetype_vals) > 1 else 0,
            emotion_vals[0] if emotion_vals else 0,
            emotion_vals[1] if len(emotion_vals) > 1 else 0,
            sum(archetype_vals),
            sum(emotion_vals),
            len(tokens),
            len(set(tokens)),
            len(entities.get("animal", [])),
            len(entities.get("person", [])),
            len(entities.get("place", [])),
            seed % 1000,
        ]

        total_tokens = max(len(tokens), 1)
        structural_features = {
            "archetype_density": sum(1 for v in archetype_scores.values() if v > 0) / len(ARCHETYPES),
            "emotion_density": sum(1 for v in emotion_scores.values() if v > 0) / len(EMOTIONS),
            "entity_diversity": sum(len(v) for v in entities.values()) / total_tokens,
            "lexical_diversity": len(set(tokens)) / total_tokens,
            "emotional_intensity": sum(emotion_vals) / max(total_tokens, 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return [t for t in text.split() if len(t) > 1]

    def _score_archetypes(self, tokens: list[str]) -> dict[str, float]:
        scores = {}
        token_set = set(tokens)
        for archetype, keywords in ARCHETYPES.items():
            matches = len(token_set & set(keywords))
            scores[archetype] = matches / max(len(keywords), 1)
        return scores

    def _score_emotions(self, tokens: list[str]) -> dict[str, float]:
        scores = {}
        token_set = set(tokens)
        for emotion, keywords in EMOTIONS.items():
            matches = len(token_set & set(keywords))
            scores[emotion] = matches / max(len(keywords), 1)
        return scores

    def _extract_entities(self, tokens: list[str]) -> dict[str, list[str]]:
        entities = {cat: [] for cat in ENTITY_CATEGORIES}
        token_set = set(tokens)
        for cat, keywords in ENTITY_CATEGORIES.items():
            entities[cat] = list(token_set & set(keywords))
        return entities
