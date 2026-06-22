"""Norse Runes wrapper using riimut."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from riimut import elder_futhark, younger_futhark, futhorc, medieval_futhork, staveless_futhark
    RIIMUT_AVAILABLE = True
except ImportError:
    RIIMUT_AVAILABLE = False

RUNE_SYSTEMS = {
    "elder_futhark": ("elder_futhark", 24),
    "younger_futhark": ("younger_futhark", 16),
    "futhorc": ("futhorc", 29),
    "medieval_futhork": ("medieval_futhork", 26),
    "staveless_futhark": ("staveless_futhark", 16),
}


@register_system
class RiimutWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "norse_runes"
    LIBRARY_BACKEND = "riimut"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)
        system = params.get("rune_system", "elder_futhark")

        results = {}
        if RIIMUT_AVAILABLE:
            for name, (module_name, count) in RUNE_SYSTEMS.items():
                try:
                    mod = {"elder_futhark": elder_futhark, "younger_futhark": younger_futhark,
                           "futhorc": futhorc, "medieval_futhork": medieval_futhork,
                           "staveless_futhark": staveless_futhark}[module_name]
                    runes_str = mod.letters_to_runes(text)
                    back = mod.runes_to_letters(runes_str)
                    results[name] = {
                        "runes": runes_str,
                        "reversed": back,
                        "rune_count": len(runes_str),
                        "alphabet_size": count,
                    }
                except Exception:
                    results[name] = {"runes": "", "reversed": "", "rune_count": 0, "alphabet_size": count}
        
        primary = results.get(system, results.get("elder_futhark", {}))
        rune_count = primary.get("rune_count", 0)
        unique_runes = len(set(primary.get("runes", "")))

        symbolic_state = {
            "input": text,
            "primary_system": system,
            "results": results,
            "primary_runes": primary.get("runes", ""),
        }
        numeric_projection = [
            rune_count, unique_runes, len(text),
            hash(primary.get("runes", "")) % 1000,
            seed % 1000,
        ] + [results.get(s, {}).get("rune_count", 0) for s in RUNE_SYSTEMS]
        structural_features = {
            "systems_available": len(results),
            "rune_diversity": unique_runes / max(rune_count, 1),
            "text_length": len(text),
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
