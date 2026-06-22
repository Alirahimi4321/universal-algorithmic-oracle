"""CLI Tarot wrapper — simple tarot card meanings."""
import logging
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

HAS_CLI_TAROT = False
try:
    from cli_tarot import card_meanings, readings
    HAS_CLI_TAROT = True
except ImportError:
    pass


@register_system
class CliTarotWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "cli_tarot"
    LIBRARY_BACKEND = "cli_tarot"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not HAS_CLI_TAROT:
            return self._build_output({}, [], {"error": "cli_tarot not installed"})

        card_index = int(entropy_packet.get("seed", entropy_packet.get("timestamp", 0))) % 78
        all_meanings = card_meanings.meanings
        total_cards = len(all_meanings)

        idx = card_index % total_cards
        meaning_text = all_meanings.get(idx, "No meaning available")
        keywords = []
        for line in str(meaning_text).split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("• "):
                keywords.append(line[2:])

        numeric = [float(idx), float(total_cards), float(len(keywords))]

        return self._build_output(
            symbolic_state={
                "card_index": idx,
                "meaning": str(meaning_text)[:500],
                "keywords": keywords[:10],
                "total_cards": total_cards,
            },
            numeric_projection=numeric,
            structural_features={
                "card_index": idx,
                "num_keywords": len(keywords),
            },
        )
