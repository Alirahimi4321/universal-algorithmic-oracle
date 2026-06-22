"""Fortune Telling Core wrapper covering 26 traditions."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system
import hashlib
import math
from typing import Any, Dict, List, Optional

try:
    from fortune_telling_core import RandomRng, ReadingRequest, reading_to_json, Querent
    FORTUNE_CORE_AVAILABLE = True
except ImportError:
    FORTUNE_CORE_AVAILABLE = False

# Traditions that use RNG (drawn from a deck)
DRAWN_TRADITIONS = {
    "tarot", "runes", "geomancy", "iching", "lenormand",
    "celtic_tree", "dominoes", "koyomi", "sukuyo",
}

# Traditions that compute from birth data or text
COMPUTED_TRADITIONS = {
    "numerology", "hebrew_gematria", "tzolkin", "haab",
    "astrology", "can_chi", "chaldean_numerology", "cjk_name_strokes",
    "cyrillic_pythagorean", "cyrillic_slavonic_numerals",
    "four_pillars", "greek_isopsephy", "name_numerology",
    "nine_star_ki", "sanmeigaku", "thaksa", "weton", "zi_wei",
}

# Map tradition names to module paths
TRADITION_MODULES = {
    "tarot": "fortune_telling_core.traditions.tarot",
    "runes": "fortune_telling_core.traditions.runes",
    "geomancy": "fortune_telling_core.traditions.geomancy",
    "iching": "fortune_telling_core.traditions.iching",
    "lenormand": "fortune_telling_core.traditions.lenormand",
    "numerology": "fortune_telling_core.traditions.numerology",
    "hebrew_gematria": "fortune_telling_core.traditions.hebrew_gematria",
    "tzolkin": "fortune_telling_core.traditions.tzolkin",
    "haab": "fortune_telling_core.traditions.haab",
    "astrology": "fortune_telling_core.traditions.astrology",
    "can_chi": "fortune_telling_core.traditions.can_chi",
    "celtic_tree": "fortune_telling_core.traditions.celtic_tree",
    "chaldean_numerology": "fortune_telling_core.traditions.chaldean_numerology",
    "cjk_name_strokes": "fortune_telling_core.traditions.cjk_name_strokes",
    "cyrillic_pythagorean": "fortune_telling_core.traditions.cyrillic_pythagorean",
    "cyrillic_slavonic_numerals": "fortune_telling_core.traditions.cyrillic_slavonic_numerals",
    "dominoes": "fortune_telling_core.traditions.dominoes",
    "four_pillars": "fortune_telling_core.traditions.four_pillars",
    "greek_isopsephy": "fortune_telling_core.traditions.greek_isopsephy",
    "koyomi": "fortune_telling_core.traditions.koyomi",
    "name_numerology": "fortune_telling_core.traditions.name_numerology",
    "nine_star_ki": "fortune_telling_core.traditions.nine_star_ki",
    "sanmeigaku": "fortune_telling_core.traditions.sanmeigaku",
    "sukuyo": "fortune_telling_core.traditions.sukuyo",
    "thaksa": "fortune_telling_core.traditions.thaksa",
    "weton": "fortune_telling_core.traditions.weton",
    "zi_wei": "fortune_telling_core.traditions.zi_wei",
}

# Traditions that require name (instead of just birth_datetime)
NAME_REQUIRED_TRADITIONS = {
    "hebrew_gematria", "chaldean_numerology", "cyrillic_pythagorean",
    "cyrillic_slavonic_numerals", "greek_isopsephy", "name_numerology",
    "cjk_name_strokes",
}


def _hash_text(text: str) -> int:
    """Simple deterministic hash of text to integer."""
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)


def _numerology_number(text: str) -> int:
    """Simple numerology: sum of letter values mod 9."""
    total = sum(ord(c) - 96 for c in text.lower() if c.isalpha())
    while total > 9:
        total = sum(int(d) for d in str(total))
    return total


def _gematria_hebrew(text: str) -> int:
    """Simplified Hebrew gematria (English letters)."""
    mapping = {
        'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7,
        'h': 8, 'i': 9, 'j': 10, 'k': 20, 'l': 30, 'm': 40, 'n': 50,
        'o': 60, 'p': 70, 'q': 80, 'r': 90, 's': 100, 't': 200, 'u': 300,
        'v': 400, 'w': 500, 'x': 600, 'y': 700, 'z': 800,
    }
    return sum(mapping.get(c, 0) for c in text.lower() if c.isalpha())


def _tzolkin_day(text: str) -> int:
    """Simplified Tzolkin day number (1-260)."""
    return _hash_text(text) % 260 + 1


def _haab_month(text: str) -> int:
    """Simplified Haab month (0-18)."""
    return _hash_text(text) % 19


def _iching_hexagram(text: str) -> int:
    """Simplified I Ching hexagram (1-64)."""
    return _hash_text(text) % 64 + 1


def _runes_symbol(text: str) -> int:
    """Simplified rune selection (0-23 Elder Futhark)."""
    return _hash_text(text) % 24


def _geomancy_figure(text: str) -> int:
    """Simplified geomancy figure (0-15)."""
    return _hash_text(text) % 16


def _lenormand_card(text: str) -> int:
    """Simplified Lenormand card (1-36)."""
    return _hash_text(text) % 36 + 1


def _tarot_card(text: str) -> int:
    """Simplified tarot card (0-77)."""
    return _hash_text(text) % 78


def _internal_fallback(question: str, seed: int) -> Dict[str, Any]:
    """Internal fallback computation when fortune_telling_core is not available."""
    h = hashlib.sha256(f"{question}{seed}".encode()).digest()
    results = {}
    results["tarot"] = {"card": _tarot_card(question), "reversed": bool(h[0] % 2)}
    results["runes"] = {"symbol": _runes_symbol(question), "reversed": bool(h[1] % 2)}
    results["geomancy"] = {"figure": _geomancy_figure(question)}
    results["iching"] = {"hexagram": _iching_hexagram(question)}
    results["lenormand"] = {"card": _lenormand_card(question)}
    results["numerology"] = {"life_path": _numerology_number(question)}
    results["hebrew_gematria"] = {"value": _gematria_hebrew(question)}
    results["tzolkin"] = {"day": _tzolkin_day(question)}
    results["haab"] = {"month": _haab_month(question)}
    return results


def _find_deck_and_spread(mod):
    """Find deck and spread objects in a tradition module."""
    deck = None
    spread = None
    
    # Look for attributes ending with _DECK
    for attr_name in dir(mod):
        if attr_name.endswith("_DECK"):
            deck = getattr(mod, attr_name, None)
            if deck is not None:
                break
    if deck is None:
        for attr_name in ["DECK", "DEFAULT_DECK", "deck"]:
            deck = getattr(mod, attr_name, None)
            if deck is not None:
                break
    
    # Look for spread - various naming conventions
    spread_names = [
        "SPREAD", "_SPREAD", "DEFAULT_SPREAD", "spread",
        "SINGLE_CARD", "SINGLE_RUNE", "SINGLE_TILE", "SHIELD",
        "CASTING", "NATAL_CHART", "SIDEREAL_ZODIAC", "TROPICAL_ZODIAC",
    ]
    for attr_name in spread_names:
        spread = getattr(mod, attr_name, None)
        if spread is not None and hasattr(spread, 'id'):
            break
    else:
        # Try any attribute ending with _SPREAD
        for attr_name in dir(mod):
            if attr_name.endswith("_SPREAD"):
                spread = getattr(mod, attr_name, None)
                if spread is not None and hasattr(spread, 'id'):
                    break
    
    return deck, spread


def _make_birth_dt_aware(birth_dt: str) -> str:
    """Ensure birth_datetime is timezone-aware (add +00:00 if missing)."""
    if birth_dt is None:
        return None
    # If already timezone-aware, return as is
    if '+' in birth_dt or birth_dt.endswith('Z') or '-00:00' in birth_dt:
        return birth_dt
    # Add UTC timezone
    return birth_dt + '+00:00'


@register_system
class FortuneTellingCoreWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "fortune_telling_core"
    LIBRARY_BACKEND = "fortune-telling-core" if FORTUNE_CORE_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        question = entropy_packet.get("raw_question", "")
        seed = entropy_packet.get("seed", 0)
        birth_dt = entropy_packet.get("birth_datetime", None)
        
        # Ensure birth_dt is timezone-aware for traditions that need it
        if birth_dt:
            birth_dt = _make_birth_dt_aware(birth_dt)

        results = {}
        if FORTUNE_CORE_AVAILABLE:
            try:
                results = self._compute_with_library(question, seed, birth_dt, params)
            except Exception:
                results = _internal_fallback(question, seed)
        else:
            results = _internal_fallback(question, seed)

        symbolic_state = {
            "question": question,
            "traditions": results,
            "tradition_count": len(results),
        }

        numeric_projection = self._build_numeric_projection(results, seed)
        structural_features = self._build_structural_features(results)

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=results,
            params=params,
        )

    def _compute_with_library(self, question: str, seed: int, birth_dt: Any, params: dict) -> Dict[str, Any]:
        """Use fortune_telling_core library for each tradition."""
        results = {}
        rng = RandomRng(seed=seed)

        for trad_name, module_path in TRADITION_MODULES.items():
            try:
                mod = __import__(module_path, fromlist=["build_engine"])
                if not hasattr(mod, "build_engine"):
                    continue
                engine = mod.build_engine()
                deck, spread = _find_deck_and_spread(mod)
                
                if deck is None or spread is None:
                    continue
                
                # Build querent attributes based on tradition requirements
                attributes = {}
                if birth_dt:
                    attributes["birth_datetime"] = birth_dt
                if trad_name in NAME_REQUIRED_TRADITIONS:
                    # Use question as name for name-based traditions
                    attributes["name"] = question[:50] if question else "Unknown"
                    if trad_name == "cjk_name_strokes":
                        attributes["surname"] = question[:25] if question else "Unknown"
                        attributes["given_name"] = question[25:50] if len(question) > 25 else "Name"
                
                querent = Querent(
                    id="querent",
                    display_name="Querent",
                    attributes=attributes if attributes else None,
                )
                
                request = ReadingRequest(
                    deck_id=deck.id,
                    spread_id=spread.id,
                    querent=querent,
                )
                
                # Use cast if available (no RNG needed), otherwise read
                if hasattr(engine, "cast"):
                    reading = engine.cast(request)
                else:
                    reading = engine.read(request, rng=rng)
                
                results[trad_name] = reading_to_json(reading)
                
            except Exception:
                continue

        if not results:
            results = _internal_fallback(question, seed)

        return results

    def _build_numeric_projection(self, results: dict, seed: int) -> List[float]:
        """Convert tradition results to numeric values."""
        projection = []
        projection.append(float(_hash_text(str(results)) % 1000))
        projection.append(float(seed % 1000))
        
        for trad, data in results.items():
            if isinstance(data, dict):
                for key in ["value", "number", "day", "month", "card", "symbol", "figure", "hexagram", "life_path"]:
                    if key in data:
                        val = data[key]
                        if isinstance(val, (int, float)):
                            projection.append(float(val))
                        break
        
        while len(projection) < 5:
            projection.append(0.0)
        return projection[:10]

    def _build_structural_features(self, results: dict) -> Dict[str, Any]:
        """Extract structural features from results."""
        features = {
            "tradition_count": len(results),
            "has_drawn": any(trad in DRAWN_TRADITIONS for trad in results),
            "has_computed": any(trad in COMPUTED_TRADITIONS for trad in results),
        }
        numeric_count = 0
        symbolic_count = 0
        for trad, data in results.items():
            if isinstance(data, dict):
                if any(isinstance(v, (int, float)) for v in data.values()):
                    numeric_count += 1
                else:
                    symbolic_count += 1
        features["numeric_tradition_count"] = numeric_count
        features["symbolic_tradition_count"] = symbolic_count
        return features